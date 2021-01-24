/*
**IPC hw1 client
**version 1
**date: 2020/10/10
*/
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h> 
#include <arpa/inet.h>
#include <string.h>
#include <unistd.h> 

#define MAXLINE 1024 // max text line length

struct message{
    uint16_t length;
	int num;
    char msg[MAXLINE];
};

// split the string depending on spl
int split(char dst[][80], char* str, const char* spl){
    int n = 0;
    char *result = NULL;
    result = strtok(str, spl);
    while( result != NULL ){
        strcpy(dst[n++], result);
        result = strtok(NULL, spl);
    }
    return n;
}

void error(char* msg){
	perror(msg);
	exit(1);
}

int main(int argc, char *argv[]){
	
	if (argc !=3)
        error("Usage: TCPClient <IP address of the server> <Port number of the server>\n");
	
    int tcp_fd, udp_port, udp_fd;
	int serv_port = atoi(argv[2]); // convert the port number from string to int
    struct sockaddr_in serv_addr;
	struct hostent *server;
	struct message msg, close_msg;
	int random_gen_num = 0;
	socklen_t servlen;

	// 1. socket()
    tcp_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (tcp_fd < 0) 
        error("ERROR on opening socket");
	
    server = gethostbyname(argv[1]);
    if (server == NULL) {
        fprintf(stderr,"ERROR, no such host\n");
        exit(0);
    }
	
    bzero((char *) &serv_addr, sizeof(serv_addr));
    serv_addr.sin_family = AF_INET;
    bcopy((char *)server->h_addr, 
         (char *)&serv_addr.sin_addr.s_addr,
         server->h_length);
    serv_addr.sin_port = htons(serv_port);
	
	// 2. connetc()
    if ( connect( tcp_fd, (struct sockaddr *) &serv_addr, sizeof(serv_addr)) < 0) 
        error("ERROR connecting");
	
	// receive the welcome txt
	char wel_txt[100];
	if (recv( tcp_fd, &wel_txt, sizeof(wel_txt), 0) == 0)
        error("The server terminated prematurely\n");
	printf("%s", wel_txt);

	/* UDP */
	//  tcp received msg.type 2, and receive udp_port of msg.length
	if ( recv( tcp_fd, &msg, sizeof(msg), 0) == 0)
		error("The server terminated prematurely\n");
	// else
		// printf("udp_port: %d", msg.num); // for debug of the udp port transport
	udp_port = msg.num;
	
	// 1. create socket()
	if ( (udp_fd = socket (AF_INET, SOCK_DGRAM, 0)) <0)
		error("ERROR on creating udp socket\n");
	servlen = sizeof(serv_addr);
	serv_addr.sin_port = htons(udp_port);

	for( ; ; ){
		// to get the command 
		printf("\%% ");
		fgets(msg.msg, sizeof(msg.msg), stdin);
		msg.length = strlen(msg.msg);
		msg.msg[msg.length-1]='\0';
		strcpy(close_msg.msg, "close");
		char split_msg[4][80] = {0};
		char copy_msg[80] = {0};
		strcpy(copy_msg, msg.msg);
		int cnt = split(split_msg, copy_msg, " ");
		// printf("msg test: %s\n", msg.msg);
		// handle the different command
		if ( strcmp("register", split_msg[0])==0 ){
			send( tcp_fd, &close_msg, sizeof(close_msg), 0);
			sendto(udp_fd, &msg, sizeof(msg), 0,(struct sockaddr *)&serv_addr, sizeof(serv_addr));
			recvfrom(udp_fd,&msg,sizeof(msg),0,(struct sockaddr *)&serv_addr, &servlen);
			printf("%s\n", msg.msg);
		} 	else if ( strcmp("whoami", msg.msg)==0 ){
			send( tcp_fd, &close_msg, sizeof(close_msg), 0);
			if (random_gen_num)
				msg.num = random_gen_num;
			sendto(udp_fd, &msg, sizeof(msg), 0,(struct sockaddr *)&serv_addr, sizeof(serv_addr));
			recvfrom(udp_fd,&msg,sizeof(msg),0,(struct sockaddr *)&serv_addr, &servlen);
			printf("%s\n", msg.msg);
		} 	else if ( strcmp("login", split_msg[0])==0 ) {
			send( tcp_fd, &msg, sizeof(msg), 0);
			recv( tcp_fd, &msg, sizeof(msg), 0);
			printf("%s\n", msg.msg);
			random_gen_num = msg.num;
			sendto(udp_fd, &close_msg, sizeof(close_msg), 0,(struct sockaddr *)&serv_addr, sizeof(serv_addr));
		}  	else if ( strcmp("logout", msg.msg)==0) {
			send( tcp_fd, &msg, sizeof(msg), 0);
			recv( tcp_fd, &msg, sizeof(msg), 0);
			printf("%s\n", msg.msg);
			random_gen_num = 0;
			sendto(udp_fd, &close_msg, sizeof(close_msg), 0,(struct sockaddr *)&serv_addr, sizeof(serv_addr));
		}	else if ( strcmp("list-user", msg.msg)==0) {
			send( tcp_fd, &msg, sizeof(msg), 0);
			recv( tcp_fd, &msg, sizeof(msg), 0);
			printf("Name\tEmail\n");
			char split_msg[30][80] = {0};
			int cnt = split(split_msg, msg.msg, " ");
			for(int i=1, j=0; i<=msg.num; i++, j+=2)
				printf("%s\t%s\n", split_msg[j], split_msg[j+1]);
			sendto(udp_fd, &close_msg, sizeof(close_msg), 0,(struct sockaddr *)&serv_addr, sizeof(serv_addr));
		}	else if (strcmp("exit", msg.msg)==0 ){
			send( tcp_fd, &msg, sizeof(msg), 0);
			goto stop;
		}	else 
			printf("Don't have this command\n");
	}
	stop:
    return 0;
}
/*
**IPC hw1 server
**version 1
**date: 2020/10/15
*/
#include <stdio.h> // for the input and output of c program
#include <sys/types.h> // a number of data types used in system calls
#include <sys/socket.h> // a number of definitions of structures needed for sockets.
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h> 
#include <sqlite3.h> // to use database to store account

#define MAXLINE 1024 // max text line length*

struct message{
    uint16_t length;
	int num;
    char msg[MAXLINE];
};

// for the sql to print out some message
static int callback( void *NotUsed, int argc, char *argv[], char *azColName[]){
	for( int i=0; i<argc; i++){
		printf("%s = %s\n", azColName[i], argv[i] ? argv[i] : "NULL");
	}
	printf("\n");
	return 0;
}

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

	// detect whether the port number is been input
	if (argc < 2)
		error("Usage: TCPServer<Port number of the server>\n");
	
	int serv_fd, cli_tcp_fd, cli_udp_fd;
	int serv_port = atoi(argv[1]); // convert port from string to int
	char buf[256];
	struct sockaddr_in serv_addr, cli_addr; // to define an endpoint address
	struct message msg, msg_tcp, msg_udp;
	pid_t childpid;
    socklen_t cli_len;
	int cli_num = 0; // to count on how many client have been connected
	int is_login = 0; // detect whether is login or not, not login == 0, login == 1
	int random_gen_num = 0; // the login randomly generated number as the identificaiton for the subsequent udp command whoami
	char username[100]; // to store the username of the login account
	
	// initialize the database variables
	sqlite3 *db;
	char *zErrMsg = 0;
	int rc;
	char *sql;
	
	// open the database
	rc = sqlite3_open("server_account.db", &db);
	if(rc){
		fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
		exit(0);
	} else 
		fprintf(stdout, "Opened database successfully\n");
	
	// Create SQL statement
	sql = "CREATE TABLE USERS(" \
		"UID INTEGER PRIMARY KEY AUTOINCREMENT," \
		"Username TEXT NOT NULL UNIQUE," \
		"Email TEXT NOT NULL,"\
		"Password TEXT NOT NULL);";
		
	// Execute SQL statement
	rc = sqlite3_exec(db, sql, callback, 0, &zErrMsg);
	if( rc != SQLITE_OK){
		fprintf(stderr, "SQL error: %s\n", zErrMsg);
		sqlite3_free(zErrMsg);
	} else
		fprintf(stdout, "SQL table created successfully\n");

	printf("Waiting the client to connect... \n");
	// 1. create a TCP socket for server
	if ( (serv_fd = socket (AF_INET, SOCK_STREAM, 0)) <0) // return -1 for erorr 0, 0 for correct
        error("ERROR on creating tcp socket\n");
	serv_addr.sin_family = AF_INET;
    serv_addr.sin_addr.s_addr = INADDR_ANY;
    serv_addr.sin_port = htons(serv_port); // networtk byte is big-endian, so we use htons to convert the port format
	
	// 2. bind() service identifier, port number
	if ( bind( serv_fd, (struct sockaddr*) &serv_addr, sizeof(serv_addr)) <0)
        error("ERROR on binding to tcp socket\n");

	// 3. listen() waits for the client to connect, convert the unconnected TCP socket to passive mode
    if ( listen(serv_fd, 30) <0 ) // backlog max is 128
		error("ERROR on listening on tcp socket\n");
	
	
    printf("Client No \tChild PID \tClient IP \tTCP/UDP \tClient Port \tAdditional Information\n");
    printf("-------------------------------------------------------------------------------------------------------------------\n");
    for ( ; ; ){
		cli_num++;
        if ( (childpid = fork ()) == 0 ){  //Child process using fork to implement 
			// 4. accept() to accept a connection
			cli_len = sizeof(cli_addr);
			cli_tcp_fd = accept(serv_fd, (struct sockaddr *) &cli_addr, &cli_len);
			if( cli_tcp_fd < 0)
				error("ERROR on accept");	
			
			// to print the welcome txt
			char wel_txt[] = 
				"********************************\n**"
				"Welcome to the BBS server. **\n"
				"********************************\n";
			send( cli_tcp_fd, &wel_txt, sizeof(wel_txt), 0);
			
			printf("New Connection.\n");
			// to create a UDP connection
			// 1. socket() 
			serv_addr.sin_port = htons(0);
			if ( (cli_udp_fd = socket(AF_INET, SOCK_DGRAM, 0)) <0 ) // udp connect
				error("ERROR on creating udp socket\n");
			// 2. bind()
			if ( bind( cli_udp_fd, (struct sockaddr *) &serv_addr, sizeof(serv_addr))<0)
				error("ERROR on binding to udp socket\n");
			
			struct sockaddr_in localAddress;
			socklen_t addressLength = sizeof(localAddress);
			getsockname( cli_udp_fd, (struct sockaddr*)&localAddress, &addressLength);
			printf("%d\t\t%d\t\t%s\t---\t\t%d\t\tUDP Port Assigned:\t  %d\n", cli_num, getpid(), inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), (int) ntohs(localAddress.sin_port));
			// send udp port 
			msg.num = (int)ntohs(localAddress.sin_port);
			send(cli_tcp_fd, &msg, sizeof(msg), 0);
			printf("Receiving... \n");

			for( ; ; ){
				// tcp case
				if( recv( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0) > 0){	
					printf("%d\t\t%d\t\t%s\tTCP\t\t%d\t\tReceived Message:\t  %s\n", cli_num, getpid(), inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), msg_tcp.msg);
					char tcp_split_msg[3][80] = {0}; // remember to clear the string! It's very important!!
					int cnt = split(tcp_split_msg, msg_tcp.msg, " ");
					// the login situation
					if (  strcmp("login", tcp_split_msg[0])==0 ){
						// if the format is wrong 
						if( strlen(tcp_split_msg[1])==0 || strlen(tcp_split_msg[2])==0 ){
							strcpy(msg_tcp.msg, "Usage: login <username> <password>");
							send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
						} else{
							// the format is correct
							// if it has already login
							if ( is_login == 1 ){
								strcpy(msg_tcp.msg, "Please logout first.");
								send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
							} else{
								// it hasn't login
								char sql_select[] = "select * from USERS where Username == '";
								strcat( sql_select, tcp_split_msg[1]);
								strcat( sql_select, "'");
								char** pResult;
								int nRow;
								int nCol;
								rc = sqlite3_get_table(db, sql_select, &pResult, &nRow, &nCol, &zErrMsg);
								if ( nRow == 0 ){
									printf("No this user!\n");
									strcpy(msg_tcp.msg, "Login failed.");
									send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
								}
								else{
									char name[100];
									strcpy( name, pResult[nCol+1]);
									char password[100];
									strcpy( password, pResult[nCol+3]);
									printf("Tests: %s\n", password); // to print the account password 
									// if the username exist, username = pResult[nCol+1], password = pResult[nCol+3]
									if( rc != SQLITE_OK ){
										fprintf(stderr, "SQL error: %s\n", zErrMsg);
										sqlite3_free(zErrMsg);
									}else{
										fprintf(stdout, "Operation done successfully\n");
									}
									// if the username and password are all correct
									if( strcmp(tcp_split_msg[1],  name)==0 && strcmp(tcp_split_msg[2], password)==0 ){
										printf("The username and password are all correct\n");
										strcpy( username, name); // if use strcpy at an empty char* it will have bug!!!
										strcpy(msg_tcp.msg, "Welcome, ");
										strcat(msg_tcp.msg, name);
										strcat(msg_tcp.msg, ".");
										msg_tcp.num = rand();
										random_gen_num = msg_tcp.num;
										send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
										is_login = 1;
									} else{
										strcpy(msg_tcp.msg, "Login failed.");
										send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
									}
								}
							}
						}
					} else if ( strcmp("logout", tcp_split_msg[0])==0 ){
						if ( is_login != 0 ){
							strcpy(msg_tcp.msg, "Bye, ");
							strcat(msg_tcp.msg, username);
							strcat(msg_tcp.msg, ".");
							send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
							random_gen_num = 0;
							memset(username, '\0', sizeof(username));
							is_login = 0;
						} else {
							strcpy(msg_tcp.msg, "Please login first.");
							send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
						}						
					} else if ( strcmp("list-user", tcp_split_msg[0])==0 ){
						printf("List-User still waiting for building\n");
						char sql_select[] = "select * from USERS";
						char** pResult;
						int nRow;
						int nCol;
						rc = sqlite3_get_table(db, sql_select, &pResult, &nRow, &nCol, &zErrMsg);
						int idx = 0;
						msg_tcp.num = nRow;
						for(int i=1; i<=nRow; i++){
							if(i==1)
								strcpy(msg_tcp.msg, pResult[nCol*i+1]);
							else
								strcat(msg_tcp.msg, pResult[nCol*i+1]);
							strcat(msg_tcp.msg, " ");
							strcat(msg_tcp.msg, pResult[nCol*i+2]);
							strcat(msg_tcp.msg, " ");
						}
						printf("%s\n", msg_tcp.msg);
						send( cli_tcp_fd, &msg_tcp, sizeof(msg_tcp), 0);
					} else if ( strcmp("exit", tcp_split_msg[0])==0 ){
						goto stop;
					}
				}
				printf("tcp receive done\n");
				
				// udp case
				if ( recvfrom(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0, (struct sockaddr*) &cli_addr, &cli_len) > 0 ) {
					msg_udp.msg[msg_udp.length]='\0';
					printf("%d\t\t%d\t\t%s\tUDP\t\t%d\t\tReceived Message:\t  %s\n", cli_num, getpid(), inet_ntoa(cli_addr.sin_addr), ntohs(cli_addr.sin_port), msg_udp.msg);
					// the command of the whoami
					if (  strcmp("whoami", msg_udp.msg)==0 ){
						if ( is_login==1){
							strcpy( msg_udp.msg, username);
							sendto(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0,(struct sockaddr *)&cli_addr, cli_len);
						} else{
							strcpy( msg_udp.msg, "Please login first.");
							sendto(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0,(struct sockaddr *)&cli_addr, cli_len);
						}
					} 	
					else{
						// the command of the register
						// split the string to get the four sub-string
						char reg_msg[4][80]= {0};
						int cnt = split(reg_msg, msg_udp.msg, " ");
						// if the first sub-string is not "register" than continue
						if( strcmp("register", reg_msg[0] ))
							continue;
						
						// the string of the SQLite insertion
						char reg_store[] = "INSERT INTO USERS (Username, Email, Password) VALUES (";
						for( int i = 1; i < cnt; i++){
							strcat( reg_store, "'");
							strcat( reg_store, reg_msg[i]);
							strcat( reg_store, "'");
							if ( i != cnt-1 )
								strcat( reg_store, ",");
						}
						strcat( reg_store, ");");
						// printf("test sql: %s\n", reg_store); // for the SQL insertion debug
						
						// return the situation base on the SQLITE insertion result
						rc = sqlite3_exec(db, reg_store, callback, 0, &zErrMsg);
						if( rc != SQLITE_OK){
							fprintf(stderr, "SQL error: %s\n", zErrMsg);
							if( !strcmp("column Username is not unique", zErrMsg)){
								strcpy( msg_udp.msg, "Username is already used.");
								sendto(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0,(struct sockaddr *)&cli_addr, cli_len);
							} else{
								strcpy( msg_udp.msg, "Usage: register <username> <email> <password>");
								sendto(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0,(struct sockaddr *)&cli_addr, cli_len);
							}
							sqlite3_free(zErrMsg);
						} else{
							fprintf(stdout, "SQL Records created successfully\n");
							strcpy( msg_udp.msg, "Register successfully.");
							sendto(cli_udp_fd, &msg_udp, sizeof(msg_udp), 0,(struct sockaddr *)&cli_addr, cli_len);
						}
					}
				}
				printf("udp receive done\n");
				fflush(stdout);
			}
        }
    }
	stop:
	close(cli_udp_fd);
	close(cli_tcp_fd);
	sqlite3_close(db);
	return 0;
}
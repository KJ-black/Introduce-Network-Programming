import sys # to use the argv
import socket 
close_recv = "close" # to close the unuse recv
if __name__ == "__main__":
    ## the host and service
    if len(sys.argv) != 3:
        sys.exit("iter_tcp_client.py {host} {portnumber}")
    else:
        port = int(sys.argv[2])
        host = sys.argv[1]
    addr = (host, port)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(addr)
    user =""
    # recv welcome
    wel = str(s.recv(1024), encoding='utf-8')
    print(wel)


    while True:
        cmd = input("% ")
        # print("Test input: %s" % cmd)
        if user =="":
            s.sendall(cmd.encode())
            msg = str(s.recv(1024), encoding='utf-8')
            if "Welcome" in msg:
                user = cmd
            print(msg)
        elif cmd=="exit":
            s.sendall(cmd.encode())
            msg = str(s.recv(1024), encoding='utf-8')
            print(msg)
            break
        elif cmd == "list-users" or cmd == "sort-users":
            s.sendall(cmd.encode())
            msg = str(s.recv(1024), encoding='utf-8')
            print(msg)

    s.close()
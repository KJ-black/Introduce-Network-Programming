#!/usr/bin/python
#coding=utf-8
import sys # argv
import socket # socket
import os # fork, _exit(0)
import select
import queue

client_num = 0
clients = []
userIDs = []

def method(conn, u):
    # variable
    id = client_num
    if_login = False
    
    # welcome 
    welcome = "********************************\n"+\
                    "** Welcome to the BBS server. **\n"+\
                    "********************************"
    conn.sendall(welcome.encode())
    
    while True:
        #tcp
        data = str(conn.recv(1024), encoding='utf-8')
        print("%d TCP recv: %s" % (id, data))
        if data == "exit":
            break
        elif "login" in data:
            data = data.split()
            if len(data)!=3:
                msg = "login <username> <password> "
            elif if_login:
                msg = "Please logout first"	
            else:
                sql = "select * from users where Username == '%s'"%data[1]
                cursor.execute(sql)
                rows = cursor.fetchall()
                if len(rows)!=0:
                    for row in rows:
                        if row[3]==data[2]:
                            msg = "Welcome, %s."%data[1]
                            user = data[1]
                            if_login = True
                    if if_login!=True:
                        msg = "Login failed"
                else:
                    msg = "Login failed"
            conn.sendall(msg.encode())
        elif data == "logout":
            if if_login == False:
                msg = "Please login first."
            else:
                if_login = False
                msg = "Bye, %s."%user
            conn.sendall(msg.encode())
        elif data == "list-user":
            sql = "select * from users"
            cursor.execute(sql)
            rows = cursor.fetchall()
            msg = "Name\tEmail"
            for row in rows:
                msg += '\n'
                msg += row[1]
                msg += '\t'
                msg += row[2]
            conn.sendall(msg.encode())

if __name__ == "__main__":
    ## the host and service
    if len(sys.argv) != 2:
        sys.exit("iter_tcp_server.py {portnumber} ")
    else:
        port = int(sys.argv[1])
    host = "127.0.0.1"
    addr = (host, port)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(addr)
    server.listen(15) # at least 10 client
    
    inputs = [server]
    outputs = []
    message_queues = {}	


    # print("Wait for connection... ")
    while inputs:
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs)
        for s in readable:
            if s is server:
                conn, addr = s.accept()
                client_num += 1
                conn.setblocking(0)
                clients.append([conn, "", addr])
                welcome = "Hello, please assign your username: "
                print("New connection from %s:%s "%(addr[0], addr[1]))
                inputs.append(conn)
                message_queues[conn] = queue.Queue()
                message_queues[conn].put(welcome)
                if conn not in outputs:
                    outputs.append(conn)
            else:
                data = str(s.recv(1024), encoding='utf-8')
                # print("%d TCP recv: %s" % (id, data))
                for item in clients:
                        if s in item: 
                            userID = item[1]
                            c_addr = item[2]
                            break
                
                if data:
                    if userID == "":
                        if data not in userIDs:  
                            userIDs.append(data)    
                            userID = data
                            for item in clients:
                                    if s in item:
                                        item[1] = data
                                        break
                            msg = "Welcome, %s"%userID
                        else:
                            msg = "The username is already used!"
                    else:
                        if data == "list-users":
                            msg = ""
                            first = True
                            for item in clients:
                                if first:
                                    first  = False
                                    if item[1] != "":
                                        msg += "%s %s:%s"%(item[1], item[2][0], item[2][1])
                                else:
                                    if item[1] != "":
                                        msg += "\n%s %s:%s"%(item[1], item[2][0], item[2][1])
                        elif data == "sort-users":
                            msg =""
                            clients = sorted(clients, key=lambda item:item[1])
                            first = True
                            for item in clients:
                                if first:
                                    first  = False
                                    if item[1] != "":
                                        msg += "%s %s:%s"%(item[1], item[2][0], item[2][1])
                                else:
                                    if item[1] != "":
                                        msg += "\n%s %s:%s"%(item[1], item[2][0], item[2][1])

                    if data == "exit":
                        msg = "Bye, %s"%userID
                
                    message_queues[s].put(msg)
                    if s not in outputs:
                        outputs.append(s)
                
                # no message receive
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del message_queues[s]
        #writable
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                outputs.remove(s)
            else:
                s.sendall(next_msg.encode())
                if "Bye" in next_msg:
                    if s in outputs:
                        outputs.remove(s)
                        inputs.remove(s)
                        for item in clients:
                            if s in item:
                                userIDs.remove(item[1])
                                clients.remove(item)
                        s.close()
                        del message_queues[s]
                        for item in clients:
                            if s in item: 
                                userID = item[1]
                                c_addr = item[2]
                                break
                        print("%s %s:%s disconnected"%(userID, c_addr[0], c_addr[1]))


        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

    s.close()
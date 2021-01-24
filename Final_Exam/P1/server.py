#!/usr/bin/python
#coding=utf-8
# version=2020/11/22
# select tcp server
import sys # argv
import socket, select, queue # socket
import os # fork, _exit(0)
import sqlite3 # database
import threading # threading
import queue # for the queue threading
import datetime

client_num = -1
client = [] # the login statu		

## date
today = str(datetime.date.today()).split("-")
date = (today[1]+'/'+today[2])

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
    client_name = None

    print("Wait for connection... ")
    while inputs:
        readable, writable, exceptional = select.select(
            inputs, outputs, inputs)
        ## readable
        for s in readable:
            if s is server:
                conn, addr = s.accept()
                # welcome 
                client_num += 1
                # conn, addr, client_num, mute
                client.append([conn, addr, "user%d"%client_num, False])
                welcome = "********************************\n"+\
                                "** Welcome to the TCP server. **\n"+\
                                "********************************\n"+\
                                "Welcome, user%d."%client_num
                print("New connection from %s:%s user%d"%(addr[0], addr[1], client_num))
                conn.setblocking(0)
                inputs.append(conn)
                message_queues[conn] = queue.Queue()
                message_queues[conn].put(welcome)
                if conn not in outputs:
                    outputs.append(conn)
            else:
                data = str(s.recv(1024), encoding='utf-8')
                # print("TCP recv: %s" % ( data))
                for item in client:
                    if s in item:
                        client_mute = item[3]
                        client_name = item[2]
                        client_addr = item[1]
                        break
                if data:
                    ## handle the comment
                    if data == "exit":
                        print("Client %s %s:%s disconnected"%(client_name, client_addr[0], client_addr[1]))
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        del message_queues[s]

                    elif data == "mute":
                        # Fail: You are already in mute mode.
                        if client_mute:
                            message = "You are already in mute mode."
                        # Success: Mute mode.
                        else:
                            for item in client:
                                if s in item:
                                    item[3] = True
                                    break
                            message = "Mute mode."
                        message_queues[s].put(message)
                        if s not in outputs:
                            outputs.append(s)

                    elif data == "unmute":
                        # Success: Unmute mode.
                        if client_mute:
                            message = "Unmute mode."
                            for item in client:
                                if s in item:
                                    item[3] = False
                                    break
                        # Fail: You are already in unmute mode.
                        else:
                            message = "Your are already in unmute mode."
                        message_queues[s].put(message)
                        if s not in outputs:
                            outputs.append(s)

                    elif "yell" in data:
                        try:
                            if data[4]!=" ":
                                pass
                        except:
                            message = "yell <message>"
                            message_queues[s].put(message)
                            if s not in outputs:
                                outputs.append(s)
                        try:
                            # Success <username>: <message>
                            s_msg = data.split()[1:]
                            message = data[5:]
                            print("DEBUG for message: %s"%message)
                            send_msg = "%s: %s"%(client_name, message)
                            for item in client:
                                if s not in item and item[3] == False:
                                    message_queues[item[0]].put(send_msg)
                                    if item[0] not in outputs:
                                        outputs.append(item[0])
                        except:
                            # Comment: yell <message>
                            message = "yell <message>"
                            message_queues[s].put(message)
                            if s not in outputs:
                                outputs.append(s)
                    
                    elif "tell" in data:
                        try:
                            receiver = data.split()[1]
                            message = data[5:]
                            message = message[message.find(" ")+1:]
                            print("DEBUG for message: %s"%message)
                            send_msg = "%s told you: %s"%(client_name, message)
                            done = False
                            for item in client:
                                if s not in item and receiver == item[2] and item[3] == False:
                                    # Success <sender> told you: <message>
                                    message_queues[item[0]].put(send_msg)
                                    if item[0] not in outputs:
                                        outputs.append(item[0])
                                    done = True
                                    break
                            if done == False:
                                # Fail: <receiver> does not exist.
                                message = "%s does not exit"%receiver
                                message_queues[s].put(message)
                                if s not in outputs:
                                    outputs.append(s)
                        except:
                            # Comment: tell <receiver> <message>
                            message = "tell <receiver> <message>"
                            message_queues[s].put(message)
                            if s not in outputs:
                                outputs.append(s)

                # no message receive
                else:
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()
                    del message_queues[s]
        
        ## writable 
        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                outputs.remove(s)
            else:
                # s.send(next_msg)
                s.sendall(next_msg.encode())

        ## exceptional
        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]
    
    s.close()
    cursor.close()
    sql_conn.close()
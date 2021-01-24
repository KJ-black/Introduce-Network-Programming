import sys # to use the argv
import socket 

## the host and service
if len(sys.argv) != 3:
    sys.exit("client.py {host} {portnumber}")
else:
    port = int(sys.argv[2])
    host = sys.argv[1]
addr = (host, port)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    cmd = input("% ")
    if cmd == "exit":
        break
    elif "send-file" in cmd:
        s.sendto("send-file".encode(), addr)
        cmd = cmd.split()
        filename = []
        filedata = []
        try:
            for i in range(1, len(cmd)):
                filename.append(cmd[i])
            for i in range(len(filename)):
                try:
                    filedata.append(open(filename[i]))
                except:
                    print("%s file doesn't exit!"%filename[i])
            for i in range(len(filedata)):
                s.sendto(filename[i].encode(), addr)
                str_file = ""
                print(filedata[i])
                for line in filedata[i]:
                        str_file += line 
                print(str_file)
                s.sendto(str_file.encode(), addr)
            s.sendto("done".encode(), addr)
        except:
            pass
s.close()
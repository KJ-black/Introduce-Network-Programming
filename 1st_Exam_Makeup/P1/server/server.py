import sys # to use the argv
import socket 

## the host and service
if len(sys.argv) != 2:
    sys.exit("server.py {portnumber} ")
else:
    port = int(sys.argv[1])
host = "127.0.0.1"
addr = (host, port)

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(addr)

print("Waiting udp data...")
while True:
    data, addr = s.recvfrom(1024)
    if str(data, encoding='utf-8') == "send-file":
        print("Saving file...")
        while True:
            file_name, addr = s.recvfrom(1024)
            if str(file_name, encoding='utf-8')  == "done":
                print("Save done!")
                break
            file_data, addr = s.recvfrom(1024)
            print("File name: %s"%str(file_name, encoding='utf-8'))
            with open(file_name, 'w') as f:
                print(str(file_data, encoding='utf-8'), file=f)
            
        

s.close()
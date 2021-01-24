# version=2020/11/19
import sys # to use the argv
import socket 
close_recv = "close" # to close the unuse recv

def command(cmd, s, addr):
	# use tcp
	if "deposit" in cmd or "withdraw" in cmd or cmd=="show-accounts":
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)

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

	# recv welcome
	wel = str(s.recv(1024), encoding='utf-8')
	print(wel)
	
	while True:
		cmd = input("")
		# print("Test input: %s" % cmd)
		
		if cmd=="exit":
			s.sendall(cmd.encode())
			break
		else:
			command(cmd, s, addr)
	s.close()
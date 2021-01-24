# version=2020/11/19
import sys # to use the argv
import socket 
close_recv = "close" # to close the unuse recv

def command(cmd, s, u, addr):
	
	# use udp
	"""
	if "register" in cmd or cmd == "whoami":
		s.sendall(close_recv.encode())
		u.sendto(cmd.encode(), addr)
		data, _ = u.recvfrom(1024)
		print(str(data, encoding='utf-8'))
	"""
	if "register" in cmd:
		s.sendall(cmd.encode())
		# u.sendto(close_recv.encode(), addr)
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
	# use tcp
	elif "login" in cmd or cmd == "logout" or cmd=="list-user":
		s.sendall(cmd.encode())
		# u.sendto(close_recv.encode(), addr)
		data = str(s.recv(1024), encoding='utf-8')
		print(data)

	## hw2 command
	elif "create-board" in cmd or "create-post" in cmd or "list-board" in cmd \
		or "list-post" in cmd or "read" in cmd or "delete-post" in cmd or "update-post" in cmd \
		or "comment" in cmd:
		s.sendall(cmd.encode())
		# u.sendto(close_recv.encode(), addr)
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
	u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(addr)

	# recv welcome
	wel = str(s.recv(1024), encoding='utf-8')
	print(wel)
	
	while True:
		cmd = input("% ")
		# print("Test input: %s" % cmd)
		
		if cmd=="exit":
			s.sendall(cmd.encode())
			break
		else:
			command(cmd, s, u, addr)
	u.close()
	s.close()
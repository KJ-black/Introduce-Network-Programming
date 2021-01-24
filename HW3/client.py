#!/usr/bin/python
# version=2020/12/16
import sys # to use the argv
import socket, select
import os
import queue # for the queue threading
import time
import datetime

import tty
import termios
user = ""
status = ""
chat_addr = ()
owner_chat_addr = ()

"""
How to use NonBlockingConsole:
with NonBlockingConsole() as nbc:
	while True:
		nbc.get_data() # to get the console input nonblockingly
"""
class NonBlockingConsole(object):
	
	def __enter__(self):
		self.old_settings = termios.tcgetattr(sys.stdin)
		tty.setcbreak(sys.stdin.fileno()) # sys.stdin.fileno() == 0 ( stdout == 1, stderr == 2)
		return self

	def __exit__(self, type, value, traceback):
		termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)


	def get_data(self):
		if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
			return sys.stdin.read(1)
		return False

## struct structure
class log:
	#__slots__ = [name, time, content]
	def __init__(self,**data):
		self.__dict__.update(data)

def create_chat(addr, owner):

	# to get the system time of hour and minutes
	def get_time():
		h_m = time.strftime("%H %M", time.localtime())
		h = h_m.split()[0]
		m = h_m.split()[1]
		return h, m
		
	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server.setblocking(0)
	server.bind(addr)
	server.listen(15) # at least 10 client
	
	inputs = [server]
	outputs = []
	message_queues = {}	
	clients = []
	users = {}
	history = []
	if_owner_first = True
	close_chatroom = False
	
	# print("Wait for connection... ")
	while inputs:
		readable, writable, exceptional = select.select(
			inputs, outputs, inputs)
		## readable
		for s in readable:
			if s is server:
				conn, addr = s.accept()
				conn.setblocking(0)
				inputs.append(conn)
				clients.append(conn)
				message_queues[conn] = queue.Queue()
				# welcome 
				welcome = "********************************\n"+\
							"** Welcome to the chatroom. **\n"+\
							"********************************"
				if len(history) != 0:
					for i in range(len(history)):
						welcome += "\n" + history[i]
				message_queues[conn].put(welcome)
				if conn not in outputs:
					outputs.append(conn)
					
			else:
				data = str(s.recv(1024), encoding='utf-8')				
				if data:
					
					if "leave-chatroom" == data:
						if owner == users[s]:
							close_chatroom = True
						message = "Welcome back to BBS."
						message_queues[s].put(message)
						if s not in outputs:
							outputs.append(s)
					
					elif "detach" == data and owner == users[s]:
						if s in outputs:
							outputs.remove(s)
						inputs.remove(s)
						if s in clients:
							clients.remove(s)
						s.close()
						del message_queues[s]
		
					elif "sys" in data:
						user = data.split()[1]
						users[s] = user
						if user==owner and if_owner_first==False:
							pass
						else:
							hour, min = get_time()
							sys = "sys[%s:%s]:%s join us."%(hour, min, user)
							for client in clients:
								if client != s:
									message_queues[client].put(sys)
									if client not in outputs:
										outputs.append(client)
						if if_owner_first:
							if_owner_first = False
						
					else:
						hour, min = get_time()
						message = "%s[%s:%s]:%s"%(users[s], hour, min, data)
						if len(history) < 3:
							history.append(message)
						else:
							del history[0]
							history.append(message)
						for client in clients:
							if client != s:
								message_queues[client].put(message)
								if client not in outputs:
									outputs.append(client)
									
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
				s.sendall(next_msg.encode())
				
				## close the chatroom socket server
				if close_chatroom == True:
					hour, min = get_time()
					sys = "sys[%s:%s]:the chatroom is close.\nWelcome back to BBS."%(hour, min)
					for client in clients:
						if client != s:
							message_queues[client].put(sys)
							if client not in outputs:
								outputs.append(client)
					if s in outputs:
						outputs.remove(s)
					inputs.remove(s)
					if s in clients:
						clients.remove(s)
					s.close()
					del message_queues[s]
					close_chatroom = False
				
				## close the chatroom socket client connection
				elif next_msg == "Welcome back to BBS.":
					# send the leave message
					hour, min = get_time()
					sys = "sys[%s:%s]:%s leave us."%(hour, min, users[s])
					for client in clients:
						if client != s:
							message_queues[client].put(sys)
							if client not in outputs:
								outputs.append(client)
					# after sending leave message, cloes the connection		
					if s in outputs:
						outputs.remove(s)
					inputs.remove(s)
					if s in clients:
						clients.remove(s)
					s.close()
					del message_queues[s]
				
				## leave-chatroom the condition of non-owner
				elif "Welcome back to BBS." in next_msg:
					if s in outputs:
						outputs.remove(s)
					inputs.remove(s)
					if s in clients:
						clients.remove(s)
					s.close()
					del message_queues[s]

		## exceptional
		for s in exceptional:
			inputs.remove(s)
			if s in outputs:
				outputs.remove(s)
			s.close()
			del message_queues[s]
			
def join_chatroom(addr, owner, if_wel):
	global user, status, chat_addr
	chat_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	chat_s.connect(addr)
	# recv welcome
	wel = str(chat_s.recv(1024), encoding='utf-8')
	if if_wel:
		print(wel)
	chat_s.sendall(("sys %s"%user).encode())
	chat_s.setblocking(0)	
	chat_s.settimeout(0.01)
	
	msgs = ""
	with NonBlockingConsole() as nbc:
		while True:
			try:
				data = str(chat_s.recv(1024), encoding='utf-8')
				print(data)
				if "Welcome back to BBS." in data:
					chat_s.close()
					break
			except:
				pass
			msg = nbc.get_data() # to get the console input nonblockingly
			if msg and ord(msg)==10:
				# print("ENTER")
				if msgs == "detach" and owner:
					chat_s.sendall(msgs.encode())
					chat_s.close()
					# sys.stdout.write('\n')
					print(msgs)
					print("Welcome back to BBS.")
					msgs=""
					break
				elif msgs == "leave-chatroom" and owner:
					status = "close"
					chat_s.sendall(msgs.encode())
					# sys.stdout.write('\n')
					print(msgs)
					msgs=""
				else:
					# msgs = user + " " + msgs
					chat_s.sendall(msgs.encode())
					# sys.stdout.write('\n')
					print(msgs)
					msgs=""
			elif msg:
				msgs += msg

def command(cmd, s, u, addr):
	global user, status, chat_addr, owner_chat_addr
	## hw1 command
	# udp
	if cmd == "whoami" or "register" in cmd:
		s.sendall("udp".encode())
		u.sendto( cmd.encode(), addr)
		data, _ = u.recvfrom(1024)
		print(str(data, encoding='utf-8'))
		
	# tcp
	elif "login" in cmd:
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
		if "Welcome" in data:
			cmd = cmd.split()
			user = cmd[1].strip()

	elif cmd == "logout":
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
		if "Bye" in data:
			user = ""
		
	elif  cmd=="list-user":
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)

	## hw2 command
	elif "create-board" in cmd or "create-post" in cmd or "list-board" in cmd \
		or "list-post" in cmd or "read" in cmd or "delete-post" in cmd or "update-post" in cmd \
		or "comment" in cmd:
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
		
	## hw3 command
	elif "create-chatroom" in cmd:
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
		status = "open"
		if "start to create" in data:
			cmd = cmd.split()
			owner_chat_addr = (addr[0], int(cmd[1]))
			pid = os.fork()
			if pid == -1:
				sys.exit("fork error")
			elif pid == 0:
				# child process
				create_chat(owner_chat_addr, user)
			else:
				time.sleep(0.01)
				join_chatroom(owner_chat_addr, True, True)
				if status == "close":
					s.sendall( "leave-chatroom".encode())
				
	elif "list-chatroom" == cmd: # list-chatroom use udp to do
		s.sendall("udp".encode())
		u.sendto( cmd.encode(), addr)
		data, _ = u.recvfrom(1024)
		print(str(data, encoding='utf-8'))
	elif "join-chatroom" in cmd:
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		if data.find("addr") == -1:
			print(data)
		else:
			chat_addr = (data[data.find("addr")+4:data.find("port")].strip(),\
				int(data[data.find("port")+4:].strip()))
			join_chatroom(chat_addr, False, True)
			
	elif "attach" == cmd:
		if user == "":
			print("Please login first.")
		elif status == "":
			print("Please create-chatroom first.")
		elif status == "close":
			print("Please restart-chatroom first.")
		else:
			print("Welcome to the chatroom.")
			join_chatroom(owner_chat_addr, True, True)
			if status == "close":
				s.sendall( "leave-chatroom".encode())
		
	elif "restart-chatroom" == cmd:
		s.sendall(cmd.encode())
		data = str(s.recv(1024), encoding='utf-8')
		print(data)
		if data == "start to create chatroom...":
			status = "open"
			join_chatroom(owner_chat_addr, True, True)
			if status == "close":
				s.sendall( "leave-chatroom".encode())
		
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
	s.close()
	u.close()
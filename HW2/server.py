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

client_num = 0
client = [] # the login statu		

## date
today = str(datetime.date.today()).split("-")
date = (today[1]+'/'+today[2])

## board shared memory
board_name = []
board = []
serial_number = 1

## to create a database
sql_conn = sqlite3.connect("user.db")
cursor = sql_conn.cursor()
sql = """CREATE TABLE IF NOT EXISTS users(
				UID INTEGER PRIMARY KEY AUTOINCREMENT,
				Username TEXT NOT NULL UNIQUE,
				Email TEXT NOT NULL,
				Password TEXT NOT NULL
			);"""
cursor.execute(sql) # execute the sql sentence
sql_conn.commit()

## threading 
class myThread (threading.Thread):
	global serial_number, board_name, board
	def __init__(self, task, arg, conn):
		threading.Thread.__init__(self)
		self.task = task
		self.arg = arg
		self.conn = conn
		self.msg =""
		
	def back(self):
		return self.msg
	
	def run(self):
		# Start the thread
		threadLock.acquire()
		if self.task == "create-board":
			self.create_board()
		elif self.task == "create-post":
			self.create_post()
		elif self.task == "list-board":
			self.list_board()
		elif self.task == "list-post":
			self.list_post()
		elif self.task == "read":
			self.read()
		elif self.task == "delete-post":
			self.delete_post()
		elif self.task == "update-post":
			self.update_post()
		elif self.task == "comment":
			self.comment()
		threadLock.release()

	def create_board(self):
	# arg element
	#	0: 		board name
	#	1:		user name
		if self.arg[0] in board_name:
			self.msg = "Board already exists."
		else:
			board_name.append(self.arg[0])
			board.append([self.arg[0], self.arg[1]])
			self.msg = "Create board successfully."
		# conn.sendall(msg.encode())
	def create_post(self):
	# arg element
	# 	0: 		board_name
	# 	1: 		title
	# 	2: 		content
		global serial_number, board_name, board
		if self.arg[0] not in board_name:
			self.msg = "Board does not exist."
		else:
			for item in board:
				if item[0] == self.arg[0]:
					item.append([serial_number, self.arg[1], self.arg[2], date, self.arg[3]])
					serial_number += 1
					break
			self.msg = "Create post successfully."
		# conn.sendall(msg.encode())
	def list_board(self):	
		# self.msg = "Index\tName\t\tModerator"
		self.msg = "%-5s %-20s %-20s"%("Index", "Name", "Moderator")
		idx = 1
		for item in board:
			# self.msg += ('\n'+str(idx)+'\t'+item[0]+'\t\t'+item[1])
			self.msg += "\n%-5s %-20s %-20s"%(str(idx), item[0], item[1])
			idx += 1
		# conn.sendall(msg.encode())
	def list_post(self):
	# arg element
	#	0:		board name
		if self.arg[0] not in board_name:
			self.msg = "Board does not exist."
		else:
			self.msg = "%-5s %-20s %-20s %-6s"%("S/N", "Title", "Author", "Date")
			for item in board:
				if item[0] == self.arg[0]:
					for i in range(2, len(item)):
						# self.msg += ('\n'+str(item[i][0])+'\t'+item[i][1]+'\t\t\t\t'+item[i][2]+'\t\t'+item[i][3])
						self.msg += "\n%-5s %-20s %-20s %-6s"%(str(item[i][0]), item[i][1], item[i][2], item[i][3])
					break
		# conn.sendall(msg.encode())
	def read(self):
		global serial_number, board_name, board
		if int(self.arg[0]) >= serial_number:
			self.msg = "Post does not exist."
		else:
			break_loop = False
			for item in board:
				for i in range(2, len(item)):
					if item[i][0] == int(self.arg[0]):
						self.msg = "Auther: " + item[i][2] + '\n'
						self.msg += ("Title: " + item[i][1] + '\n')		
						self.msg += ("Date: " + item[i][3] + '\n')
						self.msg += "--\n"
						self.msg += item[i][4] + '\n'
						self.msg += "--"
						for j in range(5, len(item[i])):
							self.msg += ('\n'+item[i][j][0]+": "+item[i][j][1])
						break_loop = True
					if break_loop:
						break
				if break_loop:
					break
			if break_loop == False:
				self.msg = "Post does not exist."
		# conn.sendall(msg.encode())
	def delete_post(self):
		global serial_number, board_name, board
		if int(self.arg[0]) >= serial_number:
			self.msg = "Post does not exist."
		else:
			break_loop = False
			for item in board:
				for i in range(2, len(item)):
					if item[i][0] == int(self.arg[0]):
						break_loop = True	
						if self.arg[1] != item[i][2]:
							# print("self.arg[1]: %s, item[i][2]: %s"%(self.arg[1], item[i][2]))
							self.msg = "Not the post owner."
						else:	
							item.remove(item[i])
							self.msg = "Delete successfully."	
					if break_loop:
						break	
				if break_loop:
					break
			if break_loop == False:
				self.msg = "Post does not exist."
		# conn.sendall(msg.encode())
	def update_post(self):
		global serial_number, board_name, board
		if int(self.arg[0]) >= serial_number:
			self.msg = "Post does not exist."
		else:
			break_loop = False
			for item in board:
				for i in range(2, len(item)):
					if item[i][0] == int(self.arg[0]):
						break_loop = True
						if self.arg[1] != item[i][2]:
							self.msg = "Not the post owner."
						else:	
							if self.arg[2] == "title":
								item[i][1] = self.arg[3]
							else: #content	
								item[i][4] = self.arg[3]
							self.msg = "Update successfully."
					if break_loop:
						break	
				if break_loop:
					break
			if break_loop == False:
				self.msg = "Post does not exist."
		# conn.sendall(msg.encode())
	def comment(self):
		global serial_number, board_name, board
		if int(self.arg[0]) >= serial_number:
			self.msg = "Post does not exist."
		else:
			break_loop = False
			for item in board:
				for i in range(2, len(item)):
					if item[i][0] == int(self.arg[0]):
						break_loop = True
						item[i].append([self.arg[1], self.arg[2]])
						self.msg = "Comment successfully."
					if break_loop:
						break	
				if break_loop:
					break
			if break_loop == False:
				self.msg = "Post does not exist."
		# conn.sendall(msg.encode())
		
threadLock = threading.Lock()
threads = []

## the method to deal with the command what clients sent to server
def method(conn, data, if_login, user):
	#tcp
	if data == "exit":
		return "exit"
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
						for item in client:
							if conn in item:
								item.append(user)
								item[1] = True
								if_login = True
								break
				if if_login!=True:
					msg = "Login failed"
			else:
				msg = "Login failed"
		# conn.sendall(msg.encode())
		return msg
	elif data == "logout":
		if if_login == False:
			msg = "Please login first."
		else:
			for item in client:
				if s in item:
					item.remove(user)
					item[1] = False
					if_login = False
					break
			msg = "Bye, %s."%user
		# conn.sendall(msg.encode())
		return msg
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
		# conn.sendall(msg.encode())
		return msg
	## hw2 command for the board
	elif "create-board" in data:
		if if_login == False:
			msg = "Please login first."
			# conn.sendall(msg.encode())
			return msg
		else:
			try:
				data = data.split()
				thread = myThread("create-board", [data[1], user], conn)
				thread.start()
				thread.join()
				return thread.back()
			except:
				return "create-board <name>"
	elif "create-post" in data:
		if if_login == False:
			msg = "Please login first."
			# conn.sendall(msg.encode())
			return msg
		else:
			try:
				board_name = data.split()[1]
				title = data[data.find("--title")+7:data.find("--content")].strip()
				content = data[data.find("--content")+9:].strip().replace("<br>", "\n")				
				thread = myThread("create-post", [board_name, title, user, content], conn)
				thread.start()
				thread.join()
				return thread.back()
			except:
				return "create-post <board-name> --title <title> --content <content>"
	elif "list-board" in data:
		thread = myThread("list-board", [], conn)
		thread.start()
		thread.join()
		return thread.back()
	elif "list-post" in data: 
		try:
			board_name = data.split()[1]
			thread = myThread("list-post", [board_name], conn)
			thread.start()
			thread.join()
			return thread.back()
		except:
			return "list-post <board-name>"
	elif "read" in data:
		try:
			s_n = data.split()[1]
			thread = myThread("read", [s_n], conn)
			thread.start()
			thread.join()
			return thread.back()
		except:
			return "read <post-S/N>"
	elif "delete-post" in data:
		if if_login == False:
			msg = "Please login first."
			# conn.sendall(msg.encode())
			return msg
		else:
			try:
				s_n = data.split()[1]
				thread = myThread("delete-post", [s_n, user], conn)
				thread.start()
				thread.join()
				return thread.back()
			except:
				return "delete-post <post-S/N>"
	elif "update-post" in data:
		if if_login == False:
			msg = "Please login first."
			# conn.sendall(msg.encode())
			return msg
		else:
			try:
				s_n = data.split()[1]
				if data.find("--title") != -1:
					title = data[data.find("--title")+7:].strip()
					thread = myThread("update-post", [s_n, user, "title", title], conn)
				else:
					content = data[data.find("--content")+9:].strip().replace("<br>", "\n")		
					thread = myThread("update-post", [s_n, user, "content", content], conn)
				thread.start()	
				thread.join()
				return thread.back()
			except:	
				"update-post <post-S/N> --title/content <new>"
	elif "comment" in data:
		if if_login == False:
			msg = "Please login first."
			# conn.sendall(msg.encode())
			return msg
		else:
			try:
				s_n = data.split()[1]
				comment = " ".join(data.split()[2:])
				# print("s_n: %s, user: %s, comment: %s"%(s_n, user, comment))
				thread = myThread("comment", [s_n, user, comment], conn)
				thread.start()
				thread.join()
				return thread.back()
			except:
				return "comment <post-S/N> <comment>"
	elif "register" in data:
		data = data.split()
		if len(data)!=4: 
			msg = "register <username> <email> <password>"
		else:
			sql = "INSERT INTO USERS (Username, Email, Password) VALUES ('%s','%s','%s')"% ( data[1], data[2], data[3] )
			try:
				cursor.execute(sql)
				sql_conn.commit()
				msg = "Register successfully."
			except:
				msg = "Username is already used."
		# conn.sendall(msg.encode())
		return msg

if __name__ == "__main__":
	## the host and service
	if len(sys.argv) != 2:
		sys.exit("iter_tcp_server.py {portnumber} ")
	else:
		port = int(sys.argv[1])
	host = "127.0.0.1"
	addr = (host, port)

	server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server.setblocking(0)
	server.bind(addr)
	u.bind(addr)
	server.listen(15) # at least 10 client
	
	inputs = [server]
	outputs = []
	message_queues = {}	
	
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
				client.append([conn, False])
				welcome = "********************************\n"+\
								"** Welcome to the BBS server. **\n"+\
								"********************************"
				print("New connection.")
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
						if_login = item[1]
						if len(item) == 3:
							user = item[2]
						else:
							user = ""
						break
				if data:
					message = method(s, data, if_login, user)
					if message == "exit":
						if s in outputs:
							outputs.remove(s)
						inputs.remove(s)
						s.close()
						del message_queues[s]
					else:
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
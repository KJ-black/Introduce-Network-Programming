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

##  shared memory
account_1 = 0
account_2 = 0

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
		if self.task == "deposit":
			self.account_deposit()
		elif self.task == "withdraw":
			self.account_withdraw()
		threadLock.release()

	def account_deposit(self):
		global account_1, account_2
		# arg element
		# 	0: 	account
		#	1:	money
		if self.arg[0] == "ACCOUNT1":
			account_1 += self.arg[1]
		else:
			account_2 += self.arg[1]

	def account_withdraw(self):
		global account_1, account_2
		if self.arg[0] == "ACCOUNT1":
			account_1 -= self.arg[1]
		else:
			account_2 -= self.arg[1]
		
threadLock = threading.Lock()
threads = []

## the method to deal with the command what clients sent to server
def method(conn,  data):
	#tcp
	if data == "exit":
		return "exit"
	elif data == "show-accounts":
		# ACCOUNT1: <money>
		# ACCOUNT2: <money>
		return "ACCOUNT1: %d\nACCOUNT2: %d"%(account_1, account_2)
	elif "deposit" in data:
		# comment: deposit <account> <money>
		try:
			account = data.split()[1] #ACCOUNT1 or ACCOUNT2
			money = data.split()[2]
		except:
			return "deposit <account> <money>"
		if account == "ACCOUNT1" or account == "ACCOUNT2":
			pass
		else:
			print("The account is wrong!")
			return "deposit <account> <money>"

		# Fail: Deposit a non-positive number into accounts.
		try:
			money = int(money)
		except:
			return "Deposit a non-positive number into accounts." 
		if money <= 0:
			return "Deposit a non-positive number into accounts."

		# Success: Successfully deposits <money> into <account>.
		thread = myThread("deposit", [account, money], conn)
		thread.start()
		thread.join()
		print("DEBUG: ACCOUNT1: %d\tACCOUNT2: %d"%(account_1, account_2))
		return "Successfully deposits %d into %s"%(money, account)
	elif "withdraw" in data:
		# comment: withdraw <account> <money>
		try:
			account = data.split()[1] #ACCOUNT1 or ACCOUNT2
			money = data.split()[2]
		except:
			return "withdraw <account> <money>"
		if account == "ACCOUNT1" or account == "ACCOUNT2":
			pass
		else:
			print("The account is wrong!")
			return "withdraw <account> <money>"

		# Fail(2): Deposit a non-positive number into accounts.
		try:
			money = int(money)
		except:
			return "Withdraw a non-positive number into accounts." 
		if money <= 0:
			return "Withdraw a non-positive number into accounts."	

		# Fail(1): Withdraw excess money from accounts.
		if (account == "ACCOUNT1" and money > account_1) or (account == "ACCOUNT2" and money > account_2):
			return "Withdraw excess money from accounts."

		# Success: Successfully withdraws <money> from <account>.
		thread = myThread("withdraw", [account, money], conn)
		thread.start()
		thread.join()
		print("DEBUG: ACCOUNT1: %d\tACCOUNT2: %d"%(account_1, account_2))
		return "Successfully withdraws %d from %s"%(money, account)


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
				if client_num == 1:
					client_name = 'A'
				elif client_num == 2:
					client_name = 'B'
				elif client_num == 3:
					client_name = 'C'
				elif client_num == 4:
					client_name = 'D'
				client.append([conn, addr, client_name])
				welcome = "********************************\n"+\
								"** Welcome to the TCP server. **\n"+\
								"********************************"
				print("New connection from %s:%s Client %s"%(addr[0], addr[1], client_name))
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
						client_name = item[2]
						client_addr = item[1]
						break
				if data:
					message = method(s, data)
					if message == "exit":
						print("Client %s %s:%s disconnected"%(client_name, client_addr[0], client_addr[1]))
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
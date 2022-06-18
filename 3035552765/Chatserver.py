#!/usr/bin/python3

# Student name and No.: Uday Jain, 3035552765
# Development platform: OSX
# Python version: 3.7.13
# Version: 1.0

from audioop import rms
from encodings import utf_8
from http import server
from pydoc import plain
import re
import socket
import string
import sys
import select
import json


# ChatServer class. The member variables are described as their use case comes up inside functions.
class ChatServer:
	def __init__(self, port):
		self.RList = []
		self.port = port

		self.PList = {}
		self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Convert PeerList to sendable format. PList is stored as a dict uid->tuple (nickname, socket). 
	# Converted to the Object list format required from the protocol. list(object{uid, un})
	def _peer_list(self):
		plist = []

		for key in self.PList.keys():
			plist.append({"UID": key, "UN": self.PList[key][0]})

		return plist

	# Sends plist to all peers in PList. Called when received JOIN or LEAVE commands to update peer list other peers.
	def __send_plist_toall(self):
		list_data = {
			"CMD": "LIST", 
			"DATA": self._peer_list()
		}
		data = json.dumps(list_data).encode('utf-8')
		
		for _, p in self.PList.values():
			# do not send peer list to self
			if(p != self.sockfd):
				p.sendall(data)


	# handles the received JOIN command and sends acknowledgments. Also sends updated peer list to all using __send_plist_toall
	def __do_JOIN(self, msg, psoc):
		p_uid = msg["UID"]
		p_un = msg["UN"]

		if p_uid in self.PList.keys():
			# peer already connected. Failed ack
			psoc.sendall('{"CMD": "ACK", "TYPE": "FAIL"}'.encode('utf-8'))
		else:
			# peer allowed to connect. Updated peer list sent to all
			self.PList[p_uid] = (p_un, psoc)

			psoc.sendall('{"CMD": "ACK", "TYPE": "OKAY"}'.encode('utf-8'))


			self.__send_plist_toall()

# handles the received SEND command and creates the corresponding MSG commands to be sent to peer(s)
	def __do_SEND(self, msg, psoc):
		msg_to =  msg["TO"]

		# Broadcast messages have TO = []. They are sent to all peers.
		if(len(msg_to) == 0):
			msg_data = {
				"CMD": "MSG", 
				"TYPE": "ALL",
				"MSG": msg["MSG"],
				"FROM": msg["FROM"]
			}

			data = json.dumps(msg_data).encode('utf-8')

			# Send message to all peers in PList
			for _, p in self.PList.values():
				if(p != self.sockfd and p != psoc):
					p.sendall(data)
		else:
			# GROUP messages are sent to more than one peer and PRIVATE to only 1
			msg_data = {
				"CMD": "MSG", 
				"TYPE": "PRIVATE" if len(msg_to) == 1 else "GROUP",
				"MSG": msg["MSG"],
				"FROM": msg["FROM"]
			}

			data = json.dumps(msg_data).encode('utf-8')

			# MSG commands send to all recipient
			for p_uid in msg_to:
				p = self.PList[p_uid][1]
				p.sendall(data)


# a sieve function of sorts. Receives the raw message string, decodes into json and passes to the respective 
# message handlers like JOIN and SEND. Unknow commands are printed as ERROR
	def __handle_rmsg(self, rmsg: string, psoc: socket.socket):
		msg = json.loads(rmsg)
		
		cmd = msg["CMD"]

		if cmd == "JOIN":
			self.__do_JOIN(msg, psoc)

		elif cmd == "SEND":
			self.__do_SEND(msg, psoc)
		
		else:
			print("[ERROR] CMD not recognized")

	# Combines the bind and listen calls of the socket connection
	def start(self):
		try:
			self.sockfd.bind(('', self.port))
		except socket.error as emsg:
			print("Socket bind error: ", emsg)
			sys.exit(1)
		
		self.sockfd.listen(5)
		self.RList = [self.sockfd]

# Basic framework from workshop 2. Calls select and listens to the RList
	def listen(self):

		while True:
			try:
				Rready, _, __ = select.select(self.RList, [], [], 10)
			except select.error as emsg:
				print("At select, caught an exception:", emsg)
				sys.exit(1)
			except KeyboardInterrupt:
				print("At select, caught the KeyboardInterrupt")
				sys.exit(1)

			if Rready:
				for sd in Rready:
					if sd == self.sockfd:
						# handles arrival of new clients
						newfd, caddr = self.sockfd.accept()
						print("A new client has arrived. It is at:", caddr)
						self.RList.append(newfd)
					else:
						rmsg = sd.recv(1024)

						if rmsg:
							# new messages are handled at the message handler __handle_rmsg
							self.__handle_rmsg(rmsg, sd)

						# if connection breaks, check if in peer list then send updated peer list to all.
						# remove from receive list regardless
						else:
							broken_uid = ""
							for k, v in self.PList.items():
								if(v[1] == sd):
									broken_uid = k
							
							# if socket associated with peer. Remove peer and send updated peer list to all
							if(broken_uid):
								del self.PList[broken_uid]
								self.__send_plist_toall()

							# remove from receive list
							self.RList.remove(sd)

			else:
				print("Idling")


# starts the Chat Server. Has a default port setting
def main(argv):
	if len(argv) == 2:
		port = int(argv[1])
	else:
		port = 32349
	
	server = ChatServer(port)
	
	server.start()
	server.listen()


if __name__ == '__main__':
	if len(sys.argv) > 2:
		print("Usage: chatserver [<Server_port>]")
		sys.exit(1)
	main(sys.argv)
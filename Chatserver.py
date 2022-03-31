#!/usr/bin/python

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


class ChatServer:
	def __init__(self, port):
		self.CList = []
		self.RList = []
		self.port = port

		self.PList = {}
		self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def _peer_list(self):
		plist = []

		for key in self.PList.keys():
			plist.append({"UID": key, "UN": self.PList[key][0]})

		return plist

	def __send_plist_toall(self):
		list_data = {
			"CMD": "LIST", 
			"DATA": self._peer_list()
		}
		res = json.dumps(list_data).encode('utf-8')
		
		for _, p in self.PList.values():
			if(p != self.sockfd):
				p.sendall(res)


	def __do_JOIN(self, msg, psoc):
		p_uid = msg["UID"]
		p_un = msg["UN"]

		if p_uid in self.PList.keys():
			print(self.PList)
			psoc.sendall('{"CMD": "ACK", "TYPE": "FAIL"}'.encode('utf-8'))
		else:
			self.PList[p_uid] = (p_un, psoc)

			psoc.sendall('{"CMD": "ACK", "TYPE": "OKAY"}'.encode('utf-8'))


			self.__send_plist_toall()

	def __do_SEND(self, msg, psoc):
		msg_to =  msg["TO"]

		if(len(msg_to) == 0):
			msg_data = {
				"CMD": "MSG", 
				"TYPE": "ALL",
				"MSG": msg["MSG"],
				"FROM": msg["FROM"]
			}
			res = json.dumps(msg_data).encode('utf-8')

			for _, p in self.PList.values():
				if(p != self.sockfd and p != psoc):
					p.sendall(res)
		else:
			msg_data = {
				"CMD": "MSG", 
				"TYPE": "PRIVATE" if len(msg_to) == 1 else "GROUP",
				"MSG": msg["MSG"],
				"FROM": msg["FROM"]
			}
			res = json.dumps(msg_data).encode('utf-8')

			for p_uid in msg_to:
				p = self.PList[p_uid][1]
				p.sendall(res)


	def __handle_rmsg(self, rmsg: string, psoc: socket.socket):
		msg = json.loads(rmsg)
		
		cmd = msg["CMD"]

		if cmd == "JOIN":
			self.__do_JOIN(msg, psoc)

		elif cmd == "SEND":
			self.__do_SEND(msg, psoc)
		
		else:
			print("[ERROR] CMD not recognized")

	
	def start(self):
		try:
			self.sockfd.bind(('', self.port))
		except socket.error as emsg:
			print("Socket bind error: ", emsg)
			sys.exit(1)
		
		self.sockfd.listen(5)
		self.RList = [self.sockfd]

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
						newfd, caddr = self.sockfd.accept()
						print("A new client has arrived. It is at:", caddr)
						self.RList.append(newfd)
						self.CList.append(newfd)
					else:
						rmsg = sd.recv(1024)

						if rmsg:
							self.__handle_rmsg(rmsg, sd)

						else:
							broken_uid = ""
							for k, v in self.PList.items():
								if(v[1] == sd):
									broken_uid = k
							
							if(broken_uid):
								del self.PList[broken_uid]
								self.__send_plist_toall()

							
							self.CList.remove(sd)
							self.RList.remove(sd)

			else:
				print("Idling")



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
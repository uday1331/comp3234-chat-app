#!/usr/bin/python

from audioop import rms
from http import server
from pydoc import plain
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

	def _jsonify_plist(self):
		plist = {}
		for key in self.PList.keys():
			plist[key] = self.PList[key][0]
		return json.dumps(plist)

	def __do_JOIN(self, p_uid, p_un, psoc: socket.socket):
		if p_uid in self.PList.keys():
			psoc.sendall('{"CMD": "ACK", "TYPE": "FAIL"}'.encode('utf-8'))
		else:
			self.PList[p_uid] = (p_un, psoc)

			psoc.sendall('{"CMD": "ACK", "TYPE": "OKAY"}'.encode('utf-8'))

			for _, p in self.PList.values():
				if(p != self.sockfd):
					plist = self._jsonify_plist()
					p.sendall(plist.encode('utf-8'))


	def __handle_rmsg(self, rmsg: string, psoc: socket.socket):
		msg = json.loads(rmsg)
		
		cmd = msg["CMD"]

		if cmd == "JOIN":
			p_uid = msg["UID"]
			p_un = msg["UN"]

			self.__do_JOIN(p_uid, p_un, psoc)

	
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
							print("A client connection is broken!!")
							
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
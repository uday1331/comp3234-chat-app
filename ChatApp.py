#!/usr/bin/python3

# Student name and No.: Uday Jain, 3035552765
# Development platform: OSX
# Python version: 3.7.13
# Version: 1.0


import string
from tkinter import *
from tkinter import ttk
from tkinter import font
import sys
import socket
import json
import os
from xmlrpc.client import Server
import threading
from _thread import start_new_thread

#
# Global variables
#
MLEN=1000      #assume all commands are shorter than 1000 bytes
USERID = None
NICKNAME = None
SERVER = None
SERVER_PORT = None



#
# Functions to handle user input
#

sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer_list = []

def search_plist(field, value):
  for p in peer_list:
    if(p[field] == value):
      return p
  
  return KeyError

def uid_from_un(un):
  p = search_plist("UN", un)
  return p["UID"]

def stringify_plist():
  s_plist = map(lambda p: f'{p["UN"]} ({p["UID"]})', peer_list)
  return ", ".join(s_plist)

def handle_rmsg(rmsg: string):
  global peer_list
  msg = json.loads(rmsg)

  if(msg["CMD"] == "LIST"):
    peer_list = msg["DATA"]
    list_print(stringify_plist())

  elif(msg["CMD"] == "MSG"):
    msg_from = search_plist("UID", msg["FROM"])
    msg_from_un = msg_from["UN"]
    msg_type = msg["TYPE"]

    print_msg = f'[{msg_from_un}] {msg["MSG"]}'
    if(msg_type == "PRIVATE"):
      chat_print(print_msg, 'redmsg')  
    elif(msg_type == "GROUP"):
      chat_print(print_msg, 'greenmsg')
    elif(msg_type == "ALL"):
      chat_print(print_msg, 'bluemsg')


def recv_cmd(sockfd: socket.socket):
  while True:
    rmsg = sockfd.recv(1024)
    if not rmsg:
      console(f'none response from server. successfully disconnected')
      break
    handle_rmsg(rmsg)
  sockfd.close()

def do_Join():
  sockfd.connect( (SERVER, SERVER_PORT) )

  cmd = {
    "CMD": "JOIN", 
    "UN": NICKNAME,
    "UID": USERID
  }
  data = json.dumps(cmd).encode('utf-8')
  sockfd.sendall(data)

  rmsg = sockfd.recv(1024)
  msg = json.loads(rmsg)

  if(msg["CMD"] == "ACK" and msg["TYPE"] == "OKAY"):
    console_print(f'successfully connected to server at: ({Server}:{SERVER_PORT})')
    start_new_thread(recv_cmd, (sockfd, ))
  else:
    console_print(f'[ ERROR ]: failed connected to server at: ({Server}:{SERVER_PORT})')
    sockfd.close()


def do_Send():
  #The following statements are just for demo purpose
  #Remove them when you implement the function

  msg_to = get_tolist()
  msg_to_un = [] if len(msg_to) == 0 else msg_to.split(", ")
  msg_to_uid = list(map(uid_from_un, msg_to_un))
  msg_msg = get_sendmsg()

  cmd = {
    "CMD": "SEND", 
    "MSG": msg_msg.strip(),
    "TO": msg_to_uid,
    "FROM": USERID
  }
  data = json.dumps(cmd).encode('utf-8')
  sockfd.sendall(data)



  ## TODO: convert nicknames to uid

def do_Leave():
  #The following statement is just for demo purpose
  #Remove it when you implement the function
  list_print("Press do_Leave()")


#################################################################################
#Do not make changes to the following code. They are for the UI                 #
#################################################################################

#for displaying all log or error messages to the console frame
def console_print(msg):
  console['state'] = 'normal'
  console.insert(1.0, "\n"+msg)
  console['state'] = 'disabled'

#for displaying all chat messages to the chatwin message frame
#message from this user - justify: left, color: black
#message from other user - justify: right, color: red ('redmsg')
#message from group - justify: right, color: green ('greenmsg')
#message from broadcast - justify: right, color: blue ('bluemsg')
def chat_print(msg, opt=""):
  chatWin['state'] = 'normal'
  chatWin.insert(1.0, "\n"+msg, opt)
  chatWin['state'] = 'disabled'

#for displaying the list of users to the ListDisplay frame
def list_print(msg):
  ListDisplay['state'] = 'normal'
  #delete the content before printing
  ListDisplay.delete(1.0, END)
  ListDisplay.insert(1.0, msg)
  ListDisplay['state'] = 'disabled'

#for getting the list of recipents from the 'To' input field
def get_tolist():
  msg = toentry.get()
  toentry.delete(0, END)
  return msg

#for getting the outgoing message from the "Send" input field
def get_sendmsg():
  msg = SendMsg.get(1.0, END)
  SendMsg.delete(1.0, END)
  return msg

#for initializing the App
def init():
  global USERID, NICKNAME, SERVER, SERVER_PORT

  #check if provided input argument
  if (len(sys.argv) > 2):
    print("USAGE: ChatApp [config file]")
    sys.exit(0)
  elif (len(sys.argv) == 2):
    config_file = sys.argv[1]
  else:
    config_file = "config.txt"

  #check if file is present
  if os.path.isfile(config_file):
    #open text file in read mode
    text_file = open(config_file, "r")
    #read whole file to a string
    data = text_file.read()
    #close file
    text_file.close()
    #convert JSON string to Dictionary object
    config = json.loads(data)
    USERID = config["USERID"].strip()
    NICKNAME = config["NICKNAME"].strip()
    SERVER = config["SERVER"].strip()
    SERVER_PORT = config["SERVER_PORT"]
  else:
    print("Config file not exist\n")
    sys.exit(0)


if __name__ == "__main__":
  init()

#
# Set up of Basic UI
#
win = Tk()
win.title("ChatApp")

#Special font settings
boldfont = font.Font(weight="bold")

#Frame for displaying connection parameters
topframe = ttk.Frame(win, borderwidth=1)
topframe.grid(column=0,row=0,sticky="w")
ttk.Label(topframe, text="NICKNAME", padding="5" ).grid(column=0, row=0)
ttk.Label(topframe, text=NICKNAME, foreground="green", padding="5", font=boldfont).grid(column=1,row=0)
ttk.Label(topframe, text="USERID", padding="5" ).grid(column=2, row=0)
ttk.Label(topframe, text=USERID, foreground="green", padding="5", font=boldfont).grid(column=3,row=0)
ttk.Label(topframe, text="SERVER", padding="5" ).grid(column=4, row=0)
ttk.Label(topframe, text=SERVER, foreground="green", padding="5", font=boldfont).grid(column=5,row=0)
ttk.Label(topframe, text="SERVER_PORT", padding="5" ).grid(column=6, row=0)
ttk.Label(topframe, text=SERVER_PORT, foreground="green", padding="5", font=boldfont).grid(column=7,row=0)


#Frame for displaying Chat messages
msgframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
msgframe.grid(column=0,row=1,sticky="ew")
msgframe.grid_columnconfigure(0,weight=1)
topscroll = ttk.Scrollbar(msgframe)
topscroll.grid(column=1,row=0,sticky="ns")
chatWin = Text(msgframe, height='15', padx=10, pady=5, insertofftime=0, state='disabled')
chatWin.grid(column=0,row=0,sticky="ew")
chatWin.config(yscrollcommand=topscroll.set)
chatWin.tag_configure('redmsg', foreground='red', justify='right')
chatWin.tag_configure('greenmsg', foreground='green', justify='right')
chatWin.tag_configure('bluemsg', foreground='blue', justify='right')
topscroll.config(command=chatWin.yview)

#Frame for buttons and input
midframe = ttk.Frame(win, relief=RAISED, borderwidth=0)
midframe.grid(column=0,row=2,sticky="ew")
JButt = Button(midframe, width='8', relief=RAISED, text="JOIN", command=do_Join).grid(column=0,row=0,sticky="w",padx=3)
QButt = Button(midframe, width='8', relief=RAISED, text="LEAVE", command=do_Leave).grid(column=0,row=1,sticky="w",padx=3)
innerframe = ttk.Frame(midframe,relief=RAISED,borderwidth=0)
innerframe.grid(column=1,row=0,rowspan=2,sticky="ew")
midframe.grid_columnconfigure(1,weight=1)
innerscroll = ttk.Scrollbar(innerframe)
innerscroll.grid(column=1,row=0,sticky="ns")
#for displaying the list of users
ListDisplay = Text(innerframe, height="3", padx=5, pady=5, fg='blue',insertofftime=0, state='disabled')
ListDisplay.grid(column=0,row=0,sticky="ew")
innerframe.grid_columnconfigure(0,weight=1)
ListDisplay.config(yscrollcommand=innerscroll.set)
innerscroll.config(command=ListDisplay.yview)
#for user to enter the recipents' Nicknames
ttk.Label(midframe, text="TO: ", padding='1', font=boldfont).grid(column=0,row=2,padx=5,pady=3)
toentry = Entry(midframe, bg='#ffffe0', relief=SOLID)
toentry.grid(column=1,row=2,sticky="ew")
SButt = Button(midframe, width='8', relief=RAISED, text="SEND", command=do_Send).grid(column=0,row=3,sticky="nw",padx=3)
#for user to enter the outgoing message
SendMsg = Text(midframe, height='3', padx=5, pady=5, bg='#ffffe0', relief=SOLID)
SendMsg.grid(column=1,row=3,sticky="ew")

#Frame for displaying console log
consoleframe = ttk.Frame(win, relief=RAISED, borderwidth=1)
consoleframe.grid(column=0,row=4,sticky="ew")
consoleframe.grid_columnconfigure(0,weight=1)
botscroll = ttk.Scrollbar(consoleframe)
botscroll.grid(column=1,row=0,sticky="ns")
console = Text(consoleframe, height='10', padx=10, pady=5, insertofftime=0, state='disabled')
console.grid(column=0,row=0,sticky="ew")
console.config(yscrollcommand=botscroll.set)
botscroll.config(command=console.yview)

win.mainloop()

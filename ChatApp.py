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

peer_list = []
sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connected = False

def search_plist(field, value):
  for p in peer_list:
    if(p[field] == value):
      return p
  
  raise KeyError

def uid_from_un(un):
  try:
    p = search_plist("UN", un)
  except:
    return None
    
  return p["UID"]

def stringify_plist():
  s_plist = map(lambda p: f'{p["UN"]} ({p["UID"]})', peer_list)
  return ", ".join(s_plist)

def handle_rmsg(msg: string):
  global peer_list
  msg_cmd = msg["CMD"]


  if(msg_cmd == "ACK"):
    msg_type = msg["TYPE"]
    if(msg_type == "OKAY"):
      console_print(f'[SUCCESS] Successfully connected to server at: ({SERVER}:{SERVER_PORT}).')
    else:
      console_print(f'[ERROR]: Failed connecting to server at: ({SERVER}:{SERVER_PORT}).')
  elif(msg_cmd == "LIST"):
    peer_list = msg["DATA"]
    list_print(stringify_plist())

  elif(msg_cmd == "MSG"):
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
    rmsg = ""
    msgs = []
    if(connected == False):
      break

    try:
      rmsg = sockfd.recv(1024)
    except:
      break

    if (rmsg):
      msgs = rmsg.decode('utf-8').split("\d")
      for msg in msgs:
        try:
          msg = json.loads(msg)
          _ = msg["CMD"]
          handle_rmsg(msg)
        except:
          pass

def do_Join():
  global sockfd, connected

  if(connected):
    console_print("[ERROR] Already connected to Server.")
    return

  try:
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sockfd.settimeout(2)
    sockfd.connect( (SERVER, SERVER_PORT) )
    sockfd.settimeout(None)
    
    connected = True
  except:
    console_print("[ERROR] Timout connecting to Server.")

  cmd = {
    "CMD": "JOIN", 
    "UN": NICKNAME,
    "UID": USERID
  }
  data = json.dumps(cmd).encode('utf-8')
  sockfd.sendall(data)

  start_new_thread(recv_cmd, (sockfd, ))


def do_Send():
  if(not connected):
    console_print("[ERROR] Connect to the server first before sending messages.")
    return

  msg_to = get_tolist()
  if(len(msg_to) == 0):
    console_print("[ERROR] Enter a list of ', ' separated recipients or enter 'ALL' for broadcast messages")
    return
  
  msg_msg = get_sendmsg()
  if(len(msg_msg) == 0):
    console_print("[ERROR] Message content cannot be empty.")
    return
    
  msg_to_un = [] if (msg_to == "ALL") else msg_to.split(", ")
  msg_to_uid = list(map(uid_from_un, msg_to_un))
  
  for uid in msg_to_uid:
    if(uid == USERID):
      console_print("[ERROR] Cannot send a message to self.")
      return
    
    if(uid == None):
      console_print("[ERROR] Invalid Nickname(s).")
      return
    
  cmd = {
    "CMD": "SEND", 
    "MSG": msg_msg.strip(),
    "TO": msg_to_uid,
    "FROM": USERID
  }
  data = json.dumps(cmd).encode('utf-8')
  sockfd.sendall(data)

  print_msg_to = 'ALL' if len(msg_to_un) == 0 else ", ".join(msg_to_un)
  chat_print(f'[To: {print_msg_to}] {msg_msg.strip()}')

def do_Leave():
  global connected

  sockfd.close()
  connected = False
  console_print('[EXIT] Successfully left the Chat')


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

#!/usr/bin/env python
import signal
import sys
import os
import time

'''
This program performs the main functionality of the program by spawning off new Servers and sending commands to the servers
using a shared file (shm.txt) and signalling the server to read from the file. It keeps track of all current servers from a global variable.
Each new server created will execlp Server.py.

Author: Kim Steffens

Version: 5 October 2017

'''

# keeps track of all Servers created: holds dictionary with server names as keys to server pids
myServers = {}


# catches Ctrl + C to exit when user commands
def signal_handler(signal, frame):
		print('You pressed Ctrl+C!')
		sys.exit(0)

# creates a new server	
def createServer(myServerCommand):
	global myServers
	
	# fork child
	child = os.fork()
	
	# execlp Server.py- send arguments to finish set up there
	if child == 0:	
		os.execlp('python', 'python', '/home/steffeki/Server.py', *myServerCommand)

	elif child < 0:
		print("There was an error in forking.")
	
	# add this server to myServers. 
	else:
		myServers[myServerCommand[3]] = child 


# display status. Displays current servers from this program and commands all servers to print out their own messages
# displays a simply message declaring who spawned who and prints out myServers dictionary and each servers' myChildren list		
def displayStatus(myCommand):

	if len(myServers) < 1:
		print("No status to print! Please create some servers!")
	
	else:	
		print("-----------------STATUS------------------------")
		print("Server Manager's active spawned servers: ")
		print("     %s"%myServers)
		
		message = ["displayStatus"]
		
		# command servers to print their status
		for server in myServers:
			message.append(server)
			sendMessage(message)
			message.remove(server)
			time.sleep(.5)
		
		# done with displayStatus
		print("-----------------------------------------------")
	
# open shared file and write message. Signal respective server
def sendMessage(message):

	# open and write
	myFile = open('shm.txt', 'w+')
	myFile.truncate()
	myFile.write(message[0])
	myFile.close()
	time.sleep(.1)
	
	# notify our server to check its messages
	os.kill(myServers[message[1]], signal.SIGUSR1)
	time.sleep(.5)
	
	
# sets up ServerManager and each server. Loops around collecting messages from the user
def ServerManager ():
	# catch SIGINT
	signal.signal(signal.SIGINT, signal_handler)
	
	# print commands for user:
	print("Your commands:")
	print("createServer <min processes> <max processes> <server name>")
	print("abortServer <server name>")
	print("createProcess <server name>")
	print("abortProcess <server name>")
	print("displayStatus: display all active processes and who spawned who.")
	
	while True:
	
		# prompt for command and split into list by spaces
		myCommand = raw_input("Please enter a command: \n")
		
		myCommand = myCommand.split()
		
		if len(myCommand) < 1:
			print("Invalid command.")
			continue
		
		# create server if command matches expected input
		if myCommand[0] == "createServer":
			if len(myCommand) != 4:
				print("Incorrect command. Please try createServer <minProcs> <MaxProcs> <server name>")
			elif myCommand[3] in myServers:
				print("Sorry, that server already exists.")
			elif int(myCommand[1]) < 0:
				print("Sorry, you can't have negative processes.")
			elif int(myCommand[1]) > int(myCommand[2]):
				print("Sorry, you can't have maxProcs greater than MinProcs")
			elif len(myCommand[3]) > 20:
				print("Sorry, your server name is too long.")
			else:
				createServer(myCommand)
		
		# abort server if it exists
		elif myCommand[0] == "abortServer":
			if len(myCommand) == 2 and (myCommand[1] in myServers):
				sendMessage(myCommand)
				os.waitpid(myServers[myCommand[1]],0)
				
				# remove from dictionary
				del myServers[myCommand[1]]
			else:
				print("Please ask to abort a server that actually exists.") 
		
		# create process on server if server exists
		elif myCommand[0] == "createProcess":
			if len(myCommand) == 2 and (myCommand[1] in myServers):
				sendMessage(myCommand)
			else:
				print("Please ask to create a process from a server that actually exists.")
		
		# abort process on server if it exists
		elif myCommand[0] == "abortProcess":
			if len(myCommand) == 2 and (myCommand[1] in myServers):
				sendMessage(myCommand)
			else:
				print("Please ask to abort a process from a server that actually exists.")
		
		# display status
		elif myCommand[0] == "displayStatus":
			displayStatus(myCommand)
		else:
			print("Invalid command. Try again.\n")
		
		# give time for output from Server
		time.sleep(1.5)
			
ServerManager()

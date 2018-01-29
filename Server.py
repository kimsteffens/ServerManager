#!/usr/bin/env python
import signal
import sys
import os
import time
import mmap
'''
This program creates and manages the server and its children. The parent server performs the majority of the functionality
by creating/ deleting processes as necessary and keeping track of the server's stats. It receives messages from the parent.
The parent server will be signalled to read from the shared file shm.txt to check messages and process any necessary commands.

Author: Kim Steffens

Version: 5 October 2017

'''

#some globals: only should be accessed from the parent

# this will store the parent's pid
originalProc = None

# the Server name
myName = None

# max procedures allowed
maxProcs = None

# min procedures allowed
minProcs = None

# the parent's children
myChildren = None


# create a new process
# only creates one process because any child who's parent is not originalProc will die
def createProcess():
	global myChildren
	
	# fork off
	child = os.fork()
	
	
	if child == 0:
		# exit out if parent is not the first parent
		if originalProc != os.getppid():
			sys.exit(0)
	elif child < 1:
		print("There has been a error in forking.")
	else:
		# wait for children if are the parent of a process and are not originalProc
		if os.getpid() != originalProc:
			os.waitpid(child, 0)
		#if this child is allowed, then add it to myChildren and print out message
		else:
			myChildren.append(child)
			print("Server %s created new child! %d"%(myName,child))
			print("Server current children: ")
			print(myChildren)


# aborts a particular process by sending a SIGINT signal to it		
def abortProcess(child):
	global myChildren
	
	# convert to int 
	child = int(child)
	
	# kill and remove from myChildren
	os.kill(child, signal.SIGINT)
	os.waitpid(child, 0)
	myChildren.remove(child)
	print("Server %s, Process %d aborted."%(myName,child))
	print("Server current children: ")
	print(myChildren)

# aborts a server by killing each child before parent is killed
def abortServer():
	# create copy of child list and kill each child
	myChildrenCopy = list(myChildren)
	for child in myChildrenCopy:
		abortProcess(child)
	
	time.sleep(1)

	# kill parent
	print('This Server (%s, pid %d) will be shut down...'%(myName,os.getpid()))
	sys.exit(0)

# read commands in from file and act upon them
def readMessage ():
	
	# open file and mmap it to virtual memory
	myFile = open('shm.txt', 'rw+')
	mm = mmap.mmap(myFile.fileno(), 0)
	myMessage = mm.readline()
	
	# create process if allowed to 
	if myMessage == "createProcess":
		print("Server %s received a message: "%myName)
		print(myMessage)
		
		# make sure there aren't too many procs
		if len(myChildren) != maxProcs:
			createProcess()
		else:
			print("Sorry there is already the max amount of processes.")
	
	# abort process if allowed
	elif myMessage == "abortProcess":
		print("Server %s received a message: "%myName)
		print(myMessage)
		
		# make sure there aren't too few procs
		if len(myChildren) != minProcs:
			abortProcess(myChildren[0])
		else:
			print("Sorry this server is at the minimum number of processes.")
	# abort this server
	elif myMessage == "abortServer":
		print("Server %s received a message: "%myName)
		print(myMessage)
		abortServer()
	
	# display status: show all children of this server
	elif myMessage == "displayStatus":
		if len(myChildren) == 0:
			print("No spawned servers on %s"%myName)
		else:
			print("%s active spawned servers:"%myName)
			print("     %s"%myChildren)
	# check for message from a child for restarting process
	else:
		myMessage = myMessage.split()
		
		# kill particular process- don't check min procs because a new child will be created for restart process
		if myMessage[0] == "killProcess":
			abortProcess(myMessage[1])
		# create replacement process- don't check max procs because a process should be deleted after this for restart process
		elif myMessage[0] == "restartProcess":
			createProcess()
	
	# close files
	mm.close()
	myFile.close()

# handle signals: SIGINT, SIGUSR1, SIGILL, and SIGABRT
# SIGILL and SIGABRT are considered unexpected signals (a new process is created and current process is deleted
def signal_handler(signalNum, frame):

		# kill this process
		if signalNum == signal.SIGINT:
			print('This Process (%s, pid %d) will be shut down...'%(myName,os.getpid()))
			time.sleep(1)
			sys.exit(0)
			
		# unexpected signal: restart process
		elif os.getpid() != originalProc and (signalNum == signal.SIGILL or signalNum == signal.SIGABRT):
			print("An unexpected signal was caught in server %s, process %d... shutting down and starting a new process!"%(myName,os.getpid()))
			
			# notify parent to create a new process
			myFile = open('shm.txt', 'w+')
			myFile.write("restartProcess")
			myFile.close()
			time.sleep(.1)
			os.kill(originalProc, signal.SIGUSR1)
			time.sleep(.5)
			
			# notify parent to kill this process
			myFile = open('shm.txt', 'w+')
			myFile.write("killProcess %d"%os.getpid())
			myFile.close()
			time.sleep(.1)
			os.kill(originalProc, signal.SIGUSR1)
		
		# this signal notifies the parent to read a message from the shared file
		elif signalNum == signal.SIGUSR1:
			readMessage()
	
# set up the server	
def Server():
	global originalProc
	global myChildren
	
	# store pid
	originalProc = os.getpid()
	
	
	global minProcs, maxProcs, myName
	
	# set signal handler for all Servers created from main server
	signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGILL, signal_handler)
	signal.signal(signal.SIGABRT, signal_handler)
	
	# only for parent server to keep track of, children may have some copies but should not be read
	if os.getpid() == originalProc:
		# catch SIGUSR1 for reading messages
		signal.signal(signal.SIGUSR1, signal_handler)
		
		# set globals
		myChildren = [] 
		minProcs = int(sys.argv[2])
		maxProcs = int(sys.argv[3])
		myName = sys.argv[4]
		print("Server %s created with pid %d"%(myName,originalProc))
		
	
	# create children up to minProcs
	for i in range(0, minProcs):
		createProcess()
	
	
	# keep running
	while(True):
		pass

# call Server()		
Server()
	

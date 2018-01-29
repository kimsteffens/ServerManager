# ServerManager
A small Python command-line program that simulates the spawning of different servers from a parent. It practices using system calls like "fork" as well as utilizing concepts such as IPC. Servers get spawned off from a parent server (ServerManager) based on user commands in a Unix terminal. Processes can further be forked from these child servers. When first spawned, a child server has a minimum and maximum number of child processes that may be running at once. There is no going below or beyond these user-defined numbers.

## Files and Program Structure

**ServerManager.py:**

This file is what is first run. It processes input from the user. It spawns off servers and keeps track of them. It does not keep track of any servers that are spawned by a server: the parent server manages that in Server.py. 

Commands from the user are not fully processed in this program, but rather are sent to the necessary Server to be dealt with through a shared file. The servers are signaled SIGUSR1 when a command needs to be read. 

**Server.py:**

This program handles the Servers and their children. The parent server keeps track of all children servers spawned, minProcs, maxProcs, and the server name.
 The parent Server reads in commands when signaled a SIGUSR1 from the parent (or a child in the case that this child needs to be restarted).

## Communication through Shared Memory
IPC is through shared memory using a shared file (shm.txt).
 
The ServerManager and each parent server has access to this file. The ServerManager writes the commands and signals the parent server to read them using SIGUSR1. Each parent server reads from this file and processes the commands. 
The only exception is when a server child receives an unusual command that causes it to reset. In this case the child server may write to shared memory and signal the parent.

Each time the shm.txt file is to be read, it gets mmapped. This maps the file to virtual memory so that all readers are kept up to date on what is in the file.

## User Commands:
CreateServer minProcs maxProcs ServerName :
  
A new child gets forked from ServerManager and execlp’s Server.py with the given command as arguments. The Server sets itself up by reading in the arguments given to it into global variables upon creation. It then spawns minProcs number of children.

AbortServer serverName :
  
The Server gets notified that it should abort by ServerManager. The parent server then loops through all its children, killing them one by one. It finally then kills itself.

createProcess serverName:
  
ServerManager sends the command. The parent server checks to make sure there are not too many processes before creating a new one. It does this by forking itself, and then killing any children that the parent Server is not a parent of (this makes sure only one process gets created, not several).

abortProcess serverName:
  
ServerManager sends this command, then the parent Server ensure there are not too few processes before it aborts a process on its list.

displayStatus:

First ServerManager prints out its dictionary of servers spawned (the server names and their pids). Then it informs each parent server to print out its list of each child server spawned.

## Fault Tolerance
Each process in Server.py catches SIGILL and SIGABRT as unusual signals that demand the restart of the server child process. The process that receives these signals will inform the parent to create a new process and delete this processes pid. It does this by writing to the shared file and then signaling the parent- just as ServerManager usually does.


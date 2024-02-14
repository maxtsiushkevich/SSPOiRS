# SSPOiRS
Network system software and distributed systems

# Lab work 1

It is necessary to implement a simple server program using the TCP protocol. 
The server must support the execution of several commands, but at least it must support the execution of the following (or similar):
  1. ECHO (returns data transmitted by the client after the command),
  2. TIME (returns the current server up-time),
  3. CLOSE (EXIT/QUIT) (closes the connection).

The client is supposed to use system utilities: telnet, netcat and others.

# Lab work 2

It is necessary to implement a client and a serial server that allow file sharing. 
The server must continue to support the commands that were implemented in Lab 1, adding a file transfer command to this. 
The request to upload a file to or download from the server must be initiated by the client. Commands can be, for example, UPLOAD/DOWNLOAD.
Files must be transferred using the TCP protocol. 
The implementation should take into account possible exceptional situations related to network problems, such as a physical or programmatic connection failure.
The server is required to support file upload/download recovery. 
If another client managed to connect, or the server was restarted, then the server has every right to delete files related to incomplete downloads.

# Lab work 3 

Add the ability to transfer files to the client and server using the UDP protocol. 
Pay attention to handling exceptional situations, such as a physical or software connection failure. 
Implement:
  1.  Mechanism for monitoring the sequence of received datagrams
  2. timeout mechanism – periodic sending of control packets to check the availability of the other side of the interaction, termination of the session with the client / server in case of absence of control packets during a fixed time interval
  3. control of the transmission flow — reducing the load on the receiver in case of slow processing

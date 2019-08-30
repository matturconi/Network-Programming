#!usr/bin/python

"""
Sender
The goal is to create a reliable transport protocol.  This is the sender side of that protocol.
Data is transferred over UDP.
Michael Santamaria
"""

import sys
import burst_transfer

MAX_BURST_SIZE = 100    #Size of burst window
DATA_SECTION_SIZE = 200  #Size of data section for packets (small numbers are good for testing)

if __name__=="__main__":
    #Start by parsing arguments given to the sender
    #Sender should be given the following args:
    #ip, port, fileToTransfer

    if(len(sys.argv) != 5):
        print("Usage")
        print("[IP][Port][DestPort][File]")
        exit()

    ip = sys.argv[1]
    port = int(sys.argv[2])
    destport = int(sys.argv[3])
    f = sys.argv[4]
    if(burst_transfer.send_file(f,ip,port,destport, MAX_BURST_SIZE, DATA_SECTION_SIZE)):
        print("File transferred successfully")
"""
    #In the case that the user wants to send multiple files we need a list of files
    i = 4
    while i!= len(sys.argv):
        fileList.append(sys.argv[i])
        i+=1

    #now we have a list of files for which we can transfer individually
    #the list result will hold the results of each file's attempt to transfer
    transferSuccess = []
    for f in fileList:
        transferSuccess.append(burst_transfer.send_file(f,ip,port,destport, MAX_BURST_SIZE, ))
"""

#!usr/bin/python
import socket
import struct
import packetize
import time

"""The burst_transfer will recieve a file, and ip address, a port, and a mtu.
   With this data the sender function will attempt to send the file to the reciever/server
   First the file will be broken into packets which can be transfered.
   Packetize will be initialized with a file and burst size.  It will return
   the same number of packets as the burst size which are saved into a burst list.
   The first burst will send all the packets to the server and wait for each one to recieve
   an ack.  The burst will not shift until each packet has been acked.
"""
def send_file(filename, ip, port, dport, burst_window, data_size = 63986):  #if a data_size is not provided, use the default packet size
        #First step is opening connection
        UDP_IP = ip
        UDP_PORT = port
        DEST_PORT = dport
        fd = filename
        MAX_BURST_SIZE = burst_window
        DATA_SIZE = data_size

        """First send the ready ack.  Ready ack is a packet with ack flag 1.  Python udp pipes will
           automatically send the sender address so I don't need to include that yet.  When burst_transfer
           recieves that ack transfer from the reciever, the coonstant for source and destination will be set.
           Ready ack will have the maximum sequence number
        """
        #ready ack
        firstPacket = packetize.getHeader(0,UDP_PORT,DEST_PORT,MAX_BURST_SIZE,0,1)    #get the header for the inital ack
        firstPacket = firstPacket[:12]
        firstPacket += packetize.compute_checksum(firstPacket)

        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)   #Make a socket to use for our transfer
        sock.bind(('',UDP_PORT))
        sock.settimeout(.5)
        #Try sending/receiving an ack and catch a timeout.
        while True:
            try: #try to send the ready packet and receive a reply
                start = time.time()
                sock.sendto(firstPacket,(UDP_IP,DEST_PORT))  #send the inital packet over the pipe
                data,RECV_ADDR = sock.recvfrom(14)  #read 14 bytes, or one header
                #print("Recieved ",data)     #Just so I know what it says
                results = check_checksum(data)  #returns a tuple with correct/incorrect, seqNum, ackFlag
                if(results[0]):    #confirm ready ack was recieved
                    break

            except socket.timeout:  #Socket times out after data isn't corrrect
                continue

        timeout = time.time()-start
        timeout = timeout * MAX_BURST_SIZE
        timeout = timeout + (timeout * .25)
        print(timeout)
        sock.settimeout(timeout)

        #ready ack finished send bursts
        burstObj = packetize.packet_burst(fd,MAX_BURST_SIZE,UDP_PORT,RECV_ADDR[1],DATA_SIZE)   #send file to packetize function to prepare for sending
        packetList = []
        while True:
            if((not burstObj.eof) and len(packetList) == 0):
                packetList = burstObj.getBurst()    #get a packet burst
            try:
                for packet in packetList:
                    sock.sendto(packet,(UDP_IP,DEST_PORT))

                #recieve acks
                ackList =[]
                while True:
                    data, RECV_ADDR = sock.recvfrom(14) #read ack from socket
                    ackList.append(data)   #add data to list

            except socket.timeout:  #on socket timeout remove the packets we have acks for
                #possible sequence numbers for packets are in the range 0-(MAX_BURST_SIZE-1)
                #because of this, turning acknowledgment sequence numbers into integers in a sorted list
                #make it easy to quickly remove them
                ackNums = []
                while(len(ackList) > 0):    #While we have not parsed an ack
                    #parse an ack
                    temp = check_checksum(ackList[0])   #temp[0] states checksum, [1] states the seqNum, [2] states the ackFlag
                    if(not(temp[1] in ackNums)):
                        ackNums.append(temp[1][0])
                    ackList.pop(0)  #don't clutter ack list
                ackNums.sort(reverse = True)    #sort the list from greatest to least

                mappingList = []    #needs to be a list of sequence nums that are acked
                for i in packetList:
                    temp = struct.unpack(">H",i[8:10])
                    mappingList.append(temp[0])

                for i in ackNums:   #i is the sequence number of ack'ed packet
                    #check if i = a sequence number in the packetlist
                    if(i in mappingList):
                        packetList.pop(mappingList.index(i))
                        mappingList.remove(i)

                if(burstObj.eof and len(packetList) == 0):   #if this is the last burst we need to send and all packets are sent
                    break
                else:
                    continue

        #send ending ack
        lastPack = packetize.getHeader(0,UDP_PORT,UDP_PORT,0,burstObj.burNum,100)    #get the header for the inital ack
        lastPack = lastPack[:12]
        lastPack += packetize.compute_checksum(lastPack)

        while True:
            try: #try to send the end packet and receive a reply
                sock.sendto(lastPack,(UDP_IP,DEST_PORT))  #send the inital packet over the pipe
                data,RECV_ADDR = sock.recvfrom(14)  #read 14 bytes, or one header
                results = check_checksum(data)  #returns a tuple with correct/incorrect, seqNum, ackFlag
                if(results[0] == True and results[2][0] == 100):    #confirm end ack was recieved
                    sock.close()    #close the socket connection
                    print("TIME ELAPSED: ", (time.time()-start))
                    return 1

            except socket.timeout:  #Socket times out after data isn't corrrect
                continue


def check_checksum(packet):
    seqNum = struct.unpack(">H",packet[8:10])
    ackFlag = struct.unpack(">H",packet[10:12])
    return (b'\x00\x00' == packetize.compute_checksum(packet), seqNum,ackFlag)

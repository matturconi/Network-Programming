import socket
import struct
import packetize
import sys
import time

TIMEOUT = 0.1

#Inserts the computed checksum into a protocol X header provided and returns it
def insert_checksum(dat):
    readyAck = dat[:12] + packetize.compute_checksum(dat)
    return readyAck

#Verifies the checksum of some data that it is passed to it and returns a boolean value
def verify_checksum(data):
    chk = packetize.compute_checksum(data)
    #print("Checksum")
    #print(chk)
    return b'\x00\x00' == chk

#This class is used to parse the header and hold the values of a packet
class datHead:
    def __init__(self):
        self.sourcePort = 0
        self.destPort = 0
        self.pakLen = 0
        self.burstNum = 0
        self.seqNum = 0
        self.ackFlag = 0
        self.checksum = 0

    def parse(self, data):
        header = data[0:14]
        tup = struct.unpack(">HHHHHHH", header)
        self.sourcePort = tup[0]
        self.destPort = tup[1]
        self.pakLen = tup[2]
        self.burstNum = tup[3]
        self.seqNum = tup[4]
        self.ackFlag = tup[5]
        self.checksum = tup[6]

    def __str__(self):
        s = str(self.sourcePort) + ", " + str(self.destPort) + ", " + str(self.pakLen) + ", "\
                 + str(self.burstNum) + ", " + str(self.seqNum) + ", " + str(self.ackFlag) + \
                 ", " + str(self.checksum)
        return s

'''
    This function runs a server like code that will listen for formatted data from a sender
    running a version of protocol X.
    Protocol X ensures reliable data transfer betweeen a sender and a receiver

    Parameters:
        localAddr = the address that this receiver is listening on
        listenPort = the port that this server is listening on

    Returns:
        Current version writes all received data to a file called recvd.txt
'''
def receiver(localAddr, listenPort):
    LISTEN_ADDR = localAddr
    LISTEN_PORT = listenPort
    DEST_PORT = 0
    DEST_ADDR = ""

    #Set up the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((LISTEN_ADDR, LISTEN_PORT))

    #Opens file descriptor to store received data
    fd = open("recvd.txt", "w")

    burstNum = 0        #The current burst number
    burstSize = 0       #Maximum burst size sent by the sender
    packsRecv = []      #Holds ints that relate to the sequence num of each received packet
    databuf = []        #Holds the data of all the received packets
    lstConsecPak = -1   #A sequential placeholder so all data is not written out of order
    startT = 0          #Used to find the RTT of the first data packet
    endT = 0
    timeoutSet = True   #Used to set the timeout rate

    head = datHead()    #Object to hold the header data

    while(True):
        #Read the header
        try:
            buf, recvAddr = sock.recvfrom(65000)
        except socket.timeout:
            continue

        #Parse the header into a header object
        head.parse(buf[:15])

        if(not verify_checksum(buf)):
            continue

        #Set the timeout rate
        if(timeoutSet == False):
            endT = time.time()
            TIMEOUT = (endT - startT) * 1.5
            sock.settimeout(TIMEOUT)
            timeoutSet = True

        #Parse out the data
        data = buf[14:].decode()


        #Check if it is a ready ack from the sender
        if(head.ackFlag == 1):
            startT = time.time()        #Gets RTT start time
            #Send Ready ACK
            readyAck = insert_checksum(packetize.getHeader(14, LISTEN_PORT, DEST_PORT, 0, 0, 1))

            #This should get the sender address
            DEST_ADDR = recvAddr[0]

            DEST_PORT = head.sourcePort
            burstSize = head.seqNum
            #packsRecv = [-1]*burstSize
            packsRecv = []
            databuf = [""]*burstSize

            #Sends the ready ack to the sender
            sock.sendto(readyAck, (DEST_ADDR, DEST_PORT))

            #Set the boolean timeoutSet to False so the timeout gets set next loop
            timeoutSet = False
            continue

        #Is this an end ack
        if(head.ackFlag == 100):
            for x in range(lstConsecPak, len(databuf)):
                fd.write(databuf[x])
                databuf[x] = ""
            endAck = insert_checksum(packetize.getHeader(14, LISTEN_PORT, DEST_PORT, 0, 0, 100))
            sock.sendto(endAck, (DEST_ADDR, DEST_PORT))
            try:
                data = sock.recv(65000)
                #This is the second end ack so close the socket
                if(struct.unpack(">H", data[10:12])[0] == 100):
                    sock.close()
                    break
            except socket.timeout:
                sock.close()
                break

        #This must be a new burst sent by the sender so clean house
        if(head.burstNum != burstNum):
            for x in range(lstConsecPak, len(databuf)):
                fd.write(databuf[x])
                databuf[x] = ""
            databuf = [""]*burstSize
            burstNum += 1
            #packsRecv = [-1]*burstSize
            packsRecv = []
            lstConsecPak = -1

        #Sends the received ack to the sender
        recvAck = insert_checksum(packetize.getHeader(14, LISTEN_PORT, DEST_PORT, head.seqNum, burstNum, 10))
        sock.sendto(recvAck, (DEST_ADDR, DEST_PORT))

        #Checks if sent packet is a duplicate
        if(head.seqNum in packsRecv):
            continue

        #Stores the packet number in the received tracker list
        packsRecv += [head.seqNum]

        #Manage the received data
        databuf[head.seqNum] = data             #Add data to data buffer
        if(head.seqNum - 1 == lstConsecPak):    #Checks to see if this is a consecutive packet
            lstConsecPak = head.seqNum          #Updates the consecutive packet
            fd.write(databuf[lstConsecPak])
            databuf[lstConsecPak] = ""
            i = lstConsecPak
            #This loop checks if there are any saved packets after this
            while((i != burstSize-1) and (databuf[i+1] != "")):
                fd.write(databuf[i+1])          #that are a higher order than the current packet
                databuf[i+1] = ""
                i += 1


def main():
    if(len(sys.argv) != 3):
        print("USAGE:")
        print("[Listen Address] [Listen Port]")
        return
    receiver(sys.argv[1], int(sys.argv[2]))

if __name__=="__main__":
    main()

#!usr/bin/python
import sys
import struct
import copy

#MAX PACKET SIZE SHOULD BE 64000

class packet_burst:
    def __init__(self, fd,maxBurstSize, sPort, dPort, data_size):
        self.burNum = 0
        self.sPort = sPort
        self.dPort = dPort
        self.maxBurstSize = maxBurstSize
        self.packet = ""
        self.packet_length = 0
        self.burst = []
        self.burstSize = 0;
        self.chunksize = data_size  #Number of data bytes in the packet
        self.fd = open(fd,mode ='rb')
        self.ackflag = 0
        self.eof = 0

    def getBurst(self):
        packetList = []
        for i in range(self.maxBurstSize): #i is the sequence number of a packet in a burst
            packetList.append(self.getPacket(i))    #add packets to burst
            if(self.eof):
                break

        self.burNum+=1   #Burst number will increase by one on the next burst
        return packetList

    def getPacket(self, seqNum):
        temp = bytearray()  #new bytearray to be a packet
        p = self.bytesFromFile()    #get data section of packet from file

        temp.extend(getHeader(self.packet_length, self.sPort, self.dPort, seqNum, self.burNum, self.ackflag))   #get header for packet
        temp.extend(p)  #add the data section of our packet to the header

        chksum = compute_checksum(temp) #drop a checksum in there
        temp[12:14] = chksum
        return temp #return the full packet

    def bytesFromFile(self):
        """This function is capable of creating packets with an empty data section"""
        content = self.fd.read(self.chunksize)  #get one packet's worth of data in bytes
        self.packet_length = len(content)   #set packet length attribute
        if(self.packet_length == 0):    #EOF
            self.eof = 1
        return content

def getHeader(packet_len,  sPort, dPort, seqNum, burNum, akFlag):
    sourcePort = sPort
    destPort = dPort
    checksum = 0
    sequenceNum = seqNum
    burstNum = burNum
    ackFlag = akFlag
    packetLength = 14 + packet_len
    header = struct.pack(">HHHHHHH", sourcePort, destPort, packetLength, burstNum, sequenceNum, ackFlag, checksum)
    return header


def compute_checksum(s):
    x = copy.deepcopy(s)
    size = len(x)
    if(size % 2 == 1):
        x += b'\x00'
        size += 1
    tot = 0

    for c in range(size//2):
        tot += struct.unpack(">H", x[0:2])[0]
        x = x[2:]
    tot = tot & 0xFFFF
    tot = 0xFFFF - tot
    return struct.pack(">H", tot)

def main():
    fileD = sys.argv[1]
    maxBurst = 1;
    burstObj = packet_burst(fileD,maxBurst)
    burstObj.getPacket();

if __name__=="__main__":
    main();

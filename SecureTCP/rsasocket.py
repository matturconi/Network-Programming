import socket
import rsa

class rsaSocket(socket.socket):
    timeout = socket.timeout

    def __init__(self, fd=None):
        if fd != None:
            super().__init__(socket.AF_INET, socket.SOCK_STREAM, 0, fileno=fd)
        else:
            super().__init__(socket.AF_INET, socket.SOCK_STREAM)

        self.keys = False
        self.encrypter = None

    def secureSend(self, data):
        #GOTTA GET THOSE KEYS!!!!
        #This if block should only be executed by a client so look for the keys the server is sending
        if self.keys == False:
            #2048 will likely be more than the max packet len since we only use 512 bit keys
            #in this iteration
            recvData = super().recv(2048).decode()
            recvData = recvData.split("\n")

            #Now send the server the client keys NO ENCRYPT FOR NOW
            msg = self.genKeyMsg()
            super().send(msg)
            #Store the public keys received from the server
            self.encrypter.set_pub_keys(int(recvData[1]), int(recvData[2]))

            #Should wait for a confirmation from the server
            ack = super().recv(10).decode()
            if ack != "READY":
                return -1

            #Sets keys to true because key exchange is over
            self.keys = True

        #Actually encrypt the message and send it
        eData = self.encrypter.encrypt(data)
        super().send(eData.encode())

    def genKeyMsg(self):
        msg = "NEW KEY\n"
        self.encrypter = rsa.rsa()
        pubkey = self.encrypter.get_pub_keys()
        N = str(pubkey[0])
        e = str(pubkey[1])
        msg += N + "\n"
        msg += e + "\n"
        return msg.encode()

    def accept(self):
        #Converts the incoming socket to one of rsasocket type
        sock, sendaddr = super()._accept()
        sock = rsaSocket(sock)
        sock.setblocking(True)

        #Send the sever pub keys to the client
        msg = sock.genKeyMsg()
        sock.send(msg)
        return sock, sendaddr

    def parseHead():
        return

    def secureRecv(self, size):
        size += self.encrypter.padSize - (size % self.encrypter.padSize)
        #REceive the data
        #Check if it is a new key for the server
        if self.keys == False:
            #Wait for the client to send its pub keys back
            pubkeys = super().recv(2048).decode()
            pubkeys = pubkeys.split("\n")
            self.encrypter.set_pub_keys(int(pubkeys[1]), int(pubkeys[2]))

            #Send ack that says key exchange is done
            super().send("READY".encode())

            #Set the connected socket to have set up keys
            self.keys = True

        try:
            eData = super().recv(size).decode()
        except socket.timeout:
            return ""
        #Actually decrypt the message and return it
        dData = self.encrypter.decrypt(eData)
        return dData

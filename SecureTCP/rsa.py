'''
The following functions were obtained from https://medium.com/@prudywsh/how-to-generate-big-prime-numbers-miller-rabin-49e6e6af32fb
is_prime()
generate_prime_candidate()
generate_prime_number()
'''
from random import randrange, getrandbits, randint


class rsa():
    bitlen = 512
    lower = 2**(bitlen-2)
    upper = 2**bitlen
    Nlen = 0
    partitionSize = 300
    msgsize = 0
    N = 0       #Holds the working N to encode Messages and should be set after init
    e = 0       #Holds the working e to encode Messages and should be set after init
    phi = 0
    pubKey = (N,e)      #Holds this encrypters public keys, should not be changed after init
    privKey = 0
    padSize = 315

    def __init__(self):
        rsa.gen_keys()

    def attr_dump(self):
        s = "\nNlen: " + str(rsa.Nlen)
        s += "\nmsgsize: " + str(rsa.msgsize)
        s += "\nN: " + str(rsa.N)
        s += "\ne: " + str(rsa.e)
        s += "\nphi: " + str(rsa.phi)
        s += "\npubkey: " + str(rsa.pubKey)
        s += "\nprivKey: " + str(rsa.privKey) + "\n"
        return s

    """Extended Euclidean Algorithm. Brilliant.org. Retrieved 10:56, April 18, 2019, from https://brilliant.org/wiki/extended-euclidean-algorithm/"""
    def egcd(a, b):
        x,y, u,v = 0,1, 1,0
        while a != 0:
            q, r = b//a, b%a
            m, n = x-u*q, y-v*q
            b,a, x,y, u,v = a,r, u,v, m,n
        gcd = b
        return gcd, x, y

    def is_prime(n, k=128):
        """ Test if a number is prime
            Args:
                n -- int -- the number to test
                k -- int -- the number of tests to do
            return True if n is prime
        """
        # Test if n is not even.
        # But care, 2 is prime !
        if n == 2 or n == 3:
            return True
        if n <= 1 or n % 2 == 0:
            return False
        # find r and s
        s = 0
        r = n - 1
        while r & 1 == 0:
            s += 1
            r //= 2
        # do k tests
        for _ in range(k):
            a = randrange(2, n - 1)
            x = pow(a, r, n)
            if x != 1 and x != n - 1:
                j = 1
                while j < s and x != n - 1:
                    x = pow(x, 2, n)
                    if x == 1:
                        return False
                    j += 1
                if x != n - 1:
                    return False
        return True

    def generate_prime_candidate(length):
        """ Generate an odd integer randomly
            Args:
                length -- int -- the length of the number to generate, in bits
            return a integer
        """
        # generate random bits
        p = getrandbits(length)
        # apply a mask to set MSB and LSB to 1
        p |= (1 << length - 1) | 1
        return p

    def generate_prime_number(length):
        """ Generate a prime
            Args:
                length -- int -- length of the prime to generate, in          bits
            return a prime
        """
        p = 4
        # keep generating while the primality test fail
        while not rsa.is_prime(p, 128):
            p = rsa.generate_prime_candidate(length)
        return p

    #Sets the public keys received by another sender
    def set_pub_keys(self, N, e):
        rsa.N = N
        rsa.e = e

    #Gemerates the public and private keys for the encryption system
    def gen_keys():
        length = rsa.bitlen
        p, q = 0,0
        while(p == q):
            p = rsa.generate_prime_number(length)
            q = rsa.generate_prime_number(length)
        rsa.N = p * q
        rsa.phi = (p-1)*(q-1)
        gcd = 0

        while(gcd != 1):
            rsa.e = randint(rsa.lower, rsa.upper)
            gcd, x, y = rsa.egcd(rsa.e, rsa.phi)
            if x < 0:
                gcd = 0
        rsa.privKey = x
        rsa.pubKey = (rsa.N, rsa.e)
        rsa.Nlen = len(str(rsa.N))
        rsa.Nlen -= rsa.Nlen%3
        rsa.msgsize = rsa.Nlen - 3

    def get_pub_keys(self):
        return self.pubKey

    #This function is crutial to the algorithm. It makes it possible to compute exponents
    #of such a high power and find the modulous
    def mod_exp(x, y, p):
        res = 1
        x = x % p
        while (y > 0):
            if (y & 1) == 1:
                res = (res*x) % p
            y = y>>1
            x = (x*x) % p
        return res


    def encrypt(self, data):
        #Convert the datastring to a number string
        numstr= ''
        for x in range(len(data)):
            num = str(ord(data[x]))
            numstr += (3 - len(num)) * '0' + num
        #Take the number string and encrypt it
        estring = ''
        while(len(numstr) > rsa.msgsize):
            m = int(numstr[:rsa.msgsize])
            num = str(rsa.mod_exp(m, rsa.e, rsa.N))
            #make each msg fixed len so pad with zeros
            l = len(num)
            if l != rsa.padSize:
                num = ((rsa.padSize - l) * "0") + num
            estring += num
            numstr = numstr[rsa.msgsize:]

        if len(numstr) != 0:
            num = str(rsa.mod_exp(int(numstr), rsa.e, rsa.N))
            l = len(num)
            if l != rsa.padSize:
                num = ((rsa.padSize - l) * "0") + num
            estring += num

        return estring

    def decrypt(self, data):
        #Decrypt the data
        rawdata = ''

        while(len(data) != 0):
            c = int(data[:rsa.padSize])
            m = str(rsa.mod_exp(c, rsa.privKey, rsa.pubKey[0]))
            l = len(m)
            if (l % 3) != 0:
                m = ((3-(l%3))*"0") + m
            rawdata += m
            data = data[rsa.padSize:]
        #convert the raw data back to letters
        string = ''
        for x in range(0, len(rawdata), 3):
            string += chr(int(rawdata[x:x+3]))
        return string


'''
bob = rsa()
alice = rsa()
bKeys = bob.get_pub_keys()
aKeys = alice.get_pub_keys()
bob.set_pub_keys(aKeys[0],aKeys[1])
alice.set_pub_keys(bKeys[0], bKeys[1])
msg = "hello hello hi how are you today.Hello howis your dayHello howis your dayHello howis your dayHello howis your dayHello howis your dayHello howis your dayHello howis your dayHello howis your day Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat\
        with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me.  Tosay it is going to rain so i brought a coat with me. ".encode()
msg = bob.encrypt(msg.decode())
print(alice.decrypt(msg))
'''

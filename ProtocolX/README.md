Our protocol is known as Protocol X.  We created this protocol from the ground up, using UDP pipes as the transport method.
The sender program will send a file to the reciever on a specified address.  The file is broken up into packets, and those
packets are sent in bursts.  Burst size and data section size (size of packet) are specified in sender.py.  Each burst is a
set of packets which are sent/acked together in a sliding window style.  Unlike sliding window, our burst window will only change
once each packet in the current window is acknowledged.  burst_transfer.py will resend the current burst until the entire burst is fully
acknowledged.
The receiver will receive each packet and send back the correspoding ack packet to the sender confirming that it received the packet.  Info is sent the the application if it has received sequential data to avoid out of order data transfer. 
If data was received out of order it will wait until it receives the out of order packet to send the data to the application layer.
At the end of each burst the receiver flushes its buffers and writes all remaining received data to the application layer.
Once all the bursts have been sent the sender and receiver will send end acks to eachother before quitting and closing their sockets.

SENDER              RECEIVER
----------------------------
BEGIN ----------->  
      <----------   ACK
BURST 1 -------->   
      <----------   ACK
BURST 2 -------->   
      <----------   ACK
ETC...

END   ---------->   
      <----------   OK END

Testing Results:
Durring our testing of our protocol we collected three data points for each type of sending and receiving condition.  We determined that our protocol works in call conditions using our test.txt as the data file.
The time it takes to send this file was quite consistent over the different degrees of sending restrictions.
To see a graph of our open the pdf named Results-Sheet1.pdf

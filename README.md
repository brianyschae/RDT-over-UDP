# RDT-over-UDP
Part of the Networks class. Implementing a Reliable Data Transfer protocol like TCP over UDP (which is not inherently reliable). It is used to transfer a text file from different host machines. It handles any packet loss, packet timeout, packet duplication, and etc.

## Sender
The sender sends packets of text (from input.txt) over UDP to the receiver.

The sender utilizes multi-threading to send multiple packets as quickly as possible.

## Receiver
The receiver receives the packets and sends signals back such as SYN, ACK, EOT, etc.

The receiver ensures reliability of the packets and writes the packets into input.txt.

## Logs
seqnum.log contains the sequence number logs (of packets)
ack.log contains the ACKed packet logs 
N.log contains window size change logs

## To run
Then run the receiver on host2:

`receiver.py host1 <UDP port # to send ACKs> <UDP port # to receive data> <output file name>`

Then run te sender on host3:

`sender.py host1 <UDP port # to send data> <UDP port # to receive ACKs> <timeout interval> <input file name>`


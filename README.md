# RDT-over-UDP
Part of the Networks class. Implementing a Reliable Data Transfer protocol like TCP over UDP (which is not inherently reliable)

# Sender
The sender sends packets of text (from input.txt) over UDP to the receiver. \n
The sender utilizes multi-threading to send multiple packets as quickly as possible.

# Receiver
The receiver receives the packets and sends signals back such as SYN, ACK, EOT, etc. \n
The receiver ensures reliability of the packets and writes the packets into input.txt.

import os
import sys
import argparse
import socket
import math
from packet import Packet

if os.path.exists("arrival.log"):
  os.remove("arrival.log")

# Writes the received content to file
def append_to_file(filename, data):
    file = open(filename, 'a')
    file.write(data)
    file.close()

def append_to_log(packet):
    """
    Appends the packet information to the log file
    """
    p = Packet(packet)

    file = open("arrival.log", 'a')
    
    if p.typ == 3:
        file.write("SYN\n")
    elif p.typ == 2:
        file.write("EOT")
    else:
        file.write(f'{p.seqnum}\n')
    
    file.close()
    

def send_ack(typ, seq_num, ne_addr, ne_port): #Args to be added
    """
    Sends ACKs, EOTs, and SYN to the network emulator. and logs the seqnum.
    """
    
    p = Packet(typ, seq_num, 0, "").encode()

    clientSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

    clientSocket.sendto(p, (ne_addr, int(ne_port)))
    
    return True
    
if __name__ == '__main__':
    # Parse args
    parser = argparse.ArgumentParser(description="Congestion Controlled GBN Receiver")
    parser.add_argument("ne_addr", metavar="<NE hostname>", help="network emulator's network address")
    parser.add_argument("ne_port", metavar="<NE port number>", help="network emulator's UDP port number")
    parser.add_argument("recv_port", metavar="<Receiver port number>", help="network emulator's network address")
    parser.add_argument("dest_filename", metavar="<Destination Filename>", help="Filename to store received data")
    args = parser.parse_args()

    # Clear the output and log files
    open(args.dest_filename, 'w').close()
    open('arrival.log', 'w').close()

    expected_seq_num = 0 # Current Expected sequence number
    seq_size = 32 # Max sequence number
    max_window_size = 10 # Max number of packets to buffer
    recv_buffer = {}  # Buffer to store the received data
    mostrecentreceived = -1

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('', int(args.recv_port)))  # Socket to receive data

        while True:
            # Receive packets, log the seqnum, and send response
            message, clientAddress = s.recvfrom(1024)
            
            
            append_to_log(message)
            packet1 = Packet(message)

            if packet1.typ == 3:
                send_ack(3, packet1.seqnum, args.ne_addr, args.ne_port) # SYN
            else:
                if packet1.seqnum == expected_seq_num:
                    if packet1.typ == 2:
                        send_ack(2, packet1.seqnum, args.ne_addr, args.ne_port) # EOT
                        break
                    else:
                        # Correct receive
                        append_to_file(args.dest_filename, packet1.data)

                        i = (packet1.seqnum + 1) % 32
                        while i in recv_buffer:
                            if recv_buffer[i].seqnum == i:
                                append_to_file(args.dest_filename, recv_buffer[i].data)
                                expected_seq_num = i
                                recv_buffer.pop(i)

                                i = (i + 1) % 32
                            else:
                                break
                    
                        send_ack(0, expected_seq_num, args.ne_addr, args.ne_port) # ACK

                        mostrecentreceived = expected_seq_num
                        expected_seq_num = (expected_seq_num + 1) % 32
                else:
                    if expected_seq_num < packet1.seqnum <= expected_seq_num + max_window_size:
                        recv_buffer[packet1.seqnum - expected_seq_num] = packet1
                    
                    send_ack(0, mostrecentreceived, args.ne_addr, args.ne_port) # ACK

            
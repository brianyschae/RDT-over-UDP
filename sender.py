#!/usr/bin/env python3

import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import threading
import argparse
import socket

from packet import Packet

packets = {}
seqnum = 0
open('seqnum.log', 'w').close()
open('N.log', 'w').close()
open('ack.log', 'w').close()

class Sender:
    def __init__(self, ne_host, ne_port, port, timeout, send_file, seqnum_file, ack_file, n_file, send_sock, recv_sock):

        self.ne_host = ne_host
        self.ne_port = ne_port
        self.port = port
        self.timeout = timeout / 1000 # needs to be in seconds

        self.send_file = send_file # file object holding the file to be sent
        self.seqnum_file = seqnum_file # seqnum.log
        self.ack_file = ack_file # ack.log
        self.n_file = n_file # N.log


        self.send_sock = send_sock
        self.recv_sock = recv_sock

        num = 0
        while True:
            data = send_file.read(500)
            if not data:
                break
            packets[num] = Packet(1, num % 32, len(data), data)
            num += 1


        # internal state
        self.lock = threading.RLock() # prevent multiple threads from accessing the data simultaneously
        self.window = [] # To keep track of the packets in the window
        self.window_size = 1 # Current window size 
        self.timer = None # Threading.Timer object that calls the on_timeout function
        self.timer_packet = None # The packet that is currently being timed
        self.current_time = 0 # Current 'timestamp' for logging purposes
        self.syntimer = None
        self.eottimer = None

    def run(self):
        self.recv_sock.bind(('', self.port))
        self.perform_handshake()

        # write initial N to log
        self.n_file.write('t={} {}\n'.format(self.current_time, self.window_size))
        self.current_time += 1

        recv_ack_thread = threading.Thread(target=sender.recv_ack)
        send_data_thread = threading.Thread(target=sender.send_data)
        recv_ack_thread.start()
        send_data_thread.start()
        
        recv_ack_thread.join()
        send_data_thread.join()
        exit()



    def send_syn(self):
        syn_packet = Packet(3, 0, 0, "")
        self.transmit_and_log(syn_packet)
        self.syntimer = threading.Timer(3.0, self.send_syn)
        self.syntimer.start()
        return True

    def send_eot(self):
        eot_packet = Packet(2, seqnum % 32, 0, "")
        self.transmit_and_log(eot_packet)
        self.eottimer = threading.Timer(self.timeout, self.send_eot)
        self.eottimer.start()
        return True
    

    def perform_handshake(self):
        "Performs the connection establishment (stage 1) with the receiver"

        syn_packet = Packet(3, 0, 0, "")
        self.transmit_and_log(syn_packet)

        self.syntimer = threading.Timer(3.0, self.send_syn)
        self.syntimer.start()
        message, clientAddress = recv_sock.recvfrom(1024)
        decode = Packet(message)

        typ, seqnum, length, data = decode.decode()
        if typ == 3:
            self.ack_file.write('t=-1 SYN\n')
            self.syntimer.cancel()

        return True    

    def transmit_and_log(self, packet):
        """
        Logs the seqnum and transmits the packet through send_sock.
        """

        p = packet.encode()
        p1 = Packet(p)
        if p1.typ == 3:
            self.seqnum_file.write('t=-1 SYN\n')
        elif p1.typ == 1:
            self.seqnum_file.write(f't={self.current_time} {p1.seqnum}\n')
        elif p1.typ == 2:
            self.seqnum_file.write(f't={self.current_time} EOT')
        
        encoded = p
        send_sock.sendto(encoded,(self.ne_host, int(self.ne_port)))
        return True


    def recv_ack(self):
        """
        Thread responsible for accepting acknowledgements and EOT sent from the network emulator.
        """
        
        while True:
            message, clientAddress = recv_sock.recvfrom(1024)
            decode = Packet(message)

            typ, seqnumrecv, length, data = decode.decode()
            if typ == 0:
                self.ack_file.write(f't={self.current_time} {seqnumrecv}\n')
                with self.lock:
                    tempwindow = [i % 32 for i in self.window]
                    if (seqnumrecv % 32) in tempwindow:

                        if seqnum == len(packets) and len(self.window) == 0:
                            self.timer.cancel()
                            break
                        
                        
                        self.timer.cancel()

                        self.window = self.window[tempwindow.index(seqnumrecv)+1:]
                        if self.window_size < 10:
                            self.window_size += 1
                            self.n_file.write(f't={self.current_time} {self.window_size}\n')
                        
                        if len(self.window) > 0:
                            self.timer_packet = self.window[0]
                            self.timer = threading.Timer(self.timeout, self.on_timeout)
                            self.timer.start()
                    
                    self.current_time += 1
            elif typ == 2:
                self.ack_file.write(f't={self.current_time} EOT')
                self.eottimer.cancel()
                break


    def send_data(self):
        """ 
        Thread responsible for sending data and EOT to the network emulator.
        """
        global seqnum
        
        while True:
            sleep = False
            with self.lock:
                if seqnum == len(packets) and len(self.window) == 0: break
                if seqnum == len(packets): continue
                if self.window == 0: sleep = True
                if len(self.window) < self.window_size:
                    
                    p = packets[seqnum]
                    self.window.append(seqnum)
                    self.transmit_and_log(p)
                    if self.timer is None:
                        self.timer = threading.Timer(self.timeout, self.on_timeout)
                    if not self.timer.is_alive():
                        self.timer = threading.Timer(self.timeout, self.on_timeout)
                        self.timer.start()
                        self.timer_packet = seqnum
                    
                    self.current_time += 1
                    seqnum += 1
                else:
                    sleep = True
            
            if sleep: time.sleep(3)

        with self.lock:
            eot_packet = Packet(2, seqnum % 32, 0, "")
            self.transmit_and_log(eot_packet)

            self.eottimer = threading.Timer(self.timeout, self.send_eot)
            self.eottimer.start()

        return True

    def on_timeout(self):
        """
        Deals with the timeout condition
        """

        with self.lock:
            self.window_size = 1
            self.n_file.write(f't={self.current_time} {self.window_size}\n')
            self.transmit_and_log(packets[self.timer_packet])
            self.timer.cancel()
            self.timer = threading.Timer(self.timeout, self.on_timeout)
            self.timer.start()
            self.current_time += 1

        return True

if __name__ == '__main__':
    # Parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("ne_host", type=str, help="Host address of the network emulator")
    parser.add_argument("ne_port", type=int, help="UDP port number for the network emulator to receive data")
    parser.add_argument("port", type=int, help="UDP port for receiving ACKs from the network emulator")
    parser.add_argument("timeout", type=float, help="Sender timeout in milliseconds")
    parser.add_argument("filename", type=str, help="Name of file to transfer")
    args = parser.parse_args()
   
    with open(args.filename, 'r') as send_file, open('seqnum.log', 'a') as seqnum_file, \
            open('ack.log', 'a') as ack_file, open('N.log', 'a') as n_file, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as send_sock, \
            socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as recv_sock:
        sender = Sender(args.ne_host, args.ne_port, args.port, args.timeout, 
            send_file, seqnum_file, ack_file, n_file, send_sock, recv_sock)
        sender.run()

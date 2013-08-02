#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Praat send operations

entry-point : main()

@author: Olivier BLIN
"""

import sys
import json
import socket
import argparse
from time import time, sleep
from threading import Thread
from subprocess import Popen, PIPE


SERVER_IP_POOL = [
    ("192.168.1.123", 5005),
    ("192.168.1.134", 5005)
]

SERV_PORT = 5005
CLIENT_PORT = 5004
SOCKET_BUFFER = 1500
NB_THREAD = 1


class RingList():
    def __init__(self):
        self.lelem = list()
        self.pos = 0

    def add(self, elem):
        self.lelem.append(elem)

    def get(self):
        if len(self.lelem) > 0:
            if self.pos < len(self.lelem):
                self.pos += 1
                return self.lelem[self.pos-1]
            else:
                self.pos = 1
                return self.lelem[0]
                



# --------------------------------
# Parser
def parser():
    """
    Create parser class to check input arguments
    """
    parser = argparse.ArgumentParser()
    # init
    parser.description = "%s" % ("Praat multi-launch")

    parser.add_argument("-t", "--thread", type=int, help="thread number", default=NB_THREAD)
    parser.add_argument("-c", "--cport", type=int, help="client port", default=CLIENT_PORT)
    return parser


def main():
    """
    main function
    """
    args = parser().parse_args()

    print "Client port :", args.cport
    print "Instance number :", args.thread
    print "Server IP pool :"
    for addr in SERVER_IP_POOL:
        print "\t%s:%i" % (addr[0], addr[1])

    print "------------------"

    # connection socket
    sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP


    counter = 0
    spool = RingList()
    for addr in SERVER_IP_POOL:
        spool.add(addr)


    server_sock = None
    try:
        start_t = time()
        for i in range(args.thread):
            message = dict()
            message["id"] = i
            message["cmd"] = "Do it !"
            message["port"] = args.cport

            addr = spool.get()
            if addr is not None:
                sock.sendto(json.dumps(message), addr)
                print "Send task to %s:%i" % (addr[0], addr[1])

        print "Wait..."

        # socket for instructions
        server_sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
        server_sock.bind(("", args.cport))

        while counter < args.thread:
            counter += 1
            data, addr = server_sock.recvfrom(SOCKET_BUFFER)
            info = json.loads(data)
            print "From %s - Id thread %i :" % (addr[0], info["id"])
            for k in ["stdout", "stderr", "time", "result"]:
                print "\t%s : %r" % (k, info[k])


        print "------------------"
        print "TIME : ", time() - start_t
    except KeyboardInterrupt:
        print "Stopping..."
        print "------------------"
    finally:
        if server_sock is not None:
            server_sock.close()

    return 0
    

if __name__ == "__main__":
    sys.exit(main())

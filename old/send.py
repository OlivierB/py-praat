#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Praat

entry-point : main()

@author: Olivier BLIN
"""

import sys
import socket
import argparse
from time import time
from threading import Thread
from subprocess import Popen, PIPE

SERV_NAME = "localhost"
SERV_START_PORT = 10000
NB_THREAD = 1
SOCKET_BUFFER = 1500


class tcp_server(Thread):

    """
    Thread class
    """

    def __init__(self, name, address="localhost", port=10000):
        Thread.__init__(self)

        self.name = name
        self.address = address
        self.port = port
        self.connection = None
        self.sock = None
        self.term = False

    def run(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        print '%s : starting up on %s:%i' % (self.name, self.address, self.port)
        self.sock.bind((self.address, self.port))

        # Listen for incoming connections
        self.sock.listen(1)

        try:
            # Wait for a connection
            # print '%s : waiting for a connection'  % (self.name)
            while not self.term:
                try:
                    self.sock.settimeout(1)
                    self.connection, client_address = self.sock.accept()
                    self.sock.settimeout(None)
                            
                    # print '%s : connection from'  % (self.name), client_address

                    # Receive the data in small chunks and retransmit it
                    while not self.term:
                        try:
                            data = self.connection.recv(SOCKET_BUFFER)
                            if data:
                                if data != "":
                                    print "%s : RECV :"  % (self.name), data
                            else:
                                break
                        except socket.error:
                            print "%s : sock error"  % (self.name)
     
                except socket.timeout:
                    pass

                finally:
                    # Clean up the connection
                    if self.connection is not None:
                        self.connection.close()

        finally:
            # print "%s : FIN" % (self.name)
            if self.sock is not None:
                self.sock.close()


    def stop(self):
        self.term = True
        # Clean up the connection
        if self.connection is not None:
            self.connection.close()

        if self.sock is not None:
            self.sock.close()


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
    return parser


def main():
    """
    main function
    """
    args = parser().parse_args()

    lprocess = list()
    lserver = list()

    try:
        print "Start %i thread(s)" % args.thread
        print "------------------"
        start_t = time()
        for i in range(args.thread):
            srv = tcp_server("Server %i" % (i+1), SERV_NAME, SERV_START_PORT+i+1)
            srv.start()
            lserver.append(srv)
            lprocess.append(Popen(["./praat", "res.praat", SERV_NAME, str(SERV_START_PORT+i+1)], stdout=PIPE))

        print "Wait..."
        for pos, process in enumerate(lprocess):
            out, err = process.communicate()
            print "%s - stdout : " % lserver[pos].name, out.replace('\n', " - ")
        print "------------------"
        print "TIME : ", time() - start_t
    except KeyboardInterrupt:
        pass
    finally:
        for server in lserver:
            server.stop()

    return 0
    

if __name__ == "__main__":
    sys.exit(main())

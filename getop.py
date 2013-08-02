#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Praat get operations

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


SERV_NAME = "localhost"
SERV_PORT = 5005
PRAAT_START_PORT = 10000
PRAAT_PATH = "./praat"
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

        self.result = ""

    def run(self):
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to the port
        # print '%s : starting up on %s:%i' % (self.name, self.address, self.port)
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
                                    # print "%s : RECV :"  % (self.name), data
                                    self.result += data
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


class PortList(object):

    """
    Singleton class to collect websocket data

    clients management
    """

    # Singleton creation
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PortList, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    #  class values
    lports = None

    def config(self, start, end):
        if self.lports is None:
            self.lports = range(start, end)

    def get(self):
        return self.lports.pop()

    def free(self, p):
        self.lports.append(p)



class Praat(Thread):
    def __init__(self, address, info, praat):
        Thread.__init__(self)

        self.address = address
        self.info = info
        self.praat = praat

        self.pref = "Thread %s - Id %i :" % (self.address, self.info["id"])

        self.connect = None
        self.process = None

    def run(self):
        print "From %s - Id %i - praat cmd : %r" % (self.address, self.info["id"], self.info["cmd"])

        
        pl = PortList()
        stdo = ""
        stde = ""
        res = ""

        try:
            port = pl.get()

            # get sendpraat
            self.connect = tcp_server("Thread %s - Id %i" % (self.address, self.info["id"]), SERV_NAME, port)
            self.connect.start()

            # start praat
            start_t = time()
            self.process = Popen([self.praat, "res.praat", SERV_NAME, str(port)], stdout=PIPE)

            # print "%s Wait..." % self.pref
            stdo, stde = self.process.communicate()

            res = self.connect.result

            print "%s End : %r" % (self.pref, res)

        except OSError as e:
            stde = str(e)
        finally:
            send_msg(self.address, self.info["port"], dict(id=self.info["id"], stdout=stdo, stderr=stde, time=(time() - start_t), result=res))
            pl.free(port)
            if self.connect is not None:
                self.connect.stop()
                self.connect = None

        # print "%s TIME : %i" % (self.pref, time() - start_t)

    def stop(self):
        if self.connect is not None:
            self.connect.stop




# --------------------------------
# Parser
def parser():
    """
    Create parser class to check input arguments
    """
    parser = argparse.ArgumentParser()
    # init
    parser.description = "%s" % ("Praat multi-launch")

    parser.add_argument("-p", "--port", type=int, help="server port", default=SERV_PORT)
    parser.add_argument("-l", "--link", help="path to praat", default=PRAAT_PATH)
    
    return parser


def send_msg(ip, port, data):
    # socket for instructions
    sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

    d = json.dumps(data)
    sock.sendto(d, (ip, port))
    sock.close()

def main():
    """
    main function
    """
    args = parser().parse_args()

    # socket for instructions
    server_sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
    server_sock.bind(("", args.port))


    # list of process and associated thread
    lpraat = list()
    counter = 0

    pl = PortList()
    pl.config(PRAAT_START_PORT, PRAAT_START_PORT+100)

    print "Server name :", SERV_NAME
    print "Server port :", args.port
    print "Praat start port :", PRAAT_START_PORT
    print "------------------"

    try:
        print "Wait command..."
        while True:
            data, addr = server_sock.recvfrom(SOCKET_BUFFER)
            info = json.loads(data)
            praat = Praat(addr[0], info, args.link)
            praat.start()
            lpraat.append(praat)
        
    except KeyboardInterrupt:
        print "Stopping..."
        print "------------------"
    finally:
        server_sock.close()
        for praat in lpraat:
            praat.stop()
        pass

    return 0
    

if __name__ == "__main__":
    sys.exit(main())

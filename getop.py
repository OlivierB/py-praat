#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Praat get operations

entry-point : main()

@author: Olivier BLIN
"""

import sys
import os
import json
import socket
import argparse
import base64
from tempfile import NamedTemporaryFile
from time import time, sleep
from threading import Thread
from subprocess import Popen, PIPE

from pylib.common import RingList, send_udp_msg

SERV_NAME = "localhost"
SERV_PORT = 5005
PRAAT_START_PORT = 10000
PRAAT_PATH = "./praat"
SOCKET_BUFFER = 50000

MAX_THREAD = 1


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
        # if self.lports is None:
        #     self.lports = range(start, end)
        if self.lports is None:
            self.lports = RingList()
            for i in range(start, end):
                self.lports.add(i)

    def get(self):
        # return self.lports.pop()
        return self.lports.get()

    def free(self, p):
        # self.lports.append(p)
        pass



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
        start_t = time()
        port = pl.get()
        self.file = None

        try:
            # temporary script file
            self.file = NamedTemporaryFile(mode='w', suffix='.praat', prefix='script_')
            self.file.write(base64.b64decode(self.info["script"]))
            self.file.flush()

            # get sendpraat
            self.connect = tcp_server("Thread %s - Id %i" % (self.address, self.info["id"]), SERV_NAME, port)
            self.connect.start()

            # start praat
            start_t = time()
            self.process = Popen([self.praat, self.file.name, SERV_NAME, str(port)], stdout=PIPE) #res.praat : test file

            # print "%s Wait..." % self.pref
            stdo, stde = self.process.communicate()

            res = self.connect.result

            print "%s End : %r" % (self.pref, res)

        except OSError as e:
            stde = str(e)
        finally:
            send_udp_msg(self.address, self.info["port"], dict(id=self.info["id"], stdout=stdo, stderr=stde, time=(time() - start_t), result=res))
            pl.free(port)

            if self.file is not None:
                self.file.close()

            if self.connect is not None:
                self.connect.stop()
                self.connect = None

        # print "%s TIME : %i" % (self.pref, time() - start_t)

    def stop(self):
        if self.connect is not None:
            self.connect.stop


# --------------------------------
# Parser
class ScriptFileException(Exception):
    def __str__(self):
        return "ScriptFileException : can not create script file"


# --------------------------------
# Parser
def parser():
    """
    Create parser class to check input arguments
    """
    parser = argparse.ArgumentParser()
    # init
    parser.description = "%s" % ("Praat multi-launch")

    parser.add_argument("-m", "--max", type=int, help="max simultaneous thread", default=MAX_THREAD)
    parser.add_argument("-p", "--port", type=int, help="server port", default=SERV_PORT)
    parser.add_argument("-l", "--link", help="path to praat", default=PRAAT_PATH)
    
    
    return parser

def main():
    """
    main function
    """
    args = parser().parse_args()

    server_sock = None

    pl = PortList()
    pl.config(PRAAT_START_PORT, PRAAT_START_PORT+100)

    print "Server name :", SERV_NAME
    print "Server port :", args.port
    print "Praat start port :", PRAAT_START_PORT
    print "Max simultaneous thread :", args.max
    print "------------------"

    try:
        # socket for instructions
        server_sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
        server_sock.bind(("", args.port))


        print "Wait command..."
        while True:
            data, addr = server_sock.recvfrom(SOCKET_BUFFER)

            try:
                info = json.loads(data)

                if "cmd" in info and "port" in info:
                    if info["cmd"] == "ping":
                        print "ping"
                        send_udp_msg(addr[0], info["port"], dict(stdout="", stderr="", time=time(), cmd="ping"))
                    elif info["cmd"] == "praat":
                        praat = Praat(addr[0], info, args.link)
                        praat.start()

            except Exception as e:
                print "Receive error :", e
        
    except KeyboardInterrupt:
        print "Stopping..."
        print "------------------"
    finally:
        if server_sock is not None:
            server_sock.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())

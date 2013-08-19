#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Server pool system

@author: Olivier BLIN
"""

import sys
import json
import socket
import base64
from time import time, sleep
from threading import Thread
from subprocess import Popen, PIPE

from common import RingList, send_udp_msg
from praatcon import getScript, result_decode
from bashutils import colors


SERVER_IP_POOL = [
    ("192.168.1.123", 5005), # SMB30623
    ("192.168.1.134", 5005), # SMB30628
    # ("192.168.1.144", 5005), # SMB30622
    # ("192.168.1.146", 5005), # SMB30632
    # ("192.168.1.93", 5005), # SMB30631
    
]

CLIENT_PORT = 5004
SOCKET_BUFFER = 1500

# After this time, algo stop to wait a result
IGNORE_TIME_SEC = 120
PING_TIMEOUT = 1

class ResultManager(Thread):

    """
    Thread class
    """

    def __init__(self, size):
        Thread.__init__(self)

        self.l_result = [None] * size
        self.size = size

        self.term = False


    def run(self):
        # UDP server
        self.server_sock = None
        

        try:
            self.server_sock = socket.socket(socket.AF_INET, # Internet
                         socket.SOCK_DGRAM) # UDP
            self.server_sock.bind(("", CLIENT_PORT))

            self.server_sock.settimeout(1)

            # Init Display
            self.display()

            # print "ResultManager : wait..."
            while not self.term:
                try:
                    # receive data
                    data, addr = self.server_sock.recvfrom(SOCKET_BUFFER)

                    try:
                        # decode data
                        info = json.loads(data)


                        ok = True

                        for elem in ["id", "result"]:
                            if elem not in info:
                                ok = False

                        if ok:
                            pos = info["id"]
                            if pos >= 0 and pos < self.size and self.l_result[pos] is not None:
                                self.l_result[pos] = info["result"]
                            else:
                                print "Can not keep this result"

                            # Display
                            self.display()

                            # Check if this is finish
                            if self.is_end():
                                self.term = True
                                sys.stdout.write("\n")

                        else:
                            print "Something wrong with this packet"


                    except Exception as e:
                        print "Receive error :", e

                except socket.timeout:
                    pass
        finally:
            if self.server_sock is not None:
                self.server_sock.close()


    def stop(self):
        self.term = True
        if self.server_sock is not None:
            self.server_sock.close()

    def is_end(self):
        r = True
        for e in self.l_result:
            if e == None or type(e) is float:
                r = False
                break
        return r

    def check_timeout(self):
        for n, e in enumerate(self.l_result):
            if type(e) is float and (e + IGNORE_TIME_SEC) <= time():
                self.l_result[n] = None

    def nbr_server_running(self):
        nb = 0
        for e in self.l_result:
            if type(e) is float:
                nb += 1
        return nb

    def nbr_ended_result(self):
        nb = 0
        for e in self.l_result:
            if type(e) is not float and e is not None:
                nb += 1
        return nb

    def get_id(self):
        for n, e in enumerate(self.l_result):
            if e == None:
                return n

    def select_id(self, ident):
        self.l_result[ident] = time()

    def display(self):
        adapt = 4
        percent = self.nbr_ended_result() / (self.size * 1.0) * 100
        done = int(percent/adapt)
        todo = int(100-percent)/adapt
        text = colors.color_text("|"*done + " "*todo, color="green", bcolor="none", effect="none")
        sys.stdout.write("\rProgress : [%s] - %i%%" % (text, percent))
        sys.stdout.flush()


class PoolManager():

    def __init__(self, ind_list):

        self.ind_list = ind_list

        self.spool = RingList()
        self.max_th = 0 # len(SERVER_IP_POOL)

        self.pool_recv = None


    def check_pool(self):
        server_sock = None
        message = dict()
        message["cmd"] = "ping"
        message["port"] = CLIENT_PORT

        try:
            server_sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
            server_sock.bind(("", CLIENT_PORT))

            server_sock.settimeout(PING_TIMEOUT)

            for address, port in SERVER_IP_POOL:
                send_udp_msg(address, port, message)

                try:
                    # receive data
                    data, addr = server_sock.recvfrom(SOCKET_BUFFER)

                    try:
                        # decode data
                        info = json.loads(data)

                        if addr[0] == address and "cmd" in info and info["cmd"] == "ping":
                            self.spool.add((address, port))
                        else:
                            print "Ping error"

                    except Exception as e:
                        print "Ping receive error :", e
                    
                except socket.timeout:
                    pass


        except Exception as e:
            print "Ping error :", e
        finally:
            server_sock.close()

        self.max_th = len(self.spool.lelem)


    def run(self):
        # Server pool
        sys.stdout.write("Looking for available server...")
        sys.stdout.flush()
        while self.max_th <= 0:
            self.check_pool()
            if self.max_th <= 0:
                sys.stdout.write(".")
                sys.stdout.flush()
        sys.stdout.write("\n\t-> %i servers found:\n" % len(self.spool.lelem))

        for elem in self.spool.lelem:
            print "\t\t%s" % elem[0]

        try:
            # Create receiver and start it
            self.pool_recv = ResultManager(len(self.ind_list))
            self.pool_recv.start()

            sleep(0.2)

            # Loop
            while not self.pool_recv.is_end():
                # check if some computer are out of the time
                self.pool_recv.check_timeout()

                # get id
                identifier = self.pool_recv.get_id()

                if self.pool_recv.nbr_server_running() < self.max_th and identifier is not None:

                    self.pool_recv.select_id(identifier)
                    # Create message
                    message = self.create_message(identifier, self.ind_list[identifier], CLIENT_PORT)

                    # send message to one of the server pool
                    addr = self.spool.get()
                    send_udp_msg(addr[0], addr[1], message)
                else:
                    sleep(0.2)

            # handlke result
            res = map(result_decode, self.pool_recv.l_result)

        finally:
            if self.pool_recv is not None:
                self.pool_recv.stop()

        return res


    def create_message(self, identifier, individual, client_port):
        message = dict()
        message["id"] = identifier
        message["cmd"] = "praat"
        message["port"] = client_port
        message["script"] = base64.b64encode(getScript(individual))
        

        return message


if __name__ == "__main__":

    pool = PoolManager([[0.5]*16]*1)
    res = pool.run()


    for elem in res:
        print "Elem", elem


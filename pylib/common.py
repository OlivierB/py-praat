#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Common functions

@author: Olivier BLIN
"""

import json
import socket
import base64

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


def send_udp_msg(ip, port, data):
    # socket for instructions
    sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

    d = json.dumps(data)
    sock.sendto(d, (ip, port))
    sock.close()
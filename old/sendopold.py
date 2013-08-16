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
import base64
from time import time, sleep
from threading import Thread
from subprocess import Popen, PIPE


SERVER_IP_POOL = [
    # ("192.168.1.135", 5005),
    # ("192.168.1.123", 5005),
    ("192.168.1.134", 5005),
]

SERV_PORT = 5005
CLIENT_PORT = 5004
SOCKET_BUFFER = 1500
NB_THREAD = len(SERVER_IP_POOL)


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
# Praat script
def getScript(val, speachtime=1, nbFormantMax=2):

    script = \
"""\
form Server
    sentence Address localhost
    natural Port 10000
endform
#-----------------------------------------------
# Project : Software synthesis using GA
# Hervo Pierre-Yves, automatic Script generated in java
#-----------------------------------------------
#-----------------------------------------------
Create Speaker... Robovox Female 2
Create Artword... phon """+str(speachtime)+"""
#-----------------------------------------------
# Supply lung energy
#-----------------------------------------------
Set target... 0.0    0.1 Lungs
Set target... 0.03     0.0 Lungs
Set target... """+str(speachtime)+"""     0.0 Lungs
#-----------------------------------------------
# Control glottis
#-----------------------------------------------
#Glottal closure
Set target... 0.0  0.5  Interarytenoid
Set target... """+str(speachtime)+"""  0.5 Interarytenoid
#
# Adduct vocal folds
Set target... 0.0   0.59 Cricothyroid
Set target... """+str(speachtime)+"""   0.51 Cricothyroid
# Close velopharyngeal port
#-----------------------------------------------
Set target... 0.0   0.3 LevatorPalatini
Set target... """+str(speachtime)+"""   0.03 LevatorPalatini
#-----------------------------------------------
#-----------------------------------------------
Set target... 0.0   0.16 Genioglossus
Set target... """+str(speachtime)+"""   0.92 Genioglossus
#
Set target... 0.0   0.97 Styloglossus
Set target... """+str(speachtime)+"""   0.36 Styloglossus
#
Set target... 0.0   0.39 Mylohyoid
Set target... """+str(speachtime)+"""   0.45 Mylohyoid
#
Set target... 0.0   0.53 OrbicularisOris
Set target... """+str(speachtime)+"""   0.14 OrbicularisOris
#-----------------------------------------------
# Shape mouth to open vowel
#-----------------------------------------------
# Lower the jaw
# -----------------------------------------
Set target... 0.0   -0.02 Masseter
Set target... """+str(speachtime)+"""   -0.17 Masseter
# Pull tongue backwards
Set target... 0.0   0.17 Hyoglossus
Set target... """+str(speachtime)+"""   0.09 Hyoglossus
# Synthesise the sound
#-----------------------------------------------
select Artword phon
plus Speaker Robovox
To Sound... 22050 25   0 0 0    0 0 0    0 0 0
#-----------------------------------------------
#-----------------------------------------------
# Automatic data extraction par
# 1) get the values
To Formant (burg)... 0 5 5500 0.025 50
numberOfFormant = Get number of formants... 1
writeInfoLine(numberOfFormant)
if numberOfFormant>="""+str(nbFormantMax)+"""
time = Get total duration
midTime = time/2
for intervalNumber from 1 to """+str(nbFormantMax)+"""
varTabFreq[intervalNumber] = Get mean... intervalNumber 0 """+str(speachtime)+""" Hertz
varTabBandWith[intervalNumber] =  Get bandwidth at time... intervalNumber midTime Hertz Linear
endfor
# convert it into string for sendsocket
temp1$=string$(varTabFreq[1])
temp2$=string$(varTabFreq[2])
sendsocket 'address$':'port' 'temp1$' 'temp2$'
writeInfoLine(temp1$, " - ", temp2$)
else
sendsocket 'address$':'port' INF
writeInfoLine("rien")
endif
"""

    return script


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
            message["script"] = base64.b64encode(getScript(0))
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

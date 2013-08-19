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

from pylib.gene import genetic_algo


# --------------------------------
# Parser
def parser():
    """
    Create parser class to check input arguments
    """
    parser = argparse.ArgumentParser()
    # init
    parser.description = "%s" % ("Praat multi-launch")

    # parser.add_argument("-t", "--thread", type=int, help="thread number", default=NB_THREAD)
    # parser.add_argument("-c", "--cport", type=int, help="client port", default=CLIENT_PORT)
    return parser


def main():
    """
    main function
    """
    args = parser().parse_args()

    print "Praat formant discovery"
    print "--------------------"
    print "Genetic algorithm"
    print "Distributed servers"
    print "--------------------"
    print "Let's go..."
    print ""

    try:
        res = genetic_algo()

    except KeyboardInterrupt:
        pass

    return 0
    

if __name__ == "__main__":
    sys.exit(main())

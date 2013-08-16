#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Manage praat dialog

@author: Olivier BLIN
"""


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
Set target... 0.0   """+str(val[0])+""" Cricothyroid
Set target... """+str(speachtime)+"""   """+str(val[1])+""" Cricothyroid
# Close velopharyngeal port
#-----------------------------------------------
Set target... 0.0   """+str(val[2])+""" LevatorPalatini
Set target... """+str(speachtime)+"""   """+str(val[3])+""" LevatorPalatini
#-----------------------------------------------
#-----------------------------------------------
Set target... 0.0   """+str(val[4])+""" Genioglossus
Set target... """+str(speachtime)+"""   """+str(val[5])+""" Genioglossus
#
Set target... 0.0   """+str(val[6])+""" Styloglossus
Set target... """+str(speachtime)+"""   """+str(val[7])+""" Styloglossus
#
Set target... 0.0   """+str(val[8])+""" Mylohyoid
Set target... """+str(speachtime)+"""   """+str(val[9])+""" Mylohyoid
#
Set target... 0.0   """+str(val[10])+""" OrbicularisOris
Set target... """+str(speachtime)+"""   """+str(val[11])+""" OrbicularisOris
#-----------------------------------------------
# Shape mouth to open vowel
#-----------------------------------------------
# Lower the jaw
# -----------------------------------------
Set target... 0.0   """+str(val[12])+""" Masseter
Set target... """+str(speachtime)+"""   """+str(val[13])+""" Masseter
# Pull tongue backwards
Set target... 0.0   """+str(val[14])+""" Hyoglossus
Set target... """+str(speachtime)+"""   """+str(val[15])+""" Hyoglossus
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


def result_decode(res):
    a, b = 0.0, 0.0

    # clean the string
    mys = ""
    for c in res:
        if ord(c) >= ord("0") and ord(c) <= ord("9")\
            or c in [" ", ".", ","]:
            mys += c

    try:
        pos = mys.find(" ")
        if len(mys) > 3 and pos != -1:
            a = float(mys[0:pos])
            b = float(mys[pos:])


    except ValueError as e:
        print "result_decode error : can not get value : %s - (%i, %i) : " % (mys, a, b), e
    except Exception as e:
        print "result_decode unknow error :", e

    return a, b

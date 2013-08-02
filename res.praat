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
Create Artword... phon 1.0
#-----------------------------------------------
# Supply lung energy
#-----------------------------------------------
Set target... 0.0    0.1 Lungs
Set target... 0.03     0.0 Lungs
Set target... 1.0     0.0 Lungs
#-----------------------------------------------
# Control glottis
#-----------------------------------------------
#Glottal closure
Set target... 0.0  0.5  Interarytenoid
Set target... 1.0  0.5 Interarytenoid
#
# Adduct vocal folds
Set target... 0.0   0.59 Cricothyroid
Set target... 1.0   0.51 Cricothyroid
# Close velopharyngeal port
#-----------------------------------------------
Set target... 0.0   0.3 LevatorPalatini
Set target... 1.0   0.03 LevatorPalatini
#-----------------------------------------------
#-----------------------------------------------
Set target... 0.0   0.16 Genioglossus
Set target... 1.0   0.92 Genioglossus
#
Set target... 0.0   0.97 Styloglossus
Set target... 1.0   0.36 Styloglossus
#
Set target... 0.0   0.39 Mylohyoid
Set target... 1.0   0.45 Mylohyoid
#
Set target... 0.0   0.53 OrbicularisOris
Set target... 1.0   0.14 OrbicularisOris
#-----------------------------------------------
# Shape mouth to open vowel
#-----------------------------------------------
# Lower the jaw
# -----------------------------------------
Set target... 0.0   -0.02 Masseter
Set target... 1.0   -0.17 Masseter
# Pull tongue backwards
Set target... 0.0   0.17 Hyoglossus
Set target... 1.0   0.09 Hyoglossus
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
if numberOfFormant>=2
time = Get total duration
midTime = time/2
for intervalNumber from 1 to 2
varTabFreq[intervalNumber] = Get mean... intervalNumber 0 0 Hertz
varTabBandWith[intervalNumber] =  Get bandwidth at time... intervalNumber midTime Hertz Linear
endfor
# convert it into string for sendsocket
temp1$=string$(varTabFreq[1])
temp2$=string$(varTabFreq[2])
sendsocket 'address$':'port' 'temp1$' 'temp2$'
else
sendsocket 'address$':'port' INF
endif

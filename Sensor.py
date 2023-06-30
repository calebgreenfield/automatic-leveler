# Sensor.py
# Caleb Greenfield
# 3/7/23

# AutoLevel Project:
# run_auto_leveler.py
# Relays.py
# Sensor.py
# Settings.py
# settings.csv


# Overview:
# This page defines helper functions for the sensor operations

import time
from time import sleep
import serial
import numpy.polynomial.polynomial

ORDER = 5

AVG_SAMPLES = 5
AVG_DELAY = 0.1

MAX_ADC_VAL = 65535
MIN_ADC_VAL = 0

ROLL = "roll"
PITCH = "pitch"

ROLL_CHANNEL = b'x'
PITCH_CHANNEL = b'y'

READ_DELAY = 0.1

e = "I\O Error"

class Sensor:
    #initializes sensor objects
    #instatntiated as pitch = Sensor("pitch", 1, ADC)   roll = Sensor("roll", 0, ADC) in run_auto_leveler.py
    #parameters are sensor name, channel on ADC, and ADC object initialized in run_auto_leveler.py
    def __init__(self, name, ADCinit, sensorVals, minutes, raw, order):
        #initalize sensor variables
        self.reading = 0
        self.name = name
        self.zero = 0
        self.ADC = ADCinit
        self.raw = raw
        
        if (name == ROLL):
            self.channel = ROLL_CHANNEL
        elif (name == PITCH):
            self.channel = PITCH_CHANNEL
        else:
            print("Invalid Sensor Name")
            exit()
        
        self.sensorVals = sensorVals
        self.minutes = minutes
            
        self.coefficients = numpy.polynomial.polynomial.Polynomial.fit(
                sensorVals, # raw values
                minutes, # corresponding angle values to the raw values
                order) # order of polynomial
        
        
    #returns string if print(sensor) is called
    def __str__(self):
        return f'{self.name}- Zero: {self.zero}  Reading: {self.reading}  Difference: {self.zero -self.reading}\n'

    #Saves current sensor reading from ADC channel output
    def read(self):
        try:
            #write required char to RS-232 ADC to trigger sensor read
            # x for roll, y for pitch
            self.ADC.write(self.channel)
            #receive value
            val = self.ADC.read()
            #wait for missed characters
            sleep(READ_DELAY)
            #pick up remainders
            val_rem = self.ADC.inWaiting()
            val +=self.ADC.read(val_rem)
            #decode value
            val = int(val.decode())
            #if valid
            if (val>=MIN_ADC_VAL and val<=MAX_ADC_VAL):
                
                if(not self.raw):
                    val = numpy.polynomial.polynomial.polyval(val, self.coefficients.convert().coef)

                #store reading
                self.reading = val
                return self.reading
            else:
                print("Sensor read error")
                exit()
        except:
            print("ERROR: No signal from sensor")
    
    def saveZero(self):
        #initialize sum variables
        sum = 0
        #readXY 5 times over 1.25 seconds
        for i in range(0,AVG_SAMPLES):
            self.read()
            sum = sum + self.reading
            time.sleep(AVG_DELAY)
        #set zero
        self.zero = sum /AVG_SAMPLES
        
        return self.zero
    
    def saveZero2(self):
        self.zero = 0
        
        return self.zero

    def getZero(self):
        return self.zero

    def getDifference(self):
        return self.zero - self.reading
    
    def getName(self):
        return self.name
    
    def getCoefficients(self):
        return self.coefficients

    
    

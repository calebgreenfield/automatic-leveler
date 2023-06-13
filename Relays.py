# Relays.py
# Caleb Greenfield
# 3/7/23

# AutoLevel Project:
# run_auto_leveler.py
# Relays.py
# Sensor.py
# Settings.py
# settings.csv


# Overview:
# This page defines variables and helper functions specifically relating to the 4 Relay Module used to
# control rig actuators.


import RPi.GPIO as GPIO
import time

#default pulse used by control act function
CONTROL_PULSE = 0.2

class Relays:
    #initializes relay object
    #parameters are pin numbers for actuator controls in the given order
    #instantiated as relays = Relays(LEFT_PIN, RIGHT_PIN, UP_PIN, DOWN_PIN) in run_auto_leveler.py
    def __init__(self, left, right, up, down):
        GPIO.setmode(GPIO.BCM)

        #set pin variables
        self.left = left
        self.right = right
        self.up = up
        self.down = down
        
        #TODO: not needed since invertRigSignal has been removed
        #self.outputInverted = False
        self.on = GPIO.LOW
        self.off = GPIO.HIGH
        
        #set inverted indicators
        self.rollInverted = 0
        self.pitchInverted = 0

        #save directions in dictionary for easy access
        self.directions = {"up": self.up, "down": self.down, "left": self.left, "right": self.right}
        
        #set pause indicator
        self.pause = False
        
        self.stayOn = False

        #set up pin outputs with provided direction values
        GPIO.setup(left,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(right,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(up,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(down,GPIO.OUT, initial=GPIO.HIGH)

    #TODO: not needed since invertRigSignal has been removed
    def setLowOut(self):
        print("switch")
        GPIO.setup(self.left,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.right,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.up,GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.down,GPIO.OUT, initial=GPIO.LOW)
        self.outPutInverted = True
        self.on = GPIO.HIGH
        self.off = GPIO.LOW
    
    #TODO: not needed since invertRigSignal has been removed
    def setHighOut(self):
        print("switch")
        GPIO.setup(self.left,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.right,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.up,GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(self.down,GPIO.OUT, initial=GPIO.HIGH)
        self.on = GPIO.LOW
        self.off = GPIO.HIGH
        self.outPutInverted = False

    #switches up and down pins and sets or resets pitchInverted indicator
    def invertPitch(self):
        self.up, self.down = self.down, self.up
        self.directions = {"up": self.up, "down": self.down, "left": self.left, "right": self.right}
        if self.pitchInverted == 0:
            self.pitchInverted = 1
        else:
            self.pitchInverted = 0

    #switches left and right pins and sets or resets rollInverted indicator
    def invertRoll(self):
        self.right, self.left = self.left, self.right
        self.directions = {"up": self.up, "down": self.down, "left": self.left, "right": self.right}
        if self.rollInverted == 0:
            self.rollInverted = 1
        else:
            self.rollInverted = 0

    #access functions for inverted  and pause indicators
    def isRollInverted(self):
        return self.rollInverted
    
    def isPitchInverted(self):
        return self.pitchInverted

    def getDirections(self):
        return self.directions

    def getPause(self):
        return self.pause
    
    def setPause(self, boolVar):
        self.pause = boolVar
        
    def getStayOn(self):
        return self.stayOn
    
    def setStayOn(self, boolVar):
        self.stayOn = boolVar

    #Triggers actuators by activating relays for given pulse time
    def moveAct(self,act,pulseSpeed):
        GPIO.output(act, self.on)
        time.sleep(pulseSpeed)
        GPIO.output(act, self.off)
        
    def moveLeft(self, pulse):
        self.moveAct(self.left, pulse)
        
    def moveRight(self, pulse):
        self.moveAct(self.right, pulse)
        
    def moveUp(self, pulse):
        self.moveAct(self.up, pulse)
    
    def moveDown(self, pulse):
        self.moveAct(self.down, pulse)



# run_auto_leveler.py
# Caleb Greenfield
# 3/7/23

# AutoLevel Project:
# run_auto_leveler.py
# Relays.py
# Sensor.py
# Settings.py
# settings.csv


# Overview:
# This program recieves data from analog tilt sensors using an signal conditioner with a built in 
# analog to digital converter. Both the sensors and signal conditioner were purchased from the Fredricks company.
# The program uses this data in its autoleveling function and sends signals to a 4 module relay
# which, when connected to rig relays, can control the movement of the midload, ABCS, and light load rigs.
# A graphical user interface provides a means for users to run the set zero and autolevel functions as well
# as save and edit setting presets for the 4 rigs and 2 sensitiviy presets.

# Operation:
# The program is serviced by an graphical user interface that consists of two tabs. The first tab contains displays
# that show the roll and pitch data read from the sensors, saved zero point data, delta data, and program status updates.
# This tab also contains 4 buttons: Level, Set Zero, Exit, and E-Stop. The Set Zero button triggers the execution of
# the saveZero() function. This function reads 5 points over 1.25 seconds and saves zeroRoll and zeroPitch as averages. This
# data point provides a reference for the autoLevel() function to return to in its operation. 
#
# The Level button triggers the operation of the autoLevel() function which continuously loops until the output of the 
# tilt sensors is equal to the saved zero point within a specified sensitivity. The autolevel() function begins by moving 
# the actuator in the X axis until sensor output is within a lesser sensitivity of sens2. When this is accomplished the 
# program does the same in the Y axis. When both X and Y are within sens2 the program alternately adjusts X and Y until 
# both are within the finer sensitivity of sens1. If at any point X or Y goes outside of sens2 the program will adjust 
# that single axis until sensor output is back within sens1. 
#
# The auto level function utilizes the adapt() function to 
# move the rig actuators. The adapt() function determines the difference between the saved zero point and current reading.
# If the reading is greater than the XL difference specified in the settings the adapt function will cause the actuator to 
# pulse for an XL pulse and then wait for the specified delay time before signaling another actuator movement. The adapt()
# function will detect 4 levels of difference (XL, L, M, S) with a specified pulse length and delay time for each range.
#
# The autolevel function will terminate when X and Y sensor output is within sens1
# or the E-Stop button is pressed. The E-Stop button stops the execution of the autolevel() function but the zero point
# will still be saved so autoleveling can be resumed if neccessary.
#
# The second tab of the GUI contains a window for settings to be adjusted for each rig as necessary. There are 8 different 
# preset options, 2 for each rig one of which is a high sensitivity preset meant to match T-Level accuracy while the other
# is a lower level sensitivity option meant to match the 1" levels. The settings can be adjusted and saved as necessary. 
# Settings are saved to the settings.csv file which should always be in the same directory as this file.
#
# This file uses the functions defined in Sensor.py, Relays.py, and Settings.py to perform the main autoleveling functions.


# Status: Functional


# Possible Improvements:
# Delay times use the time.sleep() method in the moveAct() method to pause the function of the whole program to give the sensors
# and actuators time to adjust to movements. This is not a good method as one axis could be leveling as the other is paused.
#
# Autoleveling could be made faster by triggering overlapping pitch and roll pulses so that they could both be leveled at the same time.
#
# Relay pulses can not be interupted via software since a pulse is implemented by calling .sleep() for a set time



#class objects
from Sensor import *
from Relays import *
from Settings import *

#used for communication with sensors
#import serial

#gui packages
import tkinter as tk
from tkinter import ttk
from tkinter import *
from tkinter import messagebox
#from playsound import playsound
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
NavigationToolbar2Tk)

import numpy as np


#used for storing settings
import csv

import time

SETTINGS_FILE = "settings.csv"

PITCH_RAW = [36112, 32564, 31163, 30462, 29730, 27540, 23575]
PITCH_MNTS = [7, 3, 1, 0, -1, -3.5, -8]

ROLL_RAW = [37064, 34036, 32642, 31910, 31251, 29702, 26029]
ROLL_MNTS = [7, 3, 1, 0, -1, -3, -7]

#GPIO PINS - BCM
LEFT_PIN = 16
RIGHT_PIN = 12
UP_PIN = 20
DOWN_PIN = 21

#program halts if autoleveling takes longer than:
TIME_OUT = 90  #seconds
#display color refreshes every:
COLOR_REFRESH = 150 #ms
#program calls new reading every:
READING_REFRESH = 0.06 #ms
#readings displayed with given number of decimals:
OUTPUT_FORMAT = '%.2f'
#GUI Page dimensions:
WINDOW_SIZE = "1918x1014"

RANGE = 20000

# #Serial connection settings:
# PORT = "/dev/ttyAMA0" 
# BAUDRATE = 9600
# BYTESIZE = serial.EIGHTBITS
# PARITY = serial.PARITY_NONE
# STOPBITS = serial.STOPBITS_ONE
# TIMEOUT = 1

# GUI helper functions - - - - - - - - - - - - - - - - - - - - - - - -

#updates all settings displays, radiobuttons, and switches with current values from settings.csv
def updateSettingsDisplay():
    #erase and refill setting entry displays with new values
    settingsList = ["sens1", "sens2", "xLDiff", "lDiff", "mDiff", "sDiff", "xLPulse", 
                "lPulse", "mPulse", "sPulse", "xSPulse", "xLDelay", "lDelay",  "mDelay", "sDelay", "xSDelay", "threshold"]

    for setting in settingsList:
        entry = settingEntry[setting]
        entry.delete(0, END)
        entry.insert(0, settings.getSetting(setting))
    
    if (settings.getSetting("rollInvert") != relays.isRollInverted()):
        invertRoll()
        
    if (settings.getSetting("pitchInvert") != relays.isPitchInverted()):
        invertPitch()
        
#exectures when new rig is selected, updates current settings
def selectRig():
    #show message box. Executes if yes is selected
    msg_box = messagebox.askquestion('Change Rig', 'Are you sure you want to change rigs?', icon='warning')
    if msg_box == 'yes':
        #get rig value from radio button
        settings.setRig(rigSelect.get())
        updateSettingsDisplay()
    else:
        rigSelect.set(settings.getRig())
       
#executes when new level is selected, updates current settings       
def selectLevel():
    msg_box = messagebox.askquestion('Change Level', 'Are you sure you want to change levels?', icon='warning')
    if msg_box == 'yes':
        settings.setLevel(levelSelect.get())
        updateSettingsDisplay()
    else:
        levelSelect.set(settings.getLevel())
        
#executes when new show data is selected, updates current settings       
def selectData():
    if (settings.getSetting("data") == 0):
        msg_box = messagebox.askokcancel('Show Raw Data', 'Autoleveling will not work normally when this is selected.', icon='warning')
        if msg_box:
            settings.setData(1)
            rawDataSwitch.configure(text = "On")
    else:
        settings.setData(0)
        rawDataSwitch.configure(text = "Off")
        
    msg_box = messagebox.askokcancel('Show Raw Data', 'Restart program for changes to take effect.', icon='warning')

#executes when save settings button is pressed, updates settings.csv with current settings selections
def saveSettings():
    #Shows message box, only executes if yes is selected
    msg_box = messagebox.askquestion('Change Rig Settings', 'Are you sure you want to change rig settings?', icon='warning')
    if msg_box == 'yes':
        settingsList = ["sens1", "sens2", "xLDiff", "lDiff", "mDiff", "sDiff", "xLPulse", 
                "lPulse", "mPulse", "sPulse", "xSPulse", "xLDelay", "lDelay",  "mDelay", "sDelay", "xSDelay"]

        array = [float(settingEntry[setting].get()) for setting in settingsList]

        #checkboxes
        array.append(relays.isRollInverted())
        array.append(relays.isPitchInverted())
        #array.append(relaySigInvertSelect.get())`
        
        threshold = float(settingEntry["threshold"].get())
        array.append(threshold)

        print(array)
        settings.setNewSettings(array)
        
#executes when save settings button is pressed, updates settings.csv with current settings selections
def saveSensorSettings():
    #Shows message box, only executes if yes is selected
    msg_box = messagebox.askokcancel('Changing Sensor Settings...', 'Restart program for changes to take effect.', icon='warning')
    if msg_box:
        array = []
        #set settings variable
        for i in range(7):
            array.append(pitchRawEntries[i].get())  
        
        for i in range(7):
            array.append(pitchCalcEntries[i].get()) 
        
        for i in range(7):
            array.append(rollRawEntries[i].get()) 
        
        for i in range(7):
            array.append(rollCalcEntries[i].get()) 
        
        array.append(orderEntry.get())
        
        settings.setNewSensorSettings(array)
        

#executes when new priority is selected, sets either pitch or roll to be leveled first
def setPriority():
    if prioritySelect.get() == 0:
        settings.setPriority("pitch")
    elif prioritySelect.get() == 1:
        settings.setPriority("roll")

#executes when invert pitch button is pressed, switches U and D relays
def invertPitch():
    if relays.isPitchInverted():
        invertPitchButton.configure(text = "Off")
    else:
        invertPitchButton.configure(text = "On")
    relays.invertPitch()

#executes when invert roll button is pressed, switches L and R relays
def invertRoll():
    if relays.isRollInverted():
        invertRollButton.configure(text = "Off")
    else:
        invertRollButton.configure(text = "On")
    relays.invertRoll()

#executes when exit button is pressed, terminates program    
def clickExitButton():
    msg_box = messagebox.askquestion('Exit?', 'Are you sure you want to exit?')
    if msg_box == 'yes':
        root.destroy()

#executes when pause button is pressed, halts autolevel function
def pause():
    if relays.getPause():
        #remove pause
        relays.setPause(False)
        #change color of button to original color
        pauseButton.configure(highlightbackground = '#d9d9d9')
        #reset display
        if display.cget("text") == 'Paused..':
                display['text'] = ""
        #refresh GUI
        tab1.update()
    else:
        #Engage pause
        relays.setPause(True)
        #Change button color to red
        pauseButton.configure(highlightbackground = 'red')
        #refresh GUI
        tab1.update()

#executes when Stay on button is pressed, begins stayOnLoop function
def stayOn():
    if(not relays.getPause()):
        if relays.getStayOn():
            #remove flag
            relays.setStayOn(False)
            display.configure(text = "")
            #change color of button to original color
            stayOnButton.configure(highlightbackground = '#d9d9d9')
            #refresh GUI
            tab1.update()
        else:
            msg_box = messagebox.askquestion('Stay On?', f'Threshold is set to {settings.getSetting("threshold")}', icon='warning')
            if msg_box == 'yes':
                #Engage flag
                relays.setStayOn(True)
                #Change button color to green
                stayOnButton.configure(highlightbackground = 'green')
                #begin loop
                stayOnLoop()
                #refresh GUI
                tab1.update()
    else:
        if(relays.getPause()):
            display["text"] = "Paused.."
        else:
            smallDisplay["text"] = "Zero not taken"
        stayOnButton.configure(highlightbackground = '#d9d9d9')
        relays.setStayOn(False)
        tab1.update()

#gets reading from sensors and updates GUI        
def getReading(sensor):
    reading = sensor.read()
    if sensor.getName() == "pitch":
        yData.configure(text = OUTPUT_FORMAT%reading)
        yDiff.configure(text = OUTPUT_FORMAT%(reading - sensor.getZero()))
    else:
        xData.configure(text = OUTPUT_FORMAT%reading)
        xDiff.configure(text = OUTPUT_FORMAT%(reading - sensor.getZero()))
    
    #refresh GUI
    tab1.update()
    return reading

#loops continuously and calls autolevel function if difference > threshold
def stayOnLoop():
    display.configure(text = "Waiting...")
    while relays.getStayOn():
        getReading(pitch)
        getReading(roll)
        time.sleep(READING_REFRESH)
        if abs(pitch.getDifference()) > settings.getSetting("threshold") or abs(roll.getDifference()) > settings.getSetting("threshold"):
            autoLevel()
        if relays.getPause():
            stayOn()
            display.configure(text = "")
            break

#updates color based off of difference, updates every 150 ms      
def displayColor():
    pDiff = abs(pitch.getDifference())
    rDiff = abs(roll.getDifference())
    
    greenDiff = settings.getSetting("sens1")
    yellowDiff = settings.getSetting("sens2")
    orangeDiff = settings.getSetting("mDiff")

    if pDiff <= greenDiff:
        yDiff.configure(bg = "green")
    elif pDiff <= yellowDiff:
        yDiff.configure(bg = "yellow")
    elif pDiff <= orangeDiff:
        yDiff.configure(bg = "orange")
    else:
        yDiff.configure(bg = "red")

    if rDiff <= settings.getSetting("sens1"):
        xDiff.configure(bg = "green")
    elif rDiff <= settings.getSetting("sens2"):
        xDiff.configure(bg = "yellow")
    elif rDiff <= orangeDiff:
        xDiff.configure(bg = "orange")
    else:
        xDiff.configure(bg = "red")

    tab1.after(COLOR_REFRESH, displayColor)

#Allows for variable movement response given distance from zero point. Also allows for uniqe delays for each type of movement
#input requires actuator to be moved, current reading from sensors, and axis to be moved
def adapt(reading, axis):

    directions = relays.getDirections()

    #calc difference between zero point and current reading
    if axis == "roll":
        difference = reading - roll.getZero()
        if difference > 0:
            act = directions["right"]  #right
        else:
            act = directions["left"]  #left
        print(f'reading!: {reading}  zero:{roll.getZero()}')
    else:
        difference = reading - pitch.getZero()
        if difference > 0:
            act = directions["up"]  #up
        else:
            act = directions["down"]  #down
        print(f'reading!: {reading}  zero:{pitch.getZero()}')
    print(f'DIFF!: {difference}  act{act}  axis: {axis}')
    
    difference = abs(difference)
    
    #Extra long pulse    
    if difference > settings.getSetting("xLDiff"):
        #move actuator for pulse length
        relays.moveAct(act, settings.getSetting("xLPulse"))
        #delay for given delay
        time.sleep(settings.getSetting("xLDelay"))
        #update display
        smallDisplay2['text'] = "Pulse: XL"
        print("\t Pulse: XL")
        
    #Long pulse
    elif difference <= settings.getSetting("xLDiff") and difference > settings.getSetting("lDiff"):
        relays.moveAct(act, settings.getSetting("lPulse"))
        time.sleep(settings.getSetting("lDelay"))
        smallDisplay2['text'] = "Pulse: L"
        print("\t Pulse: L")
        
    #Medium pulse
    elif difference <= settings.getSetting("lDiff") and difference > settings.getSetting("mDiff"):
        relays.moveAct(act, settings.getSetting("mPulse"))
        time.sleep(settings.getSetting("mDelay"))
        smallDisplay2['text'] = "Pulse: M"
        print("\t Pulse: M")
        
    #Small pulse
    elif difference <= settings.getSetting("mDiff") and difference > settings.getSetting("sDiff"):
        relays.moveAct(act, settings.getSetting("sPulse"))
        time.sleep(settings.getSetting("sDelay"))
        smallDisplay2['text'] = "Pulse: S"
        print("\t Pulse: S")
        
    #Extra small pulse     FIXME::::::::::::
    elif difference <= settings.getSetting("sDiff"):
        relays.moveAct(act, settings.getSetting("xSPulse"))
        time.sleep(settings.getSetting("xSDelay"))
        smallDisplay2['text'] = "Pulse: XS"
        print("\t Pulse: XS")
    else:
        print("ADAPT ERROR")
    
    #update GUI
    tab1.update()

#performs autoleveling function when called
def autoLevel():
    printSettings()
    #do not run if zero point is still equal to (0,0) or if eStop is engaged
    if(not relays.getPause()):

        #set display
        display['text'] = 'Leveling...'
        #save start time
        start = time.time()
        print("\n------------Leveling------------")
        
        zeroRoll = roll.getZero()
        zeroPitch = pitch.getZero()
        sens1 = settings.getSetting("sens1")
        sens2 = settings.getSetting("sens2")

        if settings.getPriority() == "roll":
            first = roll
            second = pitch
            zeroFirst = zeroRoll
            zeroSecond = zeroPitch
            firstAxis = "roll"
            secondAxis = "pitch"
            firstPos = "Roll Right"
            firstNeg = "Roll Left"
            firstClose = "--Roll Close--"
            secondPos = "Pitch Up"
            secondNeg = "Pitch Down"
            secondClose = "--Roll Close--"
        else:
            first = pitch
            second = roll
            zeroFirst = zeroPitch
            zeroSecond = zeroRoll
            firstAxis = "pitch"
            secondAxis = "roll"
            firstPos = "--Pitch Up--"
            firstNeg = "--Pitch Down--"
            firstClose = "--Pitch Close--"
            secondPos = "--Roll Right--"
            secondNeg = "--Roll Left--"
            secondClose = "--Roll Close--"

        r = getReading(roll)
        p = getReading(pitch)
        
        #while current reading is not within sensitivity setting 1 continue to loop
        while not ((r < zeroRoll+sens1 
                and r > zeroRoll-sens1 
                and p < zeroPitch+sens1 
                and p > zeroPitch-sens1) 
                or relays.getPause()):
            
            #If FIRST is not within sens2 
            f = getReading(first)
            if not(f < zeroFirst+sens2 and f > zeroFirst-sens2):
                #loop until Ax is within sens2 or eStop is engaged
                while not((f < zeroFirst+sens2 and f > zeroFirst-sens2) or relays.getPause()):
                    #udpate Ax and Ay
                    f = getReading(first)

                    #print data for terminal output
                    print("\n______________________________________________________________")
                    print(roll)
                    print(pitch)

                    #if reading is greater than zero+sens2 move right using adapt() function
                    if(f >= zeroFirst+sens2):
                        print(firstPos)
                        smallDisplay["text"] = firstPos
                        tab1.update()
                        adapt(f, firstAxis)
                    
                    #if reading is less than zero-sens2 move left
                    elif(f <= zeroFirst-sens2):
                        print(firstNeg)
                        smallDisplay["text"] = firstNeg
                        tab1.update()
                        adapt(f, firstAxis)

                    #else X is close, do nothing     
                    else:
                        print(firstClose)
                        smallDisplay["text"] = firstClose
                        tab1.update()

            #same process for Y
            #If Y is not within sens2 adjust until within sens2
            s = getReading(second)
            if not(s < zeroSecond+sens2 and s > zeroSecond-sens2):
                while not ((s < zeroSecond+sens2 and s > zeroSecond-sens2) or relays.getPause()):
                    s = getReading(second)

                    print("\n______________________________________________________________")
                    print(roll)
                    print(pitch)

                    if(s >= zeroSecond+sens2):
                        print(secondPos)
                        smallDisplay["text"] = secondPos
                        tab1.update()
                        adapt(s, secondAxis)

                                
                    elif(s <= zeroSecond-sens2):
                        print(secondNeg)
                        print(f'Z-{first.getZero()} read - {s}')
                        smallDisplay["text"] = secondNeg
                        tab1.update()
                        adapt(s, secondAxis)
                                
                    else:   
                        print(secondClose)
                        smallDisplay["text"] = secondClose
                        tab1.update()

            #after getting X and Y within sens2, the program will bypass the above 2 while loops and attempt to get rig within sens1
            if not relays.getPause():            
                r = getReading(roll)
                p = getReading(pitch)
                
                #terminal output
                print("\n______________________________________________________________")
                print(roll)
                print(pitch)
            
                #if X is greater than zero+sens1 move right
                if(r >= zeroRoll+sens1):
                    print("  --Roll right--")
                    smallDisplay["text"] = "--Roll right--"
                    tab1.update()
                    adapt(r, "roll")

                #if X is less than zero-sens1 move left     
                elif(r <= zeroRoll-sens1):
                    print("  --Roll left--")
                    smallDisplay["text"] =  "--Roll left--"
                    tab1.update()
                    adapt(r, "roll")

                #else X is good do nothing            
                else:
                    print("  --Roll good--")
                    smallDisplay["text"] =  "--Roll good--"
                    tab1.update()

                #if Y is greater than zero+sens1 move up
                if(p >= zeroPitch+sens1):
                    print("  --Pitch up--")
                    smallDisplay["text"] =  "--Pitch up--"
                    tab1.update()
                    adapt(p, "pitch")

                #if Y is less than zero-sens1 move down                
                elif(p <= zeroPitch-sens1):
                    print("  --Pitch down--")
                    smallDisplay["text"] =  "--Pitch down--"
                    tab1.update()
                    adapt(p, "pitch")

                #else Y is good, do nothing                
                else:
                    print("  --Pitch good--")
                    smallDisplay["text"] = "--Pitch good--"
                    tab1.update()

                #check time elapsed, if elapsed time exceeds 90 seconds quit
                end = time.time()
                if end - start > 90:
                    display['text'] = 'Time Out'
                    smallDisplay["text"] = "Time elapsed: {}".format(round(end-start, 2))
                    smallDisplay2['text'] = ""
                    return False

        # *** END OUTER WHILE LOOP ***
        #while loop exits here only if Ax and Ay are within sens1, eStop has been engaged, or 90 seconds has elapsed. If none of these happen
        # the while loop will continue to loop from the beginning. Each if statement will be checked again meaning X or Y may be changed even if 
        #they were level at one point. It is also possible that the program may reenter the initial while loops that adjust X and Y within sens2.

        #if eStop has been engaged set necessary displays
        if relays.getPause():
            display['text'] = 'Paused..'
            end = time.time()
            smallDisplay["text"] = "Time elapsed: {}".format(round(end-start, 2))
            smallDisplay2['text'] = ""

        #else eStop has not been engaged, set necessary displays
        else:
            end = time.time()
            smallDisplay["text"] = "Time elapsed: {}".format(round(end-start, 2))
            display.configure(text = 'Done')
            smallDisplay2['text'] = ""
            if relays.getStayOn():
                display.configure(text = "Waiting...")
            if display.cget("text") == 'Paused..':
                display['text'] = ""
            #playsound('Sounds/ding.mp3')
            return True
    
    #executes if pause was set before level button was pressed or if zero is still equal to (0,0)
    else:
        smallDisplay["text"] = "Zero not taken"

#executes when Set Zero is clicked, averages 5 points
def saveZeros():
    msg_box = messagebox.askquestion('Set Zero?', 'Set this point as zero?', icon='warning')
    if msg_box == 'yes':
        #update display
        display['text'] = ". . ."
        #refresh GUI
        tab1.update()
        
        #set zeros
        zeroP = pitch.saveZero()
        zeroR = roll.saveZero()

        #update displays
        xZData.configure(text = OUTPUT_FORMAT%zeroR)
        yZData.configure(text =  OUTPUT_FORMAT%zeroP)
        display.configure(text = "Zero set")
        smallDisplay.configure(text = "")

#executes when Set 0 is clicked. Sets 0 as zero
def saveZeros2():
    msg_box = messagebox.askquestion('Set Zero?', 'Set 0 min as zero?', icon='warning')
    if msg_box == 'yes':

        zeroP = pitch.saveZero2()
        zeroR = roll.saveZero2()

        #update displays
        xZData.configure(text = OUTPUT_FORMAT%zeroR)
        yZData.configure(text =  OUTPUT_FORMAT%zeroP)
        display.configure(text = "Zero set")
        smallDisplay.configure(text = "")
        
def plot(title, x,y, order, label, frame):
    
    # the figure that will contain the plot
    fig = Figure(figsize = (6, 4),
                 dpi = 100)
    # adding the subplot
    plot1 = fig.add_subplot(111)
    
    coefficients = np.polynomial.polynomial.Polynomial.fit(
    x, # raw values
    y, # corresponding angle values to the raw values
    order) # order of polynomial
    
    p = np.polynomial.polynomial.Polynomial(coefficients)

    x_new = np.linspace(min(x), max(x))

    y_fit = coefficients(x_new)

    # # Plot the data points and the fitted line
    
    
    # plotting the graph
    plot1.plot(x_new, y_fit, label='Fitted Line')
    #plot1.title(title)
    plot1.legend()
    plot1.scatter(x, y, label=label)
    plot1.set_title(title)
    plot1.set_xlabel("Raw Data")
    plot1.set_ylabel("Minutes")
    
    # creating the Tkinter canvas
    # containing the Matplotlib figure
    canvas = FigureCanvasTkAgg(fig,
                               master = frame)  
    canvas.draw()
  
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()
  
    # creating the Matplotlib toolbar
    #toolbar = NavigationToolbar2Tk(canvas,
     #                              root)
    #toolbar.update()
  
    # placing the toolbar on the Tkinter window
    #canvas.get_tk_widget().pack()
  

#not needed
#verify settings are set correctly
def printSettings():
    print(settings.getSetting("sens1"))
    print(settings.getSetting("sens2"))
    print(settings.getSetting("xLDiff"))
    print(settings.getSetting("lDiff"))
    print(settings.getSetting("mDiff"))
    print(settings.getSetting("sDiff"))
    print(settings.getSetting("xLPulse"))
    print(settings.getSetting("lPulse"))
    print(settings.getSetting("mPulse"))
    print(settings.getSetting("sPulse"))
    print(settings.getSetting("xSPulse"))

    print(settings.getSetting("xLDelay"))
    print(settings.getSetting("lDelay"))
    print(settings.getSetting("mDelay"))
    print(settings.getSetting("sDelay"))
    print(settings.getSetting("xSDelay"))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -




# Create GUI - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


#if __name__ == "__main__":

#uses Tkinter package
root = Tk()
root.title("Auto Leveler")
root.geometry(WINDOW_SIZE)

#style
custom_style = ttk.Style()
custom_style.configure('Custom.TNotebook.Tab', padding=[12,12], font=(15))

# Create GUI tabs
tabs = ttk.Notebook(root, style ='Custom.TNotebook')
tab1 = tk.Frame(tabs)
tab2 = ttk.Frame(tabs)
tab3 = ttk.Frame(tabs)
tabs.add(tab1, text ='Auto Leveler')
tabs.add(tab2, text ='Settings')
tabs.add(tab3, text ='Sensor Setup')
tabs.pack(expand = 1, fill ="both")

#initialize ADC
# try:
#     ADC = serial.Serial(port = PORT, 
#                         baudrate = BAUDRATE,
#                         bytesize=BYTESIZE,
#                         parity = PARITY,
#                         stopbits=STOPBITS,
#                         timeout = TIMEOUT)
    
#     if(ADC.isOpen() == False):
#         print("Serial Port Error")
#         GPIO.cleanup()
#         exit()
    
# except IOError as e:
#     print(e)

#initialze settings
settings = Settings(SETTINGS_FILE)

#initalize relays
relays = Relays(LEFT_PIN, RIGHT_PIN, UP_PIN, DOWN_PIN)




### Tab 1 ###


#_____Labels_____

#Tab 1 Title
Label(tab1, text = "Auto Leveler", font = ("Roboto", 100)).grid(column = 2, columnspan= 5, row = 0, pady = 9)

#Main Display
display = Label(tab1, font = ("Roboto", 70, "italic"))
display.grid(column = 3, columnspan= 2, row = 1, pady = 2)

#Small Display in top right
smallDisplay = Label(tab1, font = ("Roboto", 25, "italic"))
smallDisplay.grid(column = 6, row = 0, sticky = 'e')

#Small display only shows pulse size
smallDisplay2 = Label(tab1, font = ("Roboto", 30, "italic"))
smallDisplay2.grid(column = 6, row = 1, sticky = 'ne')

#X data display
Label(tab1, text = " Roll:", font = ("Roboto", 50)).grid(column = 1, row = 2, sticky = "e", pady = 30)
xData = Label(tab1, font = ("Roboto", 50), bg = "gray", width = 10)
xData.grid(column = 2, row = 2, sticky = "w", pady = 7)

#Y data display
Label(tab1, text = " Pitch:", font = ("Roboto", 50)).grid(column = 1, row = 3, sticky = "e", pady = 30)
yData = Label(tab1, font = ("Roboto", 50), bg = "gray", width = 10)
yData.grid(column = 2, row = 3, sticky = "w", pady = 7)

#zeroRoll display
Label(tab1, text = "  Zero:", font = ("Roboto", 50)).grid(column = 3, row = 2, sticky = "e")
xZData = Label(tab1, text = 0, font = ("Roboto", 50), bg = "gray", width = 10)
xZData.grid(column = 4, row = 2, sticky = "w")

#zeroPitch display
Label(tab1, text = "  Zero:", font = ("Roboto", 50)).grid(column = 3, row = 3, sticky = "e")
yZData = Label(tab1, text = 0, font = ("Roboto", 50), bg = "gray", width = 10)
yZData.grid(column = 4, row = 3, sticky = "w")

#X difference display
Label(tab1, text = "  Δ:", font = ("Roboto", 50)).grid(column = 5, row = 2, sticky = "e")
xDiff = Label(tab1, text = 0, font = ("Roboto", 50), bg = "gray", width = 10)
xDiff.grid(column = 6, row = 2, sticky = "w")

#Y difference display
Label(tab1, text = "  Δ:", font = ("Roboto", 50)).grid(column = 5, row = 3, sticky = "e")
yDiff = Label(tab1, text = 0, font = ("Roboto", 50), bg = "gray", width = 10)
yDiff.grid(column = 6, row = 3, sticky = "w")


#manual relay control
directions = relays.getDirections()
buttonFrame = tk.Frame(tab1)
upButton = tk.Button(buttonFrame, text = "\u2191", font = ("Roboto", 30, "bold"), command = lambda: relays.moveUp(settings.getSetting("xSPulse"))).grid(row=0,column=1)
downButton = tk.Button(buttonFrame, text = "\u2193", font = ("Roboto", 30, "bold"), command = lambda: relays.moveDown(settings.getSetting("xSPulse"))).grid(row=2,column=1)
leftButton = tk.Button(buttonFrame, text = "\u2190", font = ("Roboto", 30, "bold"), command = lambda: relays.moveLeft(settings.getSetting("xSPulse"))).grid(row=1,column=0)
rightButton = tk.Button(buttonFrame, text = "\u2192", font = ("Roboto", 30, "bold"), command = lambda: relays.moveRight(settings.getSetting("xSPulse"))).grid(row=1,column=2)
buttonFrame.grid(column=6,row=6, rowspan = 2, sticky="s")



#_____Buttons_____

#Auto Level Button
auto = Button(tab1, text = "Level", font = ("Roboto", 40), command = autoLevel, width = 10)
auto.grid(column = 2, row = 5, pady = 20)

#Zero button
zero = Button(tab1, text="Save Zero", font = ("Roboto", 40), command= saveZeros, width = 10)
zero.grid(column = 3, columnspan= 2, row = 5)

#Zero = 0 button
zero2 = Button(tab1, text="Set 0", font = ("Roboto", 30), command= saveZeros2, width = 10)
zero2.grid(column = 3, columnspan= 2, row = 6)

#Exit button
exitButton = Button(tab1, text="Exit", font = ("Roboto", 40), command= clickExitButton, width = 10)
exitButton.grid(column = 6, row = 5)

#Pause Button
pauseButton = Button(tab1, text="Pause", font = ("Roboto", 40), command= pause, width = 10)
pauseButton.grid(column = 2, row = 6, pady = 20)

#Stay On Button
stayOnButton = Button(tab1, text="Stay On", font = ("Roboto", 30), command= stayOn, width = 10)
stayOnButton.grid(column = 2, row = 7, pady = 5)


### Tab 2 ###

#pull settings from csv file
settings.setSettings()
#_____Labels_____

#Tab 2 Title
Label(tab2, text = "Settings", font = ("Roboto", 80)).grid(column = 4, columnspan= 3, row = 0, pady = 9)

#Unit labels
Label(tab2, text = "Minutes", font = ("Roboto", 25)).grid(row = 1, column = 3, pady = 5)
Label(tab2, text = "Minutes", font = ("Roboto", 25)).grid(row = 1, column = 5)
Label(tab2, text = "seconds", font = ("Roboto", 25)).grid(row = 1, column = 7)
Label(tab2, text = "seconds", font = ("Roboto", 25)).grid(row = 1, column = 9)

#divider
Label(tab2, text = "Preset:", font = ("Roboto", 25)).grid(row = 1, column = 0)
Label(tab2, text = "  -", font = ("Roboto", 25)).grid(row = 6, column = 0)
Label(tab2, text = "Priority:", font = ("Roboto", 25)).grid(row = 9, column = 0, pady = 18)

#Setting name labels
Label(tab2, text = "  Final Δ <:", font = ("Roboto", 25)).grid(row = 2, column = 2, pady = 9, sticky = "e")
Label(tab2, text = "  Initial Δ <:", font = ("Roboto", 25)).grid(row = 3, column = 2, pady = 9, sticky = "e")
Label(tab2, text = "XL Difference >", font = ("Roboto", 25)).grid(row = 2, column = 4, pady = 9, padx = 10)
Label(tab2, text = "L Difference >", font = ("Roboto", 25)).grid(row = 3, column = 4, pady = 9)
Label(tab2, text = "M Difference >", font = ("Roboto", 25)).grid(row = 4, column = 4, pady = 9)
Label(tab2, text = "S Difference >", font = ("Roboto", 25)).grid(row = 5, column = 4, pady = 9)
Label(tab2, text = "XL Pulse:", font = ("Roboto", 25)).grid(row = 2, column = 6, pady = 9, padx = 10)
Label(tab2, text = "L Pulse:", font = ("Roboto", 25)).grid(row = 3, column = 6, pady = 9)
Label(tab2, text = "M Pulse:", font = ("Roboto", 25)).grid(row = 4, column = 6, pady = 9)
Label(tab2, text = "S Pulse:", font = ("Roboto", 25)).grid(row = 5, column = 6, pady = 9)
Label(tab2, text = "XS Pulse:", font = ("Roboto", 25)).grid(row = 6, column = 6, pady = 9)
Label(tab2, text = "Delay @ XL:", font = ("Roboto", 25)).grid(row = 2, column = 8, pady = 9, padx = 10)
Label(tab2, text = "Delay @ L:", font = ("Roboto", 25)).grid(row = 3, column = 8, pady = 9)
Label(tab2, text = "Delay @ M:", font = ("Roboto", 25)).grid(row = 4, column = 8, pady = 9)
Label(tab2, text = "Delay @ S:", font = ("Roboto", 25)).grid(row = 5, column = 8, pady = 9)
Label(tab2, text = "Delay @ XS:", font = ("Roboto", 25)).grid(row = 6, column = 8, pady = 9)

Label(tab2, text = "  Stay On Threshold:", font = ("Roboto", 20)).grid(row = 12, column = 2, pady = 9)
Label(tab2, text = "minutes", font = ("Roboto", 20)).grid(row = 12, column = 4, pady = 9, sticky = "w")

Label(tab2, text = "Invert Roll", font = ("Roboto", 20)).grid(row = 12, column = 4, sticky = "e")
Label(tab2, text = "Invert Pitch", font = ("Roboto", 20)).grid(row = 12, column = 6, sticky = "e")

invertRollButton = Button(tab2, text="Off", font = ("Roboto", 20), command= invertRoll)
invertRollButton.grid(column = 5, row = 12, sticky = "w")

invertPitchButton = Button(tab2, text="Off", font = ("Roboto", 20), command= invertPitch)
invertPitchButton.grid(column = 7, row = 12, sticky = "w")

if settings.getSetting("rollInvert") != relays.isRollInverted():
    invertRoll()
if settings.getSetting("pitchInvert") != relays.isPitchInverted():
    invertPitch()



#_____Radio buttons_____

#variable contains rig radiobutton selection
rigSelect = IntVar()

#Sets last used rig as default, stored in settings[1][0]
rigSelect.set(settings.getRig())

#Rig Options
tk.Radiobutton(tab2, 
               text="Midload", variable = rigSelect, command = selectRig, font = ("Roboto", 25),
               value=2).grid(column = 0, row = 2, sticky = "w")

tk.Radiobutton(tab2, 
               text="Light Load", variable = rigSelect, command = selectRig, font = ("Roboto", 25),
               value=3).grid(column = 0, row = 3, sticky = "w")

tk.Radiobutton(tab2, 
               text="ABCS Rig", variable = rigSelect, command = selectRig, font = ("Roboto", 25),
               value=4).grid(column = 0, row = 4, sticky = "w")

tk.Radiobutton(tab2, 
               text="LLR", variable = rigSelect, command = selectRig, font = ("Roboto", 25),
               value=5).grid(column = 0, row = 5, sticky = "w")

#variable contains level radiobutton selection
levelSelect = IntVar()

#sets last used level as default, stored in settings[1][1]
levelSelect.set(settings.getLevel())

#Level Options
tk.Radiobutton(tab2, 
               text="T-Level", variable = levelSelect, command = selectLevel, font = ("Roboto", 25),
               value=2).grid(column = 0, row = 7, sticky = "w")
tk.Radiobutton(tab2, 
               text="1\" Level", variable = levelSelect, command = selectLevel, font = ("Roboto", 25),
               value=3).grid(column = 0, row = 8, sticky = "w")


#variable contains priority radiobutton selection
prioritySelect = IntVar()

#sets last used level as default, stored in settings[1][1]
prioritySelect.set(0)

#Priority Options
tk.Radiobutton(tab2, 
               text="Pitch", variable = prioritySelect, command = setPriority, font = ("Roboto", 25),
               value=0).grid(column = 0, row = 10, sticky = "w")
tk.Radiobutton(tab2, 
               text="Roll", variable = prioritySelect, command = setPriority, font = ("Roboto", 25),
               value=1).grid(column = 0, row = 11, sticky = "w")


#Entries
settingsEntryData = {
    "threshold": (12, 3),
    "sens1": (2, 3),
    "sens2": (3, 3),
    "xLDiff": (2, 5),
    "lDiff": (3, 5),
    "mDiff": (4, 5),
    "sDiff": (5, 5),
    "xLPulse": (2, 7),
    "lPulse": (3, 7),
    "mPulse": (4, 7),
    "sPulse": (5, 7),
    "xSPulse": (6, 7),
    "xLDelay": (2, 9),
    "lDelay": (3, 9),
    "mDelay": (4, 9),
    "sDelay": (5, 9),
    "xSDelay": (6, 9)
}

settingEntry = {}  # Dictionary to store the Entry widgets

for setting, position in settingsEntryData.items():
    entry = tk.Entry(tab2, width=6, font=("Roboto", 15))
    entry.insert(0, settings.getSetting(setting))
    entry.grid(row=position[0], column=position[1])
    settingEntry[setting] = entry  # Store the Entry widget in the dictionary


#save Button
save = tk.Button(tab2, text = "Save Settings", font = ("Roboto", 25), command = saveSettings)
save.grid(row = 7, column = 9, columnspan = 2, pady = 10)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

### Tab 3 ###

Label(tab3, text = "Sensor Setup", font = ("Roboto", 60)).grid(column = 4, columnspan= 3, row = 0, pady = 9)

Label(tab3, text = "Pitch:", font = ("Roboto", 30)).grid(column = 0, row = 1, pady = 15)
Label(tab3, text = "Raw Data:", font = ("Roboto", 20)).grid(column = 0, row = 2, padx = 5)
Label(tab3, text = "Minutes:", font = ("Roboto", 20)).grid(column = 0, row = 3)

Label(tab3, text = "Roll:", font = ("Roboto", 30)).grid(column = 0, row = 4, pady = 15)
Label(tab3, text = "Raw Data:", font = ("Roboto", 20)).grid(column = 0, row = 5, padx = 5)
Label(tab3, text = "Minutes:", font = ("Roboto", 20)).grid(column = 0, row = 6)

Label(tab3, text = "Order:", font = ("Roboto", 20)).grid(column = 8, row = 2)
Label(tab3, text = "Show Raw Data:", font = ("Roboto", 20)).grid(column = 8, row = 5)


pitchRaw = settings.getSetting("pitchRaw")
pitchCalc = settings.getSetting("pitchCalc")
rollRaw = settings.getSetting("rollRaw")
rollCalc = settings.getSetting("rollCalc")

pitchRawEntries = []
pitchCalcEntries = []
rollRawEntries = []
rollCalcEntries = []

# Create pitchRaw entries
for i in range(7):
    entry = tk.Entry(tab3, width=10, font=("Roboto", 20))
    entry.insert(0, pitchRaw[i])
    entry.grid(row=2, column=i+1)
    pitchRawEntries.append(entry)

# Create pitchCalc entries
for i in range(7):
    entry = tk.Entry(tab3, width=10, font=("Roboto", 20))
    entry.insert(0, pitchCalc[i])
    entry.grid(row=3, column=i+1)
    pitchCalcEntries.append(entry)

# Create rollRaw entries
for i in range(7):
    entry = tk.Entry(tab3, width=10, font=("Roboto", 20))
    entry.insert(0, rollRaw[i])
    entry.grid(row=5, column=i+1)
    rollRawEntries.append(entry)

# Create rollCalc entries
for i in range(7):
    entry = tk.Entry(tab3, width=10, font=("Roboto", 20))
    entry.insert(0, rollCalc[i])
    entry.grid(row=6, column=i+1)
    rollCalcEntries.append(entry)

orderEntry = tk.Entry(tab3, width = 5, font = ("Roboto", 20))
orderEntry.insert(0, settings.getSetting("order"))
orderEntry.grid(row = 2, column = 9)



rawDataSwitch = Button(tab3, text="Off", font = ("Roboto", 15), command= selectData)
rawDataSwitch.grid(column = 9, row = 5)

if(settings.getSetting("data") == 1):
    rawDataSwitch.configure(text = "On")

frame_pitch = Frame(tab3)
frame_pitch.grid(row=8, column=1, columnspan = 3)

frame_roll = Frame(tab3)
frame_roll.grid(row=8, column=4, columnspan = 3)


plot("Pitch", pitchRaw, pitchCalc, 3, "Pitch", frame_pitch)
plot("Roll", rollRaw, rollCalc, 3, "Roll", frame_roll)



#save Button
save = tk.Button(tab3, text = "Save Settings", font = ("Roboto", 25), command = saveSensorSettings)
save.grid(row = 7, column = 8, columnspan = 2, pady = 10)


# RUN PROGRAM - - - - - - - - - - - - - - - - - - - - - - - - - - - -

#initalize sensors
#pitch = Sensor("pitch", ADC, pitchRaw, pitchCalc, settings.getSetting("data"))
#roll = Sensor("roll", ADC, rollRaw, rollCalc, settings.getSetting("data"))

try:
    #displayColor()

    #continuously updates pitch and roll values
    #looped only for visual indication, not necessary for the function of the program
    # while True:
    #     getReading(pitch)
    #     getReading(roll)
    #     time.sleep(READING_REFRESH)
    #never reached
    root.mainloop()

except OSError as e:
    print(e)
   
except KeyboardInterrupt:
    print("ctrl + c:")
    print("Program end")
    
finally:
    print("Program end")
    ADC.close()
    GPIO.cleanup()
    exit()
    

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
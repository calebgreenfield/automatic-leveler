# Settings.py
# Caleb Greenfield
# 3/7/23

# AutoLevel Project:
# run_auto_leveler.py
# Relays.py
# Sensor.py
# Settings.py
# settings.csv


# Overview:
# This page defines variables and helper methods for accessing and changing settings stored in settings.csv


import csv
import numpy as np

#RIG IDs
MIDLOAD = 2
LIGHT_LOAD = 3
ABCS_RIG = 4
LLR = 5

#Level ID's
T_LEVEL = 2
INCH_LEVEL = 3

#Last Rig and Level csv location
LASTRIG_ROW = 1
LASTRIG_COLUMN = 0

LASTLEVEL_ROW = 1
LASTLEVEL_COLUMN = 1

#setting.csv column locations
RIG = 0
LEVEL = 1

PITCH_RAW = 10
PITCH_CALC = 11
ROLL_RAW = 12
ROLL_CALC = 13
ORDER = 14
DATA = 15

SENS1 = 2
SENS2 = 3                               
XLDIFF = 4
LDIFF = 5
MDIFF = 6
SDIFF  = 7            
XLPULSE = 8
LPULSE = 9
MPULSE = 10
SPULSE = 11
XSPULSE = 12
XLDELAY = 13
LDELAY = 14
MDELAY = 15
SDELAY = 16
XSDELAY = 17

ROLL_INVERT = 18
PITCH_INVERT = 19
#RELAY_INVERT = 20

THRESHOLD = 20




class Settings:
    #initialize settings
    #instantiated as settings = Settings(SETTINGS_FILE) in run_auto_leveler.py
    def __init__(self, file):
        #set file name
        self.csvFile = file
        #array to hold contents of csv file
        #FIXME: pd dataframe would be better
        self.settings = []

        #preset variables
        self.rig = -1           #Midload = 2, Light Load = 3, ABCS = 4, LLR = 5
        self.level = -1         #T-Level = 2, 1" Level = 3
        self.rigPreset = -1     #references column of currently selected rig in settings.csv

        #set default priority
        self.priority = "pitch"

        #settings dictionary for easy access
        self.settingDict = {}
        
        #sensor setup settings
        self.pitchRaw = np.zeros(7)
        self.pitchCalc = np.zeros(7)

        self.rollRaw = np.zeros(7)
        self.rollCalc = np.zeros(7)

    #stores current rig preset settings
    #FIXME: pd dataframe might be better
    def initDict(self):
        self.pitchRaw = [float(self.settings[PITCH_RAW][0]),
                         float(self.settings[PITCH_RAW][1]),
                         float(self.settings[PITCH_RAW][2]),
                         float(self.settings[PITCH_RAW][3]),
                         float(self.settings[PITCH_RAW][4]),
                         float(self.settings[PITCH_RAW][5]),
                         float(self.settings[PITCH_RAW][6])]
        self.pitchCalc = [float(self.settings[PITCH_CALC][0]),
                          float(self.settings[PITCH_CALC][1]),
                          float(self.settings[PITCH_CALC][2]),
                          float(self.settings[PITCH_CALC][3]),
                          float(self.settings[PITCH_CALC][4]),
                          float(self.settings[PITCH_CALC][5]),
                          float(self.settings[PITCH_CALC][6])]
        self.rollRaw = [float(self.settings[ROLL_RAW][0]),
                        float(self.settings[ROLL_RAW][1]),
                        float(self.settings[ROLL_RAW][2]),
                        float(self.settings[ROLL_RAW][3]),
                        float(self.settings[ROLL_RAW][4]),
                        float(self.settings[ROLL_RAW][5]),
                        float(self.settings[ROLL_RAW][6])]
        self.rollCalc = [float(self.settings[ROLL_CALC][0]),
                         float(self.settings[ROLL_CALC][1]),
                         float(self.settings[ROLL_CALC][2]),
                         float(self.settings[ROLL_CALC][3]),
                         float(self.settings[ROLL_CALC][4]),
                         float(self.settings[ROLL_CALC][5]),
                         float(self.settings[ROLL_CALC][6])]
        
        self.settingDict = {"sens1" : self.settings[self.rigPreset][SENS1],
                "sens2" : self.settings[self.rigPreset][SENS2],
                "xLDiff" : self.settings[self.rigPreset][XLDIFF],
                "lDiff" : self.settings[self.rigPreset][LDIFF],
                "mDiff" : self.settings[self.rigPreset][MDIFF],
                "sDiff" : self.settings[self.rigPreset][SDIFF],
                "xLPulse" : self.settings[self.rigPreset][XLPULSE],
                "lPulse" : self.settings[self.rigPreset][LPULSE],
                "mPulse" : self.settings[self.rigPreset][MPULSE],
                "sPulse" : self.settings[self.rigPreset][SPULSE],
                "xSPulse" : self.settings[self.rigPreset][XSPULSE],
                "xLDelay" : self.settings[self.rigPreset][XLDELAY],
                "lDelay" : self.settings[self.rigPreset][LDELAY],
                "mDelay" : self.settings[self.rigPreset][MDELAY],
                "sDelay" : self.settings[self.rigPreset][SDELAY],
                "xSDelay" : self.settings[self.rigPreset][XSDELAY],
                "rollInvert" : self.settings[self.rigPreset][ROLL_INVERT],
                "pitchInvert" : self.settings[self.rigPreset][PITCH_INVERT],
                "threshold" : self.settings[self.rigPreset][THRESHOLD],
                "pitchRaw" : self.pitchRaw,
                "pitchCalc" : self.pitchCalc,
                "rollRaw" : self.rollRaw,
                "rollCalc" : self.rollCalc,
                "order" : self.settings[ORDER][0],
                "data" : self.settings[DATA][0]
                            }
        
        

    def getPriority(self):
        return self.priority
    
    def setPriority(self, priority):
        self.priority = priority

    #update csv with current contents of settings array
    def updateCSV(self):
        #open settings.csv and update values
        with open(self.csvFile, "w+") as f:
            csvWriter = csv.writer(f, delimiter=',')
            csvWriter.writerows(self.settings)
    
    def getRig(self):
        return self.rig
    
    #Sets current rig and update value in csv file
    def setRig(self, rig):
        if rig == MIDLOAD:
            self.settings[LASTRIG_ROW][LASTRIG_COLUMN] = 'Midload'
        elif rig == LIGHT_LOAD:
            self.settings[LASTRIG_ROW][LASTRIG_COLUMN] = 'Light Load'
        elif rig == ABCS_RIG:
            self.settings[LASTRIG_ROW][LASTRIG_COLUMN] = 'ABCS Rig'
        elif rig == LLR:
            self.settings[LASTRIG_ROW][LASTRIG_COLUMN] = 'LLR'

        self.rig = rig
        self.updateCSV()
        self.setSettings()

    
    def getLevel(self):
        return self.level
    
    #Sets current level and updates value in csv file
    def setLevel(self, level):
        if level == T_LEVEL:
            self.settings[LASTLEVEL_ROW][LASTLEVEL_COLUMN] = 'T-Level'
        elif level == INCH_LEVEL:
            self.settings[LASTLEVEL_ROW][LASTLEVEL_COLUMN] = '1 Level'

        self.level = level
        self.updateCSV()
        self.setSettings()
        
     #Sets current level and updates value in csv file
    def setData(self, data):
        self.settings[DATA][0] = data
        self.updateCSV()
        self.setSettings()
    
    def getData(self):
        return self.settings[DATA][0]

    #returns specified setting value from settings dictionary
    def getSetting(self, setting):
        if (setting == "pitchRaw"
            or setting == "pitchCalc"
            or setting == "rollRaw"
            or setting == "rollCalc"):
            
            return self.settingDict[setting]
        elif(setting == "order"):
            return int(self.settingDict[setting])
        else:
            return float(self.settingDict[setting])

    #recives settings entries in an array from run_autoleveler.py, updates csv file
    def setNewSettings(self, array):
        self.settings[self.rigPreset][SENS1] = array[0]
        self.settings[self.rigPreset][SENS2] = array[1]
        self.settings[self.rigPreset][XLDIFF] = array[2]
        self.settings[self.rigPreset][LDIFF] = array[3]
        self.settings[self.rigPreset][MDIFF] = array[4]
        self.settings[self.rigPreset][SDIFF] = array[5]
        self.settings[self.rigPreset][XLPULSE] = array[6]
        self.settings[self.rigPreset][LPULSE] = array[7]
        self.settings[self.rigPreset][MPULSE] = array[8]
        self.settings[self.rigPreset][SPULSE] = array[9]
        self.settings[self.rigPreset][XSPULSE] = array[10]
        self.settings[self.rigPreset][XLDELAY] = array[11]
        self.settings[self.rigPreset][LDELAY] = array[12]
        self.settings[self.rigPreset][MDELAY] = array[13]
        self.settings[self.rigPreset][SDELAY] = array[14]
        self.settings[self.rigPreset][XSDELAY] = array[15]
        self.settings[self.rigPreset][ROLL_INVERT] = array[16]
        self.settings[self.rigPreset][PITCH_INVERT] = array[17]
        #self.settings[self.rigPreset][RELAY_INVERT] = array[18]
        self.settings[self.rigPreset][THRESHOLD] = array[18]

        self.updateCSV()
        self.setSettings()
        
    #recives settings entries in an array from run_autoleveler.py, updates csv file
    def setNewSensorSettings(self, array):
        self.settings[PITCH_RAW][0] = array[0]
        self.settings[PITCH_RAW][1] = array[1]
        self.settings[PITCH_RAW][2] = array[2]
        self.settings[PITCH_RAW][3] = array[3]
        self.settings[PITCH_RAW][4] = array[4]
        self.settings[PITCH_RAW][5] = array[5]
        self.settings[PITCH_RAW][6] = array[6]
        self.settings[PITCH_CALC][0] = array[7]
        self.settings[PITCH_CALC][1] = array[8]
        self.settings[PITCH_CALC][2] = array[9]
        self.settings[PITCH_CALC][3] = array[10]
        self.settings[PITCH_CALC][4] = array[11]
        self.settings[PITCH_CALC][5] = array[12]
        self.settings[PITCH_CALC][6] = array[13]
        self.settings[ROLL_RAW][0] = array[14]
        self.settings[ROLL_RAW][1] = array[15]
        self.settings[ROLL_RAW][2] = array[16]
        self.settings[ROLL_RAW][3] = array[17]
        self.settings[ROLL_RAW][4] = array[18]
        self.settings[ROLL_RAW][5] = array[19]
        self.settings[ROLL_RAW][6] = array[20]
        self.settings[ROLL_CALC][0] = array[21]
        self.settings[ROLL_CALC][1] = array[22]
        self.settings[ROLL_CALC][2] = array[23]
        self.settings[ROLL_CALC][3] = array[24]
        self.settings[ROLL_CALC][4] = array[25]
        self.settings[ROLL_CALC][5] = array[26]
        self.settings[ROLL_CALC][6] = array[27]
        self.settings[ORDER][0] = array[28]
        
        self.updateCSV()
        self.setSettings()

    #reads csv file and updates all current settings based of rig/level preset
    def setSettings(self):
        #open csv
        with open(self.csvFile) as f:
            reader = csv.reader(f)
            self.settings = list(reader)

        #pull last used rig and level
        rigName = self.settings[LASTRIG_ROW][LASTRIG_COLUMN]
        levelName = self.settings[LASTLEVEL_ROW][LASTLEVEL_COLUMN]
        
        #set rig variable value
        if rigName == "Midload":
            self.rig = MIDLOAD
        elif rigName == "Light Load":
            self.rig = LIGHT_LOAD
        elif rigName == "ABCS Rig":
            self.rig = ABCS_RIG
        elif rigName == "LLR":
            self.rig = LLR
        
        #set level variable value
        if levelName == "T-Level":
            self.level = T_LEVEL
        elif levelName == "1 Level":
            self.level = INCH_LEVEL
        
        #find rig preset for selected rig and level by iterating through rows in settings
        for r in range (2, len(self.settings)):
            #if rig and level name match
            if self.settings[r][RIG] == rigName and self.settings[r][LEVEL] == levelName:
                #save rig preset
                rigPreset = r

                self.rigPreset = rigPreset
                self.initDict()
                break
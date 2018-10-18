#! /usr/bin/python3
# Raspberry Pi photobooth with printer (Canon SELPHY CP1200) and touchscreen (Using Kivy)
# Captures 3 images and creates them into a collage, and (optionally) prints 2 copies per page
# Version: 0.4c
# Programmar: Matthew Brady
# Designer/Artist: Andrea Brady
# Woodworker: Nick Natale

import picamera
import cups
import time
from time import sleep
import os
import sys
from shutil import copyfile
import logging
import subprocess
import PIL
from PIL import Image
import kivy
kivy.require('1.10.0') # Set this to your current Kivy version
from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as kivyImage
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle

# Variables
saveDir = "/home/pi/photobooth/save" # Where the pictures that are taken are saved
logDir = "/home/pi/photobooth/logs/RasPi_Booth.log" # Where the log is saved
photoDir = "/home/pi/photobooth/photos/" # Where the magic happens with the photos
photoOne = photoDir + "1.jpg" # First taken photo
photoTwo = photoDir + "2.jpg" # Second taken photo
photoThree = photoDir + "3.jpg" # Third taken photo
collageName = "collage.jpg" # Name of the collage photo
collageNameSmall = "collage_small.jpg" # Name of the small collage photo for displaying on the screen
collageCreated = False # Script processing
collageTime = 0 # Script processing
collageTimeout = 45 # How long the latest collage will display on the screen
logoName = photoDir + "logo.jpg" # Name of the logo photo
enablePrinter = True # Set to False to disable the printer functionality + display
enablePhotoPrint = False # Set to True to enable printing each individual picture
enableTwoCopies = True # Set to True to enable printing two copies of the collage
printerName = "CP1300" # Set to the name you configured the printer in on the CUPS server
printerBusy = False # Script processing
printerTime = 0 # Script processing
printerTimeout = 60 # Script processing
printingName = photoDir + "printing.jpg" # Name of the printing/printer busy photo
frameDir = "/home/pi/photobooth/frames/" # Where the frames are stored
frameName = frameDir + "101318.jpg" # Name of the frame photo
cupsUser = "pi" # If you are using a username other than the default, change it here
photoExt = ".jpg" # Set to your desired photo extension. If not using jpg, you may have to install different libraries
photoName = time.strftime("%Y_%m_%d_%H_%M_%S") # File name format for the backup images

# Logging configuration
logging.basicConfig(filename=logDir,level=logging.DEBUG)
logging.basicConfig(format='[%(asctime)s] %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# Function to capture and save photographs.
def takePhotos(obj):
    logging.info('Function takePhotos was called.')
	
    if printerBusy == False and collageCreated == False:
        camera = picamera.PiCamera()
        camera.resolution = (1280, 720)
        camera.start_preview()
        sleep(10)
        camera.capture(photoOne)
        photoName = time.strftime("%Y_%m_%d_%H_%M_%S")
        copyfile(photoOne, saveDir + "/" + photoName + photoExt)
        camera.start_preview()
        sleep(5)
        camera.capture(photoTwo)
        photoName = time.strftime("%Y_%m_%d_%H_%M_%S")
        copyfile(photoTwo, saveDir + "/" + photoName + photoExt)
        camera.start_preview()
        sleep(5)
        camera.capture(photoThree)
        photoName = time.strftime("%Y_%m_%d_%H_%M_%S")
        copyfile(photoThree, saveDir + "/" + photoName + photoExt)
        camera.close()
        createCollage(obj)
        logging.info('Function takePhotos completed.')
 
# Function to create the collage 
def createCollage(obj):
    logging.info('Function createCollage was called.')
    subprocess.call(["montage", frameName, photoOne, photoTwo, photoThree, "-tile", "2x2", "-geometry", "+2+2", "-background", "white", photoDir + collageName])
    global collageCreated
    collageCreated = True
    global collageTime
    collageTime = 0
    photoName = time.strftime("%Y_%m_%d_%H_%M_%S")
    global collageNameSmall
    collageNameSmall = photoDir + photoName + "_collage_small" + photoExt
    subprocess.call(["montage", frameName, photoOne, photoTwo, photoThree, "-tile", "2x2", "-geometry", "720x720+2+2", "-background", "white", collageNameSmall])
    copyfile(photoDir + collageName, saveDir + "/" + photoName + "_collage" + photoExt)
    logging.info('Function createCollage completed.')

# Function to send it to the printer for printing (Using CUPS)          
def printCollage(obj):
    logging.info('Function printCollage was called.')
    global printerBusy
    
    if printerBusy == False:
        conn = cups.Connection()
        cups.setUser(cupsUser)
        global printerTime
        global printerTimeout
        printerTime = 0
        printerBusy = True
		
        if enableTwoCopies == False:
            conn.printFile(printerName, photoDir + collageName, "RasPi_Booth", {'fit-to-page':'True'})
            printerTimeout = 60
        else:
            conn.printFile(printerName, photoDir + collageName, "RasPi_Booth", {'fit-to-page':'True', 'copies':'2'})
            printerTimeout = 120
            
        logging.info('Function printCollage completed.')

# Function to print each individual photo.
def printPhotos(obj):
    logging.info('Function printPhotos was called.')
    global printerBusy
    
    if printerBusy == False:
        conn = cups.Connection()
        cups.setUser(cupsUser)
        conn.printFile(printerName, photoOne, "RasPi_Booth", {'fit-to-page':'True'})
        conn.printFile(printerName, photoTwo, "RasPi_Booth", {'fit-to-page':'True'})
        conn.printFile(printerName, photoThree, "RasPi_Booth", {'fit-to-page':'True'})
        global printerTime
        global printerTimeout
        printerTime = 0
        printerTimeout = 180
        printerBusy = True
        logging.info('Function printPhotos completed.')

# Main code of the application
class RasPi_Booth(App):
    photo = kivyImage(source=logoName) # Display logo on first launch

    def build(self):
        # Set up the layout
        photobox = GridLayout(cols=4, spacing=5, padding=5)

        # Create the UI objects
        photoButton = Button(text="Take Photos", size_hint=(.20, .30))
        photoButton.bind(on_press=takePhotos)
        printCollageButton = Button(text="Print Collage", size_hint=(.20, .30))
        printCollageButton.bind(on_press=printCollage)
        printPhotosButton = Button(text="Print Photos", size_hint=(.20, .30))
        printPhotosButton.bind(on_press=printPhotos)

        # Timer to update the displayed photo
        Clock.schedule_interval(self.photoUpdate, 3)

        # Add the UI elements to the layout
        photobox.add_widget(photoButton)
        photobox.add_widget(self.photo)
        
        if enablePrinter == True:
            photobox.add_widget(printCollageButton)
			
        if enablePhotoPrint == True:
            photobox.add_widget(printPhotosButton)

        return photobox
        
        
    # Function to update the display to the latest collage photo/logo on timeout/printer busy
    def photoUpdate(self, instance):
        global collageTime
        global collageCreated
        global printerTime
        global printerBusy
        collageTime += 3
        printerTime += 3
        
        if printerBusy == False:
            if collageCreated == True:
                if self.photo.source != collageNameSmall:
                    self.photo.source = collageNameSmall
                else:
                    if collageTime >= collageTimeout:
                        self.photo.source = logoName
                        collageCreated = False
                        os.remove(photoOne)
                        os.remove(photoTwo)
                        os.remove(photoThree)
                        os.remove(photoDir + collageName)
                        os.remove(collageNameSmall)
            elif collageCreated == False:
                if self.photo.source != logoName:
                    self.photo.source = logoName	
        elif printerBusy == True:
            if self.photo.source != printingName:
                self.photo.source = printingName
            if printerTime >= printerTimeout:
                self.photo.source = logoName
                printerBusy = False

if __name__ == '__main__':
    RasPi_Booth().run()

#! /usr/bin/python3
# Raspberry Pi photobooth with printer (Canon SELPHY CP1200) and touchscreen (Using Kivy)
# Captures 3 images and creates them into a collage, and (optionally) prints 2 copies per page
# Version: 0.3
# By: Matthew Brady, Andrea Lynn

import picamera
import cups
import time
from time import sleep
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
logDir = "/home/pi/photobooth/logs" # Where the log is saved
collageName = "collage.jpg" # Name of the collage photo
collageNameSmall = "collage_small.jpg" # Name of the small collage photo for displaying on the screen
collageCreated = False # Script processing
collageTime = 0 # Script processing
collageTimeout = 25 # How long the latest collage will display on the screen
logoName = "logo.jpg" # Name of the logo photo
enablePrinter = True # Set to False to disable the printer functionality + display
printerName = "CP1200" # Set to the name you configured the printer in on the CUPS server
printerBusy = False # Script processing
printerTime = 0 # Script processing
printerTimeout = 60 # Script processing
printingName = "printing.jpg" # Name of the printing/printer busy photo
cupsUser = "pi" # If you are using a username other than the default, change it here
photoExt = ".jpg" # Set to your desired photo extension. If not using jpg, you may have to install different libraries
photoName = time.strftime("%Y_%m_%d_%H:%M:%S") # File name format for the backup images

# Function to capture and save photographs.
def takePhotos(obj):
    if printerBusy == False:
		camera = picamera.PiCamera()
		camera.resolution = (1280, 720)
		camera.start_preview()
		sleep(3)
		camera.capture('1.jpg')
		photoName = time.strftime("%Y_%m_%d_%H:%M:%S")
		copyfile('1.jpg', saveDir + "/" + photoName + photoExt)
		camera.start_preview()
		sleep(3)
		camera.capture('2.jpg')
		photoName = time.strftime("%Y_%m_%d_%H:%M:%S")
		copyfile('2.jpg', saveDir + "/" + photoName + photoExt)
		camera.start_preview()
		sleep(3)
		camera.capture('3.jpg')
		photoName = time.strftime("%Y_%m_%d_%H:%M:%S")
		copyfile('3.jpg', saveDir + "/" + photoName + photoExt)
		camera.close()
		createCollage(obj)
        
def createCollage(obj):
    subprocess.call(["montage", '1.jpg', '1.jpg', '2.jpg', '2.jpg', '3.jpg', '3.jpg', "-tile", "2x3", "-geometry", "+2+2", collageName])
    subprocess.call(["montage", '1.jpg', '1.jpg', '2.jpg', '2.jpg', '3.jpg', '3.jpg', "-tile", "2x3", "-geometry", "640x640+2+2", collageNameSmall])
    global collageCreated
    collageCreated = True
    global collageTime
    collageTime = 0
    photoName = time.strftime("%Y_%m_%d_%H:%M:%S")
    copyfile(collageName, saveDir + "/" + photoName + "_collage" + photoExt)

# Function to send it to the printer for printing (Using CUPS)          
def printCollage(obj):
    if printerBusy == False:
		conn = cups.Connection()
		cups.setUser(cupsUser)
		conn.printFile(printerName, collageName, "RasPi_Booth", {'fit-to-page':'True'})
		global printerTime
		global printerTimeout
		global printerBusy
		printerTime = 0
		printerTimeout = 60
		printerBusy = True

def printPhotos(obj):
    if printerBusy == False:
		conn = cups.Connection()
		cups.setUser(cupsUser)
		conn.printFile(printerName, "1.jpg", "RasPi_Booth", {'fit-to-page':'True'})
		conn.printFile(printerName, "2.jpg", "RasPi_Booth", {'fit-to-page':'True'})
		conn.printFile(printerName, "3.jpg", "RasPi_Booth", {'fit-to-page':'True'})
		global printerTime
		global printerTimeout
		global printerBusy
		printerTime = 0
		printerTimeout = 180
		printerBusy = True


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
            photobox.add_widget(printPhotosButton)

        return photobox
        
        
    # Function to update the display to the lastest collage photo/logo on timeout/printer busy
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
			else:
				if self.photo.source != logoName:
					self.photo.source = logoName
		else:
			if self.photo.source != printingName:
				self.photo.source = printingName
			if printerTime >= printerTimeout:
				self.photo.source = logoName
				printerBusy = False


if __name__ == '__main__':
    RasPi_Booth().run()

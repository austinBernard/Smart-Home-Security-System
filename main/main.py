#! /usr/bin/env python3

import cv2
import face_recognition
import os, sys
from os import system
import numpy as np
import glob
import time
import serial
import adafruit_fingerprint
import RPi.GPIO as GPIO
from gpiozero import Servo
from faceRecognition import FaceRecognition
import RPi_I2C_driver
import random
import subprocess
import pygame
import requests
from datetime import datetime
from restart_main_script import restart_main_script
from password_manager import load_password_from_file, update_password_if_changed, PASSWORD
from features.trigger_alarm import trigger_alarm
from features.keypad_func import enter_password, check_password, enter_new_password, save_password_to_file, load_password_from_file

# Run pigpiod at the start of program
system("sudo pigpiod")

# Passcode to unlock door without facial recognition or finger print verification
previous_timestamp = 0

# Owner password to allow user to change password or to input a new user
OWNER_PASSWORD = "5678"

GPIO.setmode(GPIO.BOARD)

''' Setup i2c LCD'''
mylcd = RPi_I2C_driver.lcd()

''' Setup button for Keypad '''
keypad_button_pin = 36
GPIO.setup(keypad_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pin #36 GPIO 16

''' SETUP NEW BUTTON TO BE ABLE TO RESTART main.py FOR WHENEVER NEW FACES ARE ADDED TO DATASET 'faces'''
reset_button_pin = 21
GPIO.setup(reset_button_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)
GPIO.add_event_detect(reset_button_pin, GPIO.FALLING, callback=restart_main_script, bouncetime=1000) 

''' Third button that will unlock the door, allowing the user to leave from the inside '''
servo_control_button_pin = 23
GPIO.setup(servo_control_button_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

# Whenever servo control button is pressed, unlock door, wait for door to be closed, relock door
def operate_door():
    myServo.max() # Unlock door
    GPIO.output(35, False)   # Turn off the red LED
    GPIO.output(37, True)  # Turn on the green LED
    time.sleep(8)
    while GPIO.input(11) == GPIO.LOW:
        print("Door is opened")
        time.sleep(0.1)
    time.sleep(2)
    myServo.mid() # Relock door
    GPIO.output(35, True)   # Turn on the red LED
    GPIO.output(37, False)  # Turn off the green LED 

''' Setup GREEN,RED, WHITE LED '''
GPIO.setup(35, GPIO.OUT) # Red LED
GPIO.setup(37, GPIO.OUT) # Green LED
GPIO.setup(38, GPIO.OUT) # WHITE LED
# Set LED to start as red, meaning the door is locked.
GPIO.output(35, True)

GPIO.setwarnings(False)


''' Setup magnetic contact switches '''
#GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN) # Pin 11
# GPIO.input(11) == GPIO.LOW:   (switch is CLOSED)
# GPIO.input(11) == GPIO.HIGH   (switch is OPEN)


''' Setup motion sensor '''
#GPIO.setmode(GPIO.BOARD)
GPIO.setup(13, GPIO.IN) # Pin 13
# GPIO.input(13) == GPIO.HIGH (Motion is detected)


''' Setup servo motor '''
#### MUST RUN "sudo pigpiod" AT EVERY START UP ####
#servo = Servo(12, pin_factory = factory) # 12 = GPIO12 pin #32
# Turn the servo motor a full 180 degrees
myCorrection = 0.45
maxPW = (2.0 + myCorrection) / 1000
minPW = (1.0 - myCorrection) / 1000

myServo = Servo(12, min_pulse_width = minPW, max_pulse_width = maxPW)


''' Setting up fingerprint sensor '''
# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


# Directory containing the PNG files   'face_recognition/faces'
pngDir = 'faces'

''' Flask app for user verification list '''
flask_app_url = 'https://veconarts.pythonanywhere.com/upload-verification'
        
def upload_verification_data(flask_app_url, name):

    try:
        #timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        data = {'name': name, 'timestamp': timestamp}

        # Send a POST request to upload the verification data
        response = requests.post(flask_app_url, data=data)

        if response.status_code == 200:
            print('Verification data uploaded successfully')
            print(timestamp)
            return True
        else:
            print('Failed to upload verification data:', response.status_code)
            return False
    except Exception as e:
        print('Error while uploading verification data:', str(e))
        return False

# Initialize text-to-speech engine
def say_text(text, speed=None):
    command = f'echo "(Parameter.set \'Duration_Stretch {speed}) (SayText \\"{text}\\")" | festival --pipe'
    subprocess.run(command, shell=True)

# Get list of PNG files in directory
pngFiles = glob.glob(os.path.join(pngDir, "*.png"))


# Font used for all OpenCV fonts
FONT = cv2.FONT_HERSHEY_DUPLEX


# ...Folder path to use at a later date...   "face_recognition/images"
folderName = f"images"


stored_password = load_password_from_file()
if stored_password is not None:
    PASSWORD = stored_password
 

''' Function for fingerprint sensor '''
def get_fingerprint():
    mylcd.lcd_display_string("Please put finger", 2)
    mylcd.lcd_display_string("on sensor.", 3)
        
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while True:
        if GPIO.input(36) == False:
            keypadAccessRequested = True
            VerifiedPerson = False
            verifiedFace = False
            return False  # Exit the fingerprint verification function
        
        if finger.get_image() == adafruit_fingerprint.OK:
            break  # Fingerprint found, exit the loop
    
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True


# initialize LED color
led_color = 1
led_mode = 4

verifiedFace = False
VerifiedPerson = False
doorLocked = True
keypadAccessRequested = False


''' MAIN LOOP '''
while True:
    finger.set_led(mode = 4) # Reset fingerprint LED to be off in case it is on at the beginning of loop.

    # When motion is detected, it will start the facial recognition loop then the finger print scanner loop
    GPIO.output(37, False)
    
    PASSWORD, previous_timestamp = update_password_if_changed(PASSWORD, previous_timestamp)
    
    
    if GPIO.input(11) == GPIO.LOW and not VerifiedPerson:
        # Change this value to higher for final product
        trigger_alarm(15, 10)
    
    # If the server control button is pressed, unlock door, once door is closed, relocks door
    if GPIO.input(servo_control_button_pin) == GPIO.LOW and doorLocked == True:
        operate_door()
        
    if GPIO.input(13) == GPIO.HIGH and doorLocked == True: # Motion is detected
        print("Motion Detected")

        ''' Run through facial recognition class first. Once face is recognized, it will break out and move on to the fingerprint scanner loop '''
        if not VerifiedPerson and not verifiedFace:
            mylcd.lcd_clear()
            mylcd.lcd_display_string("  Motion Detected",1)
            mylcd.lcd_display_string("   Recording in", 3)
            mylcd.lcd_display_string("    process...", 4)
            
            # Run facial recognition program
            fr = FaceRecognition()
            status = fr.runRecognition() # Returns a "Verified" or "NoMotionDetected" status as well as the verified person's name
            GPIO.output(38, False) # Turn off white LED
            mylcd.lcd_clear()

            # If face is verified move onto fingerprint sensor
            if status and status[1] == "Verified":
                verifiedFace = True
                name = status[0]
            # If face is not verified, go back to detecting motion
            elif status == "NoMotionDetected":
                verifiedFace = False
            #
            elif status == "unverified" or status == "EnterPasscode":
                verifiedFace = False
                if check_password():
                    VerifiedPerson = True
                    name = "Keypad Entry"
                else:
                    VerifiedPerson = False
             
            elif status == "ServoControl":
                operate_door()
                    
        if GPIO.input(11) == GPIO.HIGH:  # Door open
            print("Door open")
            if not doorLocked:
                # Move the servo to the unlocked position and start a timer
                myServo.max()  # Turn servo to unlock position
                unlock_start_time = time.time()
                doorLocked = False
        else:
            # Door closed
            print("Door closed")
            if not doorLocked:
                # Check if the door has been unlocked for more than 10 seconds
                if time.time() - unlock_start_time >= 10:
                    # Relock the door
                    myServo.mid()  # Turn servo to relock position
                    GPIO.output(35, True)   # Turn on the red LED
                    GPIO.output(37, False)  # Turn off the green LED
                    doorLocked = True


        '''Once face is recognized, break out of the first loop and go through the second loop to verify finger print'''
        tries = 3
        while VerifiedPerson == False and verifiedFace == True:
                
            # Turn on LED for fingerprint sensor
            finger.set_led(color=3, mode=1)
            #print("----------------")

            if finger.read_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Fingerprint templates: ", finger.templates)
            if finger.count_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Number of templates found: ", finger.template_count)
            if finger.read_sysparam() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to get system parameters")

            if get_fingerprint():
                finger.set_led(color=led_color, mode=led_mode)
                finger.set_led(color = 2, mode = 3)
                print("Detected #", finger.finger_id, "with confidence", finger.confidence)
                mylcd.lcd_clear()
                mylcd.lcd_display_string("    Successfully ", 2)
                mylcd.lcd_display_string("     Verified!", 3)
                VerifiedPerson = True
                break

            # If finger not found in database, you have 3 tries to verify finger, or the loop will break
            else:
                print("Finger not found")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Invalid print.. ", 1)
                mylcd.lcd_display_string(f"Attempts left {tries - 1}", 2)
                tries -= 1
                finger.set_led(color = 1, mode = 3)
                time.sleep(1)
                mylcd.lcd_clear()
                print(f"Tries remaining: {tries}")
                if tries == 0:
                    mylcd.lcd_display_string("Fingerprint not ", 1)
                    mylcd.lcd_display_string("verified..", 2)
                    VerifiedPerson = False
                    verifiedFace = False
                    time.sleep(1)
                    mylcd.lcd_clear()
                    finger.set_led(mode = 4)
                    keypadAccessRequested = True
                    break
                    
        '''# Check if either magnetic contact switch is in contact with the other
        if GPIO.input(11) == GPIO.HIGH: # Door open
            print("Door closed")
            if doorLocked == False:
                moveServo(0) # Resets servo to original position
                time.sleep(1)
                doorLocked = True'''

    ''' If person is verified, go through the sequence of unlocking and relocking the door '''
    if VerifiedPerson == True:
        #finger.set_led(color = 2, mode = 3)
        time.sleep(1)
        finger.set_led(mode = 4)
        # Unlock the door
        myServo.max() # Turns servo 45 degrees to unlock door
        GPIO.output(35, False)
        GPIO.output(37, True)
        doorLocked = False
        time.sleep(2)
        print("Door Unlocked")
        mylcd.lcd_clear()
        
        # Signifies if the verification method was through user verification or keypad entry
        if name == 'Keypad Entry':
            print("Keypad Passcode Verified")
            mylcd.lcd_display_string("   Keypad Entry", 2)
            mylcd.lcd_display_string(f"     Accessed!", 3)
            text_to_speech = f"Keypad Entry Success!"
            speed_to_use = .9
            say_text(text_to_speech, speed=speed_to_use)
        else:   
            # Print if you were successful as well as greet the person who's name was verified
            print(f"Successfully verified! Welcome home {name}")
            mylcd.lcd_display_string("    Welcome home", 2)
            mylcd.lcd_display_string(f"      {name}!", 3)
            text_to_speech = f"Successfully verified! Welcome home {name}!"
            speed_to_use = .9
            say_text(text_to_speech, speed=speed_to_use)
        upload_verification_data(flask_app_url, name)
        
        VerifiedPerson = False
        verifiedFace = False
        verifiedPasscode = False
        # Give the person enough time to get into the door before it goes through the magnetic contact switch loop
        time.sleep(5) # <-- Increase this time at the end of project to about 15-20 seconds

        mylcd.lcd_clear()

        # Wait for door to close and magnetic contact switches to touch
        while GPIO.input(11) == GPIO.LOW: # LOW == Door opened | HIGH = Door closed
            print("Door open")
            time.sleep(0.1)

        # Relock the door after magnetic contact switches come back into contact
        doorLocked = True
        # Gives time for door to fully shut, before it relocks
        time.sleep(5) # <-- Increase this time at the end of project to about 15-20 seconds
        #### Possibly add if statement incase the user reopens the door after shutting it.. ####
        myServo.mid() # Turns servo motor 45 degrees to relock door
        time.sleep(2)
        GPIO.output(35, True)
        GPIO.output(37, False)
        print("Door has been locked!")
        tts_door_locked = "Door has been locked!"
        say_text(tts_door_locked, speed=speed_to_use)
        time.sleep(2)


    elif GPIO.input(36) == False or keypadAccessRequested == True:
        if check_password():
            VerifiedPerson = True
            keypadAccessRequested == False
            name = "Keypad Entry"
        else:
            VerifiedPerson = False
            keypadAccessRequested = False

    else:
        print("Motion Not Detected")
        time.sleep(0.1) # Wait a short period of time before checking for motion again

print("Program finished")
GPIO.cleanup()


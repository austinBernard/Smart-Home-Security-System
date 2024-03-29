import cv2
import face_recognition
import os, sys
import numpy as np
#import pyttsx3
import glob
import time
import serial
import adafruit_fingerprint
import RPi.GPIO as GPIO
from faceRecognition import FaceRecognition

# Passcode to unlock door without facial recognition or finger print verification
PASSCODE = "1234"

# Owner password to allow user to change password or to input a new user
OWNER_PASSCODE = "5678"

''' Setup magnetic contact switches '''
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.IN) # Pin 11
# GPIO.input(11) == GPIO.LOW:   (switch is CLOSED)
# GPIO.input(11) == GPIO.HIGH   (switch is OPEN)

# ''' Setup motion sensor '''
GPIO.setmode(GPIO.BOARD)
GPIO.setup(13, GPIO.IN) # Pin 13
# GPIO.input(13) == GPIO.HIGH (Motion is detected)

''' Setup servo motor '''
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(32, GPIO.OUT) # Pin 32

pwm = GPIO.PWM(32, 50) # GPIO12 (PWM), Frequency = 50Hz
#pwm.start(0)

def moveServo(angle):
    dutyCycle = angle / 18 + 2
    pwm.ChangeDutyCycle(dutyCycle)

''' Setting up fingerprint sensor '''
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
# # uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bt
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)


# Directory containing the PNG files   'face_recognition/faces'
pngDir = 'faces'


# Initialize text-to-speech engine
# engine = pyttsx3.init()


# Get list of PNG files in directory
pngFiles = glob.glob(os.path.join(pngDir, "*.png"))


# Font used for all OpenCV fonts
FONT = cv2.FONT_HERSHEY_DUPLEX


# ...Folder path to use at a later date...   "face_recognition/images"
folderName = f"images"


''' Functions for fingerprint scanner '''
def get_fingerprint():
    """Get a finger print image, template it, and see if it matches!"""
    print("Waiting for image...")
    while finger.get_image() != adafruit_fingerprint.OK:
        pass
    print("Templating...")
    if finger.image_2_tz(1) != adafruit_fingerprint.OK:
        return False
    print("Searching...")
    if finger.finger_search() != adafruit_fingerprint.OK:
        return False
    return True

def enroll_finger(location):
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
        else:
            print("Place same finger again...", end="")

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                return False
            else:
                print("Other error")
                return False

        print("Templating...", end="")
        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
            else:
                print("Other error")
            return False

        if fingerimg == 1:
            print("Remove finger")
            time.sleep(1)
            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
        else:
            print("Other error")
        return False

    print("Storing model #%d..." % location, end="")
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
        else:
            print("Other error")
        return False

    return True

def save_fingerprint_image(filename):
    """Scan fingerprint then save image to filename."""
    print("Place finger on sensor...", end="")
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")
            break
        if i == adafruit_fingerprint.NOFINGER:
            print(".", end="")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
            return False
        else:
            print("Other error")
            return False

    # let PIL take care of the image headers and file structure
    from PIL import Image  # pylint: disable=import-outside-toplevel

    img = Image.new("L", (192, 192), "white")
    pixeldata = img.load()
    mask = 0b00001111
    result = finger.get_fpdata(sensorbuffer="image")

    # this block "unpacks" the data received from the fingerprint
    #   module then copies the image data to the image placeholder "img"
    #   pixel by pixel.  please refer to section 4.2.1 of the manual for
    #   more details.  thanks to Bastian Raschke and Danylo Esterman.
    # pylint: disable=invalid-name
    x = 0
    # pylint: disable=invalid-name
    y = 0
    # pylint: disable=consider-using-enumerate
    for i in range(len(result)):
        pixeldata[x, y] = (int(result[i]) >> 4) * 17
        x += 1
        pixeldata[x, y] = (int(result[i]) & mask) * 17
        if x == 191:
            x = 0
            y += 1
        else:
            x += 1

    if not img.save(filename):
        return True
    return False

def get_num(max_number):
    """Use input() to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            i = int(input("Enter ID # from 0-{}: ".format(max_number - 1)))
        except ValueError:
            pass
    return i


# initialize LED color
led_color = 1
led_mode = 3

VerifiedPerson = False
doorLocked = True


''' MAIN LOOP '''
while True:

    # When motion is detected, it will start the facial recognition loop then the finger print scanner loop
    if GPIO.input(13) == GPIO.HIGH & doorLocked == True: # Motion is detected
        print("Motion Detected")

        ''' Run through facial recognition class first. Once face is recognized, it will break out and move on to the fingerprint scanner loop '''
        if not VerifiedPerson:
            fr = FaceRecognition()
            fr.runRecognition()
        #VerifiedPerson = True


        '''Once face is recognized, break out of the first loop and go through the second loop to verify finger print'''
        while VerifiedPerson == False:
            # Turn on LED for fingerprint sensor
            finger.set_led(color=led_color, mode=led_mode)
            print("----------------")

            if finger.read_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Fingerprint templates: ", finger.templates)
            if finger.count_templates() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to read templates")
            print("Number of templates found: ", finger.template_count)
            if finger.read_sysparam() != adafruit_fingerprint.OK:
                raise RuntimeError("Failed to get system parameters")

            print("e) enroll print")
            print("f) find print")
            print("d) delete print")
            print("s) save fingerprint image")
            print("r) reset library")
            print("l) set LED")
            print("q) quit")
            print("----------------")
            c = input("> ")

            if c == "l":
                c = input("color(r,b,p anything else=off)> ")
                led_mode = 3
                if c == "r":
                    led_color = 1
                elif c == "b":
                    led_color = 2
                elif c == "p":
                    led_color = 3
                else:
                    led_color = 1
                    led_mode = 4
            elif c == "e":
                enroll_finger(get_num(finger.library_size))
            elif c == "f":
                # breathing LED
                finger.set_led(color=3, mode=1)
                if get_fingerprint():
                    print("Detected #", finger.finger_id, "with confidence", finger.confidence)

                    VerifiedPerson = True

                    break
                else:
                    print("Finger not found")
            elif c == "d":
                if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
                    print("Deleted!")
                else:
                    print("Failed to delete")
            elif c == "s":
                if save_fingerprint_image("fingerprint.png"):
                    print("Fingerprint image saved")
                else:
                    print("Failed to save fingerprint image")
            elif c == "r":
                if finger.empty_library() == adafruit_fingerprint.OK:
                    print("Library empty!")
                else:
                    print("Failed to empty library")
            elif c == "q":
                print("Exiting fingerprint example program")
                # turn off LED
                finger.set_led(mode=4)
                raise SystemExit
            else:
                print("Invalid choice: Try again")

            # Check if either magnetic contact switch is in contact with the other
        if GPIO.input(11) == GPIO.HIGH: # Door closed
            print("Door closed")
            if doorLocked == False:
                moveServo(0) # Resets servo to original position
                time.sleep(1)
                doorLocked = True
                
    if VerifiedPerson == True:
        pwm.start(0)
        # Unlock the door
        moveServo(180) # Moves to 90 degrees
        doorLocked = False
        time.sleep(2)
        pwm.stop()


        # Print if you were successful
        print("Successfully verified!")
        #engine.say("Successfully verified! Welcome home!")
        #engine.runAndWait()
        #engine.stop()
        VerifiedPerson = False
        
        # Wait for door to close and magnetic contact switches to touch
        '''while GPIO.input(11) == GPIO.LOW: # HIGH == Door opened | LOW = Door closed
            print("Door open")
            time.sleep(0.1)'''

        # Relock the door
        pwm.start(0)
        moveServo(60) # Resets servo to lock door
        doorLocked = True
        time.sleep(2)
        pwm.stop()


    else:
        print("Motion Not Detected")
        time.sleep(0.1) # Wait a short period of time before checking for motion again

print("Program finished")
GPIO.cleanup()


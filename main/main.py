import cv2
import face_recognition
import os, sys
from os import system
import numpy as np
import pyttsx3
import glob
import time
import serial
import adafruit_fingerprint
import RPi.GPIO as GPIO
from gpiozero import Servo
from faceRecognition import FaceRecognition
import RPi_I2C_driver
import random

# Run pigpiod at the start of program
system("sudo pigpiod")

# Passcode to unlock door without facial recognition or finger print verification
PASSWORD = "1234"

# Owner password to allow user to change password or to input a new user
OWNER_PASSWORD = "5678"


''' Setup i2c LCD'''
GPIO.setmode(GPIO.BOARD)
mylcd = RPi_I2C_driver.lcd()

''' Setup button '''
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pin #36 GPIO 16


''' Setup GREEN and RED LED '''
GPIO.setup(35, GPIO.OUT) # Red LED
GPIO.setup(37, GPIO.OUT) # Green LED
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



'''while True:
    mylcd.lcd_clear()
    mylcd.lcd_display_string('{},{},{},{}'.format(scrambled_keys[(0, 0)], scrambled_keys[(0, 1)], scrambled_keys[(0, 2)], scrambled_keys[(0, 3)]), 1)
    mylcd.lcd_display_string('{},{},{},{}'.format(scrambled_keys[(1, 0)], scrambled_keys[(1, 1)], scrambled_keys[(1, 2)], scrambled_keys[(1, 3)]), 2)
    mylcd.lcd_display_string('{},{},{},{}'.format(scrambled_keys[(2, 0)], scrambled_keys[(2, 1)], scrambled_keys[(2, 2)], scrambled_keys[(2, 3)]), 3)
    mylcd.lcd_display_string('{},{},{},{}'.format(scrambled_keys[(3, 0)], scrambled_keys[(3, 1)], scrambled_keys[(3, 2)], scrambled_keys[(3, 3)]), 4)
    time.sleep(5)
    mylcd.lcd_clear()'''


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
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[10].id)

# Get list of PNG files in directory
pngFiles = glob.glob(os.path.join(pngDir, "*.png"))


# Font used for all OpenCV fonts
FONT = cv2.FONT_HERSHEY_DUPLEX


# ...Folder path to use at a later date...   "face_recognition/images"
folderName = f"images"




''' Setup Keypad '''
# Define the pins for the keypad rows and columns
ROWS = [33, 31, 29, 40] # [R1, R2, R3, R4]
COLS = [16, 18, 15, 19] # [C1, C2, C3, C4]

# Define the keypad matrix

keys = {
    (0, 0): '1', (0, 1): '2', (0, 2): '3', (0, 3): 'A',
    (1, 0): '4', (1, 1): '5', (1, 2): '6', (1, 3): 'B',
    (2, 0): '7', (2, 1): '8', (2, 2): '9', (2, 3): 'C',
    (3, 0): '*', (3, 1): '0', (3, 2): '#', (3, 3): 'D'
}

for col in COLS:
    GPIO.setup(col, GPIO.OUT)
    GPIO.output(col, GPIO.HIGH)
for row in ROWS:
    GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# Prompt the user to enter the password on the keypad
def enter_password():
    continuePass = True
    global PASSWORD  # Use the global variable for the password
    entered_password = ""
    # Define a randomly permuted version of the numbers 0-9
    scrambled_nums = random.sample(range(10), 10)

    # Define a dictionary that maps the scrambled keypad matrix indices to the corresponding scrambled numbers and characters
    scrambled_keys = {
        (0, 0): str(scrambled_nums[0]), (0, 1): str(scrambled_nums[1]), (0, 2): str(scrambled_nums[2]), (0, 3): 'A',
        (1, 0): str(scrambled_nums[3]), (1, 1): str(scrambled_nums[4]), (1, 2): str(scrambled_nums[5]), (1, 3): 'B',
        (2, 0): str(scrambled_nums[6]), (2, 1): str(scrambled_nums[7]), (2, 2): str(scrambled_nums[8]), (2, 3): 'C',
        (3, 0): '*', (3, 1): str(scrambled_nums[9]), (3, 2): '#', (3, 3): 'D'
    }

    mylcd.lcd_clear()
    #mylcd.lcd_display_string('{},{},{},{}-{},{},{},{}'.format(scrambled_keys[(0, 0)], scrambled_keys[(0, 1)], scrambled_keys[(0, 2)], scrambled_keys[(0, 3)],scrambled_keys[(1, 0)], scrambled_keys[(1, 1)], scrambled_keys[(1, 2)], scrambled_keys[(1, 3)]), 1)
    #mylcd.lcd_display_string('{},{},{},{}-{},{},{},{}'.format(scrambled_keys[(2, 0)], scrambled_keys[(2, 1)], scrambled_keys[(2, 2)], scrambled_keys[(2, 3)], scrambled_keys[(3, 0)], scrambled_keys[(3, 1)], scrambled_keys[(3, 2)], scrambled_keys[(3, 3)]), 2)

    mylcd.lcd_display_string(' {}   {}   {}  "*"'.format(scrambled_keys[(0, 0)], scrambled_keys[(0, 1)], scrambled_keys[(0, 2)]), 1)
    mylcd.lcd_display_string(' {}   {}   {}  to quit'.format(scrambled_keys[(1, 0)], scrambled_keys[(1, 1)], scrambled_keys[(1, 2)]), 2)
    mylcd.lcd_display_string(' {}   {}   {} '.format(scrambled_keys[(2, 0)], scrambled_keys[(2, 1)], scrambled_keys[(2, 2)]), 3)
    mylcd.lcd_display_string(f"     {scrambled_keys[(3, 1)]}     Pass:{entered_password}", 4)



    while len(entered_password) < len(PASSWORD) and continuePass:
        mylcd.lcd_display_string(' {}   {}   {}  "*"'.format(scrambled_keys[(0, 0)], scrambled_keys[(0, 1)], scrambled_keys[(0, 2)]), 1)
        mylcd.lcd_display_string(' {}   {}   {}  to quit'.format(scrambled_keys[(1, 0)], scrambled_keys[(1, 1)], scrambled_keys[(1, 2)]), 2)
        mylcd.lcd_display_string(' {}   {}   {} '.format(scrambled_keys[(2, 0)], scrambled_keys[(2, 1)], scrambled_keys[(2, 2)]), 3)
        mylcd.lcd_display_string(f"     {scrambled_keys[(3, 1)]}     Pass:{entered_password}", 4)
        for i, col in enumerate(COLS):
            GPIO.output(col, GPIO.LOW)
            for j, row in enumerate(ROWS):
                if not GPIO.input(row):
                    if keys[(j, i)] == "*":
                        continuePass = False
                        break
                    if scrambled_keys[(j, i)] == 'A':
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Enter the owners", 2)
                        mylcd.lcd_display_string("passcode.", 3)
                        time.sleep(1)
                        mylcd.lcd_clear()

                        mylcd.lcd_display_string(' {}   {}   {} '.format(scrambled_keys[(0, 0)], scrambled_keys[(0, 1)], scrambled_keys[(0, 2)]), 1)
                        mylcd.lcd_display_string(' {}   {}   {} '.format(scrambled_keys[(1, 0)], scrambled_keys[(1, 1)], scrambled_keys[(1, 2)]), 2)
                        mylcd.lcd_display_string(' {}   {}   {} '.format(scrambled_keys[(2, 0)], scrambled_keys[(2, 1)], scrambled_keys[(2, 2)]), 3)
                        mylcd.lcd_display_string(f"     {scrambled_keys[(3, 1)]}     Pass:{entered_password}", 4)

                        # Check if owner password is entered to allow password change
                        owner_password = ""
                        while len(owner_password) < len(OWNER_PASSWORD):
                            for i, col in enumerate(COLS):
                                GPIO.output(col, GPIO.LOW)
                                for j, row in enumerate(ROWS):
                                    if not GPIO.input(row):
                                        owner_password += scrambled_keys[(j, i)]
                                        print(f"Entered owner password: {owner_password}")
                                        mylcd.lcd_display_string(f"     {scrambled_keys[(3, 1)]}     Pass:{owner_password}", 4)
                                        time.sleep(0.2)
                                GPIO.output(col, GPIO.HIGH)
                            time.sleep(0.2)

                        if owner_password == OWNER_PASSWORD:

                            mylcd.lcd_clear()
                            mylcd.lcd_display_string("Select an option:", 1)
                            mylcd.lcd_display_string("A) enroll print", 2)
                            mylcd.lcd_display_string("B) delete print", 3)
                            mylcd.lcd_display_string("#) quit", 4)

                            print("Select an option\n")
                            print("A) enroll print")
                            print("B) find print")
                            print("C) delete print")
                            print("D) save fingerprint image")
                            print("5) reset library")
                            print("6) set LED")
                            print("#) quit")
                            print("----------------")
                            option_selected = ""
                            while not option_selected:
                                for i, col in enumerate(COLS):
                                    GPIO.output(col, GPIO.LOW)
                                    for j, row in enumerate(ROWS):
                                        if not GPIO.input(row):
                                            option_selected = scrambled_keys[(j, i)]
                                            print(f"Option selected: {option_selected}")
                                            time.sleep(0.2)
                                    GPIO.output(col, GPIO.HIGH)
                                time.sleep(0.2)

                            if option_selected == "A":
                                enroll_finger(get_num(finger.library_size))
                                break

                            elif option_selected == "#":
                                continuePass = False
                                break

                            elif option_selected == "B":
                                if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
                                    print("Deleted!")
                                    break
                                else:
                                    print("Failed to delete")

                            time.sleep(1)

                        else:
                            print("Incorrect owner password!")
                            time.sleep(2)

                    # If 'A' is not pressed, continue to enter in password to unlock door
                    else:

                        entered_password += scrambled_keys[(j, i)]
                        mylcd.lcd_display_string(f"     {scrambled_keys[(3, 1)]}     Pass:{entered_password}", 4)
                        print(f"Entered password: {entered_password}")
                        time.sleep(0.2)
            if not continuePass:
                return "breakFunction"


            GPIO.output(col, GPIO.HIGH)
        time.sleep(0.2)
    return entered_password


# Check if the entered password matches the defined password
def check_password():
    num_attempts = 3
    while num_attempts > 0:
        # Get the entered password from the user
        entered_password = enter_password()

        # Check if the entered password is correct
        if entered_password == PASSWORD:
            return True
        elif entered_password == "breakFunction":
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Exiting keypad.", 2)
            time.sleep(1.5)
            mylcd.lcd_clear()
            return False

        # Increment the number of attempts and prompt the user to try again
        num_attempts -= 1
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Incorrect password!", 1)
        mylcd.lcd_display_string("Please try again.", 2)
        mylcd.lcd_display_string(f"Attempts left: {num_attempts}", 4)
        time.sleep(2)

    # If the user fails to enter the correct password after 3 attempts, return False
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Too many attempts.", 2)
    mylcd.lcd_display_string("Access denied.", 3)
    time.sleep(2)
    mylcd.lcd_clear()
    return False



''' Functions for fingerprint scanner '''
def get_fingerprint():
    mylcd.lcd_display_string("Please put finger", 2)
    mylcd.lcd_display_string("on sensor.", 3)
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
    finger.set_led(color = 4, mode = 1)
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Place finger on ", 2)
            mylcd.lcd_display_string("sensor ", 3)
        else:
            print("Place same finger again...", end="")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Place same finger ", 2)
            mylcd.lcd_display_string("again...", 3)

        while True:
            i = finger.get_image()
            if i == adafruit_fingerprint.OK:
                print("Image taken")
                finger.set_led(color=2, mode=3)  # turn LED to blue to confirm first finger
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Image taken", 2)
                time.sleep(1)
                finger.set_led(color = 4, mode = 1)
                mylcd.lcd_clear()
                break
            if i == adafruit_fingerprint.NOFINGER:
                print(".", end="")
            elif i == adafruit_fingerprint.IMAGEFAIL:
                print("Imaging error")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Imaging error", 2)
                time.sleep(1)
                mylcd.lcd_clear()
                return False
            else:
                print("Other error")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Other error", 2)
                time.sleep(1)
                mylcd.lcd_clear()
                return False

        print("Templating...", end="")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Templating...", 1)

        i = finger.image_2_tz(fingerimg)
        if i == adafruit_fingerprint.OK:
            print("Templated")
            mylcd.lcd_display_string("Templated!", 3)
            time.sleep(1)
        else:
            if i == adafruit_fingerprint.IMAGEMESS:
                print("Image too messy")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Image too messy.", 2)
                time.sleep(1)
                mylcd.lcd_clear()
            elif i == adafruit_fingerprint.FEATUREFAIL:
                print("Could not identify features")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Could not identify", 2)
                mylcd.lcd_display_string("features.", 3)
                time.sleep(1)
                mylcd.lcd_clear()
            elif i == adafruit_fingerprint.INVALIDIMAGE:
                print("Image invalid")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Image invalid.", 2)
                time.sleep(1)
                mylcd.lcd_clear()
            else:
                print("Other error")
                mylcd.lcd_clear()
                mylcd.lcd_display_string("Other error.", 2)
                time.sleep(1)
                mylcd.lcd_clear()
            return False

        if fingerimg == 1:
            print("Remove finger")


            while i != adafruit_fingerprint.NOFINGER:
                i = finger.get_image()

    print("Creating model...", end="")
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Creating model...", 1)

    i = finger.create_model()
    if i == adafruit_fingerprint.OK:
        print("Created")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Created!", 3)
        time.sleep(1)
        mylcd.lcd_clear()
    else:
        if i == adafruit_fingerprint.ENROLLMISMATCH:
            print("Prints did not match")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Prints did not match", 2)
            time.sleep(1)
            mylcd.lcd_clear()
        else:
            print("Other error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Other error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
        return False

    print("Storing model #%d..." % location, end="")
    mylcd.lcd_clear()
    mylcd.lcd_display_string(f"Storing model #{location}...", 2)
    time.sleep(1)
    mylcd.lcd_clear()
    i = finger.store_model(location)
    if i == adafruit_fingerprint.OK:
        print("Stored")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("Stored!", 2)
        time.sleep(1)
        mylcd.lcd_clear()
        finger.set_led(mode = 4)
        return True
    else:
        if i == adafruit_fingerprint.BADLOCATION:
            print("Bad storage location")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Bad location", 2)
            time.sleep(1)
            mylcd.lcd_clear()
        elif i == adafruit_fingerprint.FLASHERR:
            print("Flash storage error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Flash error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
        else:
            print("Other error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Other error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
        return False

    return True

def save_fingerprint_image(filename):
    """Scan fingerprint then save image to filename."""
    print("Place finger on sensor...", end="")
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Place finger on", 2)
    mylcd.lcd_display_string("sensor...", 3)
    time.sleep(1)
    mylcd.lcd_clear()
    while True:
        i = finger.get_image()
        if i == adafruit_fingerprint.OK:
            print("Image taken")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Image taken", 2)
            time.sleep(1)
            mylcd.lcd_clear()
            break
        if i == adafruit_fingerprint.NOFINGER:
            print(".", end="")
        elif i == adafruit_fingerprint.IMAGEFAIL:
            print("Imaging error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Imaging error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
            return False
        else:
            print("Other error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Other error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
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

# define the keypad matrix
KEYPAD = [
    [1, 2, 3, "A"],
    [4, 5, 6, "B"],
    [7, 8, 9, "C"],
    ["*", 0, "#", "D"]
]

def get_key():
    """Reads the keypad and returns the pressed key."""
    for col_num, col_pin in enumerate(COLS):
        GPIO.output(col_pin, 0)
        for row_num, row_pin in enumerate(ROWS):
            if not GPIO.input(row_pin):
                time.sleep(0.2)
                GPIO.output(col_pin, 1)
                return KEYPAD[row_num][col_num]
        GPIO.output(col_pin, 1)
    return None


def get_num(max_number):
    """Use the keypad to get a valid number from 0 to the maximum size
    of the library. Retry till success!"""
    i = -1
    while (i > max_number - 1) or (i < 0):
        try:
            mylcd.lcd_clear()
            mylcd.lcd_display_string(f"ID # from 0-{max_number - 1}: ", 2)
            mylcd.lcd_display_string("Press '#' to comfirm", 4)
            key = None
            num_str = ""
            while key != "#":
                key = get_key()
                if key is not None and str(key).isdigit():
                    num_str += str(key)
                    mylcd.lcd_display_string(f"ID # from 0-{max_number - 1}:{num_str}", 2)
            i = int(num_str)
        except ValueError:
            pass
    return i


# initialize LED color
led_color = 1
led_mode = 4

verifiedFace = False
VerifiedPerson = False
doorLocked = True


''' MAIN LOOP '''
while True:
    finger.set_led(mode = 4) # Reset fingerprint LED to be off in case it is on at the beginning of loop.

    # When motion is detected, it will start the facial recognition loop then the finger print scanner loop
    GPIO.output(37, False)

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
                    name = "unverified user"
                else:
                    VerifiedPerson = False



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

        # Print if you were successful as well as greet the person who's name was verified
        print(f"Successfully verified! Welcome home {name}")
        mylcd.lcd_display_string("    Welcome home", 2)
        mylcd.lcd_display_string(f"      {name}!", 3)
        engine.say(f"Successfully verified! Welcome home {name}!")
        engine.runAndWait()

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
        engine.say("Door has been locked!")
        engine.runAndWait()
        engine.stop()
        time.sleep(2)


    elif GPIO.input(36) == False:
        if check_password():
            VerifiedPerson = True
            name = "unverified user"
        else:
            VerifiedPerson = False

    else:
        print("Motion Not Detected")
        time.sleep(0.1) # Wait a short period of time before checking for motion again

print("Program finished")
GPIO.cleanup()


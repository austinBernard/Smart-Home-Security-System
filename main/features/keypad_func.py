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
from password_manager import PASSWORD

# Passcode to unlock door without facial recognition or finger print verification
previous_timestamp = 0

# Owner password to allow user to change password or to input a new user
OWNER_PASSWORD = "5678"

''' Setup i2c LCD'''
GPIO.setmode(GPIO.BOARD)
mylcd = RPi_I2C_driver.lcd()

''' Setup button '''
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pin #36 GPIO 16

''' Setting up fingerprint sensor '''
# uart = busio.UART(board.TX, board.RX, baudrate=57600)

# If using with a computer such as Linux/RaspberryPi, Mac, Windows with USB/serial converter:
# # uart = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi and hardware UART:
uart = serial.Serial("/dev/serial0", baudrate=57600, timeout=1)

# If using with Linux/Raspberry Pi 3 with pi3-disable-bt
# uart = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1)

finger = adafruit_fingerprint.Adafruit_Fingerprint(uart)

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
    

def enroll_finger(location):
    finger.set_led(color = 4, mode = 1)
    """Take a 2 finger images and template it, then store in 'location'"""
    for fingerimg in range(1, 3):
        if fingerimg == 1:
            print("Place finger on sensor...", end="")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Place finger on ", 2)
            mylcd.lcd_display_string("sensor ", 3)
            mylcd.lcd_display_string("then remove", 4)
        else:
            print("Place same finger again...", end="")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Place same finger ", 2)
            mylcd.lcd_display_string("again...", 3)
            mylcd.lcd_display_string("then remove", 4)

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
            mylcd.lcd_display_string("Press '*' to quit", 1)
            mylcd.lcd_display_string("Or press 'A' to go", 3)
            mylcd.lcd_display_string("to owner settings.", 4)
        else:
            print("Other error")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Other error", 2)
            time.sleep(1)
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Press '*' to quit", 1)
            mylcd.lcd_display_string("Or press 'A' to go", 3)
            mylcd.lcd_display_string("to owner settings.", 4)
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
        mylcd.lcd_display_string("Press '*' to quit", 2)
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
                            mylcd.lcd_display_string("Select an option", 2)
                            time.sleep(1)
                            mylcd.lcd_clear()
                            mylcd.lcd_display_string("A) Enroll print", 1)
                            mylcd.lcd_display_string("B) Delete print", 2)
                            mylcd.lcd_display_string("C) Change Pass", 3)
                            mylcd.lcd_display_string("#) Quit", 4)

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
                            
                            elif option_selected == "C":
                                mylcd.lcd_clear()
                                mylcd.lcd_display_string("Enter new password:", 1)
                                new_password = enter_new_password(keys)
                                PASSWORD = new_password
                                save_password_to_file(new_password)
                                mylcd.lcd_clear()
                                mylcd.lcd_display_string("Press '*' to quit", 1)
                                mylcd.lcd_display_string("Or press 'A' to go", 3)
                                mylcd.lcd_display_string("to owner settings.", 4)
                                time.sleep(1)
                                break

                            elif option_selected == "B":
                                fingerprint_ids = finger.templates  # Read the templates
                                if fingerprint_ids:
                                    for template_id in fingerprint_ids:
                                        mylcd.lcd_clear()
                                        mylcd.lcd_display_string(f"ID: {template_id}", 2)
                                        time.sleep(2)
                                else:
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("No fingerprints found", 2)
                                    time.sleep(2)
                                if finger.delete_model(get_num(finger.library_size)) == adafruit_fingerprint.OK:
                                    print(finger.template_count)
                                    print(finger.templates)
                                    print("Deleted!")
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("Deleted Template!", 2)
                                    time.sleep(1)
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("Press '*' to quit", 1)
                                    mylcd.lcd_display_string("Or press 'A' to go", 3)
                                    mylcd.lcd_display_string("to owner settings.", 4)
                                    time.sleep(1)
                                    break
                                else:
                                    print("Failed to delete")
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("Failed to delete", 2)
                                    mylcd.lcd_display_string("Invalid number...", 3)
                                    time.sleep(2)
                                    mylcd.lcd_clear()

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


def enter_new_password(keys):
    new_password = ""
    while len(new_password) < len(PASSWORD):
        for i, col in enumerate(COLS):
            GPIO.output(col, GPIO.LOW)
            for j, row in enumerate(ROWS):
                if not GPIO.input(row):
                    if keys[(j, i)] == "*":
                        return None  # User canceled, return None
                    if keys[(j, i)] != 'A':
                        new_password += keys[(j, i)]
                        mylcd.lcd_display_string("New Password:", 3)
                        mylcd.lcd_display_string(f"Pass:{new_password}", 4)
                        time.sleep(0.2)
            GPIO.output(col, GPIO.HIGH)
        time.sleep(0.2)
    return new_password


# After changing the password, save it to a file
def save_password_to_file(password):
    with open("password.txt", "w") as file:
        file.write(password)

# Load password from the file at program startup
def load_password_from_file():
    try:
        with open("password.txt", "r") as file:
            return file.readline().strip()
    except FileNotFoundError:
        return None

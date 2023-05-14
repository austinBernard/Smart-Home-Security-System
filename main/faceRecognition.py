import cv2
import face_recognition
import os, sys
import numpy as np
import math
#import pyttsx3
import glob
import time
import datetime
import RPi.GPIO as GPIO
import boto3
import mysql.connector
from mysql.connector import Error
import pymysql
import base64


''' Setup button '''
GPIO.setmode(GPIO.BOARD)
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pin #36 GPIO 16


 #Directory containing the PNG files
pngDir = 'faces'

# Initialize text-to-speech engine
#engine = pyttsx3.init()

# Get list of PNG files in directory
pngFiles = glob.glob(os.path.join(pngDir, "*.png"))

# Font used for all OpenCV fonts
FONT = cv2.FONT_HERSHEY_DUPLEX

folderName=f"images"

''' Setup Keypad '''
# Define the pins for the keypad rows and columns
GPIO.setmode(GPIO.BOARD)
ROWS = [33, 31, 29, 40] # [R1, R2, R3, R4]
COLS = [16, 18, 15, 19] # [C1, C2, C3, C4]
GPIO.setwarnings(False)

# Define the keypad matrix
KEYS = [
    ['1', '2', '3', 'A'],
    ['4', '5', '6', 'B'],
    ['7', '8', '9', 'C'],
    ['*', '0', '#', 'D']
]

# Set up the row pins as outputs and the column pins as inputs
for i in range(4):
    GPIO.setup(ROWS[i], GPIO.OUT)
    GPIO.output(ROWS[i], GPIO.HIGH)

# Initialize column pins to input with pull-up resistors
for j in range(4):
    GPIO.setup(COLS[j], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        

class FaceRecognition:
    # Initialize some variables
    faceLocations = []
    faceEncodings = []
    faceNames = []
    knownFaceEncodings = []
    knownFaceNames = []
    
    processCurrentFrame = True
    
    def __init__(self):
        self.encodeFaces()
    
    # Function pulls all .png photos from 'faces' folder and print's the names of the .pngs
    def encodeFaces(self):
        for image in os.listdir('faces'):
            
            # Loads a picture from the 'faces' folder and learns how to recognize it
            faceImage = face_recognition.load_image_file(f'faces/{image}')
            faceEncoding = face_recognition.face_encodings(faceImage)[0]
            
            # Create arrays of known face encodings and their names
            self.knownFaceEncodings.append(faceEncoding)
            self.knownFaceNames.append(image)
            
    
    # Setup the full recognition function        
    def runRecognition(self):
        videoCapture = cv2.VideoCapture(0)
        
        verifiedFace = False
        unverifiedFace = False
        lastMotionTime = time.time()
        unknownFaceStored = False
        lastSavedTime = time.time()
        
        if not videoCapture.isOpened():
            sys.exit('Webcam not found.')
            
        # Unknown person photo counter
        #count = 0
            
        while True:
            
            ret, frame = videoCapture.read()
            
            # Only process every other frame of video to save time
            if self.processCurrentFrame:
                
                # Resize the frame of video to 1/4 size for faster face recognition
                smallFrame = cv2.resize(frame, (0, 0), fx = 0.25, fy = 0.25)
                #rgbSmallFrame = smallFrame[:, :, ::-1]
                rgbSmallFrame = cv2.cvtColor(smallFrame, cv2.COLOR_BGR2RGB)
                
                # Find all the faces and face encodings in the current frame of video
                self.faceLocations = face_recognition.face_locations(rgbSmallFrame)
                self.faceEncodings = face_recognition.face_encodings(rgbSmallFrame, self.faceLocations)
                
                self.faceNames = []
                for faceEncoding in self.faceEncodings:
                    
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(self.knownFaceEncodings, faceEncoding)
                    name = 'Unknown'
                    #confidence = 'Unknown'
                    
                     # Calculate the shortest distance to face
                    faceDistances = face_recognition.face_distance(self.knownFaceEncodings, faceEncoding)
                    bestMatchIndex = np.argmin(faceDistances)
                    
                    if matches[bestMatchIndex]:
                        name = self.knownFaceNames[bestMatchIndex]
                        #confidence = faceConfidence(faceDistances[bestMatchIndex])
                        
                    self.faceNames.append(f'{name}')
                    
                    # For the database to store the photo into.
                    if name == "Unknown" and not unknownFaceStored:
                        
                        # Setup the current time of day
                        now = datetime.datetime.now()

                        # Format the date and time to include in the filename
                        dateTime = now.strftime("%m-%d-%Y__%H:%M:%S")
                        currentTime = time.time()
                        
                        if currentTime - lastSavedTime >= 3:
                            lastMotionTime = currentTime
                            lastSavedTime = currentTime
                            _, encoded_image = cv2.imencode('.png', frame)
                            image_data = encoded_image.tobytes()
                            encoded_image_data = base64.b64encode(image_data)
                            #upload_image_to_database(encoded_image_data, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
                            
                            #unverifiedFace = True # If face is unknown, set the flag to True
                            
                            
     
                    # Reads through all .png files in the faces folder
                    for pngFile in pngFiles:
                        if name in pngFile and not verifiedFace:
                            # Gets the filename without the extension (.png)
                            name = os.path.splitext(os.path.basename(pngFile))[0]
                            
                            # Sets the verifiedFace to true, so that it only does "Welcome home" once
                            verifiedFace = True
                                

            # If person is recognized, break out of while loop
            if verifiedFace == True:
                videoCapture.release()
                cv2.destroyAllWindows()
                # Return the name of the person who was verified
                return (name, "Verified")
                
            # If not motion is detected after 15 seconds, break
            elif time.time() - lastMotionTime > 15:
                videoCapture.release()
                cv2.destroyAllWindows()
                return "NoMotionDetected"
            
            # When an unverified face is detected, take photo, and break while loop
            elif unverifiedFace == True:
                videoCapture.release()
                cv2.destroyAllWindows()
                return "unverified"
            
            # If button is pressed, break out of facial recognition
            elif GPIO.input(36) == False:
                videoCapture.release()
                cv2.destroyAllWindows()
                return "EnterPasscode"
                    
                    
                    
            self.processCurrentFrame = not self.processCurrentFrame
            
            # Display annontations
            for(top, right, bottom, left), name in zip(self.faceLocations, self.faceNames):
                
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Create the frame with the name
                cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (255, 0, 0), -1)
                cv2.putText(frame, name, (left + 6, bottom - 6), FONT, 0.9, (255, 255, 255), 1)
                
                        
            # Display the resulting image
            cv2.imshow('Face Recognition', frame)
            
            # 'q' on keyboard exited the screen
            if cv2.waitKey(1) == ord('q'):
                break
            
            
        # Release the video capture and close OpenCV window
        videoCapture.release()
        cv2.destroyAllWindows()
                
            
if __name__ == '__main__':
    fr = FaceRecognition()
    fr.runRecognition()

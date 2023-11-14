import cv2
import face_recognition
import os, sys
import numpy as np
import math
import glob
import time
from datetime import datetime
import RPi.GPIO as GPIO
import boto3
import mysql.connector
from mysql.connector import Error
import pymysql
import base64
import pickle
import hashlib
from features.alert_sender import send_email
from google.cloud import storage

'''' Setup GCP service account credentials for uploading to GCS '''
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ""

''' Setup button '''
GPIO.setmode(GPIO.BOARD)
GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP) # pin #36 GPIO 16

GPIO.setup(38, GPIO.OUT) # WHITE NIGHTIME LED

''' Third button that will unlock the door, allowing the user to leave from the inside '''
servo_control_button_pin = 23
GPIO.setup(servo_control_button_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP)

 #Directory containing the PNG files
pngDir = 'faces'

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

def upload_image_to_database(encoded_image_data, date, time):
    # Connect to MariaDB
    connection = pymysql.connect(
        host='',
        user='',
        password='',
        database=''
    )
    try:
        with connection.cursor() as cursor:
            # Insert the image data, date, and time into the database
            sql = "INSERT INTO unrecognized_faces (picture, date, time) VALUES (%s, %s, %s)"
            cursor.execute(sql, (encoded_image_data, date, time))

        connection.commit()
    finally:
        connection.close()

def upload_image_to_gcs(image_data, date, time):
    client = storage.Client()

    bucket_name = ''

    # Define the path within the bucket where you want to store the images
    blob_name = f'unrecognized_faces.{date}.{time}.png'

    # Create a bucket object
    bucket = client.get_bucket(bucket_name)

    # Create a Blob object and upload the image data
    blob = bucket.blob(blob_name)
    blob.upload_from_string(image_data, content_type='image/png')

''' Function to determine if it's nighttime to trigger LED to come on for facial recognition light '''
def is_nighttime():
    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 17, 0)  # 5 PM
    end_time = datetime(now.year, now.month, now.day, 8, 0)   # 8 AM

    return start_time <= now or now <= end_time  

class FaceRecognition:
    # Initialize some variables
    faceLocations = []
    faceEncodings = []
    faceNames = []
    knownFaceEncodings = []
    knownFaceNames = []
    
    processCurrentFrame = True
    video_filename = None
    
    def __init__(self):
        self.encodeFaces()
        self.video_writer = None
        #self.recording_start_time = None
        
    # Function to capture a screenshot using OpenCV
    def capture_screenshot():
        cap = cv2.VideoCapture(0)

        # Capture a single frame from the camera
        ret, frame = cap.read()

        # Release the camera
        cap.release()

        return frame
    
    def encodeFaces(self):
        cache_filename = 'face_encodings_cache.pkl'
        count_filename = 'image_count.txt'

        # Read the current count from the text file
        current_count = self.read_image_count(count_filename)

        if os.path.exists(cache_filename):
            with open(cache_filename, 'rb') as file:
                cached_data = pickle.load(file)
                cached_timestamp = cached_data.get('timestamp')
                cached_encodings, cached_names = cached_data.get('encodings'), cached_data.get('names')

            # Check if the image count has changed since the last caching
            current_images = set(os.listdir('faces'))
            if cached_timestamp and current_count != len(current_images):
                self.recache_encodings(cache_filename, count_filename, len(current_images))
            else:
                self.knownFaceEncodings, self.knownFaceNames = cached_encodings, cached_names
        else:
            self.recache_encodings(cache_filename, count_filename, current_count)

    def recache_encodings(self, cache_filename, count_filename, image_count):
        self.knownFaceEncodings, self.knownFaceNames = [], []
        for image in os.listdir('faces'):
            try:
                # Loads a picture from the 'faces' folder and learns how to recognize it
                faceImage = face_recognition.load_image_file(f'faces/{image}')
                faceEncoding = face_recognition.face_encodings(faceImage)[0]

                # Create arrays of known face encodings and their names
                self.knownFaceEncodings.append(faceEncoding)
                self.knownFaceNames.append(image)
            except Exception as e:
                print(f"Error processing image {image}: {str(e)}")

        # Save face encodings, timestamp, and current images to cache
        with open(cache_filename, 'wb') as file:
            pickle.dump(
                {'encodings': self.knownFaceEncodings,
                 'names': self.knownFaceNames,
                 'timestamp': datetime.now().timestamp()},
                file
            )

        # Update the image count in the text file
        self.write_image_count(count_filename, image_count)

    def read_image_count(self, count_filename):
        try:
            with open(count_filename, 'r') as file:
                return int(file.read().strip())
        except FileNotFoundError:
            return 0

    def write_image_count(self, count_filename, image_count):
        with open(count_filename, 'w') as file:
            file.write(str(image_count))
    
    '''
    # Function pulls all .png photos from 'faces' folder and print's the names of the .pngs
    def encodeFaces(self):
        if os.path.exists('face_encodings_cache.pkl'):
            with open('face_encodings_cache.pkl', 'rb') as file:
                self.knownFaceEncodings, self.knownFaceNames = pickle.load(file)
        else:
            for image in os.listdir('faces'):
                try:
                    # Loads a picture from the 'faces' folder and learns how to recognize it
                    faceImage = face_recognition.load_image_file(f'faces/{image}')
                    faceEncoding = face_recognition.face_encodings(faceImage)[0]

                    # Create arrays of known face encodings and their names
                    self.knownFaceEncodings.append(faceEncoding)
                    self.knownFaceNames.append(image)
                except Exception as e:
                    print(f"Error processing image {image}: {str(e)}")

            # Save face encodings to cache
            with open('face_encodings_cache.pkl', 'wb') as file:
                pickle.dump((self.knownFaceEncodings, self.knownFaceNames), file)
            ''''''
    def encodeFaces(self):
        for image in os.listdir('faces'):
            try:
                # Loads a picture from the 'faces' folder and learns how to recognize it
                faceImage = face_recognition.load_image_file(f'faces/{image}')
                faceEncoding = face_recognition.face_encodings(faceImage)[0]

                # Create arrays of known face encodings and their names
                self.knownFaceEncodings.append(faceEncoding)
                self.knownFaceNames.append(image)
            except Exception as e:
                print(f"Error processing image {image}: {str(e)}")
                badImagePath = os.path.join('faces', image)
                os.remove(badImagePath)
                print(f"Deleted bad image: {badImagePath}")
            '''
    # Setup the full recognition function        
    def runRecognition(self):
        videoCapture = cv2.VideoCapture(0)
        
        verifiedFace = False
        unverifiedFace = False
        lastMotionTime = time.time()
        unknownFaceStored = False
        lastSavedTime = time.time()
        #record_start_time = None
        
        
        if not videoCapture.isOpened():
            sys.exit('Webcam not found.')
            
        # Unknown person photo counter
        #count = 0
                            
        while True:
            if is_nighttime(): # If it's nighttime (between the hours of 5pm and 8am) turn on WHITE led
                GPIO.output(38, True)
                
            ret, frame = videoCapture.read()

            if self.processCurrentFrame:
                smallFrame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgbSmallFrame = cv2.cvtColor(smallFrame, cv2.COLOR_BGR2RGB)

                try:
                    self.faceLocations = face_recognition.face_locations(rgbSmallFrame)
                    self.faceEncodings = face_recognition.face_encodings(rgbSmallFrame, self.faceLocations)
                except Exception as e:
                    print(f"Error detecting faces: {str(e)}")
                    continue

                self.faceNames = []
                for faceEncoding in self.faceEncodings:
                    try:
                        matches = face_recognition.compare_faces(self.knownFaceEncodings, faceEncoding)
                        name = 'Unknown'
                        faceDistances = face_recognition.face_distance(self.knownFaceEncodings, faceEncoding)
                        bestMatchIndex = np.argmin(faceDistances)
                        if matches[bestMatchIndex]:
                            name = self.knownFaceNames[bestMatchIndex]
                        self.faceNames.append(f'{name}')

                        if name == "Unknown" and not unknownFaceStored:
                            now = datetime.now()
                            dateTime = now.strftime("%m-%d-%Y | %H:%M:%S")
                            currentTime = time.time()

                            if currentTime - lastSavedTime >= 4:
                                lastMotionTime = currentTime
                                lastSavedTime = currentTime
                                
                                _, encoded_image = cv2.imencode('.png', frame)
                                image_data = encoded_image.tobytes()
                                encoded_image_data = base64.b64encode(image_data)
                                
                                upload_image_to_gcs(image_data, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
                                upload_image_to_database(encoded_image_data, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
                                email_subject = "Unverified person detected!"
                                email_message = f"Unidentified face detected at {dateTime}"
                                email_message += f"\nENTER IN WEBSITE LINK TO UNDECTED FACES HERE"
                                send_email(email_subject, email_message, 'seniorprojects37@gmail.com')

                        for pngFile in pngFiles:
                            if name in pngFile and not verifiedFace:
                                name = os.path.splitext(os.path.basename(pngFile))[0]
                                verifiedFace = True
                    except Exception as e:
                        print(f"Error processing face: {str(e)}")
            '''
            # Record a 2-second video when motion is detected
            if record_start_time is None:
                record_start_time = time.time()

            if time.time() - record_start_time <= 2:
                if self.video_filename is None:
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')
                    now = datetime.now()
                    date = now.strftime("%Y-%m-%d")
                    time_str = now.strftime("%H-%M-%S")
                    self.video_filename = f"video_{date}_{time_str}.avi"
                    out = cv2.VideoWriter(self.video_filename, fourcc, 20.0, (640, 480))
                if ret:
                    out.write(frame)
            elif self.video_filename:
                out.release()
                # Upload the video to GCS
                client = storage.Client()
                bucket_name = 'md-videos'
                blob_name = f'{self.video_filename}'
                bucket = client.get_bucket(bucket_name)
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(self.video_filename)
                os.remove(self.video_filename)
                self.video_filename = None
            '''
            
            # If person is recognized, break out of while loop
            if verifiedFace == True:
                videoCapture.release()
                cv2.destroyAllWindows()
                # Return the name of the person who was verified
                return (name, "Verified")
                
            # If not motion is detected after 8 seconds, break
            elif time.time() - lastMotionTime > 8:
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
            
            # If servo control button is pressed, break out of facial recognition loop
            elif GPIO.input(servo_control_button_pin) == False:
                videoCapture.release()
                cv2.destroyAllWindows()
                return "ServoControl"
                 
                    
                    
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

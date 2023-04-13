import cv2
import face_recognition
import os, sys
import numpy as np
import math
#import pyttsx3
import glob
import time

# Directory containing the PNG files
pngDir = 'faces'

# Initialize text-to-speech engine
#engine = pyttsx3.init()

# Get list of PNG files in directory
pngFiles = glob.glob(os.path.join(pngDir, "*.png"))

# Font used for all OpenCV fonts
FONT = cv2.FONT_HERSHEY_DUPLEX

folderName = f"images"
  

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
        lastMotionTime = time.time()
        unknownFaceStored = False
        
        if not videoCapture.isOpened():
            sys.exit('Webcam not found.')
            
        # Unknown person photo counter
        count = 0
            
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
                        filename = os.path.join(folderName, f"{name}{count}.png")
                        
                        cv2.imwrite(filename, frame)
                        count += 1
                        if count == 5:
                            unknownFaceStored = True
                            

     
                    # Reads through all .png files in the faces folder
                    for pngFile in pngFiles:
                        if name in pngFile and not verifiedFace:
                            # Gets the filename without the extension (.png)
                            name = os.path.splitext(os.path.basename(pngFile))[0]
                            
                            # Welcome message that will say the person's name of who is recognized
                            #engine.say(f"Welcome home {name}")
                            #engine.runAndWait()
                            #engine.stop()
                            
                            # Sets the welcomeMessage to true, so that it only does "Welcome home" once
                            verifiedFace = True
                                

            # If person is recognized, break out of while loop
            if verifiedFace == True:
                print("face verified")
                break
            elif time.time() - lastMotionTime > 15:
                print("No motion detected")
                break

                    
                    
                    
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

import cv2
import os
import numpy as np
import time
#import RPi.GPIO as GPIO

"""
    Set up the Servo motor.
    &GPIO PIN& is where you place the actual pin #

"""
# servoPin = *GPIO PIN*
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(servoPin, GPIO.OUT)
# pwm = GPIO.PWM(servoPin, 50)
# pwm.start(0)


# Load the Haar Casecade Classifier for face detection
faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Setup the recognizer and train it with images in the dataset folder (ReplaceWithName)
recognizer = cv2.face.LBPHFaceRecognizer_create()
currentID = 0
labelIDs = {}
yLabels = []
xTrain = []

# Loop through the images in the dataset folder (ReplaceWithName).
for root, dirs, files in os.walk("FacialRecognition/ReplaceWithName"):
    for file in files:
        if file.endswith("jpg") or file.endswith("png"):
            path = os.path.join(root, file)
            label = os.path.basename(root).replace(" ", "-").lower()
            
            # Add a label ID for the current person
            if label not in labelIDs:
                labelIDs[label] = currentID
                currentID += 1
            id = labelIDs[label]
            
            # Load and resize the image
            pilImage = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            size = (550, 550)
            finalImage = cv2.resize(pilImage, size)
            
            # Add the image and label to the training data
            xTrain.append(finalImage)
            yLabels.append(id)
     
# Train the recognizer with the training data       
recognizer.train(xTrain, np.array(yLabels))

# Setting up the camera
camera = cv2.VideoCapture(0)
camera.set(3, 640) # Set video width
camera.set(4, 480) # Set video height

# Main loop to capture video from the camera and to detect faces.
while True:
    # Capture a frame from the camera
    rest, frame = camera.read()
    
    # Conver the frame to grayscale to find faces easier
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect faces in the frame
    faces = faceCascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)
    
    # Loop through the detected faces
    for (x, y, w, h) in faces:
        # Draw a rectangle around the detected face
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Crop the face from the frame
        face = gray[y:y + h, x:x + w]
        
        
        # Facial recognition to display your name if your face is verified. 
        # Will also turn servo motor to unlock door.
        id, confidence = recognizer.predict(face)
        if confidence < 100:
            # Get the name of the person based on the label ID
            for name, label in labelIDs.items():
                if label == id:
                    name = name.capitalize()
                    
                    # Display the name of the person above the detected face.
                    cv2.putText(frame, name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        
        
                    # For SERVO MOTOR (Testing)
                    
                    # if name == "Austin":
                    #     pwm.ChangeDutyCycle(2.5) # Rotates servo to 0 degrees
                    #     time.sleep(2)
                    #     pwm.ChangeDutyCycle(7.5) # Rotates servo to 90 degrees
                    #     time.sleep(2)
                    
                    
    # Displays the video feed with Face Recognition    
    cv2.imshow('Face Recognition', frame)
    
    # If 'q' is pressed, it will exit the loop
    if cv2.waitKey(20) & 0xFF == ord('q'):
        break
    
    
camera.release()
cv2.destroyAllWindows()
#GPIO.cleanup()
        
        
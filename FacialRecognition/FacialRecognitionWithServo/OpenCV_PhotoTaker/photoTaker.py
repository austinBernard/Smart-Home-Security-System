import cv2
import os

# Set up the camera
camera = cv2.VideoCapture(0)
camera.set(3, 640) # Set video width
camera.set(4, 480) # Set video height

# Creates the folder to store the photos
folderName = "FacialRecognition/ReplaceWithName"
if not os.path.exists(folderName):
    os.makedirs(folderName)

# Set the photo index to start at 0
photoIndex = 0

# Loop to capture photos from the camera
while True:
    # Capture a frame from the camera
    ret, frame = camera.read()
    
    # Display the video feed
    cv2.imshow('Video Feed', frame)
    
    # Wait for a key to be pressed
    key = cv2.waitKey(1) & 0xFF
    
    # If key = 'q', break the loop and quit program
    if key == ord('q'):
        break
    
    # If key = 's', take a photo and store that photo in the (ReplaceWithName) folder
    if key == ord('s'):
        # Construct the filename for the photo
        filename = os.path.join(folderName, f"photo_{photoIndex}.jpg")
        
        # Save the photo to the file
        cv2.imwrite(filename, frame)
        
        # Increment the photo index
        photoIndex += 1
        
camera.release()
cv2.destroyAllWindows()
import cv2
import os

# Will ask you for your name, which will be the path to where the photos will be stored.
name = input("What is your name? This name will be the name of the photo: ")
print("Loading... please wait")

# Set up the camera
camera = cv2.VideoCapture(0)
camera.set(3, 640) # Set video width
camera.set(4, 480) # Set video height

# Creates the folder to store the photos
folderName = f"faces"
if not os.path.exists(folderName):
    os.makedirs(folderName)

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
        filename = os.path.join(folderName, f"{name}.png")
        
        # Save the photo to the file
        cv2.imwrite(filename, frame)
        break
        
camera.release()
cv2.destroyAllWindows()

print("Picture was successfully taken and stored in the 'faces' folder.")

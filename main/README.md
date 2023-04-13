# How to Install:

    pip install CMake
    pip install face_recognition
If you get an error relating to "You do not have CMake installed" you will need to follow this <a href="https://www.geeksforgeeks.org/how-to-install-face-recognition-in-python-on-windows/" target="_blank"> link </a> to be able to properly install cmake. 
If doing this still does not work then do the following commands to insure you have everything uninstalled:

    pip uninstall CMake
    pip uninstall face_recognition

Once everything is uninstalled, you will need to download <a href="https://visualstudio.microsoft.com/downloads/" target="_blank"> Visual Studio</a> and make sure you install the "Desktop Development with C++" 

![image](https://user-images.githubusercontent.com/109118567/231017071-4715b222-baa8-499c-a3c2-d3f9a3d96760.png)

Once you have that installed proceed to the steps in the beginining by pip installing CMake, then face_recognition. Now you should have the face_recognition library installed on windows.

# Quick walkthrough

Firstly, open the photoTaker folder and run the photoTaker.py file.
It will ask you to enter the name of the user. 
Type in the name, then an OpenCV window should open using your computers webcam.
Next, you will position your face facing the direction of the camera, while being around 1-2 feet away, then you will press 's' on your keyboard.
This will take the photo and store it in the 'faces' folder.

The next step is to open the main.py file, and run the file.
The facial recognition will train and model your face from that one image.
Another OpenCV window will open and now this time, it will detect your face live and also play a message saying "Welcome home {user}"



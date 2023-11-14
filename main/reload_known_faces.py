import cv2
import face_recognition
import os, sys
import numpy as np
import math
import glob
import time
import datetime
import RPi.GPIO as GPIO

def reload_known_faces():
	global knownFaceEncodings, knownFaceNames

	knownFaceEncodings = []
	knownFaceNames = []

	for image in os.listdir('faces'):
		faceImage = face_recognition.load_image_file(f'faces/{image}')
		faceEncoding = face_recognition.face_encodings(faceImage)[0]

		knownFaceEncodings.append(faceEncoding)
		knownFaceNames.append(image)

	print("Known faces reloaded.")

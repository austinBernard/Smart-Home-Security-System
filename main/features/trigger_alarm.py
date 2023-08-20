import pygame
import time

# Init pygame for alarm sound
pygame.mixer.init()
ALARM_SOUND_PATH = "psycho-sound-11797.mp3"

''' Function for triggering the alarm '''
def trigger_alarm(duration):
    # Function to trigger the alarm when the contact switches are broken
    print("ALARM: Contact switches broken!")
    pygame.mixer.music.load(ALARM_SOUND_PATH)
    pygame.mixer.music.play()

    time.sleep(duration)  # Play the alarm sound for the specified duration

    pygame.mixer.music.stop() 

import pygame
import time
from datetime import datetime 
from features.alert_sender import send_email

# Init pygame for alarm sound
pygame.mixer.init()
ALARM_SOUND_PATH = "psycho-sound-11797.mp3"

last_alert_time = 0

''' Function for triggering the alarm '''
def trigger_alarm(duration, alert_message_duration):
    global last_alert_time
    current_datetime = datetime.now().strftime('%Y-%m-%d | %H:%M:%S')
    
    ''' If statement to decide if enough time has passed in order to send another notification 
        so that the user is now being spamed '''
    # Get the current time
    current_time = time.time()

    # Check if enough time has passed since the last alert
    if (current_time - last_alert_time) >= alert_message_duration:  # Adjust the interval as needed (e.g., 30 seconds)
        # Send emails
        email_subject = 'Security Alert: UNAUTHORIZED PERSON'
        email_message = f'Alarm triggered at {current_datetime}'
        send_email(email_subject, email_message, '8323151016@txt.att.net') # Insert in phone number as 1234567890@txt.att.net if you have at&t as your phone provider
        send_email(email_subject, email_message, 'seniorprojects37@gmail.com') # The email in which you want the alerts sent to

        # Update the last alert time
        last_alert_time = current_time
    
    # Function to trigger the alarm when the contact switches are broken
    print("ALARM: Contact switches broken!")
    pygame.mixer.music.load(ALARM_SOUND_PATH)
    pygame.mixer.music.play(-1)

    time.sleep(duration)  # Play the alarm sound for the specified duration

    pygame.mixer.music.stop()
    

import smtplib
from email.message import EmailMessage

def send_email(subject, body, to_email):
    # Email server details
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to_email
    
    user = "seniorprojects37@gmail.com"
    msg['from'] = user
    password = "ywuzwptxjodicosq"
    
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)
    
    server.quit()

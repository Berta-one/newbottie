
import smtplib
from email.mime.text import MIMEText

def send_daily_report(to_email, content):
    msg = MIMEText(content)
    msg['Subject'] = 'Daily Trading Bot Report'
    msg['From'] = 'your_email@gmail.com'
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login('your_email@gmail.com', 'your_app_password')
        server.send_message(msg)

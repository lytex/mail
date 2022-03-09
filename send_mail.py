#!/usr/bin/python3

import base64
import datetime as dt
import os
import os.path
import subprocess
from email.mime.text import MIMEText
from time import sleep

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

GOOGLE_TOKEN = os.getenv("GOOGLE_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
TEMPLATE_PATH = os.getenv("TEMPLATE_PATH")
SUBJECT = os.getenv("SUBJECT")
RECIPIENTS = os.getenv("RECIPIENTS")
SENDER = os.getenv("SENDER")
COOLDOWN_FILE = os.getenv("COOLDOWN_FILE")
COOLDOWN_SECS = os.getenv("COOLDOWN_SECS")

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main():

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(GOOGLE_TOKEN):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(GOOGLE_TOKEN, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)

    # Do not send if a mail was sent COOLDOWN_SECS seconds before
    if COOLDOWN_FILE is not None:
        now = dt.datetime.now()
        try:
            with open(COOLDOWN_FILE, "r") as f:
                then = dt.datetime.strptime(f.read().strip("\r\n"), "%d-%m-%Y %H:%M:%S")
            if (now - then).total_seconds() > int(COOLDOWN_SECS):
                print("Cooldown period expired, sending mail...")
                with open(COOLDOWN_FILE, "w+") as f:
                    f.write(dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
                sended = False
            else:
                print(f"Cooldown period ongoing, not sending mail until {COOLDOWN_SECS} secs have passed")
                sended = True
        except FileNotFoundError:
            with open(COOLDOWN_FILE, "w+") as f:
                f.write(dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
                sended = False
    else:
        sended = False
    while not sended:
        if os.system("ping -c 4 gmail.com") == 0:
            send_time = dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            uptime = subprocess.run("uptime", stdout=subprocess.PIPE).stdout.decode("utf-8")
            with open(TEMPLATE_PATH) as template:
                msg = template.read().format(send_time=send_time, uptime=uptime)

            message = create_message(
                SENDER,
                RECIPIENTS,
                SUBJECT,
                msg,
            )
            send_message(service, "me", message)
            sended = True
        else:
            sleep(60)


def gather_reporting_info():
    """gather some information about the current state and put it into a dictionary

    Returns:
        dict: a dictionary with the following values:
            send_time: local time now as per the datetime module
            uptime: result of running the uptime command (https://man7.org/linux/man-pages/man1/uptime.1.html):
                The current time, how long the system has been running, how many
                users are currently logged on, and the system load averages for
                the past 1, 5, and 15 minutes.
    """

    send_time = dt.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    uptime = subprocess.run("uptime", stdout=subprocess.PIPE).stdout.decode("utf-8")
    return {
        "send_time": send_time,
        "uptime": uptime,
    }


def create_message(sender, to, subject, message_text):
    """Create a message for an email.

    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.

    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject
    message["Content-Type"] = "text/html; charset=utf-8"
    test = {"raw": base64.urlsafe_b64encode(message.as_string().encode("utf-8")).decode("utf-8")}
    print("Sending message:")
    print(message.as_string())
    return test


def send_message(service, user_id, message):
    """Send an email message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      message: Message to be sent.

    Returns:
      Sent Message.
    """
    try:

        message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message Id: {message['id']}")
        return message
    except Exception as error:
        print(f"An error occurred: {error}")
        return None


if __name__ == "__main__":
    main()

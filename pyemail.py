import smtpd
import asyncore
import os
from email import policy
from email.parser import BytesParser
import uuid

class CustomSMTPServer(smtpd.SMTPServer):
    def process_message(self, peer, mailfrom, rcpttos, data, **kwargs):
        # Parse email
        msg = BytesParser(policy=policy.default).parsebytes(data)

        # Generate a random UUID for the filename
        file_uuid = uuid.uuid4().hex

        # Create a directory to store email payloads
        email_folder = "/Applications/reolink-rich-notifications/email"
        if not os.path.exists(email_folder):
            os.makedirs(email_folder)

        # Save the email itself
        with open(f"{email_folder}/{file_uuid}.eml", "wb") as f:
            f.write(data)

if __name__ == "__main__":
    # Start the server on localhost, port 25
    server = CustomSMTPServer(('0.0.0.0', 2525), None)
    asyncore.loop()

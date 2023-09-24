from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
import os
from email import policy
from email.parser import BytesParser
import uuid


class CustomHandler(Sink):
    async def handle_DATA(self, server, session, envelope):
        print("Handling incoming email...")
        msg = BytesParser(policy=policy.default).parsebytes(envelope.content)

        file_uuid = uuid.uuid4().hex

        current_directory = os.path.dirname(os.path.abspath(__file__))
        email_folder = os.path.join(current_directory, "email")
        if not os.path.exists(email_folder):
            os.makedirs(email_folder)

        with open(f"{email_folder}/{file_uuid}.eml", "wb") as f:
            f.write(envelope.content)

        return '250 Message accepted for delivery'


if __name__ == "__main__":
    handler = CustomHandler()
    controller = Controller(handler, hostname="0.0.0.0", port=2525)
    print("Starting server...")
    controller.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server stopped.")

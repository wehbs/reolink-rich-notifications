import subprocess
import atexit
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from email import policy
from email.parser import BytesParser
from PIL import Image
import moviepy.editor as mp
import requests
import os

# Function to terminate the SMTP server process when the main script exits


def terminate_process(process):
    print("Terminating SMTP server process.")
    process.terminate()
    process.wait()


# Start the SMTP server script as a subprocess
smtp_server_process = subprocess.Popen(['python3', 'pyemail.py'])

# Register the termination function to run when this script exits
atexit.register(terminate_process, smtp_server_process)

# Pushover credentials
PUSHOVER_APP_TOKEN = ""
PUSHOVER_USER_KEY = ""
# URL to open Reolink app
URL = "fb1675493782511558://"
URL_TITLE = "Open Reolink"

watch_folder = "/Applications/reolink-rich-notifications/email"
image_folder = "/Applications/reolink-rich-notifications/attachments"


def resize_image(image_path):
    quality = 90
    while os.path.getsize(image_path) > 2.4 * 1024 * 1024:  # 2.4 MB in bytes
        img = Image.open(image_path)
        img.save(image_path, "JPEG", quality=quality)
        quality -= 10  # reduce quality by 10% each iteration


def convert_mp4_to_gif(mp4_path, gif_path):
    clip = mp.VideoFileClip(mp4_path)

    # Use only the first 10 seconds of the video after the first 5 seconds
    clip = clip.subclip(5, 10)

    # Write GIF 2 fps
    clip.write_gif(gif_path, fps=2, program='ffmpeg')

    if os.path.getsize(gif_path) > 2.4 * 1024 * 1024:
        # If file size still too large, further reduce fps to 1
        clip.write_gif(gif_path, fps=1, program='ffmpeg')

    # Check file size again, if it's still too large, you may want to alert or log an error
    if os.path.getsize(gif_path) > 2.4 * 1024 * 1024:
        print("GIF file size is still too large.")


class Watcher:
    def __init__(self, watch_folder):
        self.watch_folder = watch_folder
        self.event_handler = Handler()
        self.observer = Observer()

    def run(self):
        self.observer.schedule(
            self.event_handler, self.watch_folder, recursive=True)
        self.observer.start()
        try:
            while True:
                pass
        except:
            self.observer.stop()
            print("Observer stopped")


class Handler(FileSystemEventHandler):
    def process(self, event):
        for file in os.listdir(watch_folder):
            if not file.endswith(".eml"):
                continue
            file_path = os.path.join(watch_folder, file)
            if os.path.exists(file_path):
                print(f"New file detected: {file_path}")
                with open(file_path, 'rb') as f:
                    msg = BytesParser(policy=policy.default).parse(f)

                text_data = ""
                attachment_filename = ""
                attachment_path = ""

                if msg.is_multipart():
                    for part in msg.iter_parts():
                        content_disposition = part.get(
                            "Content-Disposition", "")
                        if "attachment" not in content_disposition:
                            text_data = part.get_payload(
                                decode=True).decode().split(".")[0]
                        else:
                            attachment_filename = part.get_filename()
                            attachment_path = os.path.join(
                                image_folder, attachment_filename)
                            with open(attachment_path, 'wb') as f:
                                f.write(part.get_payload(decode=True))

                            if attachment_filename.endswith('.jpg'):
                                resize_image(attachment_path)
                            elif attachment_filename.endswith('.mp4'):
                                gif_path = attachment_path.replace(
                                    '.mp4', '.gif')
                                convert_mp4_to_gif(attachment_path, gif_path)
                                attachment_path = gif_path

                else:
                    text_data = msg.get_payload(
                        decode=True).decode().split(".")[0]

                # Delete the original email file after successful extraction
                os.remove(file_path)

                # Send push notification via Pushover
                payload = {
                    "token": PUSHOVER_APP_TOKEN,
                    "user": PUSHOVER_USER_KEY,
                    "message": text_data,
                    "url": URL,
                    "url_title": URL_TITLE
                }
                files = {
                    "attachment": (attachment_filename, open(attachment_path, "rb"))
                }

                response = requests.post(
                    "https://api.pushover.net/1/messages.json", data=payload, files=files)
                response_data = response.json()

                if response_data.get("status") == 1:
                    print("Push sent successfully.")

                    mp4_path = ""

                    if attachment_filename.endswith('.mp4'):
                        mp4_path = attachment_path.replace('.gif', '.mp4')

                    # Delete the .gif file after storing .mp4 path
                    os.remove(attachment_path)

                    try:
                        if mp4_path:  # Only try to delete if mp4_path is not empty
                            os.remove(mp4_path)  # Try to delete the .mp4 file
                    except FileNotFoundError:
                        pass  # File doesn't exist, ignore the error

                else:
                    print(f"Failed to send push. Response: {response_data}")

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':
    watcher = Watcher(watch_folder)
    watcher.run()

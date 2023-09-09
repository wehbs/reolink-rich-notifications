import subprocess
import atexit
from watchdog.observers import Observer
import time
from watchdog.events import FileSystemEventHandler
from email import policy
from email.parser import BytesParser
from PIL import Image
import moviepy.editor as mp
import requests
import os
import sys
import json
import logging

# Start the SMTP server script as a subprocess
smtp_server_process = subprocess.Popen(['python3', 'pyemail.py'])

# Function to terminate the SMTP server process when the main script exits


def terminate_process(process):
    print("Terminating SMTP server process.")
    process.terminate()
    process.wait()


# Register the termination function to run when this script exits
atexit.register(terminate_process, smtp_server_process)


# Checks for config file with key and token / creates it if not found and asks user for values


def load_or_create_config():
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
        config['PUSHOVER_APP_TOKEN'] = input('Enter your Pushover App Token: ')
        config['PUSHOVER_USER_KEY'] = input('Enter your Pushover User Key: ')
        with open(config_file, 'w') as f:
            json.dump(config, f)
    return config


# Pushover credentials
config = load_or_create_config()
PUSHOVER_APP_TOKEN = config['PUSHOVER_APP_TOKEN']
PUSHOVER_USER_KEY = config['PUSHOVER_USER_KEY']
# URL to open Reolink app
URL = "fb1675493782511558://"
URL_TITLE = "Open Reolink"

# Create `email` and `attachments` folder


def ensure_directories_exist():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folders = ['email', 'attachments']

    for folder in folders:
        full_path = os.path.join(script_dir, folder)
        if not os.path.exists(full_path):
            os.makedirs(full_path)


# Ensure required directories exist
ensure_directories_exist()
current_dir = os.path.dirname(os.path.abspath(__file__))
watch_folder = os.path.join(current_dir, 'email')
image_folder = os.path.join(current_dir, 'attachments')

# Checks for config file with key and token / creates it if not found and asks user for values


def load_or_create_config():
    config_file = 'config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {}
        config['PUSHOVER_APP_TOKEN'] = input('Enter your Pushover App Token: ')
        config['PUSHOVER_USER_KEY'] = input('Enter your Pushover User Key: ')
        with open(config_file, 'w') as f:
            json.dump(config, f)
    return config

# Create `email` and `attachments` folder


def ensure_directories_exist():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folders = ['email', 'attachments']

    for folder in folders:
        full_path = os.path.join(script_dir, folder)
        if not os.path.exists(full_path):
            os.makedirs(full_path)

# Resizes images if needed


def resize_image(image_path):
    quality = 90
    while os.path.getsize(image_path) > 2.4 * 1024 * 1024:  # 2.4 MB in bytes
        img = Image.open(image_path)
        img.save(image_path, "JPEG", quality=quality)
        quality -= 10  # reduce quality by 10% each iteration

# Converts video to .gif


def convert_mp4_to_gif(mp4_path, gif_path):
    retries = 0
    max_retries = 3
    while retries < max_retries:
        try:
            clip = mp.VideoFileClip(mp4_path)
            clip = clip.subclip(5, 10)
            clip.write_gif(gif_path, fps=2, program='ffmpeg')
            if os.path.getsize(gif_path) > 2.4 * 1024 * 1024:
                clip.write_gif(gif_path, fps=1, program='ffmpeg')
            if os.path.getsize(gif_path) > 2.4 * 1024 * 1024:
                print("GIF file size is still too large.")
            break  # Successfully converted, break out of loop
        except Exception as e:
            print(f"Failed to convert video to GIF: {e}. Retrying...")
            retries += 1
            time.sleep(2)
    if retries == max_retries:
        print("Max retries reached. Exiting.")
        sys.exit(1)


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
                # Initialize an empty dictionary for files
                files = {}
                # Add the attachment to the files dictionary if it exists
                if attachment_filename:
                    files["attachment"] = (
                        attachment_filename, open(attachment_path, "rb"))

                # Retry sending the push notification up to 3 times
                max_retries = 3
                for i in range(max_retries):
                    try:
                        response = requests.post(
                            "https://api.pushover.net/1/messages.json", data=payload, files=files if files else None, timeout=10)
                        response_data = response.json()
                        break  # If successful, break the loop
                    except requests.exceptions.RequestException as e:
                        logging.error(
                            f"Failed to send push notification (attempt {i + 1}): {e}")
                        if i < max_retries - 1:
                            time.sleep(5)  # Wait for 5 seconds before retrying
                        else:
                            print(
                                "All retries failed. There might be an issue with the Pushover server.")
                            print("Please restart the script later.")
                            sys.exit(1)

                # If the push notification was sent successfully, print a message
                if response_data.get("status") == 1:
                    print("Push sent successfully.")

                    mp4_path = ""

                    # Store the .mp4 file path if the attachment is a video
                    if attachment_filename.endswith('.mp4'):
                        mp4_path = attachment_path.replace('.gif', '.mp4')

                # Delete the .gif file after storing .mp4 path
                if attachment_path and os.path.exists(attachment_path):
                    os.remove(attachment_path)
                    # Check if the attachment file exists before attempting to delete it
                    try:
                        if mp4_path:  # Only try to delete if mp4_path is not empty
                            os.remove(mp4_path)  # Try to delete the .mp4 file
                    except FileNotFoundError:
                        pass  # File doesn't exist, ignore the error

    def on_created(self, event):
        self.process(event)


if __name__ == '__main__':
    # Create a Watcher instance and run it
    watcher = Watcher(watch_folder)
    watcher.run()

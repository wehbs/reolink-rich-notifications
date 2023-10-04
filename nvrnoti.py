import subprocess
import atexit
from watchdog.observers import Observer
import time
from watchdog.events import FileSystemEventHandler
from email import policy
from email.parser import BytesParser
from PIL import Image
import requests
import os
import sys
import json
import logging
import imageio_ffmpeg as ffmpeg
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
from email import policy
from email.parser import BytesParser
import uuid
import threading


# SMTP server
stop_event = threading.Event()


class CustomHandler(Sink):
    async def handle_DATA(self, server, session, envelope):
        print("Handling incoming email...")

        file_uuid = uuid.uuid4().hex

        current_directory = os.path.dirname(sys.executable)
        email_folder = os.path.join(current_directory, "email")

        with open(f"{email_folder}/{file_uuid}.eml", "wb") as f:
            f.write(envelope.content)

        return '250 Message accepted for delivery'


def start_email_server():
    # Read config.json
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            port = config.get("SMTP_PORT", 2525) or 2525
    except (FileNotFoundError, json.JSONDecodeError):
        port = 2525

    handler = CustomHandler()
    controller = Controller(handler, hostname="0.0.0.0", port=port)
    print(f"Starting server on port {port}...")
    controller.start()

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Server stopped.")


# Send push notification when script is terminated


def script_terminated():
    stop_event.set()
    send_push_notification(
        "reolink-rich-notifications has been terminated. Please restart.")

    # Remove all files in email and attachments folders
    folders_to_clean = [watch_folder, image_folder]
    for folder in folders_to_clean:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")


# Register the termination function to run when this script exits
atexit.register(script_terminated)

# Function to send push notification


def send_push_notification(message, attachment_path=None):
    payload = {
        "token": PUSHOVER_APP_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "message": message,
        "url": URL,
        "url_title": URL_TITLE
    }
    files = {}
    if attachment_path:
        attachment_filename = os.path.basename(attachment_path)
        files["attachment"] = (attachment_filename,
                               open(attachment_path, "rb"))

    max_retries = 3
    for i in range(max_retries):
        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json", data=payload, files=files if files else None, timeout=10)
            response_data = response.json()
            if response_data.get("status") == 1:
                print("Push sent successfully.")
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

    return response_data


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
        config['SMTP_PORT'] = input(
            'Enter the SMTP port to use (default is 2525, press Enter to use default): ')
        with open(config_file, 'w') as f:
            json.dump(config, f)
    return config


# Create `email` and `attachments` folder


def ensure_directories_exist():
    script_dir = os.path.dirname(sys.executable)
    folders = ['email', 'attachments']

    for folder in folders:
        full_path = os.path.join(script_dir, folder)
        if not os.path.exists(full_path):
            os.makedirs(full_path)


# Ensure required directories exist
ensure_directories_exist()

# Direcotry paths
current_dir = os.path.dirname(sys.executable)
watch_folder = os.path.join(current_dir, 'email')
image_folder = os.path.join(current_dir, 'attachments')

# Pushover credentials
config = load_or_create_config()
PUSHOVER_APP_TOKEN = config['PUSHOVER_APP_TOKEN']
PUSHOVER_USER_KEY = config['PUSHOVER_USER_KEY']
# URL to open Reolink app
URL = "fb1675493782511558://"
URL_TITLE = "Open Reolink"

# Start the SMTP server in a new thread
email_server_thread = threading.Thread(target=start_email_server)
# Daemon threads exit when the main program exits
email_server_thread.daemon = True
email_server_thread.start()

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
    scale = 480  # Initial scale width
    while retries < max_retries:
        if os.path.exists(gif_path):
            os.remove(gif_path)
        try:
            input_file = mp4_path
            output_file = gif_path

            # FFmpeg command with dynamic scaling
            ffmpeg_cmd = [
                ffmpeg.get_ffmpeg_exe(),
                "-i", input_file,  # Input file
                # Video filter chain
                "-vf", f"fps=5,scale={scale}:-1:flags=lanczos",
                "-f", "gif",  # Output format
                output_file  # Output file
            ]

            subprocess.run(ffmpeg_cmd, check=True)

            file_size = os.path.getsize(gif_path)
            if file_size > 2.4 * 1024 * 1024:
                print("GIF file size is too large. Adjusting scale...")
                scale = int(scale * 0.8)  # Reduce scale by 20%
                retries += 1  # Increment retries
                continue  # Skip to the next iteration
            else:
                print("GIF file size is acceptable.")
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
                            # Generate a unique identifier
                            unique_id = str(uuid.uuid4())[:8]
                            base_name, file_extension = os.path.splitext(
                                attachment_filename)

                            # Append the unique identifier to the filename
                            unique_filename = f"{base_name}_{unique_id}{file_extension}"
                            attachment_path = os.path.join(
                                image_folder, unique_filename)

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
                response_data = send_push_notification(
                    text_data, attachment_path)
                if response_data.get("status") == 1:

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
    try:
        # Send the initial push notification
        send_push_notification(
            "reolink-rich-notifications has been started. Enjoy!")

        # Create a Watcher instance and run it
        watcher = Watcher(watch_folder)
        watcher.run()

    except Exception as e:
        print(f"An error occurred: {e}")
        # This will signal the SMTP server thread to stop and do additional cleanup
        sys.exit(1)

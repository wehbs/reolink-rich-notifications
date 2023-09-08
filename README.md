
# Reolink Rich Notifications

## Description

This repository enhances the notification capabilities of Reolink NVRs and Cameras by offering rich notifications. You can either opt for sending an image or a .gif of the motion event. The project is currently geared to work with Pushover for sending push notifications. The end goal will be to use [ntfy](https://github.com/binwiederhier/ntfy) once they add attachments support to their IOS app.

**Features:**
- Intercepts local email data from Reolink devices.
- Converts video to .gif or resizes images as required.
- Sends enriched data via Pushover.

<img src="demo/noti.gif" height="700">

## Setup

### Hardware Requirements

- An M1 Mac Mini or equivalent.
- Reolink NVR or Camera.

### Software Requirements

- MacOS
- Python 3.x
- FFMpeg

### Folder Structure

After cloning this repository into `/Applications` on MacOS, your folder structure should look like this:

```
reolink-rich-notifications/
|-- nvrnoti.py
|-- pyemail.py
|-- requirements.txt
```

Create these two additional folders
```
|-- attachments/
|-- email/
```

### Installation Steps

1. Clone the repository: `git clone https://github.com/wehbs/reolink-rich-notifications.git` into the `/Applications` folder
2. Navigate into the directory: `cd /Applications/reolink-rich-notifications`
3. Install Python packages: `pip3 install -r requirements.txt`
4. Install FFMpeg: `brew install ffmpeg`

## Configuration

- Add your Pushover API keys and tokens to the `nvrnoti.py` script.
- Configure your Reolink device to send emails to the SMTP server started by `pyemail.py`. Set the STMP Port to `2525`.
- Set `Email Content` on Reolink device to `Text with Picture` for image push or `Text with Video` for .gif push.

## Usage

### nvrnoti.py

Run the `nvrnoti.py` script:

```bash
python3 /Applications/reolink-rich-notifcations/nvrnoti.py
```

**Note**: This script will also automatically start `pyemail.py`.

### pyemail.py

No need to manually start this script; it's automatically invoked by `nvrnoti.py`.

For additional customization or troubleshooting, consult the inline comments and documentation in the codebase.

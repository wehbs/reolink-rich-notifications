
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

- Add your Pushover API key and token to the `nvrnoti.py` script.
- Configure your Reolink device to send emails to the SMTP server started by `pyemail.py`.

```
SMTP Server: "Other"
SMTP Server: "xxx.xxx.xxx.xxx" (Replace with your server IP)
SSL OR TLS : "Off"
SMTP Port: "2525"
Sender Name: "Reolink"
Sender Address: "reo@link.com"
Password: ""
Recipient Address 1: "link@reo.com"
Recipient Address 2: ""
Recipient Address 3: ""
Email Content: "Text with Video" OR "Text with Picture"
```
**Note**: Assign your Mac server a DHCP Reservation to ensure it retains the same IP address.

## Usage

### nvrnoti.py

Run the `nvrnoti.py` script:

```bash
python3 /Applications/reolink-rich-notifcations/nvrnoti.py
```

**Note**: This script will also automatically start `pyemail.py`.

### pyemail.py

No need to manually start this script; it's automatically invoked by `nvrnoti.py`.

### Auto-Start on Boot for Mac

To ensure that the script runs automatically upon booting your Mac, follow these steps:
1. **Open Script Editor**: You can find this in the Utilities folder within your Applications folder.
2. **Create New Script**: Paste the following AppleScript code into the new document.
```
tell application "Terminal"
	activate
	do script "cd /Applications/reolink_notifications; python3 nvrnoti.py"
end tell
```
3. **Save the Script**: Go to `File > Save` and save it as an Application. Store this application in your `reolink-rich-notifications` directory.
4. **Open System Settings**: You can do this by clicking the Apple icon in the top-left corner of your screen and selecting "System Settings."
5. **Add to Login Items**: 
    - Search for and select "Login Items."
    - Click the "+" button and add the saved AppleScript application.
6. **Initial Approval**: Upon the next boot, you may have to manually approve the script to run. After this initial approval, it should run automatically on subsequent boots.

**Note**: Executing this AppleScript will open a Terminal window each time you boot up your Mac.

For additional customization or troubleshooting, consult the inline comments and documentation in the codebase.

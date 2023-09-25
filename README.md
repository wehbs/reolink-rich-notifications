
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

- FFMpeg

### Installation Steps

1. Download the latest release [here](https://github.com/wehbs/reolink-rich-notifications/releases/download/latest/nvrnoti.macos.arm64)
2. Install FFMpeg: `brew install ffmpeg`
3. Run the binary ```./nvrnoti.macos.arm64```

### Folder Structure

These will get created after the scripts first run
```
|-- attachments/
|-- email/
|-- config.json/
```
## Configuration

- Input your Pushover API key and token the first time the script is ran.
- Configure your Reolink device to send emails to the SMTP server.

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

For additional customization or troubleshooting, consult the inline comments and documentation in the codebase.

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/wehbs)
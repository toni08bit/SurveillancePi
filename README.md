# Surveillance Pi
## What's this?
This project is dedicated for a CCTV system using Raspberry Pi(s) with a [Raspberry Pi Camera Module](https://thepihut.com/products/raspberry-pi-camera-module-3)
## Requirements
### Storage/Master Pi
- Raspberry Pi
- WiFi/LAN Connection
- (Maybe?) External Storage Device (because we don't want to overwhelm the system SD card with high traffic)
### Camera Pi (Indefinitely repeatable)
- Raspberry Pi (with CAM port)
- WiFi/LAN Connection
- Camera Module ([PiHut](https://thepihut.com/products/raspberry-pi-camera-module-3)) - Old modules are working, but are giving you a red/pink picture.
## How to install
1. Use wget or curl to download the applicable install.sh file for every device.
2. (You might need to set run permissions for the file (even if you are root) with "chmod 777 install.sh")
3. On a master device, you might have to modify some config.json values, verify the broadcast address with ifconfig.
## Disclaimer
I do not take responsibility for technical failures, misuse or any other failure/unintended use. Please customize the code to your usage.

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
- Camera Module ([PiHut](https://thepihut.com/products/raspberry-pi-camera-module-3)) - Possible to use old modules, apply filter "greyworld" for relatively fine color quality, if you don't care about green being replaced with pink (trees be looking funny)
## How to install
Copy the applicable code to */home/SurveillancePi*.
Move the .service file to */etc/systemd/system* and enable it.
## Disclaimer
I do not take responsibility for technical failures, misuse or any other failure/unintended use. Please customize the code to your usage.

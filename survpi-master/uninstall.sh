if [ "$PWD" != "/home/pi/SurveillancePi" ]
then
    echo "Please run the install script inside the /home/pi/SurveillancePi folder."
    exit
fi

echo "Stopping service..."
systemctl stop survpi
systemctl disable survpi

echo "Uninstalling..."
rm -f /etc/systemd/system/survpi.service
rm -f /etc/nginx/sites-available/survpi-web
rm -f /etc/nginx/sites-enables/survpi-web
rm -f -r $PWD

echo "Thank you, goodbye!"
if [ "$PWD" != "/home/pi/SurveillancePi" ] then
    echo "Please run the install script inside the /home/pi/SurveillancePi folder."
    exit
fi

echo "Running uninstall script..."
./uninstall.sh

echo "Downloading install script..."
cd /home/pi/
wget https://raw.githubusercontent.com/BillPlayzToday/SurveillancePi/main/survpi-master/install.sh

echo "Running install script..."
./install.sh
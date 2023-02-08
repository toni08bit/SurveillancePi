if [ "$EUID" != "0" ] then
    echo "Please run the install script as root or sudo."
    exit
fi

if [ "$PWD" != "/home/pi" ] then
    echo "Please run the install script inside the /home/pi folder."
    exit
fi

echo "Updating packages..."
apt update
apt upgrade -y

echo "Installing git, if not installed."
apt install git -y

echo "Installing required packages."
apt install python3-venv -y

echo "Cloning master directory."
git clone --depth 1 --filter=blob:none --sparse https://github.com/BillPlayzToday/SurveillancePi
cd SurveillancePi
git sparse-checkout set survpi-master
cd survpi-master

echo "Installing..."
mv -f ./survpi.service /etc/systemd/system/
mv -f ./uninstall.sh /home/pi/SurveillancePi/
chmod 777 /home/pi/SurveillancePi/uninstall.sh
python3 -m venv .env

echo "Starting service..."
systemd enable survpi
systemd start survpi

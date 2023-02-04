if [ "$EUID" != "0" ]
    then echo "Please run the install script as root or sudo."
    exit
fi

echo "Updating packages..."
apt update
apt upgrade -y

echo "Installing git, if not installed."
apt install git -y

echo "Cloning camera directory."
git clone --depth 1 --filter=blob:none --sparse https://github.com/BillPlayzToday/SurveillancePi
cd SurveillancePi
git sparse-checkout set survpi-camera
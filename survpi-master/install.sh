if [ "$EUID" != "0" ]
then
    echo "Please run the install script as root or sudo."
    exit
fi

if [ "$PWD" != "/home/pi" ]
then
    echo "Please run the install script inside the /home/pi folder."
    exit
fi

echo "Updating packages..."
apt update
apt upgrade -y

echo "Installing additional packages, if not installed. (1/2)"
apt install git python3-dev python3-pip build-essential libssl-dev libffi-dev python3-setuptools python3-venv ufw nginx -y

echo "Installing required packages."
apt install python3-venv -y

echo "Cloning master directory."
git clone --depth 1 --filter=blob:none --sparse https://github.com/BillPlayzToday/SurveillancePi
cd SurveillancePi
git sparse-checkout set survpi-master
git sparse-checkout add modules
cd survpi-master

echo "Installing..."
ufw allow 22
ufw allow 80
ufw allow 8888
mv -f ./survpi.service /etc/systemd/system/
mv -f ./uninstall.sh /home/pi/SurveillancePi/
mv -f ./reinstall.sh /home/pi/SurveillancePi
mv -f ./web.nginx /etc/nginx/sites-available/survpi-web.conf
ln -f -s /etc/nginx/sites-available/survpi-web.conf /etc/nginx/sites-enabled/survpi-web.conf
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx
chmod 777 /home/pi/SurveillancePi/uninstall.sh
chmod 777 /home/pi/SurveillancePi/reinstall.sh
chmod 777 /home/pi/SurveillancePi/survpi-master/
python3 -m venv .env

echo "Installing additional packages, if not installed. (2/2)"
/home/pi/SurveillancePi/survpi-master/.env/bin/pip install wheel
/home/pi/SurveillancePi/survpi-master/.env/bin/pip install uwsgi flask

echo "Checking for existing config..."
cd ../..
mv -f ./survpi-config.json ./SurveillancePi/survpi-master

echo "Moving modules..."
mv -f -r ./SurveillancePi/modules/*.py ./SurveillancePi/survpi-master/
rm -f -r ./SurveillancePi/modules/

echo "Starting service..."
systemctl enable survpi
systemctl start survpi

echo "Done. (UFW configured, but not enabled)"
echo "Stopping service..."
systemctl stop survpi
systemctl disable survpi

echo "Uninstalling..."
rm -f /etc/systemd/system/survpi.service
rm -f -r $PWD

echo "Thank you, goodbye!"

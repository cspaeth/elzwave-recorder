 
# Setup Wifi / SSH

- https://desertbot.io/blog/headless-raspberry-pi-4-ssh-wifi-setup
- Add ssh certificate
- sudo apt-get update 
- sudo apt-get upgrade

- sudo raspi-config
    - Set locale / TZ

- sudo apt-get install libportaudio2
- sudo apt-get install ffmpeg
- sudo apt-get install git
- Checkout code
- sudo apt-get install python3-pip
- sudo pip install -r requirements.txt
- sudo python setup.py develop
- sudo ln -s /home/pi/elzwave-recorder/systemd/recorder.service /etc/systemd/system/
- sudo ln -s /home/pi/elzwave-recorder/systemd/papertrail.service /etc/systemd/system/
- sudo systemctl daemon-reload
- sudo systemctl enable recorder.service
- sudo systemctl enable papertrail.service
- sudo hostnamectl set-hostname 'elzwave-pi400'

- sudo apt-get install usbmount
    https://krausens-online.de/debianraspbian-usb-automatisch-mounten/
    https://raspberrypi.stackexchange.com/questions/100312/raspberry-4-usbmount-not-working

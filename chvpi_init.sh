#!/bin/bash

###CHV Rasberry Pi Init Script Version 3###

SCRIPT_DIR=/opt
HANDLING_USER=pi
DIALOUT_USER=villager
PYTHON2_REQS=requirements_p2.txt
PYTHON3_REQS=requirements_p3.txt

RTLSDR="${1:-nosdr}"


usage(){
	echo "This script installs all the dependencies needed for creating a V-CHV Box"
	echo "Make sure you run this as pi..."
	echo "Usage: $0 nosdr|sdr"
	echo ""
	echo "Default usage is no arguments; installs without SDR.."
	exit 1
}

if [ $1 != "sdr" ] && [ $1 != "SDR" ] && [ $1 != "nosdr" ] && [ $1 != "NOSDR" ]; then
    usage
fi

sudo cat <<"EOF"

  _   __    _______ ___   __  _____  _______________   __   __   _______ 
 | | / /___/ ___/ // / | / / /  _/ |/ / __/_  __/ _ | / /  / /  / __/ _ \
 | |/ /___/ /__/ _  /| |/ / _/ //    /\ \  / / / __ |/ /__/ /__/ _// , _/
 |___/    \___/_//_/ |___/ /___/_/|_/___/ /_/ /_/ |_/____/____/___/_/|_| 
                                                                         

EOF

echo "This script installs all the dependencies needed for creating a V-CHV Box"
echo "Make sure you run this as pi..."


read -n 1 -r -s -p $'Press enter to continue...\n'
echo ""
echo "Updating repos and upgrading to a new distribution..."
sudo apt-get -qq -y update && sudo apt-get -qq -y upgrade


echo "Installing development tools..."
sudo apt-get install -y git build-essential cmake p7zip-full
sudo apt-get install -y python-pip python-setuptools python-pil python-numpy python-pydot python-pydot-ng
sudo apt-get install -y python3-pip python3-pil python3-numpy 
sudo apt-get install -y raspberrypi-kernel-headers linux-kernel-headers 

echo "Installing development libraries"
sudo apt-get install -qq -y libusb-1.0-0-dev libboost-all-dev libpcap-dev libconfuse-dev libffi-dev libbsd-dev xorg-dev

echo "Installing additional tools..."
sudo apt-get install -qq -y doxygen autoconf graphviz autopoint
sudo apt-get install -qq -y flex gawk lexicon gettext binutils samba lynx binwalk screen can-utils tmate fail2ban

if [ $1 = "sdr" ]; then
	echo "Installing SDR tools"
	sudo apt-get install -qq -y gr-osmosdr gqrx-sdr
	sudo apt-get install -qq -y python3-numpy python3-scipy python3-matplotlib
fi

sudo cat <<EOF > $PYTHON2_REQS
manifest-tool
pexpect
RPi.GPIO
spidev
python-can
EOF

sudo cat <<EOF > $PYTHON3_REQS
can-isotp
manifest-tool
pexpect
python-can
RPi.GPIO
spidev
treelib
pyrtlsdr
EOF

if [ $1 = "sdr" ]; then
	sudo cat <<EOF >> $PYTHON3_REQS
	libffi-dev 
	libffi6
	cairocffi
	EOF

	sudo cat <<EOF > /etc/modprobe.d/no-rtl.conf
	blacklist dvb_usb_rtl28xxu
	blacklist rtl2832
	blacklist rtl2830
EOF
fi

echo "Installing python packages..."
if test -f "$PYTHON2_REQS"; then
    sudo pip install -r $PYTHON2_REQS
    sudo rm -f $PYTHON2_REQS
else
    echo "Cannot find $PYTHON2_REQS"
    exit 1
fi

if test -f "$PYTHON3_REQS"; then
    sudo pip3 install -r $PYTHON3_REQS
    sudo rm -f $PYTHON3_REQS
else
    echo "Cannot find $PYTHON3_REQS"
    exit 1
fi


echo "Getting repositories and building things..."
if [ $1 = "sdr" ]; then
	sudo cd $SCRIPT_DIR
	sudo git clone git://git.osmocom.org/rtl-sdr.git
	sudo cd $SCRIPT_DIR/rtl-sdr/
	sudo mkdir build
	sudo cd build
	sudo cmake ../ -DINSTALL_UDEV_RULES=ON
	sudo make && make install
	sudo ldconfig
	sudo cd $SCRIPT_DIR
	sudo cp $SCRIPT_DIR/rtl-sdr/rtl-sdr.rules /etc/udev/rules.d/
fi

sudo cd $SCRIPT_DIR
sudo git clone https://github.com/hartkopp/can-isotp.git
sudo make -C $SCRIPT_DIR/can-isotp/ -j4
sudo make modules_install -C $SCRIPT_DIR/can-isotp/
sudo modprobe can
sudo insmod $SCRIPT_DIR/can-isotp/net/can/can-isotp.ko

sudo cd $SCRIPT_DIR
sudo git clone --recursive https://github.com/intrepidcs/icsscand.git
sudo mkdir -p $SCRIPT_DIR/icsscand/build
sudo cmake -S $SCRIPT_DIR/icsscand/ -B $SCRIPT_DIR/icsscand/build -DCMAKE_BUILD_TYPE=Release
sudo make -C $SCRIPT_DIR/icsscand/build/. -j8
sudo $SCRIPT_DIR/icsscand/build/libicsneo-socketcan-daemon

sudo cd $SCRIPT_DIR
sudo git clone https://github.com/linted/HardwareCheckout.git
sudo ./HardwareCheckout/tmate/install.sh

echo "Enable I2C modules"
sudo echo "can" >> /etc/modules
sudo echo "can_raw" >> /etc/modules
sudo echo "can_dev" >> /etc/modules
###After enabling I2C typically a reboot is needed###

echo "Your password will expire on next login!"
passwd -e

###Creating a user with a home folder remove -m if you do not want a home folder###
sudo adduser -m village
sudo adduser --disabled-password --gecos "" -m $DIALOUT_USER

###This is not secure at all, but for automation's sake###
echo chv | passwd $DIALOUT_USER --stdin
# passwd chv

###Add villager to dialout group###
sudo usermod -a -G dialout $DIALOUT_USER

###Generate a strong ssh key###
ssh-keygen -b 4096 -f ~/.ssh/id_rsa -N ""

###Creat/Update F2B Config###
sed  '/\[sshd\]/a###CHV INSTALLER MODS###\nmaxretry = 10\nbantime = -1\niptables-multiport\nenabled = true\nfilter = sshd\n###END MODS###\n' /etc/fail2ban/jail.conf > /etc/fail2ban/jail.local.conf

sudo service fail2ban reload


###Update ###
sudo cat <<"EOF" >> ~/.profile


        
                                      _.-=\"\"_-         _
                                 _.-=\"  \"_-           | ||\"\"\"\"\"\"\"-\"--_______     __..
                     ___.===\"\"\"\"-.______-,,,,,,,,,,,,,-\\''----\" \"\"\"\"\"      \"\"\"\"\" \"_ 
              __.--\"\"     __        ,'                   o \\           __        [_|
         __-\"\"=======.--\"\"  \"\"--.=================================.--\"\"  \"\"--.=======:
        ]       [w] : /        \ : |== Welcome to the ======|    : /        \ :  [w] :
        V___________:|          |: |= Car Hacking Village ==|    :|          |:   _-
         V__________: \        / :_|=======================/_____: \        / :__-
         -----------'  \"-____-\"  --------------------------------'  \"-____-\"



        Welcome to the Car Hacking Village.  This is SUPER BETA!
        If you need help find us on the discord or slack or by phone at 617-440-8667
	Please wait while we set things up for you to hack...

EOF



## Setting up the Value Can##
sudo ~/icsscand/build/libicsneo-socketcan-daemon -d
sudo ip link set up can0

read -n 1 -r -s -p $'Press enter to reboot...\n'
sudo reboot

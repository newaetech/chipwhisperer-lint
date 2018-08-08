#!/bin/sh

#Username of final owner
USERNAME=ec2-user

#Directory setup
sudo mkdir /opt/cwlint
sudo mkdir /var/cwlint
sudo chown $USERNAME /opt/cwlint
sudo chgrp $USERNAME /opt/cwlint
sudo chown $USERNAME /var/cwlint
sudo chgrp $USERNAME /var/cwlint
sudo -u $USERNAME mkdir /var/cwlint/traces

sudo yum -y install git
sudo yum -y install python2.7 python-pip python-virtualenv python-scipy python-numpy
sudo yum -y install build-utils gcc

sudo -u $USERNAME git clone https://github.com/newaetech/chipwhisperer-lint.git /opt/cwlint/cwlint_git
cd /opt/cwlint/cwlint_git
cd server-backend
#sudo -u $USERNAME virtualenv cwlint
#sudo -u $USERNAME source cwlint/bin/activate
#sudo -u $USERNAME pip install -r requirements.txt
sudo pip install -r requirements.txt

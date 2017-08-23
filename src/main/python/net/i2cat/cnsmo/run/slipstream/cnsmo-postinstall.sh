#!/bin/bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
    # install docker
    curl -fsSL https://get.docker.com/ | sh
    current_user=$(whoami)
    usermod -aG docker ${current_user}
else
    echo "docker already installed"
fi

# download cnsmo
mkdir cnsmo
cd cnsmo
git clone --single-branch https://github.com/dana-i2cat/cnsmo.git
git clone --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git
cd ..    

# reboot to apply new kernel, upgraded by docker installation script
#reboot

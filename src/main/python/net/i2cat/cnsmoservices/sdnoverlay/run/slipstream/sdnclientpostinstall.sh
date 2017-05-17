#!/bin/bash
# Run this script using sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit 126
fi

# set working directory
DIRECTORY='/opt/odl'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

touch /var/log/sdnserverinstall.log

echo "Installing OpenvSwitch..." >> /var/log/sdnserverinstall.log
apt-get install -y openvswitch-switch
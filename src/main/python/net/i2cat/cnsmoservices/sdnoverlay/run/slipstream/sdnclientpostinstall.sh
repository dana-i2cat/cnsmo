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

printf "Installing OpenvSwitch..." 
apt-get install -y openvswitch-switch
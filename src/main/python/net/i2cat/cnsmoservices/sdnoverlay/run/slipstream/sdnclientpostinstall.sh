#!/bin/bash
# Run this script using sudo
if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit 126
fi

printf "Installing OpenvSwitch..." 
apt-get install -y openvswitch-switch
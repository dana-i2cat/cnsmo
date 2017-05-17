#!/bin/sh
# Run this script using sudo
apt-get install -y curl git cython python-pip
curl -fsSL https://get.docker.com/ | sh
cd /cnsmo
pip install -r requirements.txt

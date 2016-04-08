#!/bin/bash

# install docker
curl -fsSL https://get.docker.com/ | sh
sudo usermod -aG docker ubuntu

# download cnsmo
mkdir cnsmo
cd cnsmo
git clone --single-branch https://github.com/dana-i2cat/cnsmo.git
git clone --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git
cd ..

# install cnsmo requirements
sudo pip install -r cnsmo/cnsmo/requirements.txt


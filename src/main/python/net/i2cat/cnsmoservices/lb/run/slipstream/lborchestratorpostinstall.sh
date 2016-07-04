#!/usr/bin/env bash

# install docker
curl -fsSL https://get.docker.com/ | sh
current_user=$(whoami)
sudo usermod -aG docker ${current_user}

# download cnsmo
mkdir cnsmo
cd cnsmo
git clone --single-branch https://github.com/dana-i2cat/cnsmo.git
git clone --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git
cd ..

# install cnsmo requirements
sudo pip install -r cnsmo/cnsmo/requirements.txt

#install redis
wget http://download.redis.io/releases/redis-3.0.7.tar.gz
tar xzf redis-3.0.7.tar.gz
rm redis-3.0.7.tar.gz
cd redis-3.0.7
make
make install --quiet
cd ..

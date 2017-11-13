#!/bin/bash

DIRECTORY='/var/tmp/slipstream'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
    echo "docker MUST BE installed"
    # install docker
    curl -fsSL https://get.docker.com/ | sh
    current_user=$(whoami)
    usermod -aG docker ${current_user}
else
    echo "docker already installed"
fi

aux=$(ss-get --timeout=1000 net.i2cat.cnsmo.git.branch)

# Download the repositories from gitHub
mkdir cnsmo
cd cnsmo
git clone -b ${aux} --single-branch https://github.com/dana-i2cat/cnsmo.git
git clone -b master --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git

cd ${DIRECTORY}

# install cnsmo requirements
pip install -r cnsmo/cnsmo/requirements.txt

#install redis
wget http://download.redis.io/releases/redis-3.0.7.tar.gz
tar xzf redis-3.0.7.tar.gz
rm redis-3.0.7.tar.gz
cd redis-3.0.7
make
make install --quiet
PORT=20379
CONFIG_FILE=/etc/redis/20379.conf
LOG_FILE=/var/log/redis_20379.log
DATA_DIR=/var/lib/redis/20379
EXECUTABLE=/usr/local/bin/redis-server
echo -e \
  "${PORT}\n${CONFIG_FILE}\n${LOG_FILE}\n${DATA_DIR}\n${EXECUTABLE}\n" | \
  utils/install_server.sh
cd ..

# remove persisted network configuration (for compatibility with pre-built images)
rm -f /etc/udev/rules.d/*net*.rules

# reboot to apply new kernel, upgraded by docker installation script
reboot


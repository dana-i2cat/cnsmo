#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

file_done='/.post-install-done'
if [ ! -f $file_done ]; then
    
    if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
        # install docker
        curl -fsSL https://get.docker.com/ | sh
        current_user=$(whoami)
        usermod -aG docker ${current_user}
    else
        echo "docker already installed"
    fi
    

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/slipstream/sdnserverpostinstall.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.postinstall.ready
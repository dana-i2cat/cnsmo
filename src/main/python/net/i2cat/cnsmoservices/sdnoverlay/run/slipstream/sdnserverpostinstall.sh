#!/bin/bash

touch test0.out

echo -n "127.0.1.1 " >> /etc/hosts
hostname >> /etc/hosts

DIRECTORY='/var/tmp/slipstream'
if [ ! -d "$DIRECTORY" ]; then
  mkdir -p ${DIRECTORY}
fi
cd ${DIRECTORY}

file_done='/.post-install-done'
if [ ! -f $file_done ]; then

    touch test1.out
    
    if [ $(docker --version 1>/dev/null 2>/dev/null; echo $?) != "0" ] ; then
        # install docker
        curl -fsSL https://get.docker.com/ | sh
        current_user=$(whoami)
        usermod -aG docker ${current_user}
    else
        echo "docker already installed"
    fi
    
    touch ${file_done}

    cwd=${PWD}
    python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesserverpostinstall.py &
    disown $!
    ss-get --timeout=1200 net.services.installed # crear variable
    
fi
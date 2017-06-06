#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesserverdeployment.py &
disown $!
ss-get --timeout=1800 net.services.enabled

#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/slipstream/sdnclientdeployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.sdn.ready
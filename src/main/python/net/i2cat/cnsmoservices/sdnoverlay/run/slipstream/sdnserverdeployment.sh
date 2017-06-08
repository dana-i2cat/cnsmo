#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

services=$(ss-get net.services.enable)
if 'sdn' in services:
    cwd=${PWD}
    python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/slipstream/sdnserverdeployment.py &
    disown $!
    ss-get --timeout=1800 net.i2cat.cnsmo.service.sdn.server.ready

#!/bin/bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesclientpostinstall.py &
disown $!
ss-get --timeout=1200 net.services.installed

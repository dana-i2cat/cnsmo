#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/dns/run/slipstream/dnsclientdeployment.py &
disown $!

#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/dns/run/slipstream/dnsserverdeployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.dns.server.ready

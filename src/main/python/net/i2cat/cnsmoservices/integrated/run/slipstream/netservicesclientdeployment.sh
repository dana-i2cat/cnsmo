#!/bin/bash

wd='/var/tmp/slipstream'
cd ${wd}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/slipstream/cnsmo-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.core.ready


cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesclientdeployment.py &
disown $!
ss-get --timeout=3600 net.services.enabled
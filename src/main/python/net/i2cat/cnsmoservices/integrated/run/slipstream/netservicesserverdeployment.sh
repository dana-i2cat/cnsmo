#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/integrated/run/slipstream/netservicesserverdeployment.py &
disown $!
ss-get --timeout=1800 net.services.enabled

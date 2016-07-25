#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/vpnserverdeployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.vpn.ready

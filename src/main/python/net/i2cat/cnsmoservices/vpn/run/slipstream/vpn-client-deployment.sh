#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/vpn-client-deployment.py &
disown $!
serverid=$(ss-get vpn.server.nodeinstanceid)
ss-get --timeout=1800 ${serverid}:net.i2cat.cnsmo.service.vpn.ready

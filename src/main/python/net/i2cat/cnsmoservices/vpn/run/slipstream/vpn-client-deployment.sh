#!/usr/bin/env bash

cwd=${PWD}
python ${cmd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/vpn-client-deployment.py &
disown $!
ss-get --timeout=1800 VPN_server.1:net.i2cat.cnsmo.service.vpn.ready

#!/usr/bin/env bash

python /tmp/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/slipstream/vpn-client-deployment.py &
disown $!
ss-get --timeout=1800 VPN_server.1:net.i2cat.cnsmo.service.vpn.ready

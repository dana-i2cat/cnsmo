#!/usr/bin/env bash

python /tmp/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/vpn-server-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.vpn.ready

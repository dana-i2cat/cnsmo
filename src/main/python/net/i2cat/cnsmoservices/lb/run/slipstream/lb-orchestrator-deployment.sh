#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/lb/run/slipstream/lb-orchestrator-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.lb.ready

address=$(ss-get hostname)
port=$(ss-get lb.port)
ss-set url.service ${address}:${port}

# Set deployment global url.service
ss-set ss:url.service ${address}:${port}

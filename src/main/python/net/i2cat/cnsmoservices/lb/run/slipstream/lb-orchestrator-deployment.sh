#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/lb/run/slipstream/lb-orchestrator-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.lb.ready

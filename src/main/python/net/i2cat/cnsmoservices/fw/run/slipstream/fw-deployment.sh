#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/fw/run/slipstream/fw-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.service.fw.ready

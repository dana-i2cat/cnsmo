#!/usr/bin/env bash

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/slipstream/cnsmo-deployment.py &
disown $!
ss-get --timeout=1800 net.i2cat.cnsmo.core.ready

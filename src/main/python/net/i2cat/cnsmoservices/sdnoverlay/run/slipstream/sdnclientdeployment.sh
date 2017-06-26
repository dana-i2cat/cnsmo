#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/slipstream/sdnclientdeployment.py &
disown $!
serverid=$(ss-get --timeout=1200 vpn.server.nodeinstanceid)
# In case of timeout, serverid will not be set. But next ss-get will fail with Unknown key error.
if [[ -z "$serverid" ]]; then
exit 1
else
ss-get --timeout=1800 ${serverid}:net.i2cat.cnsmo.service.sdn.server.ready
fi
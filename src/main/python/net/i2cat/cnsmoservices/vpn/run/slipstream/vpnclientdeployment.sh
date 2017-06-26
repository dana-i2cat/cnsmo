#!/usr/bin/env bash

# set working directory
DIRECTORY='/var/tmp/slipstream'
cd ${DIRECTORY}

cwd=${PWD}
python ${cwd}/cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/vpnclientdeployment.py &
disown $!
serverid=$(ss-get --timeout=1800 vpn.server.nodeinstanceid)
# In case of timeout, serverid will not be set. But next ss-get will fail with Unknown key error.
# Better to finish script immediately (ss-get that got timeout will abort the deployment in short time)
if [[ -z "$serverid" ]]; then
exit 1
else
ss-get --timeout=1800 ${serverid}:net.i2cat.cnsmo.service.vpn.ready
fi

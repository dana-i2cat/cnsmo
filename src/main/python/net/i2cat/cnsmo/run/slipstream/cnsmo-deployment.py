#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
###

import os
import subprocess
import sys
import threading
import time


path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    deploycnsmo()


def deploycnsmo():
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)

    hostname = call('ss-get hostname').rstrip('\n')
    dss_port = "6379"
    redis_address = "%s:%s" % (hostname, dss_port)

    date = call('date')
    f = None
    try:
        f = open("/tmp/cnsmo/cnsmo.log", "w+")
        f.write("Launching CNSMO at %s" % date)
    finally:
        if f:
            f.close()

    # Launch REDIS
    tr = threading.Thread(target=launchRedis, args=(hostname, dss_port))
    tr.start()
    # TODO implement proper way to detect when the redis server is ready
    time.sleep(1)

    # Launch CNSMO
    call('ss-display \"Launching CNSMO...\"')
    tss = threading.Thread(target=launchSystemState, args=(hostname, dss_port))
    tss.start()
    # TODO implement proper way to detect when the system state is ready
    time.sleep(1)
    call("ss-set net.i2cat.cnsmo.dss.address %s" % redis_address)
    call('ss-set net.i2cat.cnsmo.core.ready true')
    call('ss-display \"CNSMO is ready!\"')


def launchRedis(hostname, dss_port):
    call('ss-display \"Launching REDIS...\"')
    call('redis-server')


def launchSystemState(hostname, dss_port):
    call('ss-display \"Launching CNSMO...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/systemstate.py -a %s -p %s" % (hostname, dss_port))


main()

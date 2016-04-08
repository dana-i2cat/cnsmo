#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
###

import subprocess
import threading
import time

from slipstream.SlipStreamHttpClient import SlipStreamHttpClient
from slipstream.ConfigHolder import ConfigHolder

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)

    # TODO get this from slipstream context, by inspecting roles each component has
    server_instance_id = "VPN_server.1"

    date = call('date')
    try:
        f = open("/tmp/cnsmo/vpn.log", "w+")
        f.write("Waiting for CNSMO at %s" % date)
    finally:
        f.close()

    call('ss-display \"Waiting for CNSMO...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id)

    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')

    call('ss-display \"Deploying VPN components...\"')

    date = call('date')
    try:
        f = open("/tmp/cnsmo/vpn.log", "a")
        f.write("Waiting for VPN orchestrator at %s" % date)
    finally:
        f.close()

    call('ss-display \"VPN: Waiting for VPN orchestrator...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.orchestrator.ready" % server_instance_id)

    hostname = call('ss-get hostname').rstrip('\n')

    date = call('date')
    try:
        f = open("/tmp/cnsmo/vpn.log", "a")
        f.write("launching VPN client at %s" % date)
    finally:
        f.close()

    tc = threading.Thread(target=launchVPNClient, args=(hostname, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the client is ready (using systemstate?)
    time.sleep(1)
    call('ss-set net.i2cat.cnsmo.service.vpn.client.listening true')

    date = call('date')
    try:
        f = open("/tmp/cnsmo/vpn.log", "a")
        f.write("Waiting for VPN to be deployed at %s" % date)
    finally:
        f.close()

    call('ss-display \"VPN: Waiting for VPN to be established...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id)

    date = call('date')
    try:
        f = open("/tmp/cnsmo/vpn.log", "a")
        f.write("VPN deployed at %s" % date)
    finally:
        f.close()

    call('ss-display \"VPN: VPN has been established!\"')
    print "VPN deployed!"


def launchVPNClient(hostname, redis_address, instance_id):
    call('ss-display \"VPN: Launching VPN client...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/client.py -a %s -p 9091 -r %s -s VPNClient-%s" % (hostname, redis_address, instance_id))


main()

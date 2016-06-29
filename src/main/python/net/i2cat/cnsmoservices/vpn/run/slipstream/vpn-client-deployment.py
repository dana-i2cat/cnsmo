#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# vpn.server.nodeinstanceid: Indicates the node.id of the component acting as VPN server
#
# Output parameters:
# net.i2cat.cnsmo.service.vpn.client.listening: Used to communicate the client to be listening for orchestrator orders
# vpn.address: Used to communicate the IPv4 address of this component
# vpn.address6: Used to communicate the IPv6 address of this component
#
# Requires the following output parameters from the VPN server:
# net.i2cat.cnsmo.core.ready: Used to communicate CNSMO core is ready.
# net.i2cat.cnsmo.dss.address: Used to communicate CNSMO distributed system state address.
# net.i2cat.cnsmo.service.vpn.orchestrator.ready: Used to communicate the vpn orchestrator is ready
# net.i2cat.cnsmo.service.vpn.ready: Used to communicate the VPN service to be configured properly
###

import subprocess
import threading
import time
import os

from slipstream.SlipStreamHttpClient import SlipStreamHttpClient
from slipstream.ConfigHolder import ConfigHolder

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    log_file = os.getcwd() + "/cnsmo/vpn.log"
    ifaces_prev = getCurrentInterfaces()

    server_instance_id = call('ss-get --timeout=1200 vpn.server.nodeinstanceid').rstrip('\n')
    if not server_instance_id:
        # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return

    date = call('date')
    logToFile("Waiting for CNSMO at %s" % date, log_file, "w+")

    call('ss-display \"Waiting for CNSMO...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id)

    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')

    call('ss-display \"Deploying VPN components...\"')

    date = call('date')
    logToFile("Waiting for VPN orchestrator at %s" % date, log_file, "a")

    call('ss-display \"VPN: Waiting for VPN orchestrator...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.orchestrator.ready" % server_instance_id)

    hostname = call('ss-get hostname').rstrip('\n')

    date = call('date')
    logToFile("launching VPN client at %s" % date, log_file, "a")

    tc = threading.Thread(target=launchVPNClient, args=(hostname, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the client is ready (using systemstate?)
    time.sleep(1)
    call('ss-set net.i2cat.cnsmo.service.vpn.client.listening true')

    date = call('date')
    logToFile("Waiting for VPN to be deployed at %s" % date, log_file, "a")

    call('ss-display \"VPN: Waiting for VPN to be established...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id)

    time.sleep(5)

    date = call('date')
    logToFile("VPN deployed at %s" % date, log_file, "a")

    # assuming the VPN interface (probably tap0) is the only one created during this script execution
    vpn_iface = None
    for current_iface in getCurrentInterfaces():
        if current_iface not in ifaces_prev:
            vpn_iface = current_iface

    if not vpn_iface:
        call("ss-abort \"%s:Failed to create tap interface, required for the VPN\"" % instance_id)
        return

    vpn_local_ipv4_address = getInterfaceIPv4Address(vpn_iface)
    vpn_local_ipv6_address = getInterfaceIPv6Address(vpn_iface)
    logToFile("VPN using interface %s with ipaddr %s and ipv6addr %s" %
              (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address), log_file, "a")

    call("ss-set vpn.address %s" % vpn_local_ipv4_address)
    call("ss-set vpn.address6 %s" % vpn_local_ipv6_address)

    call("ss-display \"VPN: VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s\"" %
         (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    print "VPN deployed!"


def launchVPNClient(hostname, redis_address, instance_id):
    call('ss-display \"VPN: Launching VPN client...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/client.py -a %s -p 9091 -r %s -s VPNClient-%s" % (hostname, redis_address, instance_id))


def getCurrentInterfaces():
    return call("""ls /sys/class/net | sed -e s/^\(.*\)$/\1/ | paste -sd ','""").rstrip('\n').split(',')


def getInterfaceIPv4Address(iface):
    return call("ifconfig " + iface + " | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'").rstrip('\n')


def getInterfaceIPv6Address(iface):
    return call("ifconfig " + iface + "| awk '/inet6 / { print $3 }'").rstrip('\n')


def logToFile(message, filename, filemode):
    f = None
    try:
        f = open(filename, filemode)
        f.write(message)
    finally:
        if f:
            f.close()

main()

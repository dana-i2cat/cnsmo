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

import logging
import subprocess
import threading
import time
import os

call = lambda command: subprocess.check_output(command, shell=True)

logging.basicConfig(filename="cnsmo-deployment.log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
logger = logging.getLogger('net.i2cat.cnsmoservices.vpn.run.slipstream.vpnclientdeployment')


def main():
    logger.debug("Running VPN client deployment script...")
    return deployvpn()


def deployvpn():
    logger.debug("Deploying VPN client on a SlipStream application...")

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    log_file = os.getcwd() + "/cnsmo/vpn.log"

    ifaces_prev = getCurrentInterfaces()
    logger.debug("Got current interfaces: %s" % ifaces_prev)

    logger.debug("Resolving vpn.server.nodeinstanceid...")
    server_instance_id = call('ss-get --timeout=1200 vpn.server.nodeinstanceid').rstrip('\n')
    if not server_instance_id:
        logger.error("Timeout waiting for vpn.server.nodeinstanceid")
        # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return -1
    logger.debug("Got vpn.server.nodeinstanceid= %s" % server_instance_id)

    logger.debug("Waiting for CNSMO...")
    call('ss-display \"Waiting for CNSMO...\"')
    response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for CNSMO. net.i2cat.cnsmo.core.ready= %s" % response)

    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')
    logger.debug("Got %s:net.i2cat.cnsmo.dss.address= %s" % (server_instance_id, redis_address))

    logger.debug("Deploying VPN components...")
    call('ss-display \"Deploying VPN components...\"')

    logger.debug("Waiting for VPN orchestrator...")
    call('ss-display \"VPN: Waiting for VPN orchestrator...\"')
    response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.orchestrator.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for VPN orchestrator.")
    if not response:
        logger.error("Timeout waiting for %s:net.i2cat.cnsmo.service.vpn.orchestrator.ready" % server_instance_id)
        return -1


    hostname = call('ss-get hostname').rstrip('\n')
    tc = threading.Thread(target=launchVPNClient, args=(hostname, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the client is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming VPN client is ready")
    call('ss-set net.i2cat.cnsmo.service.vpn.client.listening true')


    logger.debug("Waiting for VPN to be deployed...")
    call('ss-display \"VPN: Waiting for VPN to be established...\"')
    response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for VPN to be deployed. ready=%s" % response)
    if not response:
        logger.error("Timeout waiting for %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id)
        return -1
    logger.debug("VPN deployed")


    logger.debug("Locating VPN enabled interface...")
    time.sleep(5)
    # assuming the VPN interface (probably tap0) is the only one created during this script execution
    vpn_iface = detect_new_interface_in_30_sec(ifaces_prev)
    if not vpn_iface:
        logger.error("Timeout! Failed to locate tap interface, created by the VPN")
        call("ss-abort \"%s:Timeout! Failed to locate tap interface, created by the VPN\"" % instance_id)
        return -1
    logger.debug("VPN interface resolved: %s" % vpn_iface)

    logger.debug("Resolving IP addresses...")
    vpn_local_ipv4_address = getInterfaceIPv4Address(vpn_iface)
    vpn_local_ipv6_address = getInterfaceIPv6Address(vpn_iface)
    logger.debug("VPN using interface %s with ipaddr %s and ipv6addr %s"
                 % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))

    logger.debug("Announcing IP addresses...")
    call("ss-set vpn.address %s" % vpn_local_ipv4_address)
    call("ss-set vpn.address6 %s" % vpn_local_ipv6_address)

    logger.debug("VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s"
                 % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    call("ss-display \"VPN: VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s\""
         % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    return 0


def detect_new_interface_in_30_sec(ifaces_prev):
    vpn_iface = do_detect_new_interface(ifaces_prev)
    attempts = 0
    while not vpn_iface and attempts < 6:
        time.sleep(5)
        vpn_iface = do_detect_new_interface(ifaces_prev)
        attempts += 1
    return vpn_iface


def do_detect_new_interface(ifaces_prev):
    vpn_iface = None
    for current_iface in getCurrentInterfaces():
        if current_iface not in ifaces_prev:
            vpn_iface = current_iface
    return vpn_iface


def launchVPNClient(hostname, redis_address, instance_id):
    logger.debug("Launching VPN client...")
    call('ss-display \"VPN: Launching VPN client...\"')
    response = call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/client.py -a %s -p 9091 -r %s -s VPNClient-%s"
                    % (hostname, redis_address, instance_id))
    logger.debug("VPN client response: %s" % response)


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

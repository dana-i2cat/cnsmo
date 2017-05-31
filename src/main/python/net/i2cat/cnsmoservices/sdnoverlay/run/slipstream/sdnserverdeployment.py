#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
###

import logging
import os
import subprocess
import sys
import threading
import time

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

call = lambda command: subprocess.check_output(command, shell=True)

def main():
    config_logging()
    return deploysdn()

def deployvpn():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying SDN server on a SlipStream application...")

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    log_file = os.getcwd() + "/cnsmo/sdn.log"

    call('ss-set sdn.server.nodeinstanceid %s' % instance_id)
    logger.debug("Set sdn.server.nodeinstanceid= %s" % instance_id)

    logger.debug("Assuming SDN configurator is listening")
    call('ss-set net.i2cat.cnsmo.service.sdn.configurator.listening true')

    logger.debug("Assuming SDN server is listening")
    call('ss-set net.i2cat.cnsmo.service.sdn.server.listening true')

    # Wait for configurator and server to be ready
    call('ss-get net.i2cat.cnsmo.service.sdn.configurator.listening')
    call('ss-get net.i2cat.cnsmo.service.sdn.server.listening')



    ##### Wait for clients  [required for a correct working when join scenario with load balancer service]
    logger.debug("Detecting all SDN clients...")
    call('ss-display \"SDN: Looking for all clients...\"')
    # All instances in the deployment are considered vpn clients
    # except the slipstream orchestrator and the one running the vpn server
    all_instances = ss_getinstances()
    # remove slipstream orchestrator instances
    client_instances = [x for x in all_instances if not x.startswith("orchestrator")]
    # remove this instance
    client_instances.remove(instance_id)
    logger.debug("Finished detecting all SDN clients: %s" % client_instances)
    logger.debug("Waiting for all SDN clients...")
    call('ss-display \"SDN: Waiting for all clients...\"')
    # wait for clients to be ready: instance_id:net.i2cat.cnsmo.service.vpn.client.waiting=true
    for client_id in client_instances:
        logger.debug("Waiting for SDN client %s" % client_id)
        response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.sdn.client.listening" % client_id).rstrip("\n")
        if not response:
            logger.error("Timeout! Waiting for SDN client %s" % client_id)
            return -1
        logger.debug("Finished waiting for all SDN clients.")


    logger.debug("Locating VPN enabled interface...")
    call('ss-display \"VPN: Waiting before Locating VPN enabled interface...\"')
    time.sleep(15)
    # assuming the VPN interface (probably tap0) is the only one created during this script execution
    vpn_iface = detect_new_interface_in_30_sec(ifaces_prev)
    if not vpn_iface:
        logger.error("Timeout! Failed to locate tap interface, created by the VPN")
        call("ss-abort \"%s:Timeout! Failed to locate tap interface, created by the VPN\"" % instance_id)
        return -1

    logger.debug("Resolving IP addresses...")
    call('ss-display \"VPN: Resolving IP addresses...\"')
    vpn_local_ipv4_address = getInterfaceIPv4Address(vpn_iface)
    vpn_local_ipv6_address = ""
    vpn_local_ipv6_address = getInterfaceIPv6Address(vpn_iface)
    logger.debug("VPN using interface %s with ipaddr %s and ipv6addr %s" % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    logger.debug("Announcing IP addresses...")
    call('ss-display \"VPN: Announcing IP addresses...\"')
    if not vpn_local_ipv4_address:
        call("ss-abort \"%s:Timeout! Failed to obtain ipv4\"" % instance_id)
        return -1
    call("ss-set vpn.address %s" % vpn_local_ipv4_address)
    if vpn_local_ipv6_address:
        call("ss-set vpn.address6 %s" % vpn_local_ipv6_address)


    # Communicate that the VPN has been established
    logger.debug("Announcing vpn service has been deployed")
    call('ss-set net.i2cat.cnsmo.service.vpn.ready true')
    logger.debug("Set net.i2cat.cnsmo.service.vpn.ready=true")

    logger.debug("VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s" % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    call("ss-display \"VPN: VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s\"" % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))

    return 0

def config_logging():
    logging.basicConfig(filename='cnsmo-sdn-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

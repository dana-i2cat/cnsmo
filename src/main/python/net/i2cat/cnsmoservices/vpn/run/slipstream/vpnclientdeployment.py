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


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running VPN client deployment script...")
    return deployvpn()


def deployvpn(netservices):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying VPN client on a SlipStream application...")

    ifaces_prev = getCurrentInterfaces()
    logger.debug("Got current interfaces: %s" % ifaces_prev)

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    log_file = os.getcwd() + "/cnsmo/vpn.log"

    logger.debug("Resolving vpn.server.nodeinstanceid...")
    server_instance_id = call('ss-get --timeout=1200 vpn.server.nodeinstanceid').rstrip('\n')
    if not server_instance_id:
        logger.error("Timeout waiting for vpn.server.nodeinstanceid")
        # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return -1
    logger.debug("Got vpn.server.nodeinstanceid= %s" % server_instance_id)

    logger.debug("Waiting for CNSMO...")
    call('ss-display \"Waiting for CNSMO...\"')
    response_cnsmo = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for CNSMO. %s:net.i2cat.cnsmo.core.ready= %s" % (server_instance_id, response_cnsmo))

    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')
    logger.debug("Got %s:net.i2cat.cnsmo.dss.address= %s" % (server_instance_id, redis_address))

    logger.debug("Deploying VPN components...")
    call('ss-display \"Deploying VPN components...\"')

    logger.debug("Waiting for VPN orchestrator...")
    call('ss-display \"VPN: Waiting for VPN orchestrator...\"')

    response_orch = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.orchestrator.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for VPN orchestrator.")
    if not response_orch:
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
    response_vpn = call("ss-get --timeout=18000 %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for VPN to be deployed. ready=%s" % response_vpn)
    if not response_vpn:
        logger.error("Timeout waiting for %s:net.i2cat.cnsmo.service.vpn.ready" % server_instance_id)
        return -1
    logger.debug("VPN deployed")
    call('ss-display \"VPN: Finished Waiting for VPN to be deployed...\"')

    logger.debug("Locating VPN enabled interface...")
    time.sleep(5)
    # assuming the VPN interface (probably tap0) is the only one created during this script execution
    vpn_iface = detect_new_interface_in_half_hour(ifaces_prev)
    if not vpn_iface:
        logger.error("Timeout! Failed to locate tap interface, created by the VPN")
        call("ss-abort \"%s:Timeout! Failed to locate tap interface, created by the VPN\"" % instance_id)
        return -1
    logger.debug("VPN interface resolved: %s" % vpn_iface)

    logger.debug("Resolving IP addresses...")
    vpn_local_ipv4_address = getInterfaceIPv4Address(vpn_iface)
    vpn_local_ipv6_address = ""
    vpn_local_ipv6_address = getInterfaceIPv6Address(vpn_iface)
    logger.debug("VPN using interface %s with ipaddr %s and ipv6addr %s" % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))

    logger.debug("Announcing IP addresses...")
    call("ss-set vpn.address %s" % vpn_local_ipv4_address)
    if vpn_local_ipv6_address:
        call("ss-set vpn.address6 %s" % vpn_local_ipv6_address)

    logger.debug("VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s"
                 % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))
    call("ss-display \"VPN: VPN has been established! Using interface %s with ipaddr %s and ipv6addr %s\""
         % (vpn_iface, vpn_local_ipv4_address, vpn_local_ipv6_address))


    #copying resolv.conf from docker to host machine
    #logger.debug("Setting DNS server address in Client...")
    #call('ss-display \"VPN: Setting DNS server address in Client...\"')
    if 'dns' in netservices:
        #container_name must be equal to the name of docker container used for the vpn
        configure_resolvconf("client-vpn")

    return 0


def detect_new_interface_in_half_hour(ifaces_prev):
    vpn_iface = do_detect_new_interface(ifaces_prev)
    attempts = 0
    while not vpn_iface and attempts < 180:
        time.sleep(10)
        vpn_iface = do_detect_new_interface(ifaces_prev)
        attempts += 1
    return vpn_iface


def do_detect_new_interface(ifaces_prev):
    logger = logging.getLogger(__name__)
    vpn_iface = None
    call("ss-display \"VPN: detecting new interface... new attempt\"")
    for current_iface in getCurrentInterfaces():
        logger.debug("found iface ... %s" % current_iface)
        if ("tap" in current_iface) and (current_iface not in ifaces_prev):
            vpn_iface = current_iface
    return vpn_iface


def launchVPNClient(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching VPN client...")
    call('ss-display \"VPN: Launching VPN client...\"')
    response = call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/client.py -a %s -p 20091 -r %s -s VPNClient-%s"
                    % (hostname, redis_address, instance_id))
    logger.debug("VPN client response: %s" % response)


def getCurrentInterfaces():
    return call("""ls /sys/class/net | sed -e s/^\(.*\)$/\1/ | paste -sd ','""").rstrip('\n').split(',')


def getInterfaceIPv4Address(iface):
    return call("ifconfig " + iface + " | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'").rstrip('\n')


def getInterfaceIPv6Address(iface):
    return (call("ifconfig " + iface + "| awk '/inet6 / { print $3 }'").rstrip('\n').split('/'))[0]

def configure_resolvconf(container_name):
    logger = logging.getLogger(__name__)
    #copy resolv.conf from container
    filepath_in_container = "/etc/resolv.conf"
    copied_resolvconf = "/etc/resolvconf/resolv.conf.d/copy.conf"
    resolvconf_head_file = "/etc/resolvconf/resolv.conf.d/head"
    call("docker cp %s:%s %s" % (container_name,filepath_in_container,copied_resolvconf))
    #extract nameserver lines from copied file
    lines = []
    lines = extract_lines(copied_resolvconf)
    #TODO: GET LINES FROM DOCKER CONTAINER RESOLVECONF
    call("touch %s" % resolvconf_head_file)
    for l in lines:
        logger.debug("nameserver line %s" % l)
        add_line(resolvconf_head_file, l)
    call("service resolvconf restart")

def extract_lines(file_name):
    logger = logging.getLogger(__name__)
    lines =[]
    with open(file_name) as fh:
        logger.debug("opened file %s" % file_name)
        for line in fh:
            lines.append(line)
    return lines

def add_line(file_name,line):
    with open(file_name, 'a') as file:
        file.writelines(line) 


def logToFile(message, filename, filemode):
    f = None
    try:
        f = open(filename, filemode)
        f.write(message)
    finally:
        if f:
            f.close()


def config_logging():
    logging.basicConfig(filename='cnsmo-vpn-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

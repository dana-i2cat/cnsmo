#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# net.i2cat.cnsmo.service.sdn.allowedip
# net.i2cat.cnsmo.service.sdn.allowedport
#
# Output parameters:
# net.i2cat.cnsmo.core.ready: Used to communicate CNSMO core is ready.
# net.i2cat.cnsmo.dss.address: Used to communicate CNSMO distributed system state address.
# net.i2cat.cnsmo.service.sdn.server.ready: Used to communicate the SDN service to be configured properly
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

callWithResp = lambda command: subprocess.check_output(command, shell=True)
call = lambda command: subprocess.call(command, shell=True)

def check_error(err):
    logger = logging.getLogger(__name__)
    if err != 0:
        logger.error("Error!")
        return -1
    return 0

def check_preconditions(sdn_server_instance_id):
    logger = logging.getLogger(__name__)

    """
    logger.debug("Resolving net.i2cat.cnsmo.service.sdn.allowedip...")
    allowed_ip_and_mask = callWithResp('ss-get --timeout=1200 net.i2cat.cnsmo.service.sdn.allowedip').rstrip('\n')
    if not allowed_ip_and_mask:
        logger.error("Timeout waiting for net.i2cat.cnsmo.service.sdn.allowedip")
        #timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return -1
    logger.debug("Got net.i2cat.cnsmo.service.sdn.allowedip= %s" % allowed_ip_and_mask)

    logger.debug("Resolving net.i2cat.cnsmo.service.sdn.allowedport...")
    allowed_port = callWithResp('ss-get --timeout=1200 net.i2cat.cnsmo.service.sdn.allowedport').rstrip('\n')
    if not allowed_port:
        logger.error("Timeout waiting for net.i2cat.cnsmo.service.sdn.allowedport")
        #timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return -1
    logger.debug("Got net.i2cat.cnsmo.service.sdn.allowedport= %s" % allowed_port)
    """

    logger.debug("Waiting for SDN to be deployed...")
    call('ss-display \"SDN: Waiting for SDN to be established...\"')
    response_sdn = callWithResp("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.sdn.server.ready" % sdn_server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for SDN to be deployed. ready=%s" % response_sdn)
    if not response_sdn:
        logger.error("Timeout waiting for %s:net.i2cat.cnsmo.service.sdn.server.ready" % sdn_server_instance_id)
        return -1
    logger.debug("SDN deployed")
    call('ss-display \"SDN: Finished Waiting for SDN to be deployed...\"')

    # Checking if ovs is installed
    inst = callWithResp("which ovs-vsctl")
    if not "ovs-vsctl" in inst:
        logger.debug("OpenvSwitch not installed!")
        return -1

    # Checking if the ovs bridge is created , if created exit
    inst = callWithResp("ifconfig")
    if "br-ext" in inst:
        logger.debug("Bridge br-ext already created!")
        return -1

    # Checking if host is connected to a bridged VPN, otherwise exit
    if not "tap" in inst:
        logger.debug("Machine not connected to a bridged VPN.")
        return -1
    return 0

def configure_bridge(NIC, IP, GW, MAC, MASK):
    totalErr = 0
    logger = logging.getLogger(__name__)
    call('ss-display \"Creating an OpenvSwitch bridge to the physical interface...\"')
    logger.debug("Creating an OpenvSwitch bridge to the physical interface...")
    err = call("sudo ovs-vsctl add-br br-ext -- set bridge br-ext other-config:hwaddr=%s > /dev/null 2>&1" % (MAC))
    totalErr = totalErr + check_error(err)
    err = call("sudo ovs-vsctl set bridge br-ext")
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")
    
    #in order to avoid being disconnected we have to execute several commands as a single script
    call('ss-display \"starting bash script temp.sh...\"')
    err = call("sudo echo \"#!/bin/bash\" >> ./temp.sh")
    totalErr = totalErr + check_error(err)
    err = call("sudo chmod +x ./temp.sh")
    totalErr = totalErr + check_error(err)
    logger.debug("Adding the physical interface to the ovs bridge...")
    call('ss-display \"Add to Bash script: Adding the physical interface to the ovs bridge...\"')
    err = call("sudo echo \"ovs-vsctl add-port br-ext %s > /dev/null 2>&1\" >> ./temp.sh" % (NIC))
    totalErr = totalErr + check_error(err)
    logger.debug("Removing IP address from the physical interface...")
    call('ss-display \"Add to Bash script: Removing IP address from the physical interface...\"')
    err = call("sudo echo \"ifconfig %s 0.0.0.0 > /dev/null 2>&1\" >> ./temp.sh" % (NIC))
    totalErr = totalErr + check_error(err)
    logger.debug("Giving the ovs bridge the host IP address...")
    call('ss-display \"Add to Bash script: Giving the ovs bridge the host IP address...\"')
    err = call("sudo echo \"ifconfig br-ext %s/%s > /dev/null 2>&1\" >> ./temp.sh" % (IP,MASK))
    totalErr = totalErr + check_error(err)

    logger.debug("Changing the interface MAC address...")
    LAST_MAC_CHAR=list(MAC)[len(MAC)-1]
    AUX=MAC[:-1]
    NL=LAST_MAC_CHAR
    if LAST_MAC_CHAR.isalpha():
        NL="1"
    else:
        NL="a"

    NEW_MAC=AUX+NL
    call('ss-display \"Add to Bash script: Configuring bridge...\"')
    err = call("sudo echo \"ifconfig %s down > /dev/null 2>&1\" >> ./temp.sh" % (NIC))
    totalErr = totalErr + check_error(err)
    err = call("sudo echo \"ifconfig %s hw ether %s > /dev/null 2>&1\" >> ./temp.sh" % (NIC,NEW_MAC))
    totalErr = totalErr + check_error(err)
    err = call("sudo echo \"ifconfig %s up > /dev/null 2>&1\" >> ./temp.sh" % (NIC))
    totalErr = totalErr + check_error(err)
    call('ss-display \"Add to Bash script: Configuring route table while loop...\"')
    logger.debug("Routing traffic through the new bridge...")
    err = call("sudo echo \"while ip route del default; do :; done\" >> ./temp.sh")
    totalErr = totalErr + check_error(err)
    call('ss-display \"Add to Bash script: Configuring route table default gw...\"')
    err = call("sudo echo \"ip route add default via %s dev br-ext > /dev/null 2>&1\" >> ./temp.sh" % (GW))
    totalErr = totalErr + check_error(err)

    call('ss-display \"Executing Bash script...\"')
    err = call("sudo ./temp.sh")
    totalErr = totalErr + check_error(err)
    call('ss-display \"Executed Bash Script...\"')

    return totalErr

def subscribe_to_controller(PROTO_SDN,SDN_CTRL_IP_PORT):
    totalErr = 0
    logger = logging.getLogger(__name__)
    
    #in order to avoid being disconnected we have to execute several commands as a single script
    call('ss-display \"starting bash script temp2.sh...\"')
    err = call("sudo echo \"#!/bin/bash\" >> ./temp2.sh")
    totalErr = totalErr + check_error(err)
    err = call("sudo chmod +x ./temp2.sh")
    totalErr = totalErr + check_error(err)

    logger.debug("Connecting OVS brige to controller...")
    call('ss-display \"Add to Bash script: Connecting OVS brige to controller...\"')
    err = call("sudo echo \"ovs-vsctl set-controller br-ext %s:%s protocols=OpenFlow10,OpenFlow12,OpenFlow13 > /dev/null 2>&1\" >> ./temp2.sh" % (PROTO_SDN,SDN_CTRL_IP_PORT))
    totalErr = totalErr + check_error(err)

    logger.debug("Updating problematic OpenFlow rules if any...")
    call('ss-display \"Add to Bash script: Updating problematic OpenFlow rules if any...\"')
    err = call("sudo echo \"ovs-ofctl del-flows br-ext > /dev/null 2>&1\" >> ./temp2.sh")
    totalErr = totalErr + check_error(err)
    err = call("sudo echo \"ovs-ofctl add-flow br-ext \"in_port=LOCAL, priority=500, actions:output=1\" > /dev/null 2>&1\" >> ./temp2.sh")
    totalErr = totalErr + check_error(err)
    err = call("sudo echo \"ovs-ofctl add-flow br-ext \"in_port=1, priority=500, actions:output=LOCAL\" > /dev/null 2>&1\" >> ./temp2.sh")
    totalErr = totalErr + check_error(err)

    call('ss-display \"Executing Bash script...\"')
    err = call("sudo ./temp2.sh")
    totalErr = totalErr + check_error(err)
    call('ss-display \"Executed Bash Script...\"')

    return totalErr


def configureOvs():
    logger = logging.getLogger(__name__)
    # Configuration values
    NIC = "eth0"    
    SDN_PORT_CONCAT=":6633"
    VPN_SERVER_IP="10.10.10.1"
    VPN_SERVER_IP= callWithResp("ss-get --timeout=3600 vpn.server.address")
    SDN_CTRL_IP_PORT=str(VPN_SERVER_IP)+str(SDN_PORT_CONCAT)
    call('ss-display \"Deploying SDN...\"')

    PROTO_SDN="tcp"
    IP = callWithResp("ip addr show %s | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1" % (NIC))
    IP = IP.split('\n')[0]
    GW = callWithResp("ip route | grep default | awk '{{print $3}}'")
    GW = GW.split('\n')[0]
    MAC = callWithResp("ifconfig %s | grep 'HWaddr ' | awk '{{print $5}}'" % (NIC))
    MAC = MAC.split('\n')[0]
    MASK = callWithResp("ip addr show %s | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f2" % (NIC))
    MASK = MASK.split('\n')[0]

    # Configure OVS bridge
    call('ss-display \"Configuring SDN bridge...\"')
    totalErr = configure_bridge(NIC, IP, GW, MAC, MASK)

    call('ss-display \"Subscribing to controller...\"')
    totalErr = totalErr + subscribe_to_controller(PROTO_SDN,SDN_CTRL_IP_PORT)

    call('ss-display \"SDN ovs bridge configured successfully\"')
    
    logger.debug("Assuming SDN client is ready")
    return totalErr

def config_logging():
    logging.basicConfig(filename='cnsmo-sdn-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running SDN client deployment script...")
    err = check_preconditions()
    if err == 0:
        configureOvs()
    else:
        logger.debug("::: ERROR ::: Preconditions not fully satisfied")
        return -1

if __name__ == "__main__":
    main()

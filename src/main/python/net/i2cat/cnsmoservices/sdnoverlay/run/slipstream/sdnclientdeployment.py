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

call = lambda command: subprocess.call(command, shell=True)

def check_error(err):
    logger = logging.getLogger(__name__)
    if err == "0":
        logger.error("Error!")
        return -1
    return 0

def check_preconditions():
    logger = logging.getLogger(__name__)

    # Checking if ovs is installed
    inst = call("which ovs-vsctl > /dev/null 2>&1")
    if inst != 0:
        logger.debug("OpenvSwitch not installed!")
        return -1

    # Checking if the ovs bridge is created, if created exit
    inst = call("ifconfig | grep br-ext > /dev/null 2>&1")
    if inst == 0:
        logger.debug("Bridge br-ext already created!")
        return -1

    # Checking if host is connected to a bridged VPN, otherwise exit
    inst = call("ifconfig | grep tap  > /dev/null 2>&1")
    if inst == 0:
        logger.debug("Machine not connected to a bridged VPN.")
        return -1
    return 0

def configure_bridge(NIC, IP, GW, MAC, MASK):
    totalErr = 0
    logger = logging.getLogger(__name__)
    logger.debug("Creating an OpenvSwitch bridge to the physical interface...")
    err = subprocess.call("sudo ovs-vsctl add-br br-ext -- set bridge br-ext other-config:hwaddr=%s > /dev/null 2>&1" % (MAC), shell=True)
    totalErr = totalErr + check_error(err)
    err = subprocess.call("sudo ovs-vsctl set bridge br-ext protocols=OpenFlow10,OpenFlow12,OpenFlow13", shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Adding the physical interface to the ovs bridge...")
    err = subprocess.call("sudo ovs-vsctl add-port br-ext %s > /dev/null 2>&1" % (NIC), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Adding the VPN interface to the ovs bridge...")
    err = subprocess.call("sudo ovs-vsctl add-port br-ext tap0 > /dev/null 2>&1", shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Removing IP address from the physical interface...")
    err = subprocess.call("sudo ifconfig %s 0.0.0.0 > /dev/null 2>&1" % (NIC), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Giving the ovs bridge the host IP address...")
    err = subprocess.call("sudo ifconfig br-ext %s/%s > /dev/null 2>&1" % (IP,MASK), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Changing the interface MAC address...")
    LAST_MAC_CHAR=list(MAC)[len(MAC)-1]
    AUX=MAC[:-1]
    NL=LAST_MAC_CHAR
    if LAST_MAC_CHAR.isalpha():
        NL="1"
    else:
        NL="a"

    NEW_MAC=AUX+NL
    call('ss-display \"Configuring bridge and route table...\"')
    err = subprocess.call("sudo ifconfig %s down > /dev/null 2>&1" % (NIC), shell=True)
    totalErr = totalErr + check_error(err)
    err = subprocess.call("sudo ifconfig %s hw ether %s > /dev/null 2>&1" % (NIC,NEW_MAC), shell=True)
    totalErr = totalErr + check_error(err)
    err = subprocess.call("sudo ifconfig %s up > /dev/null 2>&1" % (NIC), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Routing traffic through the new bridge...")

    while (subprocess.call("sudo ip route del default > /dev/null 2>&1", shell=True) == 0):
        pass

    err = subprocess.call("sudo ip route add default via %s dev br-ext > /dev/null 2>&1" % (GW), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")
    return totalErr


def configure_ovs():
    logger = logging.getLogger(__name__)
    # Configuration values
    NIC = "eth0"    
    SDN_PORT_CONCAT=":6633"
    SDN_CTRL_IP=call("ss-get --timeout=3600 vpn.server.address")
    SDN_CTRL_IP=SDN_CTRL_IP+SDN_PORT_CONCAT
    #SDN_CTRL_IP="10.8.44.55:6633"
    call('ss-display \"Deploying SDN...\"')

    PROTO_SDN="tcp"
    IP = subprocess.check_output("ip addr show %s | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1" % (NIC), shell=True)
    IP = IP.split('\n')[0]
    GW = subprocess.check_output("ip route | grep default | awk '{{print $3}}'", shell=True)
    GW = GW.split('\n')[0]
    MAC = subprocess.check_output("ifconfig %s | grep 'HWaddr ' | awk '{{print $5}}'" % (NIC), shell=True)
    MAC = MAC.split('\n')[0]
    MASK = subprocess.check_output("ip addr show %s | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f2" % (NIC), shell=True)
    MASK = MASK.split('\n')[0]

    # Configure OVS bridge
    call('ss-display \"Configuring SDN bridge...\"')
    totalErr = configure_bridge(NIC, IP, GW, MAC, MASK)

    # Connect OVS and update rules
    logger.debug("Connecting OVS brige to controller...")
    err = subprocess.call("sudo ovs-vsctl set-controller br-ext %s:%s> /dev/null 2>&1" % (PROTO_SDN,SDN_CTRL_IP), shell=True)
    totalErr = totalErr + check_error(err)
    logger.debug("Done!")

    logger.debug("Updating problematic OpenFlow rules if any...")
    time.sleep(5)
    subprocess.call('sudo ovs-ofctl mod-flows br-ext "actions:output=1" > /dev/null 2>&1', shell=True)
    subprocess.call('sudo ovs-ofctl mod-flows br-ext "in_port=1, actions:output=LOCAL" > /dev/null 2>&1', shell=True)
    logger.debug("Done!")
    call('ss-display \"SDN ovs bridge configured successfully\"')
    
    logger.debug("Assuming SDN client is ready")
    call('ss-set net.i2cat.cnsmo.service.sdn.client.listening true')
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
        return configure_ovs()
    else:
        logger.debug("::: ERROR ::: Configuring")
        return -1

if __name__ == "__main__":
    main()

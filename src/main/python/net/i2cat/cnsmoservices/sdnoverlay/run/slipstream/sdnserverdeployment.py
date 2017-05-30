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

from src.main.python.net.i2cat.cnsmoservices.sdn.manager.sdn import SDNManager

call = lambda command: subprocess.call(command, shell=True)

def check_error(err):
    logger = logging.getLogger(__name__)
    if err != "0":
        logger.error("Error!")
        return -1

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

def configure_bridge(NIC, IP, GW, MAC, MASK):
    logger.debug("Creating an OpenvSwitch bridge to the physical interface...")
    err = subprocess.call("sudo ovs-vsctl add-br br-ext -- set bridge br-ext other-config:hwaddr=%s > /dev/null 2>&1" % (MAC), shell=True)
    check_error(err)
    err = subprocess.call("sudo ovs-vsctl set bridge br-ext protocols=OpenFlow10,OpenFlow12,OpenFlow13", shell=True)
    check_error(err)
    logger.debug("Done!")

    logger.debug("Adding the physical interface to the ovs bridge...")
    err = subprocess.call("sudo ovs-vsctl add-port br-ext %s > /dev/null 2>&1" % (NIC), shell=True)
    check_error(err)
    logger.debug("Done!")

    logger.debug("Adding the VPN interface to the ovs bridge...")
    err = subprocess.call("sudo ovs-vsctl add-port br-ext tap0 > /dev/null 2>&1", shell=True)
    check_error(err)
    logger.debug("Done!")

    logger.debug("Removing IP address from the physical interface...")
    err = subprocess.call("sudo ifconfig %s 0.0.0.0 > /dev/null 2>&1" % (NIC), shell=True)
    check_error(err)
    logger.debug("Done!")

logger.debug("Giving the ovs bridge the host IP address...")
err = subprocess.call("sudo ifconfig br-ext %s/%s > /dev/null 2>&1" % (IP,MASK), shell=True)
check_error(err)
logger.debug("Done!")

logger.debug("Changing the interface MAC address...")
subprocess.call("LAST_MAC_CHAR=${%s:(-1)}" % (MAC), shell=True)

LAST_MAC_CHAR=${MAC:(-1)}
AUX="${MAC:0:${#MAC}-1}"
if [ "$LAST_MAC_CHAR" -eq "$LAST_MAC_CHAR" ] 2>/dev/null; then
NL="a"
else
NL="1"
fi

def configure_ovs():
    logger = logging.getLogger(__name__)

    # Configuration values
    NIC = "eth0"    
    SDN_CTRL_IP="10.8.44.55:6633"
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
    configure_bridge(NIC, IP, GW, MAC, MASK)




if __name__ == "__main__":
    main()

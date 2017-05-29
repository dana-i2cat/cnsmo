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

def  check_error(err):
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
    inst = call("$(ifconfig | grep br-ext > /dev/null 2>&1 )")
    if inst == 0:
        logger.debug("Bridge br-ext already created!")
        return -1

    # Checking if host is connected to a bridged VPN, otherwise exit
    inst = call("$(ifconfig | grep tap  > /dev/null 2>&1)")
    if inst == 0:
        logger.debug("Machine not connected to a bridged VPN.")
        return -1

def configure_ovs():
    # Configuration values
    NIC = "eth0"
    SDN_CTRL_IP="10.8.44.55:6633"
    PROTO_SDN="tcp"
    IP = subprocess.check_output("$(ip addr show $NIC | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1)", shell=True)
    GW = subprocess.check_output("$(ip route | grep default | awk '{print $3}')", shell=True)
    MAC = subprocess.check_output("$(ifconfig $NIC | grep 'HWaddr\b' | awk '{print $5}')", shell=True)
    MASK = subprocess.check_output("$(ip addr show $NIC | grep 'inet\b' | awk '{print $2}' | cut -d/ -f2)", shell=True)



def main():
    config_logging()
    return deploysdn()


def deploysdn():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying SDN server on a SlipStream application...")

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    log_file = os.getcwd() + "/cnsmo/sdn.log"

    ifaces_prev = getCurrentInterfaces()
    logger.debug("Got current interfaces: %s" % ifaces_prev)

    call('ss-set vpn.server.nodeinstanceid %s' % instance_id)
    logger.debug("Set vpn.server.nodeinstanceid= %s" % instance_id)

    # wait for CNSMO core
    logger.debug("Waiting for CNSMO...")
    response_cnsmo = call('ss-get net.i2cat.cnsmo.core.ready').rstrip('\n')
    logger.debug("Finished waiting for CNSMO. net.i2cat.cnsmo.core.ready= %s" % response_cnsmo)

    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get net.i2cat.cnsmo.dss.address").rstrip('\n')
    logger.debug("Got net.i2cat.cnsmo.dss.address= %s" % redis_address)

    logger.debug("Deploying VPN components...")
    call('ss-display \"Deploying VPN components...\"')


    # Launch VPN orchestrator
    logger.debug("Launching VPN orchestrator...")
    call('ss-display \"VPN: Launching VPN orchestrator...\"')
    vpn_orchestrator = VPNManager(redis_address)
    to = threading.Thread(target=vpn_orchestrator.start)
    to.start()
    # TODO implement proper way to detect when the orchestrator is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming VPN orchestrator is ready")
    call('ss-set net.i2cat.cnsmo.service.vpn.orchestrator.ready true')

    # Wait for orchestrator
    call('ss-get net.i2cat.cnsmo.service.vpn.orchestrator.ready')
    # Launch the rest of VPN services

    # Launch VPN configurator
    tc = threading.Thread(target=launchVPNConfigurator, args=(hostname, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the configurator is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming VPN configurator is listening")
    call('ss-set net.i2cat.cnsmo.service.vpn.configurator.listening true')

    # Launch VPN server
    ts = threading.Thread(target=launchVPNServer, args=(hostname, redis_address, instance_id))
    ts.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming VPN server is listening")
    call('ss-set net.i2cat.cnsmo.service.vpn.server.listening true')


    # Wait for configurator and server to be ready
    call('ss-get net.i2cat.cnsmo.service.vpn.configurator.listening')
    call('ss-get net.i2cat.cnsmo.service.vpn.server.listening')

    ##### Wait for clients  [required for a correct working when join scenario with load balancer service]
    logger.debug("Detecting all VPN clients...")
    call('ss-display \"VPN: Looking for all clients...\"')
    # All instances in the deployment are considered vpn clients
    # except the slipstream orchestrator and the one running the vpn server
    all_instances = ss_getinstances()
    # remove slipstream orchestrator instances
    client_instances = [x for x in all_instances if not x.startswith("orchestrator")]
    # remove this instance
    client_instances.remove(instance_id)
    logger.debug("Finished detecting all VPN clients: %s" % client_instances)
    logger.debug("Waiting for all VPN clients...")
    call('ss-display \"VPN: Waiting for all clients...\"')
    # wait for clients to be ready: instance_id:net.i2cat.cnsmo.service.vpn.client.waiting=true
    for client_id in client_instances:
        logger.debug("Waiting for VPN client %s" % client_id)
        response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.client.listening" % client_id).rstrip("\n")
        if not response:
            logger.error("Timeout! Waiting for VPN client %s" % client_id)
            return -1
        logger.debug("Finished waiting for all VPN clients.")


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


def detect_new_interface_in_30_sec(ifaces_prev):
    vpn_iface = do_detect_new_interface(ifaces_prev)
    attempts = 0
    while not vpn_iface and attempts < 50:
        time.sleep(5)
        vpn_iface = do_detect_new_interface(ifaces_prev)
        attempts += 1
    return vpn_iface


def do_detect_new_interface(ifaces_prev):
    logger = logging.getLogger(__name__)
    call("ss-display \"SDN: detecting new interface... new attempt\"")
    vpn_iface = None
    for current_iface in getCurrentInterfaces():
        logger.debug("found iface ... %s" % current_iface)
        if ("tap" in current_iface) and (current_iface not in ifaces_prev):
            vpn_iface = current_iface
    return vpn_iface


def launchRedis(hostname, dss_port):
    call('ss-display \"Launching REDIS...\"')
    call('redis-server')


def launchSystemState(hostname, dss_port):
    call('ss-display \"Launching CNSMO...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/systemstate.py -a %s -p %s" % (hostname, dss_port))


def launchVPNConfigurator(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching VPN configurator...")
    call('ss-display \"VPN: Launching VPN configurator...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/configurator.py -a %s -p 20093 -r %s -s VPNConfigurator-%s --vpn-server-ip %s --vpn-server-port 9004 --vpn-address 10.10.10.0 --vpn-mask 255.255.255.0" % (hostname, redis_address, instance_id, hostname))


def launchVPNServer(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching VPN server...")
    call('ss-display \"VPN: Launching VPN server...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/vpn/run/server.py -a %s -p 20092 -r %s -s VPNServer-%s" % (hostname, redis_address, instance_id))


def getCurrentInterfaces():
    logger = logging.getLogger(__name__)
    logger.debug("asking current interfaces")
    return call("""ls /sys/class/net | sed -e s/^\(.*\)$/\1/ | paste -sd ','""").rstrip('\n').split(',')


def getInterfaceIPv4Address(iface):
    logger = logging.getLogger(__name__)
    call("ss-display \"VPN: begin getting Interface IP... \"")
    ip = call("ip addr show " + iface + " | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1")
    logger.debug("found ip ... %s" % ip)
    call("ss-display \"VPN: getting Interface IP... atempt 0  \"")
    attempts = 0
    while not ip and attempts < 50:
        time.sleep(5)
        ip = call("ifconfig " + iface + " | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'").rstrip('\n')
        #line = call("ip addr show " + iface + " | grep 'inet\b' | awk '{print $2}' | cut -d/ -f1").rstrip('\n')
        line = call("ip addr show " + iface).rstrip('\n')
        logger.debug("found ip ... %s" % ip)
        logger.debug("found line ... %s" % line)
        call("ss-display \"VPN: getting Interface IP...new atempt \"")
        attempts += 1
    call("ss-display \"VPN: returning IP... %s \"" % ip )
    return ip


def getInterfaceIPv6Address(iface):
    logger = logging.getLogger(__name__)
    #ip = call("ip addr show " + iface + " | grep 'inet6\b' | awk '{print $2}' | cut -d/ -f1")
    ip = (call("ifconfig " + iface + "| awk '/inet6 / { print $3 }'").rstrip('\n').split('/'))[0]
    logger.debug("found ip ... %s" % ip)
    return ip

# Gets the instances that compose the deployment
# NOTE: Currently there is no way to directly retrieve all nodes intances in a deployment.
#       As of now we have to find them out by parsing the ss:groups, and then the node's
#       <nodename>:<id> runtime parameters.
#       There is an issue to implement this enhancement: https://github.com/slipstream/SlipStreamServer/issues/628
def ss_getinstances():
    # ss:groups  cyclone-fr2:VPN,cyclone-fr1:client2,cyclone-fr2:client1

    groups = call("ss-get ss:groups").rstrip('\n')
    cloud_node_pairs = groups.split(",")

    nodes = list()
    for pair in cloud_node_pairs:
        nodes.append(pair.split(":")[1])

    # nodes = VPN, client2, client1

    indexes = dict()
    # client1:ids     1,2
    for node in nodes:
        indexes[node] = call("ss-get %s:ids" % node).split(",")

    # {"client1":["1","2"]}
    instances = list()
    for node, node_indexes in indexes.iteritems():
        for index in node_indexes:
            instances.append(node + "." + index.rstrip('\n'))

    return instances


def config_logging():
    logging.basicConfig(filename='cnsmo-vpn-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

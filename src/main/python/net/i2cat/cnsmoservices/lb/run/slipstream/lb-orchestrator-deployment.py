#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# lb.port: Indicates the tcp port to load balance
# lb.node: Indicates tne SlipStream node whose instances will be load balanced.
# lb.mode: Indicates the load balancer mode. Accepted values: leastconn/roundrobin/source. Defaults to leastconn.
#
# Output parameters:
# net.i2cat.cnsmo.core.ready: Used to communicate CNSMO core is ready.
# net.i2cat.cnsmo.dss.address: Used to communicate CNSMO distributted system state address.
# net.i2cat.cnsmo.service.lb.ready: Used to communicate LB service is ready
###

import os
import subprocess
import sys
import threading
import time

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmoservices.lb.run.orchestrator import deploy_lb

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    # deploycnsmo()
    deploylb()


def deploycnsmo():
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    log_file = os.getcwd() + "/cnsmo/lb.log"

    hostname = call('ss-get hostname').rstrip('\n')
    dss_port = "6379"
    redis_address = "%s:%s" % (hostname, dss_port)

    date = call('date')
    logToFile("Launching CNSMO at %s" % date, log_file, "w+")


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


def deploylb():
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    log_file = os.getcwd() + "/cnsmo/lb.log"

    # wait for CNSMO core
    call('ss-get net.i2cat.cnsmo.core.ready')
    redis_address = call("ss-get net.i2cat.cnsmo.dss.address").rstrip('\n')

    date = call('date')
    logToFile("Gathering LB input at %s" % date, log_file, "w+")
    call('ss-display \"LB: Gathering LB input...\"')

    # retrieve instances to be load balanced:
    # 1. Retrieve port to lb with ss-get
    lb_port = call('ss-get lb.port').rstrip('\n')

    # 2. Retrieve lb_mode with ss-get (defaults to leastconn)
    lb_mode = call('ss-get lb.mode').rstrip('\n')
    if not lb_mode:
        lb_mode = "leastconn"

    # 3. Retrieve role to lb with ss-get
    role_to_lb = call('ss-get lb.node').rstrip('\n')

    # 4. Retrieve instances with role to lb
    instances_to_lb = ss_getinstances([role_to_lb])

    # 5. Retrieve IP addresses for that instances
    # Assuming the ip address is the public one!!!
    ips_to_lb = list()
    for instance in instances_to_lb:
        # never use lb_address as a lb_backend_server
        if instance != instance_id:
            ips_to_lb.append(call('ss-get %s:hostname' % instance).rstrip('\n'))

    # 6. Build comma-separated list of ip:port to balance
    lb_backend_servers = [x + ":" + lb_port for x in ips_to_lb]

    logToFile("LB port: " + lb_port)
    logToFile("LB mode: " + lb_mode)
    logToFile("LB backend servers: " + str(lb_backend_servers))

    # 7. Retrieve IP address of the LB with ss-get hostname (already done)

    # 8. Check hostname is not a lb_backend_server
    if hostname + ":" + lb_port in lb_backend_servers:
        call("ss-abort \"%s:Invalid input. Can't use LB address as backend address!\"")

    # Launch orchestrator with gathered data
    date = call('date')
    logToFile("Deploying LB at %s" % date, log_file, "a")
    call('ss-display \"LB: Launching LB orchestrator...\"')
    deploy_lb(hostname, redis_address, lb_port, lb_mode, lb_backend_servers)

    call('ss-set net.i2cat.cnsmo.service.lb.ready true')
    call('ss-display \"LB: LB has been deployed!\"')

    date = call('date')
    logToFile("LB deployed at %s" % date, log_file, "a")


def launchRedis(hostname, dss_port):
    call('ss-display \"Launching REDIS...\"')
    call('redis-server')


def launchSystemState(hostname, dss_port):
    call('ss-display \"Launching CNSMO...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmo/run/systemstate.py -a %s -p %s" % (hostname, dss_port))


def logToFile(message, filename, filemode):
    f = None
    try:
        f = open(filename, filemode)
        f.write(message)
    finally:
        if f:
            f.close()


# Gets the instances that compose the deployment
# NOTE: Currently there is no way to directly retrieve all nodes intances in a deployment.
#       As of now we have to find them out by parsing the ss:groups, and then the node's
#       <nodename>:<id> runtime parameters.
#       There is an issue to implement this enhancement: https://github.com/slipstream/SlipStreamServer/issues/628
def ss_getinstances(included_node_names):

    # ss:groups  cyclone-fr2:VPN,cyclone-fr1:client2,cyclone-fr2:client1
    groups = call("ss-get ss:groups").rstrip('\n')
    cloud_node_pairs = groups.split(",")

    nodes = list()
    for pair in cloud_node_pairs:
        current_node_name = pair.split(":")[1]
        if current_node_name in included_node_names:
            nodes.append(current_node_name)

    # nodes = VPN, client2, client1

    indexes = dict()
    # client1:ids     1,2
    for node in nodes:
        indexes[node] = call("ss-get %s:ids" % node).split(",")

    # indexes = {"client1":["1","2"]}
    instances = list()
    for node, node_indexes in indexes.iteritems():
        for index in node_indexes:
            instances.append(node + "." + index.rstrip('\n'))

    return instances

main()

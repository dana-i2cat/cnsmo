#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# lb.port: Indicates the tcp port to load balance
# lb.node: Indicates the SlipStream node whose instances will be load balanced.
# lb.mode: Indicates the load balancer mode. Accepted values: leastconn/roundrobin/source. Defaults to leastconn.
#
# Output parameters:
# net.i2cat.cnsmo.core.ready: Used to communicate CNSMO core is ready.
# net.i2cat.cnsmo.dss.address: Used to communicate CNSMO distributted system state address.
# net.i2cat.cnsmo.service.lb.ready: Used to communicate LB service is ready
###

import json
import logging
import os
import subprocess
import sys

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmoservices.lb.run.orchestrator import deploy_lb

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running LB deployment script...")
    return deploylb()


def deploylb():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying LB orchestrator on a SlipStream application...")

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')

    # wait for CNSMO core
    logger.debug("Waiting for CNSMO...")
    response = call('ss-get net.i2cat.cnsmo.core.ready').rstrip('\n')
    logger.debug("Finished waiting for CNSMO. net.i2cat.cnsmo.core.ready= %s" % response)

    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get net.i2cat.cnsmo.dss.address").rstrip('\n')
    logger.debug("Got net.i2cat.cnsmo.dss.address= %s" % redis_address)

    logger.debug("Gathering LB input...")
    call('ss-display \"LB: Gathering LB input...\"')

    # retrieve instances to be load balanced:
    # 1. Retrieve port to lb with ss-get
    lb_port = call('ss-get lb.port').rstrip('\n')
    logger.debug("Got lb.port = %s" % lb_port)

    # 2. Retrieve lb_mode with ss-get (defaults to leastconn)
    lb_mode = call('ss-get lb.mode').rstrip('\n')
    if not lb_mode:
        lb_mode = "leastconn"
    logger.debug("Got lb.mode = %s" % lb_port)

    # 3. Retrieve role to lb with ss-get
    role_to_lb = call('ss-get lb.node').rstrip('\n')
    logger.debug("Got lb.node = %s" % role_to_lb)

    # 4. Retrieve instances with role to lb
    logger.debug("Retrieving instances to load balance...")
    instances_to_lb = ss_getinstances([role_to_lb])
    logger.debug("Got instances to load balance = %s" % json.dumps(instances_to_lb))


    # 5. Retrieve IP addresses for that instances
    logger.debug("Retrieving their IP addresses...")
    # Assuming the ip address is the public one!!!
    ips_to_lb = list()
    for instance in instances_to_lb:
        # never use lb_address as a lb_backend_server
        if instance != instance_id:
            ips_to_lb.append(call('ss-get %s:hostname' % instance).rstrip('\n'))

    # 6. Build comma-separated list of ip:port to balance
    lb_backend_servers = [x + ":" + lb_port for x in ips_to_lb]

    logger.debug("Got following LB configuration")
    logger.debug("LB port: " + lb_port)
    logger.debug("LB mode: " + lb_mode)
    logger.debug("LB backend servers: " + str(lb_backend_servers))

    # 7. Retrieve IP address of the LB with ss-get hostname (already done)

    # 8. Check hostname is not a lb_backend_server
    if hostname + ":" + lb_port in lb_backend_servers:
        logger.error("Invalid input. Can't use LB address as backend address!")
        call("ss-abort \"%s:Invalid input. Can't use LB address as backend address!\"" % instance_id)

    # Launch orchestrator with gathered data
    logger.debug("Deploying LB...")
    call('ss-display \"LB: Launching LB orchestrator...\"')
    deploy_lb(hostname, redis_address, lb_port, lb_mode, lb_backend_servers)

    logger.debug("Assuming LB service is ready")
    call('ss-set net.i2cat.cnsmo.service.lb.ready true')
    call('ss-display \"LB: LB has been deployed!\"')

    logger.debug("LB deployed!")
    return 0


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


def config_logging():
    logging.basicConfig(filename='cnsmo-lb-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

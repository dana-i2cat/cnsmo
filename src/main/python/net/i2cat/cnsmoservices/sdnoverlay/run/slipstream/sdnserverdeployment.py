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

def deploysdn():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying SDN server on a SlipStream application...")

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    log_file = os.getcwd() + "/cnsmo/sdn.log"

    call('ss-set sdn.server.nodeinstanceid %s' % instance_id)
    logger.debug("Set sdn.server.nodeinstanceid= %s" % instance_id)

    # Launch SDN server
    logger.debug("Assuming SDN server is listening")
    call('ss-set net.i2cat.cnsmo.service.sdn.server.listening true')

    # Wait for configurator and server to be ready
    call('ss-get net.i2cat.cnsmo.service.sdn.server.listening')

    ##### Wait for clients  [required for a correct working when join scenario with load balancer service]
    logger.debug("Detecting all SDN clients...")
    call('ss-display \"SDN: Looking for all clients...\"')
    # All instances in the deployment are considered sdn clients
    # except the slipstream orchestrator and the one running the sdn server
    all_instances = ss_getinstances()
    # remove slipstream orchestrator instances
    client_instances = [x for x in all_instances if not x.startswith("orchestrator")]
    # remove this instance
    client_instances.remove(instance_id)
    logger.debug("Finished detecting all SDN clients: %s" % client_instances)
    logger.debug("Waiting for all SDN clients...")
    call('ss-display \"SDN: Waiting for all clients...\"')
    # wait for clients to be ready: instance_id:net.i2cat.cnsmo.service.sdn.client.waiting=true
    for client_id in client_instances:
        logger.debug("Waiting for SDN client %s" % client_id)
        response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.sdn.client.listening" % client_id).rstrip("\n")
        if not response:
            logger.error("Timeout! Waiting for SDN client %s" % client_id)
            return -1
        logger.debug("Finished waiting for all SDN clients.")

    # Communicate that the VPN has been established
    logger.debug("Announcing sdn service has been deployed")
    call('ss-set net.i2cat.cnsmo.service.sdn.ready true')
    logger.debug("Set net.i2cat.cnsmo.service.sdn.ready=true")
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

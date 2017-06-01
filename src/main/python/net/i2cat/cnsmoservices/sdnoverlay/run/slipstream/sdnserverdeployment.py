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

    call('ss-set vpn.server.nodeinstanceid %s' % instance_id)
    logger.debug("Set vpn.server.nodeinstanceid= %s" % instance_id)

    # Launch SDN server
    logger.debug("Assuming SDN server is listening")
    call('ss-set net.i2cat.cnsmo.service.vpn.server.listening true')

    # Wait for configurator and server to be ready
    call('ss-get net.i2cat.cnsmo.service.vpn.server.listening')

    # Communicate that the SDN has been established
    logger.debug("Announcing sdn service has been deployed")
    call('ss-set net.i2cat.cnsmo.service.vpn.ready true')
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

#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:

#
# Output parameters:
# net.i2cat.cnsmo.core.ready: Used to communicate CNSMO core is ready.
# net.i2cat.cnsmo.dss.address: Used to communicate CNSMO distributed system state address.
# net.i2cat.cnsmo.service.dns.server.ready: Used to communicate the DNS service to be configured properly
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


def deploydns():
    logger = logging.getLogger(__name__)
    # Configuration values
    
    call('ss-display \"Configuring DNS in client...\"')

    call('ss-display \"DNS client configured successfully\"')
    logger.debug("Error is: %s " % (totalErr))
    logger.debug("Assuming SDN client is ready")
    return totalErr

def config_logging():
    logging.basicConfig(filename='cnsmo-dns-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running DNS client deployment script...")
    configureDNS()
    else:
        logger.debug("::: ERROR ::: Preconditions not fully satisfied")
        return -1

if __name__ == "__main__":
    main()

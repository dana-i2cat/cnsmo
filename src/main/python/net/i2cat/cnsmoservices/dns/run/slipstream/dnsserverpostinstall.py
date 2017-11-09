#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
# 
# Output parameters:
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

call = lambda command: subprocess.check_output(command, shell=True)
callWithResp = lambda command: subprocess.check_output(command, shell=True)

def main():
    config_logging()
    return postinstalldns()
    
def config_logging():
    logging.basicConfig(filename='cnsmo-dns-postinstall.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

def postinstallsdn():
    logger = logging.getLogger(__name__)
    logger.debug("Post-installation of DNS server...")
    call('ss-display \"Running post-install of DNS server..."') 


    logger.debug("DNS post-install successfully")
    return err

if __name__ == "__main__":
    main()
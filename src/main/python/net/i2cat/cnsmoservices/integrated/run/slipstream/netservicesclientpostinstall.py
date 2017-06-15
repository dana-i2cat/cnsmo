#!/usr/bin/env python

###
# This script postinstalls CNSMo network services in a SlipStream postinstall.
# It is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# net.services.enable: A json encoded list of strings indicating the network services to be enabled. e.g. ['vpn', 'fw', 'lb']
#
# Output parameters:
# net.services.enabled: A json encoded list of strings indicating the network services that has been enabled. e.g. ['vpn', 'fw', 'lb']
###

import json
import logging

import os
import subprocess
import sys
import threading

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)


call = lambda command: subprocess.check_output(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services client postinstall script")
    call('ss-display \"Running net services client postinstall script\"')

    os.chdir("/var/tmp/slipstream")

    logger.debug("Postinstall SDN client on a SlipStream application...")
    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","cnsmo/cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("sudo rm -f /etc/udev/rules.d/*net*.rules")

    logger.debug("Finished posinstalling net services")
    call("ss-set net.services.installed true")
    logger.debug("Set net.services.installed = true")
    return 0

def config_logging():
    logging.basicConfig(filename='cnsmo-integrated-postinstall.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

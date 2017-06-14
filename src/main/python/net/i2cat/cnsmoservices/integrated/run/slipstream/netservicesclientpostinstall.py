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

    git_branch=call("ss-get --timeout=1200 net.i2cat.cnsmo.git.branch")
    logger.debug("Downloading CNSMO from gitHub")

    call("echo 'holaaaaaaaaaaa' > hola.txt")

    # Download the repositories from gitHub
    call("git clone -b %s --single-branch https://github.com/dana-i2cat/cnsmo.git ./cnsmo" % git_branch)
    call("git clone -b master --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git ./cnsmo-net-services")
    
    os.chdir("/var/tmp/slipstream")

    logger.debug("Postinstall SDN client on a SlipStream application...")
    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","./cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("rm -f /etc/udev/rules.d/*net*.rules")

    logger.debug("Finished posinstalling net services")
    call('ss-display \"Successfully posinstalled network services: %s\"' % netservices_enabled)

    call('ss-set net.services.installed \'%s\'' % json.dumps(netservices_enabled))
    logger.debug("Set net.services.installed = %s" % json.dumps(netservices_enabled))
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

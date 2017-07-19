#!/usr/bin/env python

###
# This script postinstalls CNSMo network services in a SlipStream postinstall.
# It is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Output parameters:
# net.services.installed: A json encoded list of strings indicating the network services that has been installed. e.g. ['vpn', 'fw', 'lb']
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

def install_redis():
    logger = logging.getLogger(__name__)

    logger.debug("Configuring integration with slipstream")
    os.chdir("/var/tmp/slipstream")

    logger.debug("Install redis")
    call("wget http://download.redis.io/releases/redis-3.0.7.tar.gz")
    call("tar xzf redis-3.0.7.tar.gz")
    call("rm redis-3.0.7.tar.gz")
    os.chdir("/var/tmp/slipstream/redis-3.0.7")
    call("make")
    call("sudo make install --quiet")

    PORT="20379"
    CONFIG_FILE="/etc/redis/20379.conf\n"
    LOG_FILE="/var/log/redis_20379.log\n"
    DATA_DIR="/var/lib/redis/20379\n"
    EXECUTABLE="/usr/local/bin/redis-server\n"

    p = Popen(['/var/tmp/slipstream/redis-3.0.7/utils/install_server.sh'], stdin=PIPE, shell=True)
    p.communicate(input='20379\n')


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services client postinstall script")
    call('ss-display \"Running net services client postinstall script\"')

    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","cnsmo/cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("rm -f /etc/udev/rules.d/*net*.rules")

    os.chdir("/var/tmp/slipstream")
    install_redis()

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
 
#!/usr/bin/env python

###
# This script postinstalls CNSMo network services in a SlipStream postinstall.
# It is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# net.services.enable: A json encoded list of strings indicating the network services to be enabled. e.g. ['vpn','sdn','fw', 'lb']
#
# Output parameters:
# net.services.installed: Boolean indicating if the services were installed properly
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

from src.main.python.net.i2cat.cnsmoservices.sdnoverlay.run.slipstream.sdnserverpostinstall import postinstallsdn
from subprocess import Popen, PIPE


call = lambda command: subprocess.check_output(command, shell=True)


def install_redis():
    logger = logging.getLogger(__name__)

    logger.debug("Postinstall SDN server on a SlipStream application...")
    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","cnsmo/cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("rm -f /etc/udev/rules.d/*net*.rules")

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
    logger.debug("Running net services server postinstall script")
    call('ss-display \"Running net services server postinstall script\"')

    os.chdir("/var/tmp/slipstream")
    install_redis()
    
    netservices = get_net_services_to_enable()
    if (('vpn' not in netservices) and ('sdn' in netservices)): netservices.append('vpn')
    logger.debug("Will install software for the following services %s" % json.dumps(netservices))
    
    logger.debug("Postinstall net services...")
    if 'sdn' in netservices:
        if postinst_sdn_and_wait() == 0:
            logger.debug("SDN installed")
        else:
            logger.error("Error postinstalling SDN. Aborting script")
            return -1

    logger.debug("Finished postinstalling net services")
    call('ss-display \"Successfully postinstalled network services: %s\"' % netservices)

    call("ss-set net.services.installed true")
    logger.debug("Set net.services.installed = true")
    return 0

def postinst_sdn_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall SDN...")
    return postinstallsdn()

def get_net_services_to_enable():
    """
    :return: A list of strings representing which services must be enabled. e.g. ['vpn', 'fw', 'lb']
    """
    logger = logging.getLogger(__name__)
    try:
        netservices_str = call('ss-get net.services.enable').rstrip('\n')
        if netservices_str:
            netservices = json.loads(netservices_str)
            return netservices
        else:
            raise ValueError("Couldn't get value for net.services.enable")
    except subprocess.CalledProcessError as e:
        logger.error("Command {} returned non-zero exit status {} with output {}".format(e.cmd, e.returncode, e.output))
        call('ss-abort \"Error reading network services to enable\"')
        raise
    except Exception as e:
        logger.error(e.message)
        call('ss-abort \"Error reading network services to enable\"')
        raise


def config_logging():
    logging.basicConfig(filename='cnsmo-integrated-postinstall.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

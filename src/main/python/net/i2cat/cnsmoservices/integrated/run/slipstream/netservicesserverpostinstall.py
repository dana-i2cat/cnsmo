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

from src.main.python.net.i2cat.cnsmoservices.sdnoverlay.run.slipstream.sdnserverpostinstall import postinstsdn


call = lambda command: subprocess.check_output(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services server postinstall script")
    call('ss-display \"Running net services server postinstall script\"')
    netservices = get_net_services_to_enable()
    logger.debug("Will postinst following services %s" % json.dumps(netservices))
    call('ss-display \"Deploying network services \'%s\'\"' % json.dumps(netservices))

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    cnsmo_server_instance_id = instance_id

    call('ss-set cnsmo.server.nodeinstanceid %s' % cnsmo_server_instance_id)
    logger.debug("Set cnsmo.server.nodeinstanceid= %s" % cnsmo_server_instance_id)

    if (('vpn' not in netservices) and ('sdn' in netservices)): netservices.append('vpn')
    logger.debug("Postinstall net services...")
    netservices_enabled = list()
    if 'vpn' in netservices:
        if postinst_vpn_and_wait() == 0:
            logger.debug("Marking vpn as enabled")
            netservices_enabled.append('vpn')
        else:
            logger.error("Error postinsting VPN. Aborting script")
            return -1
    logger.debug("Finished postinsting net services")
    call('ss-display \"Successfully postinsted network services: %s\"' % netservices_enabled)

    call('ss-set net.services.enabled \'%s\'' % json.dumps(netservices_enabled))
    logger.debug("Set net.services.enabled= %s" % json.dumps(netservices_enabled))
    return 0


def postinst_vpn_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall VPN...")
    return postinstvpn()

def postinst_sdn_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall SDN...")
    return postinstsdn()

def postinst_fw_and_wait(cnsmo_server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall FW...")
    return postinstfw(cnsmo_server_instance_id)


def postinst_lb_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying LB...")
    return postinstlb()
    

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

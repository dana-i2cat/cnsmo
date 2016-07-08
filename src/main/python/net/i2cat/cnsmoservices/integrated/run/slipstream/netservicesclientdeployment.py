#!/usr/bin/env python

###
# This script deploys CNSMo network services in a SlipStream deployment.
# It is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# cnsmo.server.nodeinstanceid: Indicates the node.id of the component acting as CNSMO server
# vpn.server.nodeinstanceid: Indicates the node.id of the component acting as VPN server
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

from src.main.python.net.i2cat.cnsmoservices.vpn.run.slipstream.vpnclientdeployment import deployvpn
from src.main.python.net.i2cat.cnsmoservices.fw.run.slipstream.fwdeployment import deployfw

call = lambda command: subprocess.check_output(command, shell=True)

logging.basicConfig(filename="cnsmo.log")
logger = logging.getLogger('net.i2cat.cnsmoservices.integrated.run.slipstream.netservicesclientdeployment')


def main():
    logger.debug("Running net services client deployment script")
    call('ss-display \"Running net services client deployment script\"')
    netservices = get_net_services_to_enable()
    logger.debug("Will deploy following services %s" % netservices)
    call('ss-display \"Deploying network services %s\"' % netservices)
    netservices_enabled = list()

    logger.debug("Resolving cnsmo.server.nodeinstanceid...")
    cnsmo_server_instance_id = call('ss-get --timeout=1200 cnsmo.server.nodeinstanceid').rstrip('\n')
    if not cnsmo_server_instance_id:
        logger.error("Timeout waiting for cnsmo.server.nodeinstanceid")
        # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
        return -1
    logger.debug("Got cnsmo.server.nodeinstanceid= %s" % cnsmo_server_instance_id)

    logger.debug("Deploying net services...")
    if 'vpn' in netservices:
        vpn_server_instance_id = call('ss-get --timeout=1200 vpn.server.nodeinstanceid').rstrip('\n')
        if not vpn_server_instance_id:
            # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
            return -1
        if deploy_vpn_and_wait(vpn_server_instance_id):
            netservices_enabled.append('vpn')
        else:
            return -1

    if 'fw' in netservices:
        if deploy_fw_and_wait(cnsmo_server_instance_id):
            netservices_enabled.append('fw')
        else:
            return -1

    if 'lb' in netservices:
        # nothing to do, lb is only in the server
        netservices_enabled.append('lb')
    logger.debug("Finished deploying net services")

    call('ss-set net.services.enabled %s' % netservices_enabled)
    logger.debug("Set net.services.enabled= %s" % netservices_enabled)
    return 0


def deploy_vpn_and_wait(vpn_server_instance_id):
    logger.debug("Deploying VPN...")
    tvpn = threading.Thread(target=deployvpn)
    tvpn.start()
    logger.debug("Waiting for VPN to be established...")
    response = call('ss-get --timeout=1800 %s:net.i2cat.cnsmo.service.vpn.ready' % vpn_server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for VPN. established=%s" % response)
    if response != 'true':
        logger.error("Timeout waiting for VPN service to be established")
        call('ss-abort \"Timeout waiting for VPN service to be established\"')
        return -1
    return 0


def deploy_fw_and_wait(cnsmo_server_instance_id):
    logger.debug("Deploying FW...")
    tfw = threading.Thread(target=deployfw, args=cnsmo_server_instance_id)
    tfw.start()
    logger.debug("Waiting for FW to be established...")
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.fw.ready').rstrip('\n')
    logger.debug("Finished waiting for FW. established=%s" % response)
    if response != 'true':
        logger.error("Timeout waiting for FW service to be established")
        call('ss-abort \"Timeout waiting for FW service to be established\"')
        return -1
    return 0


def get_net_services_to_enable():
    """
    :return: A list of strings representing which services must be enabled. e.g. ['vpn', 'fw', 'lb']
    """
    netservices_str = call('ss-get net.services.enable').rstrip('\n')
    netservices = json.loads(netservices_str)
    return netservices

main()

if __name__ == "__main__":
    main()

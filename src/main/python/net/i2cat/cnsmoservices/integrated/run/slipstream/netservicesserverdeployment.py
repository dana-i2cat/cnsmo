#!/usr/bin/env python

###
# This script deploys CNSMo network services in a SlipStream deployment.
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

from src.main.python.net.i2cat.cnsmoservices.vpn.run.slipstream.vpnserverdeployment import deployvpn
from src.main.python.net.i2cat.cnsmoservices.fw.run.slipstream.fwdeployment import deployfw
from src.main.python.net.i2cat.cnsmoservices.lb.run.slipstream.lborchestratordeployment import deploylb

call = lambda command: subprocess.check_output(command, shell=True)

logging.basicConfig(filename="cnsmo.log")
logger = logging.getLogger('net.i2cat.cnsmoservices.integrated.run.slipstream.netservicesserverdeployment')


def main():
    logger.debug("Running net services server deployment script")
    call('ss-display \"Running net services server deployment script\"')
    netservices = get_net_services_to_enable()
    logger.debug("Will deploy following services %s" % netservices)
    call('ss-display \"Deploying network services %s\"' % netservices)
    netservices_enabled = list()

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    cnsmo_server_instance_id = instance_id

    call('ss-set cnsmo.server.nodeinstanceid %s' % cnsmo_server_instance_id)
    logger.debug("Set cnsmo.server.nodeinstanceid= %s" % cnsmo_server_instance_id)

    logger.debug("Deploying net services...")
    if 'vpn' in netservices:
        if deploy_vpn_and_wait():
            netservices_enabled.append('vpn')
        else:
            return -1

    if 'fw' in netservices:
        if deploy_fw_and_wait(cnsmo_server_instance_id):
            netservices_enabled.append('fw')
        else:
            return -1

    if 'lb' in netservices:
        if deploy_lb_and_wait():
            netservices_enabled.append('lb')
        else:
            return -1

    logger.debug("Finished deploying net services")
    call('ss-set net.services.enabled %s' % netservices_enabled)
    logger.debug("Set net.services.enabled= %s" % netservices_enabled)
    return 0


def deploy_vpn_and_wait():
    logger.debug("Deploying VPN...")
    tvpn = threading.Thread(target=deployvpn)
    tvpn.start()
    logger.debug("Waiting for VPN to be established...")
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.vpn.ready').rstrip('\n')
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


def deploy_lb_and_wait():
    logger.debug("Deploying LB...")
    tlb = threading.Thread(target=deploylb)
    tlb.start()
    logger.debug("Waiting for LB to be established...")
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.lb.ready').rstrip('\n')
    logger.debug("Finished waiting for LB. established=%s" % response)
    if response != 'true':
        logger.error("Timeout waiting for LB service to be established")
        call('ss-abort \"Timeout waiting for LB service to be established\"')
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

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

from src.main.python.net.i2cat.cnsmoservices.dns.run.slipstream.dnsserverdeployment import deploydns
from src.main.python.net.i2cat.cnsmoservices.vpn.run.slipstream.vpnserverdeployment import deployvpn
from src.main.python.net.i2cat.cnsmoservices.fw.run.slipstream.fwdeployment import deployfw
from src.main.python.net.i2cat.cnsmoservices.lb.run.slipstream.lborchestratordeployment import deploylb
from src.main.python.net.i2cat.cnsmoservices.sdnoverlay.run.slipstream.sdnserverdeployment import deploysdn


call = lambda command: subprocess.check_output(command, shell=True)
callNoResp = lambda command: subprocess.call(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services server deployment script")
    call('ss-display \"Running net services server deployment script\"')
    netservices = get_net_services_to_enable()
    if (('vpn' not in netservices) and ('sdn' in netservices)): netservices.append('vpn')
    logger.debug("Will deploy following services %s" % json.dumps(netservices))
    call('ss-display \"Deploying network services \'%s\'\"' % json.dumps(netservices))

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    cnsmo_server_instance_id = instance_id

    call('ss-set cnsmo.server.nodeinstanceid %s' % cnsmo_server_instance_id)
    logger.debug("Set cnsmo.server.nodeinstanceid= %s" % cnsmo_server_instance_id)

    logger.debug("Deploying net services...")
    netservices_enabled = list()
    if 'dns' in netservices:   
        if deploy_dns_and_wait(netservices) == 0:
            logger.debug("Marking dns as enabled")
            netservices_enabled.append('dns')
        else:
            logger.error("Error deploying DNS. Aborting script")
            return -1
    if 'vpn' in netservices:
        if deploy_vpn_and_wait(netservices) == 0:
            logger.debug("Marking vpn as enabled")
            netservices_enabled.append('vpn')
        else:
            logger.error("Error deploying VPN. Aborting script")
            return -1
    if 'sdn' in netservices:
        if deploy_sdn_and_wait() == 0:
            logger.debug("Marking sdn as enabled")
            netservices_enabled.append('sdn')
        else:
            logger.error("Error deploying SDN. Aborting script")
            return -1

    if 'fw' in netservices:
        if deploy_fw_and_wait(cnsmo_server_instance_id) == 0:
            logger.debug("Marking fw as enabled")
            netservices_enabled.append('fw')
        else:
            logger.error("Error deploying FW. Aborting script")
            return -1

    if 'lb' in netservices:
        if deploy_lb_and_wait() == 0:
            logger.debug("Marking lb as enabled")
            netservices_enabled.append('lb')
        else:
            logger.error("Error deploying LB. Aborting script")
            return -1

    #Restart dns service if dns is activated
    logger.debug("Restarting DNS service...")
    call('ss-display \"VPN: Restarting DNS Service...\"')
    if 'dns' in netservices:
        callNoResp("service dnsmasq restart")
        logger.debug("restarted dnsmasq")
        
    logger.debug("Finished deploying net services")
    call('ss-display \"Successfully deployed network services: %s\"' % netservices_enabled)

    call('ss-set net.services.enabled \'%s\'' % json.dumps(netservices_enabled))
    logger.debug("Set net.services.enabled= %s" % json.dumps(netservices_enabled))
    return 0

def deploy_dns_and_wait(netservices):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying DNS...")
    return deploydns(netservices)

def deploy_vpn_and_wait(netservices):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying VPN...")
    return deployvpn(netservices)

def deploy_sdn_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying SDN...")
    return deploysdn()

def deploy_fw_and_wait(cnsmo_server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying FW...")
    return deployfw(cnsmo_server_instance_id)


def deploy_lb_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Deploying LB...")
    return deploylb()
    

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
    logging.basicConfig(filename='cnsmo-integrated-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

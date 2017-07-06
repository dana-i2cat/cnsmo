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
# net.services.enable: A json encoded list of strings indicating the network services to be enabled. e.g. ['vpn', 'fw', 'lb', 'sdn']
#
# Output parameters:
# net.services.enabled: A json encoded list of strings indicating the network services that has been enabled. e.g. ['vpn', 'fw', 'lb', 'sdn']
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
from src.main.python.net.i2cat.cnsmoservices.sdnoverlay.run.slipstream.sdnclientdeployment import configureOvs

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services client deployment script")
    call('ss-display \"Running net services client deployment script\"')
    netservices = get_net_services_to_enable()
    if (('vpn' not in netservices) and ('sdn' in netservices)): netservices.append('vpn')
    logger.debug("Will deploy following services %s" % json.dumps(netservices))
    call('ss-display \"Deploying network services \'%s\'\"' % json.dumps(netservices))
    netservices_enabled = list()

    if netservices:
        logger.debug("Resolving cnsmo.server.nodeinstanceid...")
        cnsmo_server_instance_id = call('ss-get --timeout=3000 cnsmo.server.nodeinstanceid').rstrip('\n')
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
            if deploy_vpn_and_wait(vpn_server_instance_id) == 0:
                logger.debug("Marking vpn as enabled")
                netservices_enabled.append('vpn')
            else:
                logger.error("Error deploying VPN. Aborting script")
                return -1

        if 'sdn' in netservices:
            sdn_server_instance_id = call('ss-get --timeout=1200 vpn.server.nodeinstanceid').rstrip('\n')
            if not sdn_server_instance_id:
                # timeout! Abort the script immediately (ss-get will abort the whole deployment in short time)
                return -1
            if deploy_sdn_and_wait(sdn_server_instance_id) == 0:
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
            # nothing to do, lb is only in the server
            logger.debug("Marking lb as enabled")
            netservices_enabled.append('lb')

    logger.debug("Finished deploying net services")

    call('ss-display \"Successfully deployed network services: %s\"' % netservices_enabled)

    call('ss-set net.services.enabled \'%s\'' % json.dumps(netservices_enabled))
    logger.debug("Set net.services.enabled= %s" % json.dumps(netservices_enabled))
    return 0


def deploy_vpn_and_wait(vpn_server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying VPN...")
    return deployvpn()

def deploy_sdn_and_wait(sdn_server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying SDN...")
    return configureOvs()

def deploy_fw_and_wait(cnsmo_server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying FW...")
    return deployfw(cnsmo_server_instance_id)


def get_net_services_to_enable():
    """
    :return: A list of strings representing which services must be enabled. e.g. ['vpn', 'fw', 'lb', 'sdn']
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

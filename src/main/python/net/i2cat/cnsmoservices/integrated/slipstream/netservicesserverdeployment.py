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


def main():
    netservices = get_net_services_to_enable()
    netservices_enabled = list()

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    cnsmo_server_instance_id = instance_id

    call('ss-set cnsmo.server.nodeinstanceid %s' % cnsmo_server_instance_id)

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

    call('ss-set net.services.enabled %s' % netservices_enabled)
    return 0


def deploy_vpn_and_wait():
    tvpn = threading.Thread(target=deployvpn)
    tvpn.start()
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.vpn.ready').rstrip('\n')
    if response != 'true':
        call('ss-abort \"Timeout waiting for VPN service to be established\"')
        return -1
    return 0


def deploy_fw_and_wait(cnsmo_server_instance_id):
    tfw = threading.Thread(target=deployfw, args=cnsmo_server_instance_id)
    tfw.start()
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.fw.ready').rstrip('\n')
    if response != 'true':
        call('ss-abort \"Timeout waiting for FW service to be established\"')
        return -1
    return 0


def deploy_lb_and_wait():
    tlb = threading.Thread(target=deploylb)
    tlb.start()
    response = call('ss-get --timeout=1800 net.i2cat.cnsmo.service.lb.ready').rstrip('\n')
    if response != 'true':
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

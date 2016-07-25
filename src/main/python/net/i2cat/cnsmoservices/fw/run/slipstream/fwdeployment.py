#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following variables to be declared in the SlipStream component:
# - net.i2cat.cnsmo.service.fw.rules: Input variable. Json list with FW rules in the format:
# [{"direction":"in/out", "protocol":"tcp/udp/...", "dst_port":"[0,65535]", "ip_range":"cidr_notation", "action":"drop/acpt"},
# {...}, {...}]
# - net.i2cat.cnsmo.service.fw.server.listening: Output variable. Tells when the firewall agent is up and listening.
# - net.i2cat.cnsmo.service.fw.ready: Output variable. Tells when the firewall service is already configured with specified rules.
#
# Uses the following SlipStream application run context variables:
# - CNSMO_server.1:net.i2cat.cnsmo.dss.address: Address of the distributed system state
# - CNSMO_server.1:net.i2cat.cnsmo.core.ready: Tells when CNSMO core is ready
###

import json
import logging
import requests
import subprocess
import threading
import time

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running FW deployment script...")

    # TODO get this from slipstream context, by inspecting roles each component has
    server_instance_id = "CNSMO_server.1"
    logger.debug("Using hardcoded server_instance_id=%s " % server_instance_id)

    return launch_fw(server_instance_id)


def deployfw(server_instance_id):
    return launch_fw(server_instance_id)


def launch_fw(server_instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying FW on a SlipStream application...")
    logger.debug("Using server %s" % server_instance_id)

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)

    logger.debug("Waiting for CNSMO...")
    call('ss-display \"Waiting for CNSMO...\"')
    response = call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id).rstrip('\n')
    logger.debug("Finished waiting for CNSMO. %s:net.i2cat.cnsmo.core.ready= %s" % (server_instance_id, response))

    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')
    logger.debug("Got %s:net.i2cat.cnsmo.dss.address= %s" % (server_instance_id, redis_address))

    logger.debug("Deploying FW components...")
    call('ss-display \"Deploying FW components...\"')

    hostname = call('ss-get hostname').rstrip('\n')
    port = "9095"

    tc = threading.Thread(target=launchFWServer, args=(hostname, port, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(5)
    logger.debug("Assuming FW server is deployed")

    # build the FW
    logger.debug("Building the FW internal server internal...")
    r = requests.post("http://%s:%s/fw/build/" % (hostname, port))
    r.raise_for_status()
    time.sleep(1)
    logger.debug("Assuming FW internal server is listening")
    call('ss-set net.i2cat.cnsmo.service.fw.server.listening true')

    # Configure rules from input parameter
    logger.debug("Configuring FW rules...")
    call('ss-display \"FW: Configuring FW rules...\"')

    logger.debug("Retrieving FW rules...")
    rules_srt = call('ss-get net.i2cat.cnsmo.service.fw.rules').rstrip('\n')
    logger.debug("Got FW rules: %s" % rules_srt)

    rules = json.loads(rules_srt)
    for rule in rules:
        logger.debug("Configuring rule: %s" % json.dumps(rule))
        r = requests.post("http://%s:%s/fw/" % (hostname, port), data=json.dumps(rule))
        r.raise_for_status()
        logger.debug("Configured rule: %s" % json.dumps(rule))

    logger.debug("FW configured successfully")

    logger.debug("Announcing FW service ready...")
    call('ss-set net.i2cat.cnsmo.service.fw.ready true')

    logger.debug("FW service configured!")
    call('ss-display \"FW: Firewall configured!\"')
    return 0


def launchFWServer(hostname, port, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching FW server...")
    call('ss-display \"FW: Launching FW server...\"')
    response = call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/fw/run/server.py -a %s -p %s -r %s -s FWServer-%s" % (hostname, port, redis_address, instance_id))
    logger.debug("FW server response: %s" % response)


def config_logging():
    logging.basicConfig(filename='cnsmo-fw-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

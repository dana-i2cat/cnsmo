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
import requests
import subprocess
import threading
import time
import os

from slipstream.SlipStreamHttpClient import SlipStreamHttpClient
from slipstream.ConfigHolder import ConfigHolder

call = lambda command: subprocess.check_output(command, shell=True)


def main():
    # TODO get this from slipstream context, by inspecting roles each component has
    server_instance_id = "CNSMO_server.1"

    launch_fw(server_instance_id)


def deployfw(server_instance_id):
    launch_fw(server_instance_id)


def launch_fw(server_instance_id):
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    log_file = os.getcwd() + "/cnsmo/fw.log"

    date = call('date')
    logToFile("Waiting for CNSMO at %s" % date, log_file, "w+")

    call('ss-display \"Waiting for CNSMO...\"')
    call("ss-get --timeout=1800 %s:net.i2cat.cnsmo.core.ready" % server_instance_id)

    redis_address = call("ss-get %s:net.i2cat.cnsmo.dss.address" % server_instance_id).rstrip('\n')

    call('ss-display \"Deploying FW components...\"')

    hostname = call('ss-get hostname').rstrip('\n')
    port = "9095"

    date = call('date')
    logToFile("Launching Firewall server at %s" % date, log_file, "a")

    tc = threading.Thread(target=launchFWServer, args=(hostname, port, redis_address, instance_id))
    tc.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(5)
    call('ss-set net.i2cat.cnsmo.service.fw.server.listening true')

    # build the FW
    r = requests.post("http://%s:%s/fw/build/" % (hostname, port))
    r.raise_for_status()
    time.sleep(1)
    call('ss-set net.i2cat.cnsmo.service.fw.server.listening true')

    date = call('date')
    logToFile("FW deployed at %s" % date, log_file, "a")

    call('ss-display \"FW: FW has been created!\"')
    print "FW deployed!"

    # Configure rules from input parameter
    call('ss-display \"FW: Configuring FW rules...\"')

    rules_srt = call('ss-get net.i2cat.cnsmo.service.fw.rules').rstrip('\n')
    print rules_srt

    rules = json.loads(rules_srt)
    for rule in rules:
        print rule
        r = requests.post("http://%s:%s/fw/" % (hostname, port), data=json.dumps(rule))
        r.raise_for_status()

    date = call('date')
    logToFile("FW configured successfully at %s" % date, log_file, "a")

    call('ss-set net.i2cat.cnsmo.service.fw.ready true')
    call('ss-display \"FW: Firewall configured!\"')
    print "FW configured!"


def launchFWServer(hostname, port, redis_address, instance_id):
    call('ss-display \"FW: Launching FW server...\"')
    print "Launching FW"
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/fw/run/server.py -a %s -p %s -r %s -s FWServer-%s" % (hostname, port, redis_address, instance_id))


def logToFile(message, filename, filemode):
    f = None
    try:
        f = open(filename, filemode)
        f.write(message)
    finally:
        if f:
            f.close()

if __name__ == "__main__":
    main()

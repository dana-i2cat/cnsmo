#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Output parameters:
# net.i2cat.cnsmo.service.dns.server.ready: Used to communicate the DNS service to be configured properly
###

import logging
import os
import subprocess
import sys
import threading
import time

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

call = lambda command: subprocess.check_output(command, shell=True)

def main():
    config_logging()
    return deploydns()


def launchDNSServer(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching DNS server...")
    call('ss-display \"DNS: Launching DNS server...\"')
    os.chdir("/var/tmp/slipstream")
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/dns/run/server.py -a %s -p 20200 -r %s -s DNSServer-%s" % (hostname, redis_address, instance_id))


def deploydns():
    logger = logging.getLogger(__name__)

    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get net.i2cat.cnsmo.dss.address").rstrip('\n')

    logger.debug("Configuring DNS server...")
    call('ss-display \"Configuring DNS server..."')

    logger.debug("DNS configured successfully")

    ts = threading.Thread(target=launchDNSServer, args=(hostname, redis_address, instance_id))
    ts.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming DNS server is listening")

    logger.debug("Announcing dns service has been deployed")
    call('ss-set net.i2cat.cnsmo.service.dns.server.ready true')
    logger.debug("Set net.i2cat.cnsmo.service.dns.server.ready=true")
    return 0

def config_logging():
    logging.basicConfig(filename='cnsmo-dns-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

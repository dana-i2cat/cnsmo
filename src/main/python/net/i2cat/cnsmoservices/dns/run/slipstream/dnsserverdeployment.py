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
import json
import os
import subprocess
import sys
import threading
import time
import fileinput
import re

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

call = lambda command: subprocess.check_output(command, shell=True)

def main():
    config_logging()
    return deploydns("")

def launchDNSServer(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching DNS server API...")
    call('ss-display \"DNS: Launching DNS server API...\"')
    os.chdir("/var/tmp/slipstream")
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/dns/run/server.py -a %s -p 20200 -r %s -s DNSServer-%s" % (hostname, redis_address, instance_id))

def configure_dnsmasq(upstream_servers, local_listeners, hostnames):
    resolvconf_head_file = "/etc/resolvconf/resolv.conf.d/head"
    for server in upstream_servers:
        l = "server="+server+"\n"
        add_line("/etc/dnsmasq.conf", l)
        laux = "nameserver "+server+"\n"
        add_line(resolvconf_head_file,laux)
    call("service resolvconf restart")
    for listen in local_listeners:
        l = "listen-address="+listen+"\n"
        add_line("/etc/dnsmasq.conf", l)
    l = "expand-hosts\n"
    add_line("/etc/dnsmasq.conf", l)
    for host in hostnames:
        l = host+"\n"
        add_line("/etc/hosts", l)

def prepend_after(file_name,pattern,value=""):
    fh=fileinput.input(file_name,inplace=True)
    for line in fh:
        replacement=value + line
        line=re.sub(pattern,replacement,line)
        sys.stdout.write(line)
    fh.close()

def add_line(file_name,line):
    with open(file_name, 'a') as file:
        file.writelines(line)   

def deploydns(netservices):
    logger = logging.getLogger(__name__)
    logger.debug("Deploying DNS server...")
    call('ss-display \"DNS: Deploying DNS server...\"')
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    hostname = call('ss-get hostname').rstrip('\n')
    logger.debug("Resolving net.i2cat.cnsmo.dss.address...")
    redis_address = call("ss-get net.i2cat.cnsmo.dss.address").rstrip('\n')

    logger.debug("Configuring DNS server...")
    call('ss-display \"Configuring DNS server..."')
    
    upstream = ["8.8.8.8", "8.8.4.4"]
    ethIface = getFirstEthernetInterface()
    ip = call("ifconfig "+ ethIface +" | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'").rstrip('\n')
    listeners = [ip]

    hostnames = [""]

    if 'vpn' in netservices:
        hostnames = get_default_dns_records()
        listeners = [ip,"10.10.10.1"]
    
    configure_dnsmasq(upstream, listeners, hostnames)
    
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

def get_default_dns_records():
    """
    :return: A list of strings for each dns record which we want to enable by default
    """
    logger = logging.getLogger(__name__)
    try:
        recordlist_str = call('ss-get dns.recordlist').rstrip('\n')
        if recordlist_str:
            recordlist = json.loads(recordlist_str)
            return recordlist
        else:
            raise ValueError("Couldn't get value for dns.recordlist")
    except subprocess.CalledProcessError as e:
        logger.error("Command {} returned non-zero exit status {} with output {}".format(e.cmd, e.returncode, e.output))
        call('ss-abort \"Error reading dns record list\"')
        raise
    except Exception as e:
        logger.error(e.message)
        call('ss-abort \"Error reading dns record list\"')
        raise

def getFirstEthernetInterface():
    return call("""ls /sys/class/net | grep \"en\|eth\" | head -1""").rstrip('\n')


def config_logging():
    logging.basicConfig(filename='cnsmo-dns-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

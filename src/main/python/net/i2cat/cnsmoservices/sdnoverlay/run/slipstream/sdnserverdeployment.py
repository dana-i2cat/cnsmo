#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Output parameters:
# net.i2cat.cnsmo.service.sdn.server.ready: Used to communicate the SDN service to be configured properly
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
    return deploysdn()


def launchSDNServer(hostname, redis_address, instance_id):
    logger = logging.getLogger(__name__)
    logger.debug("Launching SDN server...")
    call('ss-display \"SDN: Launching SDN server...\"')
    call("python cnsmo/cnsmo/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/server.py -a %s -p 20092 -r %s -s VPNServer-%s" % (hostname, redis_address, instance_id))


### Uncomment everything before MERGE!!!!!!!!!!!!!!!!!!!!!


def deploysdn():
    logger = logging.getLogger(__name__)
    logger.debug("Installing karaf and features...")
    call('ss-display \"Installing karaf and features..."')

    #os.chdir("/opt/odl/distribution-karaf-0.3.2-Lithium-SR2")

    KARAF_DIR='/opt/odl/distribution-karaf-0.3.2-Lithium-SR2'
    DLUX_DIRECTORY=str(KARAF_DIR)+'/system/org/opendaylight/dlux'
    #call("rm -R %s/*" % DLUX_DIRECTORY)
    CNSMO_DIRECTORY='/var/tmp/slipstream/cnsmo/cnsmo/dlux-Lithium-SR2-MOD.zip'
    #call("cp %s  %s/" % (CNSMO_DIRECTORY , DLUX_DIRECTORY))
    #os.chdir("/opt/odl/distribution-karaf-0.3.2-Lithium-SR2/system/org/opendaylight/dlux/")
    #call("sudo unzip dlux-Lithium-SR2-MOD.zip")
    #os.chdir(KARAF_DIR)

    #with open("./bin/setenv", "a") as myfile:
    #    myfile.write("export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64")

    #os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-7-openjdk-amd64'
    logger.debug("Starting karaf server...")
    #p = subprocess.Popen(["sudo","./bin/karaf","server"])

    logger.debug("Installing karaf features")
    time.sleep(30)

    #p = subprocess.Popen(["./bin/client","-u","karaf","feature:install","odl-openflowjava-all","odl-netconf-all","odl-dlux-all","odl-l2switch-packethandler","odl-l2switch-loopremover","odl-l2switch-arphandler","odl-l2switch-switch-ui","odl-restconf-all","odl-l2switch-addresstracker","odl-l2switch-switch-rest","odl-l2switch-switch","odl-mdsal-all","odl-openflowjava-all","odl-mdsal-apidocs","odl-openflowplugin-all","odl-ovsdb-all"])    
    #p.wait()
    logger.debug("Karaf features installed successfully and ready to run!")

    ts = threading.Thread(target=launchSDNServer, args=(hostname, redis_address, instance_id))
    ts.start()
    # TODO implement proper way to detect when the server is ready (using systemstate?)
    time.sleep(1)
    logger.debug("Assuming SDN server is listening")

    logger.debug("Announcing sdn service has been deployed")
    call('ss-set net.i2cat.cnsmo.service.sdn.server.ready true')
    logger.debug("Set net.i2cat.cnsmo.service.sdn.server.ready=true")
    return 0

def config_logging():
    logging.basicConfig(filename='cnsmo-sdn-deployment.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

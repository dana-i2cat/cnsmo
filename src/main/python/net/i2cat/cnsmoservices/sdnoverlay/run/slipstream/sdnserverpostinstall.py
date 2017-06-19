#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
# Requires the following output parameters from the SDN server:
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
    return postinstallsdn()
    
def config_logging():
    logging.basicConfig(filename='cnsmo-sdn-postinstall.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

def install_karaf():
    logger = logging.getLogger(__name__)
    logger.debug("Installing Java 7 JDK and other components...")        
    call("apt-get -y update")
    call("apt-get install -y openjdk-7-jdk")

    logger.debug("Downloading opendaylight executable")
    call("wget https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/distribution-karaf/0.3.2-Lithium-SR2/distribution-karaf-0.3.2-Lithium-SR2.zip")
    call("sudo unzip distribution-karaf-0.3.2-Lithium-SR2.zip")
    os.chdir("/opt/odl/distribution-karaf-0.3.2-Lithium-SR2")

    with open("./bin/setenv", "a") as myfile:
        myfile.write("export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64")

    os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-7-openjdk-amd64'
    logger.debug("Starting karaf server...")
    p = subprocess.Popen(["sudo","./bin/karaf","server"])

    logger.debug("Installing karaf features")
    time.sleep(30)

    p = subprocess.Popen(["./bin/client","-u","karaf","feature:install","odl-openflowjava-all","odl-netconf-all","odl-dlux-all","odl-l2switch-packethandler","odl-l2switch-loopremover","odl-l2switch-arphandler","odl-l2switch-switch-ui","odl-restconf-all","odl-l2switch-addresstracker","odl-l2switch-switch-rest","odl-l2switch-switch","odl-mdsal-all","odl-openflowjava-all","odl-mdsal-apidocs","odl-openflowplugin-all","odl-ovsdb-all"])    
    logger.debug("Karaf features installed successfully and ready to run!")

def postinstallsdn():
    logger = logging.getLogger(__name__)
    
    logger.debug("Set working directory")
    if not os.path.isdir("/opt/odl"):
        os.makedirs("/opt/odl")

    os.chdir("/opt/odl")
    
    install_karaf()    
    call('ss-set net.i2cat.cnsmo.service.sdn.server.ready true')

if __name__ == "__main__":
    main()
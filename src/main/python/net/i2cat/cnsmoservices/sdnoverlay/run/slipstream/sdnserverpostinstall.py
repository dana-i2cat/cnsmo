#!/usr/bin/env python

###
# This script is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
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


def postinstallsdn():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall SDN server on a SlipStream application...")
    
    git_branch=call("ss-get --timeout=1200 git.branch")

    logger.debug("Downloading CNSMO")
    
    # Download the repositories from gitHub
    call("git clone -b %s --single-branch https://github.com/dana-i2cat/cnsmo.git ./cnsmo" % git_branch)
    call("git clone -b master --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git ./cnsmo-net-services")
    
    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","./cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("rm -f /etc/udev/rules.d/*net*.rules")

    logger.debug("Configuring integration with slipstream")
    os.chdir("/var/tmp/slipstream")

    logger.debug("Install redis")
    
    call("wget http://download.redis.io/releases/redis-3.0.7.tar.gz")
    call("tar xzf redis-3.0.7.tar.gz")
    call("rm redis-3.0.7.tar.gz")
    call("make -C ./redis-3.0.7")
    call("sudo make install --quiet -C ./redis-3.0.7")

    PORT="20379"
    CONFIG_FILE="/etc/redis/20379.conf"
    LOG_FILE="/var/log/redis_20379.log"
    DATA_DIR="/var/lib/redis/20379"
    EXECUTABLE="/usr/local/bin/redis-server"

    call("echo -e '%s\n%s\n%s\n%s\n%s\n' | sudo ./redis-3.0.7/utils/install_server.sh" %(PORT,CONFIG_FILE,LOG_FILE,DATA_DIR,EXECUTABLE) )
        
    logger.debug("Set working directory")

    if not os.path.isdir("/opt/odl"):
        os.makedirs("/opt/odl")
    
    os.chdir("/opt/odl")
    
    netservices = get_net_services_to_enable()
    call("echo %s >> /var/log/sdnserverinstall.log" % netservices)

    if 'sdn' in netservices:
        logger.debug("Installing Java 7 JDK and other components...")        
        call("apt-get -y update")
        call("apt-get install -y openjdk-7-jdk")
   
        logger.debug("Downloading opendaylight executable")
        call("wget https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/distribution-karaf/0.3.2-Lithium-SR2/distribution-karaf-0.3.2-Lithium-SR2.zip")
        call("unzip distribution-karaf-0.3.2-Lithium-SR2.zip")
        os.chdir("./distribution-karaf-0.3.2-Lithium-SR2")

        with open("./bin/setenv", "a") as myfile:
            myfile.write("export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64")

        os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-7-openjdk-amd64'
        logger.debug("Starting karaf server...")
        p = subprocess.Popen(["sudo","./bin/karaf","server"])

        logger.debug("Installing karaf features")
        time.sleep(30)

        p = subprocess.Popen(["./bin/client","-u","karaf","feature:install","odl-openflowjava-all","odl-netconf-all","odl-dlux-all","odl-l2switch-packethandler","odl-l2switch-loopremover","odl-l2switch-arphandler","odl-l2switch-switch-ui","odl-restconf-all","odl-l2switch-addresstracker","odl-l2switch-switch-rest","odl-l2switch-switch","odl-mdsal-all","odl-openflowjava-all","odl-mdsal-apidocs","odl-openflowplugin-all","odl-ovsdb-all"])    
        logger.debug("Karaf features installed successfully and ready to run!")

if __name__ == "__main__":
    main()
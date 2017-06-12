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
    
def postinstallsdn():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall SDN server on a SlipStream application...")
    
    git_branch=call("ss-get --timeout=1200 git.branch")

    logger.debug("Downloading CNSMO")
    # Download the repositories from gitHub
    call("git clone -b %s --single-branch https://github.com/dana-i2cat/cnsmo.git ./cnsmo" % git_branch)
    call("git clone -b master --single-branch https://github.com/dana-i2cat/cnsmo-net-services.git ./cnsmo-net-services")
    
    logger.debug("Installing CNSMO requirements")

    return 0
    
    # install cnsmo requirements
    pip install -r cnsmo/cnsmo/requirements.txt
    
    cwd=${PWD}
    echo "CWD is ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::"
    echo ${cwd}
    
    touch /var/tmp/cnsmo.env
    echo ${cwd} >> /var/tmp/cnsmo.env
    echo ${current_user} >> /var/tmp/cnsmo.env
    
    # remove persisted network configuration (for compatibility with pre-built images)
    rm -f /etc/udev/rules.d/*net*.rules
    
    touch ${file_done}
    
    #configuring integration with slipstream
    wd='/var/tmp/slipstream'
    cd ${wd}

    #install redis
    wget http://download.redis.io/releases/redis-3.0.7.tar.gz
    tar xzf redis-3.0.7.tar.gz
    rm redis-3.0.7.tar.gz
    cd redis-3.0.7
    make
    make install --quiet

    PORT=20379
    CONFIG_FILE=/etc/redis/20379.conf
    LOG_FILE=/var/log/redis_20379.log
    DATA_DIR=/var/lib/redis/20379
    EXECUTABLE=/usr/local/bin/redis-server

    echo -e "${PORT}\n${CONFIG_FILE}\n${LOG_FILE}\n${DATA_DIR}\n${EXECUTABLE}\n" | utils/install_server.sh
    cd ..
    
    # reboot to apply new kernel  upgraded by docker installation script
    #reboot
    
    # set working directory
    DIRECTORY='/opt/odl'
    if [ ! -d "$DIRECTORY" ]; then
      mkdir -p ${DIRECTORY}
    fi
    cd ${DIRECTORY}
    
    services=$(ss-get net.services.enable)
    echo $services >> /var/log/sdnserverinstall.log
    if [[ $services == *"sdn"* ]]; then
      touch /var/log/sdnserverinstall.log
    
      echo "Installing Java 7 JDK and other components..." >> /var/log/sdnserverinstall.log
      apt-get -y update
      apt-get install -y openjdk-7-jdk 
    
      # download opendaylight
      echo "Downloading opendaylight executable..." >> /var/log/sdnserverinstall.log
      wget https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/distribution-karaf/0.3.2-Lithium-SR2/distribution-karaf-0.3.2-Lithium-SR2.zip
      unzip distribution-karaf-0.3.2-Lithium-SR2.zip
      cd distribution-karaf-0.3.2-Lithium-SR2
    
      echo 'export JAVA_HOME="/usr/lib/jvm/java-7-openjdk-amd64"' >> ./bin/setenv
      source ./bin/setenv
      # start karaf server
      echo "Starting karaf server..." >> /var/log/sdnserverinstall.log
      ./bin/karaf server &
      #./bin/start
    
      # install features
      echo "Installing karaf features..." >> /var/log/sdnserverinstall.log
      sleep 30
    
      ./bin/client -u karaf feature:install odl-openflowjava-all odl-netconf-all odl-dlux-all odl-l2switch-packethandler odl-l2switch-loopremover odl-l2switch-arphandler odl-l2switch-switch-ui odl-restconf-all odl-l2switch-addresstracker odl-l2switch-switch-rest odl-l2switch-switch odl-mdsal-all odl-openflowjava-all odl-mdsal-apidocs odl-openflowplugin-all odl-ovsdb-all
      echo "Karaf features installed successfully and ready to run!" >> /var/log/sdnserverinstall.log
    fi
fi

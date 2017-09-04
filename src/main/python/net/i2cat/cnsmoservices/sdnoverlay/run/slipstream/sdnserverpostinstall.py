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
callWithResp = lambda command: subprocess.check_output(command, shell=True)

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
    call('ss-display \"Downloading opendaylight executable\"')
    call("wget https://nexus.opendaylight.org/content/repositories/opendaylight.release/org/opendaylight/integration/distribution-karaf/0.3.2-Lithium-SR2/distribution-karaf-0.3.2-Lithium-SR2.zip")
    call("sudo unzip distribution-karaf-0.3.2-Lithium-SR2.zip")

    call('ss-set net.services.installed true')
    logger.debug("Set net.services.installed=true")
    return 0

def install_gui():
    os.chdir("/var/tmp")

    # install api node dependencies
    call("echo fase 1 - clone api node project... >> /var/tmp/hola.txt")
    call("curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -")
    call("sudo apt-get install -y nodejs")
    call("git clone https://github.com/jiponsI2cat/cnsmo-api.git")
    call("echo fase 2 - install api node dependencies... >> /var/tmp/hola.txt")
    os.chdir("/var/tmp/cnsmo-api")
    call("npm install")
    call("echo '\"use strict\";\n\nmodule.exports = {\n  BASE_URL: \"/api/v1\",\n  MONGO_URL: \"mongodb://localhost/cnsmo\",\n  DOMAIN: \"127.0.0.1\",\n  PROTOCOL: \"http\",\n  port: process.env.PORT || 8081,\n  SWAGGER: true,\n  JWT_SECRET: \"cnsmosecret\",\n  TOKEN_EXPIRATION_DAYS: 10,\n};' > config/env/production.js")
    
    call("echo fase 3 - retrive host ip and generate environment.prod.ts file... >> /var/tmp/hola.txt")
    # retrive host ip and generate environment.prod.ts file
    os.chdir("/var/tmp/cnsmo-api/node_modules/cnsmo_web/src/environments")
    IPADDR = callWithResp("ip addr show eth0 | grep 'inet ' | grep -Fv 127.0.0.1 | awk '{{print $2}}' | cut -d/ -f1")
    IPADDR = IPADDR.split('\n')[0]
    aux = "http://"+str(IPADDR)+":8081/api/v1"
    call("echo 'export const environment = {\n production: true,\n api: \"%s\",\n authUrl: \"/authenticate\"\n };' > environment.prod.ts " % aux)
    os.chdir("/var/tmp/cnsmo-api/node_modules/cnsmo_web")

    call("echo fase 4 - install cnsmo_web dependencies... >> /var/tmp/hola.txt")
    # install cnsmo_web dependencies
    call("sudo npm install -g @angular/cli@1.3.2")
    call("npm install --save-dev @angular/cli@1.3.2")
    call("npm install")

    call("echo fase 5 - building cnsmo_web...  >> /var/tmp/hola.txt")
    # build cnsmo_web
    call("ng build --prod --aot=false")
    os.chdir("/var/tmp/cnsmo-api")
    ss_user = call('ss-get cnsmo.user').rstrip('\n')
    ss_password = call('ss-get cnsmo.password').rstrip('\n')

    call("echo fase 6 - retrive access credentials and generating config file... >> /var/tmp/hola.txt")
    call("echo '{\"credentials\": {\"username\": \"%s\",\"password\": \"%s\"}}' > /var/tmp/cnsmo-api/core/config/initConfig.json" % (ss_user,ss_password))
     call("sudo npm install pm2@latest -g")
    call("echo fase 7 - starting process... >> /var/tmp/hola.txt")
    call("pm2 start process.yml")
    call("echo Done - API and UI installed correctly >> /var/tmp/hola.txt")

def postinstallsdn():
    logger = logging.getLogger(__name__)

    call('pip install requests')

    install_gui()
    
    logger.debug("Set working directory")
    if not os.path.isdir("/opt/odl"):
        os.makedirs("/opt/odl")

    os.chdir("/opt/odl")
    err=install_karaf()    
    return err

if __name__ == "__main__":
    main()
#!/usr/bin/env python

###
# This script postinstalls CNSMo network services in a SlipStream postinstall.
# It is meant to be run by SlipStream, using a privileged user
#
# All ss-get/ss-set applies to local node variables, unless a node instance_id is prefixed.
#
# Requires the following parameters in slipstream application component:
# Input parameters:
# net.services.enable: A json encoded list of strings indicating the network services to be enabled. e.g. ['vpn','sdn','fw', 'lb']
#
# Output parameters:
# net.services.installed: Boolean indicating if the services were installed properly
###

import json
import logging

import os
import subprocess
import sys
import threading

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmoservices.sdnoverlay.run.slipstream.sdnserverpostinstall import postinstallsdn
from subprocess import Popen, PIPE


call = lambda command: subprocess.check_output(command, shell=True)


def install_redis():
    logger = logging.getLogger(__name__)
    os.chdir("/var/tmp/slipstream")

    logger.debug("Install redis")
    call("wget http://download.redis.io/releases/redis-3.0.7.tar.gz")
    call("tar xzf redis-3.0.7.tar.gz")
    call("rm redis-3.0.7.tar.gz")
    os.chdir("/var/tmp/slipstream/redis-3.0.7")
    call("make")
    call("sudo make install --quiet")

    PORT="20379"
    CONFIG_FILE="/etc/redis/20379.conf\n"
    LOG_FILE="/var/log/redis_20379.log\n"
    DATA_DIR="/var/lib/redis/20379\n"
    EXECUTABLE="/usr/local/bin/redis-server\n"

    p = Popen(['/var/tmp/slipstream/redis-3.0.7/utils/install_server.sh'], stdin=PIPE, shell=True)
    p.communicate(input='20379\n')


def main():
    config_logging()
    logger = logging.getLogger(__name__)
    logger.debug("Running net services server postinstall script")
    call('ss-display \"Running net services server postinstall script\"')

    logger.debug("Installing CNSMO requirements")
    p = subprocess.Popen(["pip","install","-r","cnsmo/cnsmo/requirements.txt"])

    logger.debug("Remove persisted network configuration (for compatibility with pre-built images)")
    call("rm -f /etc/udev/rules.d/*net*.rules")

    os.chdir("/var/tmp/slipstream")
    install_redis()

    install_gui()
    
    netservices = get_net_services_to_enable()
    if (('vpn' not in netservices) and ('sdn' in netservices)): netservices.append('vpn')
    logger.debug("Will install software for the following services %s" % json.dumps(netservices))
    
    logger.debug("Postinstall net services...")
    if 'sdn' in netservices:
        if postinst_sdn_and_wait() == 0:
            logger.debug("SDN installed")
        else:
            logger.error("Error postinstalling SDN. Aborting script")
            return -1

    logger.debug("Finished postinstalling net services")
    call('ss-display \"Successfully postinstalled network services: %s\"' % netservices)

    call("ss-set net.services.installed true")
    logger.debug("Set net.services.installed = true")
    return 0

def install_gui():
    os.chdir("/var/tmp")

    call("echo fase 1 - clone api node project... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    call("curl -sL https://deb.nodesource.com/setup_6.x | sudo -E bash -")
    call("sudo apt-get install -y nodejs")
    call("git clone https://github.com/jiponsI2cat/cnsmo-api.git")
    call("echo fase 2 - install api node dependencies... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    os.chdir("/var/tmp/cnsmo-api")
    call("npm install")
    PORT = "8081"
    BASE_URL = "/api/v1"
    call("echo '\"use strict\";\n\nmodule.exports = {\n  BASE_URL: \""+BASE_URL+"\",\n  MONGO_URL: \"mongodb://localhost/cnsmo\",\n  DOMAIN: \"127.0.0.1\",\n  PROTOCOL: \"http\",\n  port: "+PORT+",\n  SWAGGER: true,\n  JWT_SECRET: \"cnsmosecret\",\n  TOKEN_EXPIRATION_DAYS: 10,\n};' > config/env/production.js")
    
    call("echo fase 3 - retrive host ip and generate environment.prod.ts file... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    os.chdir("/var/tmp/cnsmo-api/node_modules/cnsmo_web/src/environments")
    IPADDR = call('ss-get hostname').rstrip('\n')
    aux = "http://"+str(IPADDR)+":"+PORT+BASE_URL
    call("echo 'export const environment = {\n production: true,\n api: \"%s\",\n authUrl: \"/authenticate\"\n };' > environment.prod.ts " % aux)
    os.chdir("/var/tmp/cnsmo-api/node_modules/cnsmo_web")

    call("echo fase 4 - install cnsmo_web dependencies... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    call("sudo npm install -g @angular/cli@1.3.2")
    call("npm install --save-dev @angular/cli@1.3.2")
    call("npm install")

    call("echo fase 5 - building cnsmo_web...  >> /var/tmp/slipstream/cnsmo_api_gui.log")
    call("ng build --prod --aot=false")
    os.chdir("/var/tmp/cnsmo-api")
    ss_user = call('ss-get cnsmo.user').rstrip('\n')
    password = ""
    password = call('ss-random').rstrip('\n')
    resp = call('ss-set cnsmo.password %s' % password)

    call("echo fase 6 - retrive access credentials and generating config file... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    call("echo '{\"credentials\": {\"username\": \"%s\",\"password\": \"%s\"}}' > /var/tmp/cnsmo-api/core/config/initConfig.json" % (ss_user,password))
    call("sudo npm install pm2@latest -g")
    call("echo fase 7 - starting process... >> /var/tmp/slipstream/cnsmo_api_gui.log")
    call("pm2 start process.yml")
    call("echo Done - API and UI installed correctly >> /var/tmp/slipstream/cnsmo_api_gui.log")

def postinst_sdn_and_wait():
    logger = logging.getLogger(__name__)
    logger.debug("Postinstall SDN...")
    return postinstallsdn()

def get_net_services_to_enable():
    """
    :return: A list of strings representing which services must be enabled. e.g. ['vpn', 'sdn', 'fw', 'lb']
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


def config_logging():
    logging.basicConfig(filename='cnsmo-integrated-postinstall.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG,
                        disable_existing_loggers=False)

if __name__ == "__main__":
    main()

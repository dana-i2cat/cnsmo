import getopt
import json
import os
import sys
import subprocess

call = lambda command: subprocess.call(command, shell=True)


path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager


def get_app_request(host, port, service_id, lb_address, lb_port, lb_mode, lb_backend_servers):

    bind_address = "0.0.0.0"

    gitBranch = call('ss-get --timeout=500 net.i2cat.cnsmo.git.branch')

    d = dict(service_id=service_id,

             trigger='python configurator.py -a %s -p %s -s %s -t %s -m %s -b %s' % (bind_address, port, lb_address, lb_port, lb_mode, lb_backend_servers),

             resources = ["https://raw.githubusercontent.com/dana-i2cat/cnsmo/"+str(gitBranch)+"/src/main/python/net/i2cat/cnsmoservices/lb/app/configurator.py",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/lb/start.bash",
                          ],
             dependencies=[],
             endpoints=[{"uri":"http://%s:%s/lb/configs/haproxy/" %(host, port), "driver":"REST", "logic":"get", "name":"get_haproxy_config"},
                        {"uri":"http://%s:%s/lb/configs/docker/" %(host, port), "driver":"REST", "logic":"get", "name":"get_dockerfile"},])
    return d


def launch_configurator(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers):

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager(redis_address, service_id, "LBConfigManager", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request(host, port, service_id, lb_address, lb_port, lb_mode, lb_backend_servers))
    configurer.launch_service(service_id)


def main(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers):
    launch_configurator(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers)


if __name__ == "__main__":

    # Usage:
    # python configurator.py -a 127.0.0.1 -p 9097 -r 127.0.0.1:6379 -s LBConfig-8008 --lb-address=127.0.0.1 --lb-port=8008 --lb-mode=roundrobin --lb-backend-servers='["127.0.0.1:8080", "127.0.0.1:8081"]'

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", ["lb-address=", "lb-port=", "lb-mode=", "lb-backend-servers="])

    host = "0.0.0.0"
    port = "9096"
    redis_address = "127.0.0.1:6379"
    service_id = "LBConfig"
    lb_mode = "roundrobin"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg
        elif opt == "--lb-address":
            lb_address = arg
        elif opt == "--lb-port":
            lb_port = arg
        elif opt == "--lb-mode":
            lb_mode = arg
        elif opt == "--lb-backend-servers":
            lb_backend_servers = json.loads(arg)

    main(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers)

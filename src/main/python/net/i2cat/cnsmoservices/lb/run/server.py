import sys
import os
import time
import getopt
import subprocess

call = lambda command: subprocess.call(command, shell=True)

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager


def get_server_app_request(host, port, service_id, lb_port):

    bind_address = "0.0.0.0"

    gitBranch = call('ss-get --timeout=500 net.i2cat.cnsmo.git.branch')

    d = dict(service_id=service_id,
             trigger='python server.py -a %s -p %s -t %s -w "$(pwd)"' % (bind_address, port, lb_port),
             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/"+str(gitBranch)+"/src/main/python/net/i2cat/cnsmoservices/lb/app/server.py",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/lb/start.bash",],
             dependencies=[],
             endpoints=[{"uri":"http://%s:%s/lb/server/config/" %(host, port), "driver":"REST", "logic":"upload",
                         "name":"set_haproxy_config"},
                        {"uri":"http://%s:%s/lb/server/docker/" %(host, port), "driver":"REST", "logic":"upload",
                         "name":"set_docker"},
                        {"uri": "http://%s:%s/lb/server/build/" % (host, port), "driver": "REST", "logic": "post",
                         "name": "build_lb"},
                        {"uri": "http://%s:%s/lb/server/start/" % (host, port), "driver": "REST", "logic": "post",
                         "name": "start_lb"},
                        ])
    return d


def launch_server(host, port, redis_address, service_id, lb_port):

    bash_deployer = BashDeployer(None)
    server = CNSMOManager(redis_address, service_id, "LBServer", bash_deployer, None)
    server.start()
    time.sleep(0.5)
    server.compose_service(**get_server_app_request(host, port, service_id, lb_port))
    server.launch_service(service_id)


def main(host, port, redis_address, service_id, lb_port):
    launch_server(host, port, redis_address, service_id, lb_port)


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:t:", ["lb-port="])

    host = "0.0.0.0"
    port = "9097"
    redis_address = "127.0.0.1:6379"
    service_id = "LBServer"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg
        elif opt == "-t" or opt == "--lb-port":
            lb_port = arg

    main(host, port, redis_address, service_id, lb_port)

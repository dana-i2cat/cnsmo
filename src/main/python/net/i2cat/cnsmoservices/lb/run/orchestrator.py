import getopt
import json
import os
import sys
import threading
import time

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmoservices.lb.manager.lbmanager import LBManager
from src.main.python.net.i2cat.cnsmoservices.lb.run.server import launch_server
from src.main.python.net.i2cat.cnsmoservices.lb.run.configurator import launch_configurator


def deploy_lb(host, redis_address, lb_port, lb_mode, lb_backend_servers):

    # define service ids
    config_sid = "LBConfigManager-{}".format(lb_port)
    server_sid = "LBServer-{}".format(lb_port)
    service_ids = [config_sid, server_sid]

    print("Retrieving backend servers")
    lb_backend_servers_str = ",".join(lb_backend_servers)
    print("Backend servers: " + lb_backend_servers_str)

    # run manager with previous ids, lb_backend_servers
    print("Launching manager")
    manager = LBManager(service_ids, lb_backend_servers_str, redis_address)
    # manager.start()
    tm = threading.Thread(target=manager.start)
    tm.start()

    # wait for it to be up
    time.sleep(5)

    # launch configurator with lb_mode, lb_backend_servers, lb_port, lb_address
    config_port = "20096"
    config_host = host
    lb_address = host
    print("Launching configurator")
    # launch_configurator(config_host, config_port, redis_address, config_sid, lb_address, lb_port, lb_mode, lb_backend_servers)
    tc = threading.Thread(target=launch_configurator, args=(config_host, config_port, redis_address, config_sid,
                                                            lb_address, lb_port, lb_mode, lb_backend_servers_str))
    tc.start()

    # launch server with lb_port
    server_port = "20097"
    server_host = host
    print("Launching server")
    # launch_server(server_host, server_port, redis_address, server_sid, lb_port)
    ts = threading.Thread(target=launch_server, args=(server_host, server_port, redis_address, server_sid, lb_port))
    ts.start()

    # deploy the lb
    manager.deploy_blocking()

if __name__ == "__main__":

    # Usage:
    # python orchestrator.py -a 127.0.0.1 -r 127.0.0.1:6379 --lb-port=8008 --lb-mode=roundrobin --lb-backend-servers='["127.0.0.1:8080", "127.0.0.1:8081"]'

    opts, _ = getopt.getopt(sys.argv[1:], "a:r:", ["lb-port=", "lb-mode=", "lb-backend-servers="])
    redis_address = "127.0.0.1:6379"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "--lb-port":
            lb_port = arg
        elif opt == "--lb-mode":
            lb_mode = arg
        elif opt == "--lb-backend-servers":
            lb_backend_servers = json.loads(arg)

    deploy_lb(host, redis_address, lb_port, lb_mode, lb_backend_servers)

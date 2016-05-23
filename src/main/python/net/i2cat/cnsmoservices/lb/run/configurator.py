import time
import os
import sys


def get_app_request(host, port, service_id, lb_address, lb_port, lb_mode, lb_backend_servers):

    d = dict(service_id=service_id,

             trigger= 'python configurator.py -a %s -p %s -s %s -t %s -m %s -b %s' %(host, port, lb_address, lb_port, lb_mode, lb_backend_servers),

             resources = ["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/main/python/net/i2cat/cnsmoservices/lb/app/configurator.py",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/lb/start.bash",
                          ],
             dependencies=[],
             endpoints=[{"uri":"http://%s:%s/lb/configs/haproxy/" %(host, port), "driver":"REST", "logic":"get", "name":"get_haproxy_config"},
                        {"uri":"http://%s:%s/lb/configs/docker/" %(host, port), "driver":"REST", "logic":"get", "name":"get_dockerfile"},])
    return d


def main(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers):

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager(redis_address, service_id, "LBConfigManager", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request(host, port, service_id, lb_address, lb_port, lb_mode, lb_backend_servers))
    configurer.launch_service(service_id)

if __name__ == "__main__":
    import sys
    import os
    import time
    import getopt

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../../"
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", ["lb-address=", "lb-port=", "lb-mode=", "lb-backend-servers="])

    host = "0.0.0.0"
    port = "9093"
    redis_address = "127.0.0.1:6379"
    service_id = "VPNConfig"
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
        elif opt == "--lb_port":
            lb_port = arg
        elif opt == "--lb-mode":
            lb_mode = arg
        elif opt == "--lb-backend-servers":
            lb_backend_servers = arg

    main(host, port, redis_address, service_id, lb_address, lb_port, lb_mode, lb_backend_servers)

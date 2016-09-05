

def get_app_request(host, port, service_id):

    bind_address = "0.0.0.0"

    d = dict(service_id=service_id,
             trigger='python client.py -a %s -p %s -w "$(pwd)"' % (bind_address, port),

             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/feature/use-ports-20000-25000/src/main/python/net/i2cat/cnsmoservices/vpn/app/client.py",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/client/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/client/tun_manager.sh",
                        ],

             dependencies=[],

             endpoints=[{"uri":"http://%s:%s/vpn/client/config/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_config"},
                        {"uri":"http://%s:%s/vpn/client/cert/ca/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                        {"uri":"http://%s:%s/vpn/client/cert/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                        {"uri":"http://%s:%s/vpn/client/key/" %(host, port),  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                        {"uri":"http://%s:%s/vpn/client/build/" %(host, port), "driver":"REST", "logic":"post", "name":"build_client"},
                        {"uri":"http://%s:%s/vpn/client/start/" %(host, port),  "driver":"REST", "logic":"post", "name":"start_client"},
                        {"uri":"http://%s:%s/vpn/server/stop/" %(host, port), "driver":"REST", "logic":"post", "name":"stop_client"},])
    return d


def main(host, port, redis_address, service_id):

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager(redis_address, service_id, "VPNClient", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request(host, port, service_id))
    configurer.launch_service(service_id)

    #while True:
    #    time.sleep(1)


if __name__ == "__main__":
    import sys
    import os
    import time
    import getopt

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", [])

    host = "0.0.0.0"
    port = "9092"
    redis_address = "127.0.0.1:6379"
    service_id = "ClientVPN"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg

    main(host, port, redis_address, service_id)

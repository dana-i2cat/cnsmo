def get_server_app_request(host, port, service_id):

    bind_address = "0.0.0.0"

    d = dict(service_id=service_id,
             trigger='python server.py -a %s -p %s' % (bind_address, port),
             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/SDNdevelop/src/main/python/net/i2cat/cnsmoservices/fw/app/server.py",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/develop/src/main/docker/fw/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/develop/src/main/docker/fw/sc-manager.py",],
             dependencies=[],
             endpoints=[{ "uri":"http://%s:%s/fw/" %(host, port), "driver":"REST", "logic":"post", "name":"add_rule"},
                        { "uri":"http://%s:%s/fw/" %(host, port), "driver":"REST", "logic":"delete", "name":"delete_rule"},])
    return d


def main(host, port, redis_address, service_id):

    bash_deployer = BashDeployer(None)
    server = CNSMOManager(redis_address, service_id, "FWServer", bash_deployer, None)
    server.start()
    time.sleep(0.5)
    server.compose_service(**get_server_app_request(host, port, service_id))
    server.launch_service(service_id)


if __name__ == "__main__":

    import sys
    import os
    import time
    import getopt

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", [])

    host = "0.0.0.0"
    port = "9095"
    redis_address = "127.0.0.1:6379"
    service_id = "ServerFW"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    main(host, port, redis_address, service_id)

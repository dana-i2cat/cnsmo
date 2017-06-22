import subprocess

call = lambda command: subprocess.call(command, shell=True)

def get_server_app_request(host, port, service_id):

    bind_address = "0.0.0.0"

    call("touch /var/tmp/abansgitbranch.txt")
    gitBranch = call('ss-get net.i2cat.cnsmo.git.branch')
    call("echo %s >> /var/tmp/abansgitbranch.txt" % gitBranch)

    d = dict(service_id=service_id,
             trigger='python server.py -a %s -p %s -w "$(pwd)"' %(bind_address, port),
             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/main/python/net/i2cat/cnsmoservices/vpn/app/server.py"% gitBranch,
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/server/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/server/tun_manager.sh",],
             dependencies=[],
             endpoints=[{ "uri":"http://%s:%s/vpn/server/dh/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_dh"},
                        { "uri":"http://%s:%s/vpn/server/config/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_config_file"},
                        { "uri":"http://%s:%s/vpn/server/cert/ca/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                        { "uri":"http://%s:%s/vpn/server/cert/server/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_server_cert"},
                        { "uri":"http://%s:%s/vpn/server/key/server/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_server_key"},
                        { "uri":"http://%s:%s/vpn/server/build/" %(host, port), "driver":"REST", "logic":"post", "name":"build_server"},
                        { "uri":"http://%s:%s/vpn/server/start/" %(host, port), "driver":"REST", "logic":"post", "name":"start_server"},
                        { "uri":"http://%s:%s/vpn/server/stop/" %(host, port), "driver":"REST", "logic":"post", "name":"stop_server"},
                        { "uri":"http://%s:%s/vpn/server/status/" %(host, port), "driver": "REST", "logic": "get", "name":"get_status"},
                        ]
             )
    return d


def main(host, port, redis_address, service_id):

    bash_deployer = BashDeployer(None)
    server = CNSMOManager(redis_address, service_id, "VPNServer", bash_deployer, None)
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
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", [])

    host = "0.0.0.0"
    port = "9092"
    redis_address = "127.0.0.1:6379"
    service_id = "ServerVPN"

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

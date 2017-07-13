import time
import os
import sys
import subprocess

def get_app_request(host, port, service_id, vpn_server_address, vpn_server_port, vpn_address):

    bind_address = "0.0.0.0"

    call = lambda command: subprocess.check_output(command, shell=True)

    os.chdir("/var/tmp/slipstream/cnsmo/cnsmo")

    gitBranch = call('git branch').rstrip('\n').lstrip('* ')

    d = dict(service_id=service_id,
             trigger= 'mkdir -p keys && chmod +x "$(pwd)"/build-* && python configurator.py -a %s -p %s -w "$(pwd)"/keys/ -s %s -m %s -v %s -o %s' % (bind_address, port, vpn_server_address, vpn_mask, vpn_address, vpn_server_port),
             resources = ["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/main/python/net/i2cat/cnsmoservices/vpn/app/configurator.py" % gitBranch,
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_ca.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_client.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_index.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_server.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/build-ca",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/build-key",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/build-key-server",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/vars",
                          ],
             dependencies=[],
             endpoints=[{"uri":"http://%s:%s/vpn/configs/dh/" %(host, port), "driver":"REST", "logic":"get", "name":"get_dh"},
                        {"uri":"http://%s:%s/vpn/configs/server/" %(host, port), "driver":"REST", "logic":"get", "name":"get_server_config"},
                        {"uri":"http://%s:%s/vpn/configs/client/{param}/" %(host, port), "driver":"REST", "logic":"get", "name":"get_client_config"},
                        {"uri":"http://%s:%s/vpn/configs/certs/ca/" %(host, port), "driver":"REST", "logic":"get", "name":"get_ca_cert"},
                        {"uri":"http://%s:%s/vpn/configs/certs/client/{param}/" %(host, port), "driver":"REST", "logic":"get", "name":"get_client_cert"},
                        {"uri":"http://%s:%s/vpn/configs/keys/client/{param}/" %(host, port), "driver":"REST", "logic":"get", "name":"get_client_key"},
                        {"uri":"http://%s:%s/vpn/configs/certs/server/" %(host, port), "driver":"REST", "logic":"get", "name":"get_server_cert"},
                        {"uri":"http://%s:%s/vpn/configs/keys/server/" %(host, port), "driver":"REST", "logic":"get", "name":"get_server_key"},
                        {"uri":"http://%s:%s/vpn/configs/certs/ca/" %(host, port), "driver":"REST", "logic":"post", "name":"generate_ca_cert"},
                        {"uri":"http://%s:%s/vpn/configs/certs/client/{param}/" %(host, port), "driver":"REST", "logic":"post", "name":"generate_client_cert"},
                        {"uri":"http://%s:%s/vpn/configs/certs/server/" %(host, port), "driver":"REST", "logic":"post", "name":"generate_server_cert"},
                        {"uri":"http://%s:%s/vpn/configs/status/" %(host, port), "driver": "REST", "logic": "get", "name":"get_status"},
                        ]
             )
    return d


def main(host, port, redis_address, service_id, vpn_server_address, vpn_server_port, vpn_address, vpn_port):

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager(redis_address, service_id, "VPNConfigManager", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request(host, port,service_id, vpn_server_address, vpn_server_port, vpn_address))
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

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", ["vpn-server-ip=", "vpn-server-port=", "vpn-address=", "vpn-mask="])

    host = "0.0.0.0"
    port = "9093"
    redis_address = "127.0.0.1:6379"
    service_id = "VPNConfig"
    vpn_server_ip = "1.1.1.1"
    vpn_server_port = "1194"
    vpn_address = "10.10.10.0"
    vpn_mask = "255.255.255.0"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg
        elif opt == "--vpn-server-ip":
            vpn_server_ip = arg
        elif opt == "--vpn-server-port":
            vpn_server_port = arg
        elif opt == "--vpn-address":
            vpn_address = arg
        elif opt == "--vpn-mask":
            vpn_mask = arg

    main(host, port, redis_address, service_id, vpn_server_ip, vpn_server_port, vpn_address, vpn_mask)

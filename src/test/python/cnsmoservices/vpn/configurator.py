import time
import os
import sys
import subprocess

def get_app_request():

    d = dict(service_id="VPNConfigurer",
             # trigger= 'python configurator.py -a 127.0.0.1 -p 9093 -w "$( cd "$( dirname "$0" )" && pwd )"/keys/ -s 84.88.40.11 -m 255.255.255.0 -v 10.10.10 -o 1194',
             trigger= 'mkdir -p keys && python configurator.py -a 127.0.0.1 -p 9093 -w "$(pwd)"/keys/ -s 84.88.40.11 -m 255.255.255.0 -v 10.10.10 -o 1194',

             resources = ["https://raw.githubusercontent.com/dana-i2cat/cnsmo/SDNdevelop/src/main/python/net/i2cat/cnsmoservices/vpn/app/configurator.py",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_ca.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_client.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_index.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/gen_server.sh",
                          "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/easy-rsa/vars",
                          ],
             dependencies=[],
             endpoints=[{"uri":"http://127.0.0.1:9093/vpn/configs/dh/", "driver":"REST", "logic":"get", "name":"get_dh"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/server/", "driver":"REST", "logic":"get", "name":"get_server_config"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/client/", "driver":"REST", "logic":"get", "name":"get_client_config"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/ca/", "driver":"REST", "logic":"get", "name":"get_ca_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"get", "name":"get_client_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/keys/client/", "driver":"REST", "logic":"get", "name":"get_client_key"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"get", "name":"get_server_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/keys/server/", "driver":"REST", "logic":"get", "name":"get_server_key"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/ca/", "driver":"REST", "logic":"post", "name":"generate_ca_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"post", "name":"generate_client_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"post", "name":"generate_server_cert"},])
    return d


def main():

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager("localhost:6379", "configurer", "CredentialManager", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request())
    configurer.launch_service("VPNConfigurer")

    while True:
        time.sleep(1)


if __name__== "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../../"
    if not src_dir in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    main()

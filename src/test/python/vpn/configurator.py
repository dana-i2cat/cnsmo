import threading
import time
from main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager


def get_app_request():

    d = dict(service_id="VPNConfigurer",
             trigger= 'python configurator.py -a 127.0.0.1 -p 9093 -w "$( cd "$( dirname "$0" )" && pwd )"/keys/ -s 84.88.40.11 -m 255.255.255.0 -v 10.10.10 -o 1194',
             resources = ["http://stash.i2cat.net/projects/CYCLONE/repos/cnsmo/browse/src/main/python/net/i2cat/cnsmo/app/vpn/configurator.py?at=03619b943323bf27a581afe54f0259001239f2ad&raw",
                          "http://stash.i2cat.net/projects/CYCLONE/repos/network-services/browse/src/main/docker/vpn/easy-rsa/gen_ca.sh?at=7efa386719fabd68b4ab29a91dda65748b6dd70c&raw",
                          "http://stash.i2cat.net/projects/CYCLONE/repos/network-services/browse/src/main/docker/vpn/easy-rsa/gen_client.sh?at=7efa386719fabd68b4ab29a91dda65748b6dd70c&raw",
                          "http://stash.i2cat.net/projects/CYCLONE/repos/network-services/browse/src/main/docker/vpn/easy-rsa/gen_index.sh?at=7efa386719fabd68b4ab29a91dda65748b6dd70c&raw",
                          "http://stash.i2cat.net/projects/CYCLONE/repos/network-services/browse/src/main/docker/vpn/easy-rsa/gen_server.sh?at=7efa386719fabd68b4ab29a91dda65748b6dd70c&raw",
                          "http://stash.i2cat.net/projects/CYCLONE/repos/network-services/browse/src/main/docker/vpn/easy-rsa/vars?at=72fac7ee5870334d7a8ee13f7982200dea03ce46&raw",
                          ],
             dependencies=[],
             endpoints=[{ "uri":"http://127.0.0.1:9093/server/{param}", "driver":"REST", "logic":"get", "name":"start"}])
    return d


def main():

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager("localhost:6379", "configurer", "CredentialManager", bash_deployer, None)
    configurer.start()
    time.sleep(0.5)
    configurer.compose_service(**get_app_request())
    configurer.launch_service("VPNConfigurer")


if __name__== "__main__":
    main()
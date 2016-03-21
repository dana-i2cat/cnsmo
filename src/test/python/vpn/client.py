import sys
import os
import time


def get_app_request():

    d = dict(service_id="ClientVPN",
             trigger='python client.py -a 127.0.0.1 -p 9092 -w "$(pwd)"',

             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/main/python/net/i2cat/cnsmo/app/vpn/client.py"
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/feature/script-install-docker/src/main/docker/vpn/client/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/feature/script-install-docker/src/main/docker/vpn/client/tun_manager.sh",
                        ],

             dependencies=[],

             endpoints=[{"uri":"/vpn/client/config/", "driver":"REST", "logic":"get", "name":"set_config"},
                        {"uri":"/vpn/client/cert/ca/", "driver":"REST", "logic":"get", "name":"set_ca"},
                        {"uri":"/vpn/client/cert/", "driver":"REST", "logic":"get", "name":"set_client_cert"},
                        {"uri":"/vpn/client/key/",  "driver":"REST", "logic":"get", "name":"set_client_key"},
                        {"uri":"/vpn/client/build/", "driver":"REST", "logic":"get", "name":"build_client"},
                        {"uri":"/vpn/client/start/",  "driver":"REST", "logic":"get", "name":"start"},
                        {"uri":"/vpn/server/stop/", "driver":"REST", "logic":"get", "name":"stop"},])
    return d


def main():

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager("localhost:6379", "client", "ClientVPN", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request())
    configurer.launch_service("ClientVPN")

    while True:
        time.sleep(1)


if __name__ == "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../"
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    main()
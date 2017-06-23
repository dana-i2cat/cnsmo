import sys
import os
import time
import subprocess

def get_app_request():

    gitBranch = subprocess.check_output("echo $(ss-get --timeout=1000 net.i2cat.cnsmo.git.branch)")

    d = dict(service_id="ClientVPN",
             trigger='python client.py -a 127.0.0.1 -p 9092 -w "$(pwd)"',

             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/main/python/net/i2cat/cnsmoservices/vpn/app/client.py" % gitBranch,
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/client/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/master/src/main/docker/vpn/client/tun_manager.sh",
                        ],

             dependencies=[],

             endpoints=[{"uri":"http://127.0.0.1:9092/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                        {"uri":"http://127.0.0.1:9092/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca"},
                        {"uri":"http://127.0.0.1:9092/vpn/client/cert/", "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                        {"uri":"http://127.0.0.1:9092/vpn/client/key/",  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                        {"uri":"http://127.0.0.1:9092/vpn/client/build/", "driver":"REST", "logic":"post", "name":"build_client"},
                        {"uri":"http://127.0.0.1:9092/vpn/client/start/",  "driver":"REST", "logic":"post", "name":"start"},
                        {"uri":"http://127.0.0.1:9092/vpn/server/stop/", "driver":"REST", "logic":"post", "name":"stop"},])
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
    src_dir = configurator_path + "/../../../../../"
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    main()
import time
import sys
import os
vds_path = os.path.dirname(os.path.abspath(__file__))
orchestrator_src_dir = vds_path + "/../../../"
if orchestrator_src_dir not in sys.path:
    sys.path.append(orchestrator_src_dir)
from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager


def get_server_app_request():

    d = dict(service_id="VPNServerService",
             trigger= 'python server.py -a 127.0.0.1 -p 9094 -w "$(pwd)"',
             resources = ["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/main/python/net/i2cat/cnsmo/app/vpn/server.py",],
             dependencies=[],
             endpoints=[{ "uri":"http://127.0.0.1:9094/server/{param}", "driver":"REST", "logic":"get", "name":"start"}])
    return d


def main():

    bash_deployer = BashDeployer(None)
    server = CNSMOManager("localhost:6379", "server", "VPNServer", bash_deployer, None)
    server.start()
    time.sleep(0.5)
    server.compose_service(**get_server_app_request())
    server.launch_service("VPNServerService")

    while True:
        time.sleep(1)


if __name__== "__main__":
    main()

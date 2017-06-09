import time
import sys
import os


def get_server_app_request():

    d = dict(service_id="VPNServerService",
             trigger='python server.py -a 127.0.0.1 -p 9094 -w "$(pwd)"',
             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/SDNdevelop/src/main/python/net/i2cat/cnsmoservices/vpn/app/server.py",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/SDNdevelop/src/main/docker/vpn/server/Dockerfile",
                        "https://raw.githubusercontent.com/dana-i2cat/cnsmo-net-services/SDNdevelop/src/main/docker/vpn/server/tun_manager.sh",],
             dependencies=[],
             endpoints=[{ "uri":"http://127.0.0.1:9094/vpn/server/dh/", "driver":"REST", "logic":"upload", "name":"set_dh"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/config/", "driver":"REST", "logic":"upload", "name":"set_config_file"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/cert/server/", "driver":"REST", "logic":"upload", "name":"set_server_cert"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/key/server/", "driver":"REST", "logic":"upload", "name":"set_server_key"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/build/", "driver":"REST", "logic":"post", "name":"build_server"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/start/", "driver":"REST", "logic":"post", "name":"start_server"},
                        { "uri":"http://127.0.0.1:9094/vpn/server/stop/", "driver":"REST", "logic":"post", "name":"stop_server"},])
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


if __name__ == "__main__":

    server_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = server_path + "/../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    main()

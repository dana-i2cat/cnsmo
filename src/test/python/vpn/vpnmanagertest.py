import os
import sys
import unittest
import threading


class ConfiguratorServiceTest(unittest.TestCase):

    def setUp(self):
        redis_address = "localhost:6379"
        bash_deployer = BashDeployer(None)

        # Configuring each service in a different Thread to make things feel real
        self.configurator_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "VPNConfigurer-234", "VPNConfigurer", bash_deployer, self.get_configurator_app_request()))

        self.server_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "VPNServerService-234", "VPNServer", bash_deployer, self.get_server_app_request()))

        self.client1_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "ClientVPN-1-234", "VPNClient", bash_deployer, self.get_client1_app_request()))

        self.client2_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "ClientVPN-2-234", "VPNClient", bash_deployer, self.get_client2_app_request()))

        self.vpn_manager = VPNManager(redis_address)
        self.vpn_manager_t = threading.Thread(target=self.vpn_manager.start)

        self.configurator_t.start()
        self.server_t.start()
        #self.client1_t.start()
        #self.client2_t.start()
        # self.vpn_manager_t.start()
        self.vpn_manager.start()

    def test_vpn_manager_should_register_all_services(self):
        print self.vpn_manager

    def deploy_service(self, redis_address, service_name, service_type, deployer, request):

        service_manager = CNSMOManager(redis_address, service_name, service_type, deployer, None)
        service_manager.start()
        service_manager.compose_service(**request)
        service_manager.launch_service(service_name)

        return service_manager

    def get_server_app_request(self):
        d = dict(service_id="VPNServerService-234",
                 trigger='python server.py -a 127.0.0.1 -p 9094 -w "$(pwd)"',
                 # using server.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/test/python/mock/server.py",],
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

    def get_client1_app_request(self):
        d = dict(service_id="ClientVPN-1-234",
                 trigger='python client.py -a 127.0.0.1 -p 9092 -w "$(pwd)"',
                 # using client.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/test/python/mock/client.py",],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9092/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/cert/", "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/key/",  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/build/", "driver":"REST", "logic":"post", "name":"build_client"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/start/",  "driver":"REST", "logic":"post", "name":"start"},
                            {"uri":"http://127.0.0.1:9092/vpn/server/stop/", "driver":"REST", "logic":"post", "name":"stop"},])
        return d

    def get_client2_app_request(self):
        d = dict(service_id="ClientVPN-2-234",
                 trigger='python client.py -a 127.0.0.1 -p 9091 -w "$(pwd)"',
                 # using client.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/test/python/mock/client.py",],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9091/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/cert/", "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/key/",  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/build/", "driver":"REST", "logic":"post", "name":"build_client"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/start/",  "driver":"REST", "logic":"post", "name":"start"},
                            {"uri":"http://127.0.0.1:9091/vpn/server/stop/", "driver":"REST", "logic":"post", "name":"stop"},])
        return d

    def get_configurator_app_request(self):
        d = dict(service_id="VPNConfigurer-234",
                 trigger='mkdir -p keys && python configuratorserver.py -a 127.0.0.1 -p 9093 -w "$(pwd)"/keys/ -s 84.88.40.11 -m 255.255.255.0 -v 10.10.10 -o 1194',
                 # using configuratorserver.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/master/src/test/python/mock/configuratorserver.py",],
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

if __name__ == "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../"
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
    from src.main.python.net.i2cat.cnsmo.manager.vpn import VPNManager

    unittest.main()

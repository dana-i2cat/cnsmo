import os
import sys
import threading
import time
import unittest

configurator_path = os.path.dirname(os.path.abspath(__file__))
src_dir = configurator_path + "/../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class ConfiguratorServiceTest(unittest.TestCase):

    def __init__(self):
        super(ConfiguratorServiceTest, self).__init__()

        # service threads
        self.vpn_manager_t = None
        self.configurator_t = None
        self.server_t = None
        self.client1_t = None
        self.client2_t = None

        # references to service objects
        self.vpn_manager = None

    def setUp(self):
        """
        Initializes all threads (without starting them), and the vpn_manager
        :return:
        """
        redis_address = "localhost:6379"
        bash_deployer = BashDeployer(None)

        system_state = SystemStateFactory.generate_system_state_manager("localhost:6379")
        system_state_t = threading.Thread(target=system_state.start)
        system_state_t.start()
        time.sleep(1)

        # Configuring each service in a different Thread to make things feel real
        self.configurator_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "VPNConfigurer-234", "VPNConfigManager", bash_deployer, self.get_configurator_app_request()))

        self.server_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "VPNServerService-234", "VPNServer", bash_deployer, self.get_server_app_request()))

        self.client1_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "ClientVPN-1-234", "VPNClient", bash_deployer, self.get_client1_app_request()))

        self.client2_t = threading.Thread(target=self.deploy_service, args=
            (redis_address, "ClientVPN-2-234", "VPNClient", bash_deployer, self.get_client2_app_request()))

        self.vpn_manager = VPNManager(redis_address)
        self.vpn_manager_t = threading.Thread(target=self.vpn_manager.start)

    # ######
    # TESTS
    # ######

    def test_vpn_manager_notices_when_services_get_registered(self):

        # before registering any client
        self.assertEqual(self.vpn_manager._VPNManager__client_services, set(),
                         "There should be no clients registered")
        self.client1_t.start()
        time.sleep(1)
        # after registering client1
        self.assertEqual(len(self.vpn_manager._VPNManager__client_services), 1,
                         "There should be one registered client service")
        self.client1_t.start()
        time.sleep(1)
        # after registering client2
        self.assertEqual(len(self.vpn_manager._VPNManager__client_services), 2,
                         "There should be 2 registered client services")

        # before registering configurator
        self.assertIsNone(self.vpn_manager._VPNManager__configuration_manager)
        self.configurator_t.start()
        time.sleep(1)
        # after registering configurator
        self.assertIsNotNone(self.vpn_manager._VPNManager__configuration_manager)

        # before registering server
        self.assertIsNone(self.vpn_manager._VPNManager__server_service)
        self.server_t.start()
        time.sleep(1)
        # after registering server
        self.assertIsNotNone(self.vpn_manager._VPNManager__server_service)

    def test_vpn_manager_gets_ready_when_configurator_and_server_are_registered(self):

        # before registering any service
        self.assertIsNone(self.vpn_manager._VPNManager__configuration_manager)
        self.assertIsNone(self.vpn_manager._VPNManager__server_service)
        self.assertEqual(self.vpn_manager._VPNManager__status, "Initializing",
                         "Before registering services manager status should be 'Initializing'")

        self.configurator_t.start()
        while not self.vpn_manager._VPNManager__configuration_manager:
            time.sleep(0.2)
        # after registering configurator

        self.assertEqual(self.vpn_manager._VPNManager__status, "Initializing",
                         "Before registering both configurator and server vpn_manager status should be 'Initializing'")

        self.server_t.start()
        while not self.vpn_manager._VPNManager__server_service:
            time.sleep(0.2)
        # after registering server

        if not self.vpn_manager._VPNManager__server_deployed:
            self.assertEqual(self.vpn_manager._VPNManager__status, "Deploying server",
                             "Having both configurator and server registered, " +
                             "vpn_manager status should be 'Deploying server'")

        while not self.vpn_manager._VPNManager__server_deployed:
            time.sleep(0.2)

        self.assertEqual(self.vpn_manager._VPNManager__status, "Listening",
                         "Having configurator registered and server already deployed, " +
                         "vpn_manager status should be 'Listening'")

    def test_vpn_manager_automatically_publishes_server_when_it_gets_ready(self):
        self.configurator_t.start()
        self.server_t.start()

        while self.vpn_manager._VPNManager__status is not "Listening":
            time.sleep(0.2)

        self.assertTrue(self.vpn_manager._VPNManager__server_deployed)

    def test_vpn_manager_publishes_clients_previously_registered_when_it_gets_ready(self):
        self.client1_t.start()
        while not self.vpn_manager._VPNManager__client_services:
            time.sleep(0.2)
        num_clients = len(self.vpn_manager._VPNManager__client_services)

        self.configurator_t.start()
        self.server_t.start()

        while self.vpn_manager._VPNManager__status is not "Listening":
            time.sleep(0.2)

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), num_clients,
                         "All client services registered before manager is listening, " +
                         "should be deployed when it gets to listening state")

    def test_vpn_manager_publishes_clients_upon_registration_when_it_is_ready(self):
        self.configurator_t.start()
        self.server_t.start()

        while self.vpn_manager._VPNManager__status is not "Listening":
            time.sleep(0.2)

        self.client1_t.start()
        while len(self.vpn_manager._VPNManager__client_services) != 1:
            time.sleep(0.2)

        time.sleep(10)

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), 1,
                         "All client services registered when manager is listening, " +
                         "should be deployed upon arrival")

        self.client2_t.start()
        while len(self.vpn_manager._VPNManager__client_services) != 2:
            time.sleep(0.2)

        time.sleep(10)

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), 2,
                         "All client services registered when manager is listening, " +
                         "should be deployed upon arrival")

    # ######
    # HELPER METHODS
    # ######

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
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/develop/src/test/python/cnsmoservices/vpn/mock/server.py",],
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
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/develop/src/test/python/cnsmoservices/vpn/mock/client.py",],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9092/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
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
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/develop/src/test/python/cnsmoservices/vpn/mock/client.py",],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9091/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
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
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/develop/src/test/python/cnsmoservices/vpn/mock/configuratorserver.py",],
                 dependencies=[],
                 endpoints=[{"uri":"http://127.0.0.1:9093/vpn/configs/dh/", "driver":"REST", "logic":"get", "name":"get_dh"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/server/", "driver":"REST", "logic":"get", "name":"get_server_config"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/client/{param}/", "driver":"REST", "logic":"get", "name":"get_client_config"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/ca/", "driver":"REST", "logic":"get", "name":"get_ca_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/{param}/", "driver":"REST", "logic":"get", "name":"get_client_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/keys/client/{param}/", "driver":"REST", "logic":"get", "name":"get_client_key"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"get", "name":"get_server_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/keys/server/", "driver":"REST", "logic":"get", "name":"get_server_key"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/ca/", "driver":"REST", "logic":"post", "name":"generate_ca_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/{param}/", "driver":"REST", "logic":"post", "name":"generate_client_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"post", "name":"generate_server_cert"},])
        return d


if __name__ == "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../../"
    if not src_dir in sys.path:
       sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
    from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager

    unittest.main()

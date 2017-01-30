import os
import sys
import threading
import time
import unittest
from random import randint


configurator_path = os.path.dirname(os.path.abspath(__file__))
src_dir = configurator_path + "/../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory
from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager


class ConfiguratorServiceTest(unittest.TestCase):

    def setUp(self):
        """
        Initializes all service managers (without starting them), and the vpn_manager. Starts the vpn_manager
        :return:
        """
        self.git_branch_name = "test/dyn-vpn-orch-workflow"

        redis_address = "localhost:6379"

        system_state = SystemStateFactory.generate_system_state_manager("localhost:6379")
        system_state_t = threading.Thread(target=system_state.start)
        system_state_t.start()
        time.sleep(1)

        setup_id = randint(1, 999999)
        service_id = "VPNConfigurer-234-" + str(setup_id)

        self.deploy_configurator = self.make_service_deployer(redis_address, service_id, "VPNConfigManager",
                                                              BashDeployer(None), self.get_configurator_app_request(service_id))

        service_id = "VPNServerService-234-" + str(setup_id)
        self.deploy_server = self.make_service_deployer(redis_address, service_id, "VPNServer",
                                                        BashDeployer(None), self.get_server_app_request(service_id))

        service_id = "ClientVPN-1-234-" + str(setup_id)
        self.deploy_client1 = self.make_service_deployer(redis_address, service_id, "VPNClient",
                                                         BashDeployer(None), self.get_client1_app_request(service_id))

        service_id = "ClientVPN-2-234-" + str(setup_id)
        self.deploy_client2 = self.make_service_deployer(redis_address, service_id, "VPNClient",
                                                         BashDeployer(None), self.get_client2_app_request(service_id))

        self.vpn_manager = VPNManager(redis_address)
        self.vpn_manager.start()

        self.client1_manager = None
        self.client2_manager = None
        self.configurator_manager = None
        self.server_manager = None
        print("SETUP COMPLETE")

    def tearDown(self):
        print("TEAR DOWN...")
        if self.client1_manager is not None:
            self.undeploy_service(self.client1_manager.get_name(), self.client1_manager)
            print("Undeployed client1")
        if self.client2_manager is not None:
            self.undeploy_service(self.client2_manager.get_name(), self.client2_manager)
            print("Undeployed client2")
        if self.configurator_manager is not None:
            self.undeploy_service(self.configurator_manager.get_name(), self.configurator_manager)
            print("Undeployed configurator")
        if self.server_manager is not None:
            self.undeploy_service(self.server_manager.get_name(), self.server_manager)
            print("Undeployed server")

        # self.vpn_manager.stop()
        self.vpn_manager = None
        time.sleep(10)
        print("TEAR DOWN COMPLETE")

    # ######
    # TESTS
    # ######

    def test_vpn_manager_notices_when_services_get_registered(self):

        # before registering any client
        self.assertFalse(self.vpn_manager._VPNManager__client_services,
                         "There should be no clients registered")
        self.client1_manager = self.deploy_client1()
        time.sleep(1)
        # after registering client1
        self.assertEqual(len(self.vpn_manager._VPNManager__client_services), 1,
                         "There should be one registered client service. Found %s" %
                         str(len(self.vpn_manager._VPNManager__client_services)))
        self.client2_manager = self.deploy_client2()
        time.sleep(1)
        # after registering client2
        self.assertEqual(len(self.vpn_manager._VPNManager__client_services), 2,
                         "There should be 2 registered client services. Found %s " %
                         str(len(self.vpn_manager._VPNManager__client_services)))

        # before registering configurator
        self.assertIsNone(self.vpn_manager._VPNManager__configuration_manager)
        self.configurator_manager = self.deploy_configurator()
        time.sleep(1)
        # after registering configurator
        self.assertIsNotNone(self.vpn_manager._VPNManager__configuration_manager)

        # before registering server
        self.assertIsNone(self.vpn_manager._VPNManager__server_service)
        self.server_manager = self.deploy_server()
        time.sleep(1)
        # after registering server
        self.assertIsNotNone(self.vpn_manager._VPNManager__server_service)

    def test_vpn_manager_gets_ready_when_configurator_and_server_are_registered(self):

        # before registering any service
        self.assertIsNone(self.vpn_manager._VPNManager__configuration_manager)
        self.assertIsNone(self.vpn_manager._VPNManager__server_service)
        self.assertEqual(self.vpn_manager._VPNManager__status, "initializing",
                         "Before registering services manager status should be 'initializing'. %s found."
                         % self.vpn_manager._VPNManager__status)

        self.configurator_manager = self.deploy_configurator()
        while not self.vpn_manager._VPNManager__configuration_manager:
            time.sleep(0.2)
        # after registering configurator

        self.assertEqual(self.vpn_manager._VPNManager__status, "initializing",
                         "Before registering both configurator and server vpn_manager status should be 'initializing'. %s found."
                         % self.vpn_manager._VPNManager__status)

        self.server_manager = self.deploy_server()
        while not self.vpn_manager._VPNManager__server_service:
            time.sleep(0.2)
        # after registering server

        if not self.vpn_manager._VPNManager__server_deployed:
            self.assertEqual(self.vpn_manager._VPNManager__status, "deploying server",
                             "Having both configurator and server registered, " +
                             "vpn_manager status should be 'deploying server'. %s found."
                             % self.vpn_manager._VPNManager__status)

        while not self.vpn_manager._VPNManager__server_deployed:
            time.sleep(0.2)

        self.assertEqual(self.vpn_manager._VPNManager__status, "listening",
                         "Having configurator registered and server already deployed, " +
                         "vpn_manager status should be 'listening'. %s found."
                         % self.vpn_manager._VPNManager__status)

    def test_vpn_manager_automatically_publishes_server_when_it_gets_ready(self):
        self.configurator_manager = self.deploy_configurator()
        self.server_manager = self.deploy_server()

        print("Waiting for VPNManager to get status == listening")
        waited = 0
        while (self.vpn_manager._VPNManager__status is not "listening") & (waited < 10):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.2)
            waited += 0.2
        if waited >= 10:
            print("Timeout! Waiting for VPNManager to get status == listening")

        self.assertEqual(self.vpn_manager._VPNManager__status, "listening",
                         "Having configurator registered and server already deployed, " +
                         "vpn_manager status should be 'listening'. %s found."
                         % self.vpn_manager._VPNManager__status)

        self.assertTrue(self.vpn_manager._VPNManager__server_deployed)

    def test_vpn_manager_publishes_clients_previously_registered_when_it_gets_ready(self):
        self.client1_manager = self.deploy_client1()
        while not self.vpn_manager._VPNManager__client_services:
            time.sleep(0.2)
        num_clients = len(self.vpn_manager._VPNManager__client_services)

        self.configurator_manager = self.deploy_configurator()
        self.server_manager = self.deploy_server()

        print("Waiting for VPNManager to get status == listening")
        waited = 0
        while (self.vpn_manager._VPNManager__status is not "listening") & (waited < 10):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.2)
            waited += 0.2
        if waited >= 10:
            print("Timeout! Waiting for VPNManager to get status == listening")

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), num_clients,
                         "All client services registered before manager is listening, " +
                         "should be deployed when it gets to listening state")

    def test_vpn_manager_publishes_clients_upon_registration_when_it_is_ready(self):
        self.configurator_manager = self.deploy_configurator()
        self.server_manager = self.deploy_server()

        print("Waiting for VPNManager to get status == listening")
        waited = 0
        while (self.vpn_manager._VPNManager__status is not "listening") & (waited < 10):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.2)
            waited += 0.2
        if waited >= 10:
            print("Timeout! Waiting for VPNManager to get status == listening")
            self.fail("Timeout! Waiting for VPNManager to get status == listening")

        self.client1_manager = self.deploy_client1()
        waited = 0
        while (len(self.vpn_manager._VPNManager__client_services) != 1) & (waited < 10):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.2)
            waited += 0.2
        if waited >= 10:
            print("Timeout! Waiting for VPNManager to get client1 registered")
            self.fail("Timeout! Waiting for VPNManager to get client1 registered")

        print("Sleeping to let VPNClient to be configured")
        time.sleep(10)

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), 1,
                         "All client services registered when manager is listening, " +
                         "should be deployed upon arrival")

        self.client2_manager = self.deploy_client2()
        waited = 0
        while (len(self.vpn_manager._VPNManager__client_services) != 2) & (waited < 10):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(0.2)
            waited += 0.2
        if waited >= 10:
            print("Timeout! Waiting for VPNManager to get client2 registered")
            self.fail("Timeout! Waiting for VPNManager to get client2 registered")

        print("Sleeping to let VPNClient to be configured")
        time.sleep(10)

        self.assertEqual(len(self.vpn_manager._VPNManager__deployed_client_services), 2,
                         "All client services registered when manager is listening, " +
                         "should be deployed upon arrival")

    # ######
    # HELPER METHODS
    # ######

    def make_service_deployer(self, redis_address, service_name, service_type, deployer, request):
        """
        Generates a function to deploy the service specified by given arguments.
        Implements a closure to create a context for the deploy_service function, with given arguments
        :param redis_address:
        :param service_name:
        :param service_type:
        :param deployer:
        :param request:
        :return:
        """
        def deploy_service():
            service_manager = CNSMOManager(redis_address, service_name, service_type, deployer, None)
            service_manager.start()
            service_manager.compose_service(**request)
            service_manager.launch_service(service_name)
            return service_manager

        return deploy_service

    def undeploy_service(self, service_id, service_manager):
        service_manager.stop_service(service_id)
        service_manager.stop()

    def get_server_app_request(self, service_id):
        d = dict(service_id=service_id,
                 trigger='python server.py -a 127.0.0.1 -p 9094 -w "$(pwd)"',
                 # using server.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/test/python/cnsmoservices/vpn/mock/server.py" % self.git_branch_name,],
                 dependencies=[],
                 endpoints=[{ "uri":"http://127.0.0.1:9094/vpn/server/dh/", "driver":"REST", "logic":"upload", "name":"set_dh"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/config/", "driver":"REST", "logic":"upload", "name":"set_config_file"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/cert/server/", "driver":"REST", "logic":"upload", "name":"set_server_cert"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/key/server/", "driver":"REST", "logic":"upload", "name":"set_server_key"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/build/", "driver":"REST", "logic":"post", "name":"build_server"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/start/", "driver":"REST", "logic":"post", "name":"start_server"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/stop/", "driver":"REST", "logic":"post", "name":"stop_server"},
                            { "uri":"http://127.0.0.1:9094/vpn/server/status/", "driver": "REST", "logic": "get", "name":"get_status"},])
        return d

    def get_client1_app_request(self, service_id):
        d = dict(service_id=service_id,
                 trigger='python client.py -a 127.0.0.1 -p 9092 -w "$(pwd)"',
                 # using client.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/test/python/cnsmoservices/vpn/mock/client.py" % self.git_branch_name,],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9092/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/cert/", "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/key/",  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/build/", "driver":"REST", "logic":"post", "name":"build_client"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/start/",  "driver":"REST", "logic":"post", "name":"start_client"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/stop/", "driver":"REST", "logic":"post", "name":"stop_client"},
                            {"uri":"http://127.0.0.1:9092/vpn/client/status/", "driver": "REST", "logic": "get",
                             "name": "get_status"}, ])
        return d

    def get_client2_app_request(self, service_id):
        d = dict(service_id=service_id,
                 trigger='python client.py -a 127.0.0.1 -p 9091 -w "$(pwd)"',
                 # using client.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/test/python/cnsmoservices/vpn/mock/client.py" % self.git_branch_name,],

                 dependencies=[],

                 endpoints=[{"uri":"http://127.0.0.1:9091/vpn/client/config/", "driver":"REST", "logic":"upload", "name":"set_config"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/cert/ca/", "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/cert/", "driver":"REST", "logic":"upload", "name":"set_client_cert"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/key/",  "driver":"REST", "logic":"upload", "name":"set_client_key"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/build/", "driver":"REST", "logic":"post", "name":"build_client"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/start/",  "driver":"REST", "logic":"post", "name":"start_client"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/stop/", "driver":"REST", "logic":"post", "name":"stop_client"},
                            {"uri":"http://127.0.0.1:9091/vpn/client/status/", "driver": "REST", "logic": "get",
                             "name": "get_status"}, ])
        return d

    def get_configurator_app_request(self, service_id):
        d = dict(service_id=service_id,
                 trigger='mkdir -p keys && python configuratorserver.py -a 127.0.0.1 -p 9093 -w "$(pwd)"/keys/ -s 84.88.40.11 -m 255.255.255.0 -v 10.10.10 -o 1194',
                 # using configuratorserver.py mock, which does not require any other resource
                 resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/test/python/cnsmoservices/vpn/mock/configuratorserver.py" % self.git_branch_name,],
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
                            {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"post", "name":"generate_server_cert"},
                            {"uri":"http://127.0.0.1:9093/vpn/configs/status/", "driver": "REST", "logic": "get",
                             "name": "get_status"}, ])
        return d


if __name__ == "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
    from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager

    unittest.main()

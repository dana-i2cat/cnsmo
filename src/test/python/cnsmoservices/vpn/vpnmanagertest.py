import os
import sys
import threading
import time
import unittest

configurator_path = os.path.dirname(os.path.abspath(__file__))
src_dir = configurator_path + "/../../../../../"
if not src_dir in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class ConfiguratorServiceTest(unittest.TestCase):

    def setUp(self):
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


        self.vpn_manager.start()
        time.sleep(5)
        self.configurator_t.start()
        time.sleep(1)
        self.server_t.start()
        time.sleep(1)
        self.client1_t.start()
        time.sleep(1)
        self.client2_t.start()
        time.sleep(3)

    def test_vpn_manager_should_register_all_services(self):

        print "VPNMANAGER:", self.vpn_manager.__dict__
        time.sleep(2)
        self.assertTrue(self.vpn_manager._VPNManager__server_service)
        self.assertTrue(self.vpn_manager._VPNManager__configuration_manager)
        self.assertTrue(self.vpn_manager._VPNManager__client_services)
        self.assertEquals(2, len(self.vpn_manager._VPNManager__client_services))
        print "ALL Service are created"
        print "Checking the VPN Internal State..."
        self.assertEquals("ready", self.vpn_manager._VPNManager__status)

        configurator = self.vpn_manager._VPNManager__configuration_manager
        client_1, client_2 = self.vpn_manager._VPNManager__client_services
        server = self.vpn_manager._VPNManager__server_service

        print "Testing Configurator"
        print configurator.__dict__
        print configurator.generate_ca_cert(None)
        print configurator.generate_server_cert(None)

        dh = configurator.get_dh(None).content
        ca = configurator.get_ca_cert(None).content
        server_cert =  configurator.get_server_cert(None).content
        server_key = configurator.get_server_key(None).content
        config = configurator.get_server_config(None).content

        self.assertEquals("GotDH", dh)
        self.assertEquals("GotCACert", ca)
        self.assertEquals("GotServerKey", server_key)
        self.assertEquals("GotServerCert", server_cert)
        self.assertEquals("GotServerConfig", config)

        print "Starting Server Test"
        print dh

        dh_added = server.set_dh({"file":("test", dh)})

        ca_added = server.set_ca_cert({"file":("test", ca)})
        server_cert_added = server.set_server_cert({"file":("test", server_cert)})
        server_key_added = server.set_server_key({"file":("test", server_key)})
        server_config_added = server.set_config_file({"file":("test", config)})

        print dh_added.content
        print ca_added.content
        print server_cert_added.content
        print server_key_added.content
        print server_config_added.content

        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/ca.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/dh2048.pem"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/server.key"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/server.conf"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/server.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/VPNServerService-234/server.py"))

        print "Testing Client 1"
        client_id = "Client-1"
        client_config_generated = configurator.generate_client_cert(client_id, None).content
        self.assertEquals("ClientCert " + client_id, client_config_generated)

        client_cert = configurator.get_client_cert(client_id).content
        client_key = configurator.get_client_key(client_id).content
        client_config = configurator.get_client_config(client_id).content

        self.assertEquals("GotClientKey " + client_id, client_key)
        self.assertEquals("GotClientCert " + client_id, client_cert)
        self.assertEquals("GotClientConfig " + client_id, client_config)

        client_1.set_ca_cert({"file":("test", ca)})
        client_1.set_config({"file":("test", client_config)})
        client_1.set_client_cert({"file":("test", client_cert)})
        client_1.set_client_key({"file":("test", client_key)})

        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-1-234/ca.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-1-234/client.key"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-1-234/client.conf"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-1-234/client.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-1-234/client.py"))


        print "Testing Client 2"
        client_id = "Client-2"
        client_config_generated = configurator.generate_client_cert(client_id, None).content
        self.assertEquals("ClientCert " + client_id, client_config_generated)

        client_cert = configurator.get_client_cert(client_id).content
        client_key = configurator.get_client_key(client_id).content
        client_config = configurator.get_client_config(client_id).content

        self.assertEquals("GotClientKey " + client_id, client_key)
        self.assertEquals("GotClientCert " + client_id, client_cert)
        self.assertEquals("GotClientConfig " + client_id, client_config)

        client_2.set_ca_cert({"file":("test", ca)})
        client_2.set_config({"file":("test", client_config)})
        client_2.set_client_cert({"file":("test", client_cert)})
        client_2.set_client_key({"file":("test", client_key)})

        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-2-234/ca.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-2-234/client.key"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-2-234/client.conf"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-2-234/client.crt"))
        self.assertTrue(os.path.exists("/home/CNSMO/ENVS/ClientVPN-2-234/client.py"))

        print "Test Done!"


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

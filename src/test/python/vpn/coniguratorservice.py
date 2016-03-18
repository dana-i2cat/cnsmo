import unittest
import threading
from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
from src.test.python.mock.configuratorserver import main


class ConfiguratorServiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        t = threading.Thread(target=main, args=("127.0.0.1",9093))
        t.start()

    def setUp(self):
        self.app_request = self.given_this_endpoints()
        self.service = ServiceMaker().make_service("configurator", self.app_request["endpoints"])

    def test_should_create_service(self):
        print self.service
        print self.service.__dict__

    def test_should_generate_ca(self):
        self.assertEquals("CaCert", self.service.generate_ca_cert(None).content)


    def given_this_endpoints(self):
        return dict(endpoints=[{"uri":"http://127.0.0.1:9093/vpn/configs/dh/", "driver":"REST", "logic":"get", "name":"get_dh"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/server/", "driver":"REST", "logic":"get", "name":"get_server_config"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/client/", "driver":"REST", "logic":"get", "name":"get_client_config"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/ca/", "driver":"REST", "logic":"get", "name":"get_ca_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"get", "name":"get_client_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/keys/client/", "driver":"REST", "logic":"get", "name":"get_client_key"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/server/", "driver":"REST", "logic":"get", "name":"get_server_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/keys/server/", "driver":"REST", "logic":"get", "name":"get_server_key"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"post", "name":"generate_ca_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"post", "name":"generate_client_cert"},
                        {"uri":"http://127.0.0.1:9093/vpn/configs/certs/client/", "driver":"REST", "logic":"post", "name":"generate_server_cert"},])



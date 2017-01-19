import logging
import threading
import time
import random

from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class VPNManager:

    def __init__(self, bind_address, system_state_manager=None, vpn_port=234):
        """
        VPN orchestrator manager example, it does not deploy VPNs but it could do it if properly configured.
        Right now is stand-alone module, but the idea is to integrate this as an app of a CNSMO instance
        :param bind_address:
        :param system_state_manager:
        :param vpn_port:
        :return:
        """
        self.__bind_address = bind_address
        self.__system_state_manager = system_state_manager
        self.__name = "VPN_SERVICE_MANAGER"
        self.__vpn_port = vpn_port

        self.__server_service = None
        self.__client_services = set()
        self.__configuration_manager = None

        self.__thread_pool = set()
        self.lock = threading.Lock()

        self.__status = "power_off"
        self.__logger = logging.getLogger(__name__)

    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(self.__bind_address, "myVpn", "VPNManager",
                                                                                      self.__status, ["VPNServer", "VPNClient", "VPNConfigManager"],
                                                                                      self.register_service)

    def start(self):
        self.__logger.debug("Starting system state client...")
        self.__configure_system_state()
        self.__system_state_manager.start()
        self.__logger.debug("Started system state client")

    # Crec que aquesta funcio no es crida
    def deploy(self):
        self.__logger.debug("deploy function is called")
        if self.__status == "listening":
            self.__deploy_vpn()
        else:
            try:
                self.__thread_pool.add(threading.Thread(target= self.deploy))
            except:
                pass

    def deploy_blocking(self):
        self.__logger.debug("Waiting for status ready to deploy VPN")
        while True:
            if self.__status == "listening":
                break
            time.sleep(0.2)

        self.__generate_and_deploy_server()

    def get_status(self):
        return self.__status

    def register_service(self, service):
        """
        Meant to be registered by the systemState, This manager expects 3 services (only 2 for the PoC)
        the client, the server and the credential manager. Only after have registered these services,
        the VPN is ready
        :param service:
        :return:
        """

        self.__logger.debug("Detected new service of type %s" % service.get_service_type())

        if service.get_service_type() == "VPNClient":
            client_service = ServiceMaker().make_service("Client", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.lock.acquire()
            try:
                if (self.__status != "listening"):
                    self.__logger.debug("Server not Listening, add client to queue")
                    self.__client_services.add(client_service)
                else:
                    self.__logger.debug("Server is listening, deploy the client now")
                    ca_crt = self.__configuration_manager.get_ca_cert(None).content
                    client_id = "VPNclient" + str(random.randint(1,999999))
                    self.__generate_and_deploy_client(client_service, client_id, ca_crt)
            finally:
                self.lock.release()

        elif service.get_service_type() == "VPNServer":
            server_service = ServiceMaker().make_service("Server", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.__server_service = server_service

        elif service.get_service_type() == "VPNConfigManager":
            cred_service = ServiceMaker().make_service("CredentialManager", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.__configuration_manager = cred_service
        else:
            return

        self.__update_state()

    def __update_state(self):

        self.__logger.debug("Status: Server %s, ConfigManager %s, Clients %s"
                            % (self.__server_service, self.__configuration_manager, self.__client_services))
        if self.__server_service and self.__configuration_manager and self.__status != "listening":
            self.__logger.debug("Switching to status listening!")
            self.lock.acquire()
            try:
                self.__status = "listening"
            finally:
                 self.lock.release()
            for client_service in self.__client_services:
                client_id = "VPNclient" + str(random.randint(1,999999))
                self.__logger.debug("Generating vpn client configuration...")
                self.__configuration_manager.generate_client_cert(client_id, None)
                client_key = self.__configuration_manager.get_client_key(client_id).content
                client_crt = self.__configuration_manager.get_client_cert(client_id).content
                client_conf = self.__configuration_manager.get_client_config(client_id).content
                self.__configure_and_start_vpn_client(client_service, client_id, ca_crt, client_key, client_crt, client_conf)
            [ t.start() for t in self.__thread_pool]

    def __generate_and_deploy_server(self):
        self.__logger.debug("Deploying VPN...")
        print "Deploying VPN..."

        self.__logger.debug("generating security mechanism...")
        print "generating security mechanism..."

        # Generate DH and CA cert
        self.__configuration_manager.generate_ca_cert(None)

        self.__logger.debug("generating vpn server configuration...")
        print "generating vpn server configuration..."
        # Generate server key and cert
        self.__configuration_manager.generate_server_cert(None)

        # Get all config files
        dh = self.__configuration_manager.get_dh(None).content
        ca_crt = self.__configuration_manager.get_ca_cert(None).content
        server_key = self.__configuration_manager.get_server_key(None).content
        server_crt = self.__configuration_manager.get_server_cert(None).content
        server_conf = self.__configuration_manager.get_server_config(None).content

        # TODO find a proper name for the server
        self.__configure_and_start_vpn_server("server", dh, ca_crt, server_key, server_crt, server_conf)

    def __generate_and_deploy_client(self, client_service, client_id, ca_crt):
        self.__logger.debug("generating vpn client configuration...")
        print "generating vpn client configuration..."
        self.__configuration_manager.generate_client_cert(client_id, None)
        client_key = self.__configuration_manager.get_client_key(client_id).content
        client_crt = self.__configuration_manager.get_client_cert(client_id).content
        client_conf = self.__configuration_manager.get_client_config(client_id).content

        self.__configure_and_start_vpn_client(client_service, client_id, ca_crt, client_key, client_crt, client_conf)


    def __configure_and_start_vpn_server(self, name, dh, ca_crt, server_key, server_crt, server_conf):
        """
        Helper method that configures server service with given configuration and starts the service
        """
        self.__logger.debug("configuring vpn server " + name + " ...")
        print "configuring vpn server " + name + " ..."
        self.__server_service.set_dh({"file":("dh2048.pem", dh)})
        self.__server_service.set_ca_cert({"file":("ca.crt", ca_crt)})
        self.__server_service.set_server_key({"file":("server.key", server_key)})
        self.__server_service.set_server_cert({"file":("server.crt", server_crt)})
        self.__server_service.set_config_file({"file":("server.conf", server_conf)})

        self.__server_service.build_server({})

        self.__logger.debug("starting vpn server " + name + " ...")
        print "starting vpn server " + name + " ..."
        self.__server_service.start_server({})

    def __configure_and_start_vpn_client(self, client_service, name, ca_crt, client_key, client_crt, client_conf):
        """
        Helper method that configures given client service with given configuration and starts the service
        """
        self.__logger.debug("configuring vpn client " + name + " ...")
        print "configuring vpn client " + name + " ..."
        client_service.set_ca_cert({"file":("ca.crt", ca_crt)})
        client_service.set_client_key({"file":("client.key", client_key)})
        client_service.set_client_cert({"file":("client.crt", client_crt)})
        client_service.set_config({"file":("client.conf", client_conf)})

        client_service.build_client({})

        self.__logger.debug("starting vpn client " + name + " ...")
        print "starting vpn client " + name + " ..."
        client_service.start_client({})

import logging
import threading
import time
import random
from requests import ConnectionError

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

        self.__server_deployed = False
        self.__deployed_client_services = set()

        self.__registered_services = set()

        self.lock = threading.Lock()

        self.__status = "power_off"
        self.__logger = logging.getLogger(__name__)

    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(self.__bind_address, "myVpn", "VPNManager",
                                                                                      self.__status, ["VPNServer", "VPNClient", "VPNConfigManager"],
                                                                                      self.process_advertisement)

    def start(self):
        self.__logger.debug("Starting system state client...")
        self.__configure_system_state()
        self.__system_state_manager.start()
        self.__status = "initializing"
        self.__logger.debug("Started system state client")

    def stop(self):
        self.__logger.debug("Stopping system state client...")
        # TODO stop any service deployment in progress
        self.__system_state_manager.stop()
        self.__status = "power_off"
        self.__logger.debug("Stopped system state client")

    def get_status(self):
        return self.__status

    def process_advertisement(self, service):
        if service.get_message_type() == "new":
            self.register_service(service)
        elif service.get_message_type() == "shutdown":
            self.unregister_service(service)
        else:
            self.__logger.warn("Unknown advertisement message_type=%s" % service.get_message_type)
            self.__logger.warn(service)

    def register_service(self, service):
        """
        Meant to be registered by the systemState, This manager expects 3 services (only 2 for the PoC)
        the client, the server and the credential manager. Only after have registered these services,
        the VPN is ready
        :param service:
        :return:
        """
        self.lock.acquire()
        try:
            if service.get_service_id() in self.__registered_services:
                self.__logger.warn("Ignoring duplicated advertisement for service %s:%s" % (service.get_service_type(), service.get_service_id()))
                return

            self.__registered_services.add(service.get_service_id())
        finally:
            self.lock.release()

        self.__logger.debug("Detected new service %s:%s" % (service.get_service_type(), service.get_service_id()))

        if service.get_service_type() == "VPNClient":
            client_service = ServiceMaker().make_service("Client", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.lock.acquire()
            try:
                if self.__status != "listening":
                    self.__logger.debug("Server not Listening, add client to queue")
                    self.__client_services.add(client_service)
                else:
                    self.__logger.debug("Server is listening, deploy the client now")
                    self.__client_services.add(client_service)
                    ca_crt = self.__configuration_manager.get_ca_cert(None).content
                    client_id = "VPNclient" + str(random.randint(1,999999))
                    self.__logger.debug("Waiting for client presence...")
                    self.wait_for_service_presence(client_service)
                    self.__generate_and_deploy_client(client_service, client_id, ca_crt)
            finally:
                self.lock.release()

        elif service.get_service_type() == "VPNServer":
            if self.__server_service is None:
                server_service = ServiceMaker().make_service("Server", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
                self.__logger.debug("Waiting for server presence...")
                self.wait_for_service_presence(server_service)
                self.__server_service = server_service
                self.__update_state()

        elif service.get_service_type() == "VPNConfigManager":
            if self.__configuration_manager is None:
                cred_service = ServiceMaker().make_service("CredentialManager", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
                self.__logger.debug("Waiting for credential manager presence...")
                self.wait_for_service_presence(cred_service)
                self.__configuration_manager = cred_service
                self.__update_state()

        else:
            return

    def unregister_service(self, service):
        # TODO implement as opposite of register_service(service)
        self.lock.acquire()
        try:
            if service.get_service_id() not in self.__registered_services:
                self.__logger.warn("Ignoring shutdown advertisement for non-registered service %s:%s" % (service.get_service_type(), service.get_service_id()))
                return

            self.__logger.debug("Detected service shutdown %s:%s  IGNORED!" % (service.get_service_type(), service.get_service_id()))
            self.__registered_services.remove(service.get_service_id())
        finally:
            self.lock.release()

    def __update_state(self):

        self.__logger.debug("Status: Server %s, ConfigManager %s, Clients %s"
                            % (self.__server_service, self.__configuration_manager, self.__client_services))
        if (self.__server_service is not None) and (self.__configuration_manager is not None) and \
                self.__status == "initializing":
            self.__logger.debug("Switching to status deploying server!")
            self.lock.acquire()
            try:
                self.__status = "deploying server"
                self.__logger.debug("Generating vpn server configuration...")
                self.__generate_and_deploy_server()
            finally:
                self.lock.release()

        if self.__status == "deploying server" and self.__server_deployed:
            self.__logger.debug("Switching to status listening!")
            self.lock.acquire()
            try:
                self.__status = "listening"
            finally:
                self.lock.release()

            if not self.__client_services:
                self.__logger.debug("No clients already registered to deploy")
            else:
                self.__logger.debug("Deploying already registered clients")

            for client_service in self.__client_services:
                client_id = "VPNclient" + str(random.randint(1,999999))
                self.__logger.debug("Waiting for client presence...")
                self.wait_for_service_presence(client_service)
                self.__logger.debug("Generating vpn client configuration...")
                ca_crt = self.__configuration_manager.get_ca_cert(None).content
                self.__generate_and_deploy_client(client_service, client_id, ca_crt)

    def __generate_and_deploy_server(self):
        self.__logger.debug("Deploying VPN...")
        print "Deploying VPN..."

        self.__logger.debug("generating security mechanism...")
        print "generating security mechanism..."

        # Generate DH and CA cert
        self.__logger.debug("Generate DH and CA cert")
        print "Generate DH and CA cert..."
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

        self.__configure_and_start_vpn_server("server", dh, ca_crt, server_key, server_crt, server_conf)
        self.__server_deployed = True

    def __generate_and_deploy_client(self, client_service, client_id, ca_crt):
        self.__logger.debug("generating vpn client configuration...")
        print "generating vpn client configuration..."
        self.__configuration_manager.generate_client_cert(client_id, None)
        client_key = self.__configuration_manager.get_client_key(client_id).content
        client_crt = self.__configuration_manager.get_client_cert(client_id).content
        client_conf = self.__configuration_manager.get_client_config(client_id).content

        self.__configure_and_start_vpn_client(client_service, client_id, ca_crt, client_key, client_crt, client_conf)
        self.__deployed_client_services.add(client_service)

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

    def wait_for_service_presence(self, service):
        presence = False
        while not presence:
            time.sleep(0.2)
            try:
                r = service.get_status(None)
                presence = True
            except ConnectionError:
                # service API is not yet deployed
                # ignore the error
                pass
        return r.status_code

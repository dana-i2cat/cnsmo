import threading

from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
from src.main.python.net.i2cat.factory.system.state.factory import SystemStateFactory


class VPNManager:

    def __init__(self, bind_address, system_state_manager=None, vpn_port=234):
        """
        VPN orchestrator manger example, it does not deploy VPNs but it could do it if properly configured.
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

        self.__status = "power_off"

    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(self.__bind_address, "myVpn", "VPNManager",
                                                                                      self.__status, ["VPNServer", "VPNClient", "VPNConfigManager"],
                                                                                      self.register_service)

    def start(self):
        self.__configure_system_state()
        self.__system_state_manager.start()

    def deploy(self):
        if self.__status == "ready":
            self.__deploy_vpn()
        else:
            try:
                self.__thread_pool.add(threading.Thread(target= self.deploy))
            except:
                pass

    def register_service(self, service):
        """
        Meant to be registered by the systemState, This manger expects 3 services (only 2 for the PoC)
        the client, the server and the credential manager. Only after have registered these services,
        the VPN is ready
        :param service:
        :return:
        """

        if service.get_service_type() == "VPNClient":
            client_service = ServiceMaker().make_service("Client", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.__client_services.add(client_service)

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

        #self.__client_services = True
        if self.__server_service and self.__client_services and self.__configuration_manager:
            self.__status = "ready"
            [ t.start() for t in self.__thread_pool]

    def __deploy_vpn(self):
        """
        Main service of the VPN orchestrator. Here is the logic of the VPN manager, this method is called after start()
        successfully works.

        The idea is to deploy all the VPN instances all over the context and manage them. For the Poc, we only read the
        two server strings provided by the two deployed apps
        :return:
        """
        print "Deploying VPN..."

        print "generating security mechanism..."

        # Generate DH and CA cert
        self.__configuration_manager.generate_ca_cert(None)

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

        # for each client:
        # Generate client config, get it and configure the client service
        i = 0
        for client_service in self.__client_services:
            print "generating vpn client configuration..."
            self.__configuration_manager.generate_client_cert(None)
            client_key = self.__configuration_manager.get_client_key(None).content
            client_crt = self.__configuration_manager.get_client_cert(None).content
            client_conf = self.__configuration_manager.get_client_config(None).content

            # TODO find a proper name for each client
            self.__configure_and_start_vpn_client(client_service, "client-" + str(i), ca_crt, client_key, client_crt, client_conf)
            i += 1

        print "VPN deployed."

    def __configure_and_start_vpn_server(self, name, dh, ca_crt, server_key, server_crt, server_conf):
        """
        Helper method that configures server service with given configuration and starts the service
        """
        print "configuring vpn server " + name + " ..."
        self.__server_service.set_dh({"file":("dh2048.pem", dh)})
        self.__server_service.set_ca_cert({"file":("ca.crt", ca_crt)})
        self.__server_service.set_server_key({"file":("server.key", server_key)})
        self.__server_service.set_server_cert({"file":("server.crt", server_crt)})
        self.__server_service.set_config_file({"file":("server.conf", server_conf)})

        self.__server_service.build_server({})

        print "starting vpn server " + name + " ..."
        self.__server_service.start_server({})

    def __configure_and_start_vpn_client(self, client_service, name, ca_crt, client_key, client_crt, client_conf):
        """
        Helper method that configures given client service with given configuration and starts the service
        """
        print "configuring vpn client " + name + " ..."
        client_service.set_ca_cert({"file":("ca.crt", ca_crt)})
        client_service.set_client_key({"file":("client.key", client_key)})
        client_service.set_client_cert({"file":("client.crt", client_crt)})
        client_service.set_config({"file":("client.conf", client_conf)})

        client_service.build_client()
        print "starting vpn client " + name + " ..."
        client_service.start_server()

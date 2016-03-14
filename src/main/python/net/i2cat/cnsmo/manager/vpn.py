import threading

from main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
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
        self.__credential_manager = None

        self.__thread_pool = set()

        self.__status = "power_off"



    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(self.__bind_address, "myVpn","VPNManager",
                                                                                      self.__status, ["Server", "Client", "CredentialManager"],
                                                                                      self.register_service)

    def start(self):
        self.__configure_system_state()
        self.__system_state_manager.start()

    def deploy(self):
        print self.__status
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
            print "Making Server Service..."
            server_service = ServiceMaker().make_service("Server", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.__server_service = server_service
            print self.__server_service.__dict__

        elif service.get_service_type() == "VPNConfigManager":
            print "Making Credential Manager..."
            cred_service = ServiceMaker().make_service("CredentialManager", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
            self.__credential_manager = cred_service
            print self.__credential_manager.__dict__
        else:
            return

        self.__update_state()

    def __update_state(self):

        self.__client_services = True
        if self.__server_service and self.__client_services and self.__credential_manager:
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
        print "getting DH..."
        dh = self.__credential_manager.get_dh(*[""])
        print "DH is", dh.text
        print self.__server_service.start(dh.text).text






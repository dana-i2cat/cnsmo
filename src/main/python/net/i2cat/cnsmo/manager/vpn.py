import threading


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

    def start(self):
        print self.__status
        if self.__status == "ready":
            self.__deploy_vpn()
        else:
            try:
                self.__thread_pool.add(threading.Thread(target= self.start))
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
        print "-----registering service", service
        service = self.__system_state_manager.load(service)
        if service.get_type() == "Client":
            self.__client_services.add(service)

        elif service.get_type() == "Server":
            self.__server_service = service

        elif service.get_type() == "CredentialManager":
            self.__credential_manager = service

        self.__update_state()

    def __update_state(self):
        #XXX: Ultra Hack
        self.__client_services = True
        print self.__server_service, self.__client_services, self.__credential_manager
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






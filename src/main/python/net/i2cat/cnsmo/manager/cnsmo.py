from src.main.python.net.i2cat.lib.model.service import Service
from src.main.python.net.i2cat.factory.system.state.factory import SystemStateFactory


class CNSMOManager:

    def __init__(self, address, name=None, type=None, deployment_driver=None,
                 system_state_manager=None, services=dict()):
        """
        Main CNSMO Service instances, this are meant to be super-recursive and the base object of every service
        triggered by OpenNaas
        :param bind_address:
        :param name:
        :param type:
        :param deployment_driver:
        :param system_state_manager:
        :return:
        """
        self.__address =  address
        self.__deployment_driver = deployment_driver
        self.__system_state_manager = None
        self.__name = name
        self.__type = type
        self.__services = services
        self.__is_running = False
        self.__status = None

    def start(self):
        if not self.__is_running:
            self.__configure_system_state()
            self.__deployment_driver.start()
            self.__connect()
            self.__is_running = True

    def stop(self):
        if self.__is_running:
            self.__system_state_manager.stop()
            self.__deployment_driver.stop()
            self.__disconnect()
            self.__is_running = False

    def __connect(self):
        pass

    def __disconnect(self):
        pass

    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(address=self.__address, service_id=self.__name, service_type=self.__type,
                                                                                      service_status=self.__status, subscriptions=[],
                                                                                      callback=self.update_service)
        self.__system_state_manager.start()
        print "State up to date"

    def update_service(self, message):
        pass

    def get_system_state_manager(self):
        return self.__system_state_manager

    def get_deployment_driver(self):
        return self.__deployment_driver

    def get_type(self):
        return self.__type

    def get_name(self):
        return self.__name

    def set_deployment_driver(self, driver):
        self.__deployment_driver = driver

    def set_system_state_manager(self, manager):
        self.__system_state_manager = manager

    def set_name(self, name):
        self.__name = name

    def set_type(self, type):
        self.__type = type

    def register_service(self, service):
        """
        This call is meant to be triggered by the System State
        :param service:
        :return:
        """
        self.__system_state_manager.save(service)
        print "saved"
        print service.get_service_id()
        self.__services.update({service.get_service_id():service})

    def deregister_service(self, service):
        """
        This call is meant to be triggered by the system State
        :param service:
        :return:
        """
        self.__services.pop(service)

    def compose_service(self, **kwargs):
        service = Service()
        service.objectify(**kwargs)
        self.register_service(service)

    def launch_service(self, service):
        """
        Given the app request, it launches an app using the deployment driver.
        Right now is only bash, but it could be more deployers, like docker, OpenStack
        etc.
        :param kwargs:
        :return:
        """
        self.__deployment_driver.launch_app(**self.__services.get(service).dictionarize())
        self.__system_state_manager.advertise()








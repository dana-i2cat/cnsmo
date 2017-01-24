import logging

from src.main.python.net.i2cat.cnsmo.lib.model.service import Service
from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class CNSMOManager:

    def __init__(self, address, name=None, type=None, deployment_driver=None,
                 system_state_manager=None, services=None):
        """
        CNSMOManager represents a service instance and acts as a wrapper for it.
        It has a key role in CNSMO architecture:
        - it advertises itself to the CNSMO system state, enabling service discovery.
        - it is also the responsible for launching and stopping the service, via a deployment driver.

        This class is meant to be super-recursive and the base object of every service triggered by CNSMO.

        :param address: Where the distributed system state is
        :param name: Service name
        :param type: Service type
        :param deployment_driver: Driver being used by to launch the service
        :param system_state_manager:
        :return:
        """
        self.__address = address
        self.__deployment_driver = deployment_driver
        self.__system_state_manager = None
        self.__name = name
        self.__type = type
        if services is None:
            self.__services = dict()
        else:
            self.__services = services
        self.__service_instances = dict()
        self.__is_running = False
        self.__status = None
        self.__logger = logging.getLogger(__name__)

    def start(self):
        if not self.__is_running:
            self.__logger.debug("Starting CNSMOManager...")
            self.__configure_system_state()
            self.__deployment_driver.start()
            self.__connect()
            self.__is_running = True
            self.__logger.debug("CNSMOManager started.")

    def stop(self):
        if self.__is_running:
            self.__logger.debug("Stopping CNSMOManager...")
            self.__system_state_manager.stop()
            self.__deployment_driver.stop()
            self.__disconnect()
            self.__is_running = False
            self.__logger.debug("CNSMOManager stopped.")

    def __connect(self):
        pass

    def __disconnect(self):
        pass

    def __configure_system_state(self):
        self.__logger.debug("Starting system state client...")
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(address=self.__address, service_id=self.__name, service_type=self.__type,
                                                                                      service_status=self.__status, subscriptions=[],
                                                                                      callback=self.update_service)
        self.__system_state_manager.start()
        self.__logger.debug("Started system state client")
        print("State up to date")

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
        Registers given service via the system state client
        :param service:
        :return:
        """
        self.__system_state_manager.save(service)
        print("saved")
        print(service.get_service_id())
        self.__services.update({service.get_service_id():service})
        self.__logger.debug("Registered service %s" % service.get_service_id())

    def deregister_service(self, service):
        """
        De-registers given service via the system state manager
        :param service:
        :return:
        """
        # TODO delete service from system_state_manager
        # self.__system_state_manager.delete(service)
        self.__services.pop(service)
        self.__logger.debug("Deregistered service %s" % service.get_service_id())

    def compose_service(self, **kwargs):
        service = Service()
        service.objectify(**kwargs)
        self.register_service(service)

    def launch_service(self, service_id):
        """
        Given the app request, it launches an app using the deployment driver.
        Right now the driver is only bash, but it could be more deployers, like docker, OpenStack
        etc.
        It advertises the service through the system state client, so others may react to it being launched.
        :param service_id: Identifier of the service to launch
        :return:
        """
        app_instance = self.__deployment_driver.launch_app(**self.__services.get(service_id).dictionarize())
        self.__service_instances[service_id] = app_instance
        self.__system_state_manager.advertise()

    def stop_service(self, service_id):
        """
        It stops the app (if launched), using the deployment driver.
        Right now the deployer is only bash, but it could be more deployers, like docker, OpenStack
        etc.
        It advertises the service through the system state client, so others may react to it being stopped.
        :param service_id: Identifier of the service whose app should stop
        :return: service_id of the stopped app, if any is stopped. None otherwise.
        """
        if service_id in self.__services.keys():
            if service_id in self.__service_instances:
                app_instance = self.__service_instances.get(service_id)
                if app_instance:
                    self.__system_state_manager.deadvertise()
                    self.__deployment_driver.stop_app(app_instance)
                    return service_id
        return None

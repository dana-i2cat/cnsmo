class CNSMOManager:

    def __init__(self, bind_address, name=None, type=None, deployment_driver=None, system_state_manager=None):
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
        self.__bind_address =  bind_address
        self.__deployment_driver = deployment_driver
        self.__system_state_manager = system_state_manager
        self.__name = name
        self.__type = type
        self.__is_running = False

        self.__services = dict()
        self.__apps = set()

    def start(self):
        if not self.__is_running:
            self.__system_state_manager.start()
            self.__deployment_driver.start()
            self.__bind()
            self.__is_running = True

    def stop(self):
        if self.__is_running:
            self.__system_state_manager.stop()
            self.__deployment_driver.stop()
            self.__unbind()
            self.__is_running = False

    def __bind(self):
        pass

    def __unbind(self):
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
        self.__services.update(service)

    def deregister_service(self, service):
        """
        This call is meant to be triggered by the system State
        :param service:
        :return:
        """
        self.__services.pop(service)

    def launch_app(self, **kwargs):
        """
        Given the app request, it launches an app using the deployment driver.
        Right now is only bash, but it could be more deployers, like docker, OpenStack
        etc.
        :param kwargs:
        :return:
        """
        return self.__deployment_driver.launch_app(**kwargs)









from src.main.python.net.i2cat.lib.model.base import Base


class Service(Base):

    def __init__(self):
        self.__service_id = None
        self.__trigger = None
        self.__resources = list()
        self.__dependencies = list()
        self.__endpoints = list()

    def get_service_id(self):
        return self.__service_id

    def get_trigger(self):
        return self.__trigger

    def get_resources(self):
        return self.__resources

    def get_dependencies(self):
        return self.__dependencies

    def get_endpoints(self):
        return self.__endpoints

    def set_service_id(self, service_id):
        self.__service_id = service_id

    def set_trigger(self, trigger):
        self.__trigger = trigger

    def set_resources(self, resources):
        self.__resources = resources

    def set_dependencies(self, dependencies):
        self.__dependencies = dependencies

    def set_endpoints(self, endpoints):
        self.__endpoints = endpoints




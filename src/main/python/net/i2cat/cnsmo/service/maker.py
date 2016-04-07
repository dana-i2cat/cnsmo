import requests


class ServiceMaker:

    def __init__(self):
        """
        Kind of mind blowing class.
        It creates customized instances at run-time that provides the methods required by the
        service instances download by the CNSMO/Orchestrators

        Providing a set of Drivers, logic, uri and a name, this class provides an instance
        containign all the methods to control the remote service.

        For example, provided the required endpoints to manage the Server and CredentialManager apps
        this class will create two instances that will do a request.get(URL, **params) to the VPN orchestrator

        The idea here is to create REMOTE service Manager instances at run-time via the system-state manager
        :return:
        """
        pass

    def make_service(self, type, endpoints):
        """
        This will provide the service instance with all the methods required via the endpoints
        :param type:
        :param endpoints:
        :return:
        """
        service = Service(type)
        [ self.add_method(service, endpoint) for endpoint in endpoints ]
        return service

    def add_method(self, service, endpoint):
        """
        Povided an instance and an endpoint, get al the params and add the method created
        :param service:
        :param endpoint:
        :return:
        """

        uri = endpoint.get("uri")
        driver = self.get_driver(endpoint.get("driver"))
        logic = endpoint.get("logic")
        method = self.construct_method(driver, logic, uri)
        setattr(service, endpoint.get("name"), method)

    def get_driver(self, driver):
        """
        This is meant to return some kind of factory class that will provide the methods
        :param driver:
        :return:
        """
        return "REST"

    def construct_method(self, driver, logic, uri):
        """
        Since it is just a PoC and there is only one driver, this identifies, the driver - REST
        the logic (the REST method) and the URI (URL to call)

        This will create a lambda function that will be passed as a method, that will call the lib()
        :param driver:
        :param logic:
        :param uri:
        :return:
        """
        lib = self.get_lib(driver, logic)
        clean_uri, has_params = self.clean_uri(uri)
        if has_params:
            if logic == "post":
                func = lambda *x : lib(url=clean_uri % x[:-1], json=x[-1])

            elif logic == "upload":
                func = lambda *x : lib(url=clean_uri % x[:-1], files=x[-1])

            else:
                func = lambda *x: lib(url=clean_uri % x)

        else:
            if logic == "post":
                func = lambda x : lib(url=clean_uri, json=x)

            if logic == "upload":
                func = lambda x : lib(url=clean_uri, files=x)

            else:
                func = lambda x: lib(url=clean_uri)
        return func

    def get_lib(self, driver, logic):
        """
        Given the driver and the logic this will return a method to create the lambda functions
        :param driver:
        :param logic:
        :return:
        """

        if logic == "get":
            return requests.get
        elif logic == "post" or logic == "upload":
            return requests.post
        else:
            return None

    def clean_uri(self, uri):
        """
        If there is an URL that has params, this method transforms the URL to properly call the methods

        :return:
        """
        if "{param}" in uri:
            return uri.replace("{param}", "%s"), True
        return uri, False


class Service:

    def __init__(self, type):
        self.__type = type

    def set_type(self, type):
        self.__type = type

    def get_type(self):
        return self.__type

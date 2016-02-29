from abc import ABCMeta
from abc import abstractmethod


class Service:

    def __init__(self):
        pass

    __metaclass__ = ABCMeta

    @abstractmethod
    def start(self, bind_address):
        """
        Setups all the internal modules and binds to a TCP or IPC address
        params: String address: TCP/IPC address to bind
        return: Int Id of the system
        """
        pass

    @abstractmethod
    def stop(self):
        """
        Stops all the internal modules, dumps the state if (necessary) and
        closes the socket of it's binded address
        params: None
        returns: Void
        """

        pass

    @abstractmethod
    def restart(self):
        """
        Reloads all the modules setup when the system started and
        rebinds the to the same address
        params: None
        returns: Void
        """
        pass

    @abstractmethod
    def save(self):
        """
        Saves the current instances and service to a database or system stat. Push state
        params: None
        Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def load(self, MgmtInstanceId):
        """
        Recovers all the registered Services and instances. Pull state
        param: Int MgmtInstanceId: Id of the "OpenNaas" instance
        return: Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def register_service(self, service):
        """
        Register a new service and opens an API to instantiate and manage the given service
        params:  Service service: Service instance
        returns: Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def deregister_service (self, service):
        """
        Deletes the given services from the services pool
        params:  Service service: Service instance
        returns: Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def list_registered_services(self):
        """
        Returns all the registered services, if no services are available, it returns an empty Set
        params: None
        returns: Set<Service>: Set of services or Eempty set
        """
        pass

    @abstractmethod
    def service_exists(self, service):
        """
        Returns true id specific service is registered or false  if the service does not exists
        params: Service service: Service to list
        returns Service service or null if the service does not exists
        """
        pass

    @abstractmethod
    def create_instance(self, service, **kwargs):
        """
        Creates a new instance of a given service and their specific keyword arguments
        param: Service service: Service type to instantiate
        param: **Kwargs: Keyword arguments required to instantiate the service
        returns: Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def terminate_instance(self, instanceId):
        """
        Terminates an instance no matter what service Type it is
        param: Int instanceId
        returns: Int returnCode: code indicating whether the service could be registered or not
        """
        pass

    @abstractmethod
    def list_instances(self):
        """
        Returns a set containing all the instances managed by system
        params: None
        returns: Set<Instance> Instance Set or empty set if no services are instantiated
        """
        pass

    @abstractmethod
    def features(self, instance):
        """
        returns a struct containing all the features of the current instance or empty if the instance does not exist.
        (e.g. kwargs content, IP address, ports, docker image, ...)
        params: Instance instance
        returns Struct, struct containing all the features of the instance or null if the instance does not exists
        """
        pass


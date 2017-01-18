from src.main.python.net.i2cat.cnsmo.lib.model.service import Service
from src.main.python.net.i2cat.cnsmo.lib.message.newservice import NewService
from src.main.python.net.i2cat.cnsmo.lib.message.serviceshutdown import ServiceShutdown
from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker


class SystemStateClient:

    DEFAULT_CHANNEL = "DISCOVERY"

    def __init__(self, client=None, publisher=None, listener=None,
                 service_id=None, service_type=None, service_status=None,
                 subscriptions=None, callback=None):
        """
        Default manager for CSNMO Instances.

        :param client: System State Client Instance
        :param publisher: System State Publisher Instance
        :param listener: System State Listener Instance
        :param service_id: Id of the service managed by this client
        :param service_type: Type of the service managed
        :param service_status: Status of the service
        :param subscriptions: List of services that need to be synched by the CNSMO instance
        :param callback: Callback to be called after a subscribed service is discovered
        :return:
        """

        self.__client = client
        self.__publisher = publisher
        self.__listener = listener

        self.__service_data = (service_type, service_id, service_status)
        self.__subscriptions = subscriptions
        self.__callback = callback

        self.__is_running = False

    def start(self):
        if not self.__is_running:
            self.__client.start()
            self.__publisher.start()

            self.subscribe_all()
            #TODO Check wether advertise is needed whne the system state starts or not
            #TODO Since at this moment there is no check of the CNSMO Container APP it may not be needed
            #self.advertise()
            self.__listener.start()

    def stop(self):
        # TODO Implement stop properly, as the opposite of start
        pass

    def subscribe_all(self):
        """
        Subscribes all the services
        :return:
        """
        [self.subscribe(channel) for channel in self.__subscriptions if self.__subscriptions]

    def subscribe(self, channel):
        """
        Atomic method that call the listener to subscribe to a service update
        :param channel:
        :return:
        """
        self.__listener.subscribe(channel, self.callback)

    def advertise(self):
        """
        Publishes into the DISCOVERY topic himself
        :return:
        """
        self.__publisher.publish(self.DEFAULT_CHANNEL, NewService(*self.__service_data).jsonify())

    def deadvertise(self):
        """
        Publishes into the DISCOVERY topic himself is no longer registered
        :return:
        """
        self.__publisher.publish(self.DEFAULT_CHANNEL, ServiceShutdown(*self.__service_data).jsonify())

    def callback(self, message):
        """
        When the client is instanciated, it registers a claaback function that is wrapped into this function.
        In this wayt, the raw messages handled by the listener can be formated into the CNSMO DM
        :param message:
        :return:
        """
        service = NewService()
        service.objectify_from_json(message.get("data"))
        return self.__callback(service)

    def save(self, service):
        """
        Saves a Service
        :param service:
        :return:
        """

        key = service.get_service_id()
        value = service.jsonify()
        self.__client.save(key, value)

    def load(self, service_id):
        """
        Loads a Service
        :param service_id:
        :return:
        """
        service = Service()
        service.objectify_from_json(self.__client.load(service_id))
        return service

from src.main.python.net.i2cat.lib.message.newservice import NewService


class SystemStateManager:

    DEFAULT_CHANNEL = "DISCOVERY"

    def __init__(self, client=None, publisher=None, listener=None):
        """
        First Implementation of the System State Manager.
        It only serves as a proxy that publish updates
        that appear in the DISCOVERy topic
        :param client:
        :param publisher:
        :param listener:
        :return:
        """
        self.__client = client
        self.__publisher = publisher
        self.__listener = listener

        self.__channels = set()

        self.__is_running = False

    def start(self):
        if not self.__is_running:
            self.__client.start()
            self.__publisher.start()
            self.subscribe(self.DEFAULT_CHANNEL)
            self.__listener.start()

    def register_channel(self, channel):
        """
        Registers a new channel
        :param channel:
        :return:
        """
        try:
            self.__channels.add(channel)
        except Exception as e:
            #Dangerous
            pass

    def register_service(self, message):
        """
        Callback triggered after a service is published on the DISCOVERY topic.
        It creates a NewService message that is published in the service topic provided
        by the data contained in the DISCOVERY MEssage
        :param message:
        :return:
        """
        service = NewService()
        service.objectify_from_json(message.get("data"))
        self.register_channel(service.get_service_type())
        self.publish(service.get_service_type(), service.jsonify())

    def subscribe(self, channel):
        """
        Subscribes to a channel
        :param channel:
        :return:
        """
        self.__listener.subscribe(channel, self.register_service)

    def publish(self, channel, data):
        """
        Publish into a channel
        :param channel:
        :param data:
        :return:
        """
        self.__publisher.publish(channel, data)






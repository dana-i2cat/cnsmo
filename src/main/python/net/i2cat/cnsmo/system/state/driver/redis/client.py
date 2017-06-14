import redis


class RedisDriver:

    def __init__(self, redis_address):
        """
        Defines the most basic driver for a Redis Client
        :param redis_address:
        :return:
        """
        self.__client_address = redis_address
        self.__client = None
        self.__is_running = False

    def start(self):
        if not self.__is_running:
            self.__client = redis.Redis(self.__client_address.split(":")[0], int(self.__client_address.split(":")[1]))
            self.__is_running = True

    def stop(self):
        if self.__is_running:
            self.__client = None
            self.__is_running = False

    def save(self, key, value):
        self.__client.set(key, value)

    def load(self, key):
        return self.__client.get(key)

    def delete(self, key):
        self.__client.delete(key)


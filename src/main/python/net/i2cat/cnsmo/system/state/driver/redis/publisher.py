import redis


class RedisPublisher:

    def __init__(self, redis_address):
        """
        Most basic Redis publisher
        :param redis_address:
        :return:
        """
        self.__stream = redis.Redis(redis_address.split(":")[0], int(redis_address.split(":")[1]))

    def publish(self, channel, message):
        self.__stream.publish(channel, message)

    def start(self):
        pass

    def stop(self):
        pass

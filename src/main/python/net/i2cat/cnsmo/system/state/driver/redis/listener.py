import redis
import threading


class RedisListener(threading.Thread):

    def __init__(self, redis_address):
        """
        Most basic Redis driver for the listeners
        :param redis_address:
        :return:
        """
        threading.Thread.__init__(self)
        print redis_address
        self.__should_stop = False
        self.__stream = redis.Redis(redis_address.split(":")[0], int(redis_address.split(":")[1])).pubsub()

    def subscribe(self, channel, callback):
        """
        Subscribes to channel and calls the provided callback when it receives a new message
        :param channel:
        :param callback:
        :return:
        """
        self.__stream.subscribe(**{channel:callback})

    def unsubscribe(self, channel):
        self.__stream.unsubscribe(channel)

    def stop(self):
        self.__should_stop = True

    def run(self):
        for item in self.__stream.listen():
            #This is only blocking the thread, messages will be handled by the provided callback
            if self.__should_stop:
                break

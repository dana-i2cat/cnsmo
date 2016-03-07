from src.main.python.net.i2cat.system.state.driver.redis.client import RedisDriver
from src.main.python.net.i2cat.system.state.driver.redis.listener import RedisListener
from src.main.python.net.i2cat.system.state.driver.redis.publisher import RedisPublisher

from src.main.python.net.i2cat.system.state.client.systemstate import SystemStateClient
from src.main.python.net.i2cat.system.state.manager.systemstate import SystemStateManager


class SystemStateFactory:
    """
    Factory class that should be properly used and integrated, it just helps to quicly setUo SystemState clients and
    managers given the minimum set of input params
    """

    @staticmethod
    def generate_system_state_client(address, service_id, service_type, service_status, subscriptions, callback):
        """
        Returns a System State Client
        :param address:
        :param service_id:
        :param service_type:
        :param service_status:
        :param subscriptions:
        :param callback:
        :return:
        """
        driver = RedisDriver(address)
        listener = RedisListener(address)
        publisher = RedisPublisher(address)

        client = SystemStateClient(client=driver, listener=listener, publisher=publisher, service_id=service_id, service_type=service_type,
                                   service_status=service_status, subscriptions=subscriptions, callback=callback)
        return client

    @staticmethod
    def generate_system_state_manager(address):
        """
        Return System State Server
        :param address:
        :return:
        """
        driver = RedisDriver(address)
        listener = RedisListener(address)
        publisher = RedisPublisher(address)

        manager = SystemStateManager(client=driver, listener=listener, publisher=publisher)
        return manager

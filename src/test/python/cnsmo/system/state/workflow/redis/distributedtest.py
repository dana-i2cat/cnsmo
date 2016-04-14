from src.main.python.net.i2cat.cnsmo.system.state.driver.redis.listener import RedisListener
from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory
from src.main.python.net.i2cat.cnsmo.system.state.driver.redis.publisher import RedisPublisher
import time
import threading
import multiprocessing


class DistributedRedisTest:

    def __init__(self):
        call = threading.Thread
        self.client = SystemStateFactory.generate_system_state_client("localhost:6379", "Client",
                                                                      "Ready", ["Client2"], self.client_pipe)

        self.client2 = SystemStateFactory.generate_system_state_client("localhost:6379", "Client2",
                                                                      "Ready", ["Client"], self.client_pipe)

        self.manager = SystemStateFactory.generate_system_state_manager("localhost:6379")

        t = call(target=self.manager.start)
        t.start()
        time.sleep(0.5)
        t2 = call(target=self.client2.start)
        t2.start()
        time.sleep(0.5)
        t3 =  call(target=(self.client.start))
        t3.start()

    def client_pipe(self, message):
        print "New Message Recieved", message

    def get_local_listener(self):
        return RedisListener("localhost:6379")


if __name__ == "__main__":
    DistributedRedisTest()


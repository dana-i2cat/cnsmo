from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class Client2Test:

    def __init__(self):
        self.client = SystemStateFactory.generate_system_state_client("localhost:6379", "Client2",
                                                                      "Ready", ["Client1"], self.pipe)

        self.client.start()

    def pipe(self, message):
        print "Message recieved!!", message

if __name__ == "__main__":
    Client2Test()

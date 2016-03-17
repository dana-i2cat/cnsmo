from main.python.net.i2cat.factory.system.state.factory import SystemStateFactory


class Client1Test:

    def __init__(self):

        self.client = SystemStateFactory.generate_system_state_client("localhost:6379", "Client1","Client",
                                                                      "Ready", ["Client2"], self.pipe)
        self.client.start()

    def pipe(self, message):
        print "Message recieved!!", message

if __name__ == "__main__":
    Client1Test()



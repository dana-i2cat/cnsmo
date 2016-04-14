from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class DistributedSystemState:

    def __init__(self):

        self.manager = SystemStateFactory.generate_system_state_manager("localhost:6379")
        self.manager.start()


if __name__ == "__main__":
    DistributedSystemState()

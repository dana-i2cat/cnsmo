def launch_system_state(redis_address="localhost:6379"):
    """
    Launches the system state manager, backed by a redis server instance.
    Requires a redis server running at given address.
    :param redis_address: Address of hte redis server
    :return:
    """
    system_state = SystemStateFactory.generate_system_state_manager(redis_address)
    system_state.start()

if __name__ == "__main__":

    import os
    import sys
    import getopt

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:", [] )

    host = "0.0.0.0"
    port = "6379"
    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../"
    print src_dir
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory

    redis_address = host + ":" + port
    launch_system_state(redis_address)

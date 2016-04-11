def main(redis_address="localhost:6379"):
    system_state = SystemStateFactory.generate_system_state_manager(redis_address)
    system_state.start()

if __name__ == "__main__":

    import os
    import sys
    import time
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
    src_dir = path + "/../../../../../../"
    print src_dir
    if not src_dir in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory

    redis_address = host + ":" + port
    main(redis_address)


def main(redis_address):

    vpn_manager = VPNManager(redis_address)
    vpn_manager.start()

    while True:
        if vpn_manager.get_status() == "ready":
            vpn_manager.deploy()
            break
        time.sleep(1)
        print vpn_manager.get_status()
        print "====================================================="
        print vpn_manager.__dict__
        print "====================================================="


if __name__ == "__main__":

    import sys
    import os
    import time
    import getopt

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../"
    if not src_dir in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager

    opts, _ = getopt.getopt(sys.argv[1:], "r:", [])
    redis_address = "127.0.0.1:6379"
    service_id = "ServerVPN"

    for opt, arg in opts:
        if opt == "-r":
            redis_address = arg

    main(redis_address)

import subprocess

def get_app_request(host, port, service_id):

    bind_address = "0.0.0.0"

    call = lambda command: subprocess.check_output(command, shell=True)

    os.chdir("/var/tmp/slipstream/cnsmo/cnsmo")

    gitBranch = call('git branch').rstrip('\n').lstrip('* ')

    d = dict(service_id=service_id,
             trigger='python client.py -a %s -p %s -w "$(pwd)"' % (bind_address, port),
             resources=["https://raw.githubusercontent.com/dana-i2cat/cnsmo/%s/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/app/client.py" % gitBranch,
                        ],

             dependencies=[],

             endpoints=[{"uri":"http://%s:%s/sdn/client/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_config"},
                        {"uri":"http://%s:%s/sdn/client/" %(host, port), "driver":"REST", "logic":"upload", "name":"set_ca_cert"},
                        ]
             )
    return d


def main(host, port, redis_address, service_id):

    bash_deployer = BashDeployer(None)
    configurer = CNSMOManager(redis_address, service_id, "SDNClient", bash_deployer, None)
    configurer.start()
    configurer.compose_service(**get_app_request(host, port, service_id))
    configurer.launch_service(service_id)


if __name__ == "__main__":
    import sys
    import os
    import time
    import getopt

    path = os.path.dirname(os.path.abspath(__file__))
    src_dir = path + "/../../../../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
    from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:r:s:", [])

    host = "0.0.0.0"
    port = "9098"
    redis_address = "127.0.0.1:6379"
    service_id = "ClientSDN"

    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg
        elif opt == "-r":
            redis_address = arg
        elif opt == "-s":
            service_id = arg

    main(host, port, redis_address, service_id)

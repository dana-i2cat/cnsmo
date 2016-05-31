import sys
import os
import getopt
import json
import threading
import time

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


class LBManager:

    def __init__(self, related_service_ids, load_balanced_addresses, bind_address, system_state_manager=None):
        """
        :param related_service_ids: List with the service id of related LBServer and LBConfigManager
        :param load_balanced_addresses: List with addresses being balanced in the format ["ip:port", "ip:port",...]
        :param bind_address:
        :param system_state_manager:
        """
        print("LBManager(related_service_ids={}, load_balanced_addresses={}, bind_address={}, system_state_manager={})"
              .format(related_service_ids, load_balanced_addresses, bind_address, system_state_manager))
        self.__bind_address = bind_address
        self.__system_state_manager = system_state_manager
        self.__name = "LB_SERVICE_MANAGER"
        self.__load_balanced_addresses = load_balanced_addresses

        self.__related_service_ids = related_service_ids
        self.__server_service = None
        self.__configuration_manager = None

        self.__thread_pool = set()

        self.__status = "power_off"

    def __configure_system_state(self):
        self.__system_state_manager = SystemStateFactory.generate_system_state_client(self.__bind_address, "myLb", "LBManager",
                                                                                      self.__status, ["LBServer", "LBConfigManager"],
                                                                                      self.register_service)

    def start(self):
        self.__configure_system_state()
        self.__system_state_manager.start()

    def deploy(self):
        if self.__status == "ready":
            self.__deploy_lb()
        else:
            try:
                self.__thread_pool.add(threading.Thread(target=self.deploy))
            except:
                pass

    def deploy_blocking(self):
        while True:
            if self.__status == "ready":
                break
            time.sleep(0.2)

        time.sleep(5)
        self.__deploy_lb()

    def get_status(self):
        return self.__status

    def register_service(self, service):
        """
        Meant to be registered by the systemState,
        This manger expects 2 services, the server and the config manager. But must be the ones with selected ids.
        Only after these services have registered , the LB can be deployed.
        :param service:
        :return:
        """
        if service.get_service_id() in self.__related_service_ids:
            if service.get_service_type() == "LBServer":
                server_service = ServiceMaker().make_service("Server", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
                self.__server_service = server_service
                self.__update_state()

            elif service.get_service_type() == "LBConfigManager":
                config_service = ServiceMaker().make_service("ConfigManager", self.__system_state_manager.load(service.get_service_id()).get_endpoints())
                self.__configuration_manager = config_service
                self.__update_state()

    def __update_state(self):

        if self.__server_service and self.__configuration_manager:
            self.__status = "ready"
            [t.start() for t in self.__thread_pool]

    def __deploy_lb(self):
        """
        Main service of the LB manager. Here is the logic of the LB manager, this method is called after start()
        successfully works.

        The idea is to deploy all the LB instances all over the context and manage them.
        :return:
        """
        print "Deploying LB..."

        print "generating lb server configuration..."

        # Get all config files
        haproxy_config = self.__configuration_manager.get_haproxy_config(None).content
        dockerfile = self.__configuration_manager.get_docker(None).content

        # TODO find a proper name for the server
        self.__configure_and_start_lb_server("lb-server", haproxy_config, dockerfile, self.__load_balanced_addresses)

        print "LB deployed."

    def __configure_and_start_lb_server(self, name, haproxy_cfg, dockerfile, load_balanced_addresses):
        """
        Helper method that configures server service with given configuration and starts the service
        """
        print "configuring lb server " + name + " ..."
        self.__server_service.set_docker({"file":("Dockerfile", dockerfile)})
        self.__server_service.set_haproxy_config({"file":("haproxy.cfg", haproxy_cfg)})

        self.__server_service.build_lb({})

        print "starting lb server " + name + " ..."
        self.__server_service.start_lb(load_balanced_addresses)


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "i:b:r:")

    for opt, arg in opts:
        if opt in ("-i",):
            formatted_service_ids = json.loads(arg)

        elif opt == "-b":
            formatted_balanced_services = json.loads(arg)

        elif opt == "-r":
            redis_address = arg

    manager = LBManager(formatted_service_ids, formatted_balanced_services, redis_address)
    manager.start()
    manager.deploy_blocking()

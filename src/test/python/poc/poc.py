from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager


def get_server_app_request():
    """
    Main request necessary to create an APP from a service.
    It contains the ID, no resources and no dependencies. The trigger, which is the command to execute this app
    The trigger is quite intrusive, it requires some refactor to make it clearer and easy to use
    :return:
    """
    return dict(service_id="server_123",
                trigger= "cp /home/oscarcillo/example/server.py /home/CNSMO/ENVS/server_123/server.py && python /home/CNSMO/ENVS/server_123/server.py",
                resources = [],
                dependencies=[])

def get_cert_app_request():
    return dict(service_id="cert_123",
                trigger= "cp /home/oscarcillo/example/cert.py /home/CNSMO/ENVS/cert_123/cert.py && python cert.py",
                resources = [],
                dependencies=[])


def main():
    """
    This i a basic proof of concept of the CYCLONE CNSMO architecture
    The idea is the following:
    :We have a system state, which is representedby this main() and the mocked System state class.
    :We also have the VPN Manager which is a kind of orchestrator for different services
    :the credentialManager service represents the entity that will provide the config files and stuff
    :The Server is meant to be the service that will deploy the VPN server daemon

    the credential and server services are both configured with a basic bash deployer. That means
    that any launched app in that service, will be spawned via bash.
    For simplicity this PoC just launches to python REST servers that only respond with dummy responses.
    :return:
    """
    #Configuring basic stuff
    system_state = SystemState()
    #Just configureing the mocked system state (None arguments represents the systemstate argument)
    bash_deployer = BashDeployer(None)

    #VPN manager example, configured with the mocked system state
    vpn_manager = VPNManager(None, system_state)

    #This is a simulation. It represents that this is a distributed system
    #The service Server is spawned at some place
    server = CNSMOManager(None, "Server","server", bash_deployer, None)
    #The service Credential is spawned at another place
    credential = CNSMOManager(None, "CredentialManager", "cert", bash_deployer, None)

    #The system launches an APP to the server service (which is the python server app)
    server.launch_app(**get_server_app_request())
    #Same here but with another app
    credential.launch_app(**get_cert_app_request())

    #We sleep here in order to let the servers spawn correctly, in therry there should be callbacks or something
    import time
    time.sleep(0.5)

    #Now since we are some kind of system state, we report to the VPN Manager that the services, Server and
    #Credential Manager just were ready to use
    vpn_manager.register_service("Server")
    vpn_manager.register_service("CredentialManager")


    #We start the VPN manager here to avoid concurrency problems but it could be started at the beginig
    vpn_manager.start()


from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker


class SystemState:

    def __init__(self):
        """
        Mocked class to represent some of the system state functionalities.
        This class is passed to the VPN manager in order to let it think that is actually
        loading something.

        One of the key features of this class is that is more or less functional is allows
        to directly create Services from provided endpoints of the users.
        Service Maker class provides more info about this
        :return:
        """
        self.service_maker = ServiceMaker()

    def start(self):
        pass

    def load(self, service):
        """
        From the user given endpoints it creates a Service instance that povides a set of methods distinguished
        byt the <name> enpoind param that are automatically configured to call an endpoint given the URI and the
        driver

        For example: There will be a service instance provided to the VPN server that will have the get_dh() method.
        This method will do a GET Rest call to the URI provided
        :param service:
        :return:
        """

        server_dict = dict(uri="http://127.0.0.1:9092/server/{param}",
                           driver="REST", logic="get", name="start")

        credential_manager_dict = dict(uri="http://127.0.0.1:9091/dh/",
                                              driver="REST", logic="get", name="get_dh")

        if service == "Server":
            return self.service_maker.make_service("Server", [server_dict])

        elif service == "CredentialManager":
            return self.service_maker.make_service("CredentialManager", [credential_manager_dict])

        return None


if __name__ == "__main__":
    main()


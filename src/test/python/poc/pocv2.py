import threading
import time

from src.main.python.net.i2cat.cnsmo.lib.model.service import Service

from src.main.python.net.i2cat.cnsmo.deployment.bash import BashDeployer
from src.main.python.net.i2cat.cnsmo.manager.cnsmo import CNSMOManager
from src.main.python.net.i2cat.cnsmoservices.vpn.manager.vpn import VPNManager
from src.main.python.net.i2cat.cnsmo.factory.system.state.factory import SystemStateFactory


def get_server_app_request():
    """
    Main request necessary to create an APP from a service.
    It contains the ID, no resources and no dependencies. The trigger, which is the command to execute this app
    The trigger is quite intrusive, it requires some refactor to make it clearer and easy to use
    :return:
    """
    d = dict(service_id="server_123",
                trigger= "cp /home/oscarcillo/example/server.py /home/CNSMO/ENVS/server_123/server.py && python /home/CNSMO/ENVS/server_123/server.py",
                resources = [],
                dependencies=[],
                endpoints= [{ "uri":"http://127.0.0.1:9092/server/{param}",
                         "driver":"REST",
                        "logic":"get",
                         "name":"start"}])

    service = Service()
    service.objectify(**d)
    return service


def get_cert_app_request():
    d =  dict(service_id="cert_123",
                trigger= "cp /home/oscarcillo/example/cert.py /home/CNSMO/ENVS/cert_123/cert.py && python cert.py",
                resources = [],
                dependencies=[],
                endpoints=[{"uri":"http://127.0.0.1:9091/dh/",
                            "driver":"REST",
                            "logic":"get",
                            "name":"get_dh"}])


    service = Service()
    service.objectify(**d)
    return service


def main():
    """
    This is the second proof of concept of the CYCLONE CNSMO architecture
    The idea is the following:
    :We have a distributed  system state, which is actually implmemented.
    :We also have the VPN Manager which is a kind of orchestrator for different services
    :the credentialManager service represents the entity that will provide the config files and stuff
    :The Server is meant to be the service that will deploy the VPN server daemon

    the credential and server services are both configured with a basic bash deployer. That means
    that any launched app in that service, will be spawned via bash.
    For simplicity this PoC just launches to python REST servers that only respond with dummy responses.
    :return:
    """
    #Configuring the System State Manager, it listen to new services
    system_state = SystemStateFactory.generate_system_state_manager("localhost:6379")
    t = threading.Thread(target=system_state.start)
    t.start()
    time.sleep(1) #Sleeping for synchronization

    #The bash deployer to be used by the Server and the credential manager
    bash_deployer = BashDeployer(None)

    #Configuring the VPN Orchestrator in a different Thread to make things feel real
    vpn = VPNManager("localhost:6379")
    t2 = threading.Thread(target=vpn.start)
    t2.start()
    time.sleep(1) #Sleeping for synch

    #At this point the VPN Manager is advertising himself to the SystemState,
    #There is a Main topic called Discovery.
    #By default the VPN Orchestrator is susbcribed to Client, Server and Credential MAnager Topics


    #Configuring the Server Manager
    server = CNSMOManager("localhost:6379", "server_123", "Server", bash_deployer, None)

    #Configuring the Credential Manager
    credential = CNSMOManager("localhost:6379", "cert_123", "CredentialManager", bash_deployer, None)

    #Launching the server in another thread to make things feel real
    t3 = threading.Thread(target=server.start)
    t3.start()
    time.sleep(1)

    #Launching the credential manager in a different thread to make things feel real
    t4 = threading.Thread(target=credential.start)
    t4.start()
    time.sleep(1)

    #Now we simulate that we are composing a server service for the ServerManager
    server.compose_service(**get_server_app_request().dictionarize())
    #...And launch it
    server.launch_service("server_123")
    time.sleep(0.5)# Again, for synch, this is just to help to read the logs in the correct order


    #Let's compose a service for the credential manager as well
    credential.compose_service(**get_cert_app_request().dictionarize())
    #...And of course, launch it
    credential.launch_service("cert_123")

    #We sleep here in order to let the servers spawn correctly...
    time.sleep(0.5)
    #to finally deploy the VPN...
    vpn.deploy()


if __name__ == "__main__":
    main()
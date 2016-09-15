# CNSMO

CNSMO is a platform providing network services in Cloud computing environments.
It aims to bring to the Cloud ecosystem the possibility to automate the deployment of network services, thus limiting the intervention of human agents to specific cases.

For more information about its mission, who may benefit from it and much more, please visit the [website](http://opennaas.org/opennaas-cnsmo/).
You'll find some interesting videos too!


## CNSMO key concepts
CNSMO is a lightweight micro-services framework. Leveraging the base concepts of Apache Mesos, CNSMO is a lightweight distributed platform defining a basic service API and service life-cycle, together with an inter-service communication mechanism implementing the actor model and supporting different communication protocols. The system is capable of deploying and running multiple services in both local and remote environments.

CNSMO is composed by two components:
* The CNSMO core
* CNSMO agents running networking services

CNSMO core contains a CNSMO agent running services that are key to CNSMO platform itself. It is not directly related to any networking service. Instead, it runs the distributed system state and other support services CNSMO couldn’t work without.

The System State is used to store the application state, so it can recover from failure or system shutdown. By using it intensively, module can become stateless which turns out to be very useful when scaling. Moreover, the System State has a message queue that is used by every component to communicate to each others. It offers serialization mechanisms providing implementation independency between modules. It also offers load balancing features, useful to distribute the application load between multiple instances of the same CNSMO component, in this case, multiple instances of the same specific network service module (e.g. VPN service module). It also allows a framework where every CNSMO context announces itself when it is ready and allows other service to subscribe to status changes of services enabling service orchestration if needed.

CNSMO agents are wrappers for a specific service providing CNSMO the ability to manage that service. Thanks to these agents CNSMO discovers the services, is able to spawn or delete service instances but also orchestrate service deployment between many VMs. CNSMO agents are active and report to the CNSMO core (more specifically to the distributed system state) when launched. A different agent is required for each service in each machine.


## CNSMO network services
The following network services are currently available:
* A VPN service, enabling all VMs in a deployment to join it and communicate securely despite them being in distant data centers.
* A firewalling service in each VM filtering the network traffic according to specific rules or policies.
* A load balancing service, balancing the load between a group of VMs in a deployment (a subset of the whole deployment).

For a detailed description of each of them, please refer to [CNSMO networking services guide for application developers](http://opennaas.org/download/17172/).

### Website:
http://opennaas.org/opennaas-cnsmo/

### Authors:
Oscar Moya
Isart Canyameres

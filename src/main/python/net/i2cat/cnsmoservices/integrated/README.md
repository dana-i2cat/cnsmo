# CNSMO services configuration

In this file we find the information on how to configure properly the CNSMO services [vpn,sdn, fw, lb]. Every service uses some global parameters (whose configuration can be found in this file) and some parameters that are specific for the service (the links can be found at the bottom of this file).

The Input/Output parameters are used for the correct synchronization between client, server and orchestrator, and they are also used in order to pass important information between them. Depending on which services we want to deploy on the machines, we will need to configure different parameters so that we make visible the private information needed for the services to work properly. For example, a VPN server should make his IP address visible to the clients so that they can stablish a VPN with the server.

Parameters of a SlipStream application that need to be created and their values or mappings. 

* Agent

Input parameter cnsmo.server.nodeinstanceid is mapped to output Server:cnsmo.server.nodeinstanceid

Input parameter net.i2cat.cnsmo.git.branch has to be set to the git branch from where the code has to be downloaded

Input parameter net.services.enable parameter is used to indicate which network service has to be deployed following the format ["vpn","fw","lb","sdn"]

Output parameter net.i2cat.cnsmo.core.ready set to default

Output parameter net.i2cat.cnsmo.dss.address set to default

Output parameter net.services.enabled set to default 

* Server

Input parameter net.i2cat.cnsmo.git.branch has to be set to the git branch from where the code has to be downloaded.

Input parameter net.services.enable parameter is used to indicate which network service has to be deployed following the format ["vpn","fw","lb","sdn"]

Output parameter cnsmo.server.nodeinstanceid set to default

Output parameter net.i2cat.cnsmo.core.ready set to default

Output parameter net.i2cat.cnsmo.dss.address set to default

Output parameter net.services.enabled set to default

### Some services might need additional parameters to be configured. Read services documentation in:

* [LB documentation](/src/main/python/net/i2cat/cnsmoservices/lb/run/slipstream/README.md)
* [FW documentation](/src/main/python/net/i2cat/cnsmoservices/fw/run/slipstream/README.md)
* [SDN documentation](/src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run/slipstream/README.md)
* [VPN documentation](/src/main/python/net/i2cat/cnsmoservices/vpn/run/slipstream/README.md)
# This directory contains the set of scripts SlipStream runs to deploy the SDN
Currently, the SDN requieres a version of Ubuntu 14.04 in order to run properly. We are planning to widen the compatibility requirements in the future.

SlipStream defines the following phases which are run in this order in each VM:
pre-install, install, post-install, deployment and reporting.

In the install phase, the following packages must be installed in both client and server VMs:
curl
cython
git
python-pip
openvswitch-switch
unzip

### About the scripts:
* sdn-client-postinstall.sh is meant to be copied on the SlipStream webApp postinstall field. This is like this so that all the code is together in one place.
* sdn-client-deployment.sh is meant to run in the sdn-client VM at deployment phase, after post-install.
* sdn-client-deployment.py is executed by sdn-client-deployment.sh. It contains the deployment instructions.
* sdn-server-postinstall.sh is meant to be copied on the SlipStream webApp postinstall field. 
* sdn-server-deployment.sh is meant to run in the sdn-server VM at deployment phase, after post-install.
* sdn-server-deployment.py is executed by sdn-server-deployment.sh. It contains the deployment instructions.

## About Slipstream Parameters
The common parameters for all services need to be created and mapped properly. In the case of SDN, VPN has to be configured, together with the corresponding parameters, and the following parameters are the additional ones for the SDN service.

* Agent

Input parameter net.i2cat.cnsmo.service.sdn.server.ready set to default

Output parameter net.services.installed	set to default

* Server

Output parameter net.i2cat.cnsmo.service.sdn.server.ready set to default


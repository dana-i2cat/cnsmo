# This directory contains the set of scripts SlipStream runs to deploy the DNS
Currently, the dns requieres a version of Ubuntu 14.04 in order to run properly. We are planning to widen the compatibility requirements in the future.

SlipStream defines the following phases which are run in this order in each VM:
pre-install, install, post-install, deployment and reporting.

In the install phase, the following packages must be installed in both client and server VMs:
curl
cython
git
python-pip
dnsmasq
unzip

### About the scripts:
* dns-client-postinstall.sh is meant to be copied on the SlipStream webApp postinstall field. This is like this so that all the code is together in one place.
* dns-client-deployment.sh is meant to run in the dns-client VM at deployment phase, after post-install.
* dns-client-deployment.py is executed by dns-client-deployment.sh. It contains the deployment instructions.
* dns-server-postinstall.sh is meant to be copied on the SlipStream webApp postinstall field. 
* dns-server-deployment.sh is meant to run in the dns-server VM at deployment phase, after post-install.
* dns-server-deployment.py is executed by dns-server-deployment.sh. It contains the deployment instructions.

## About Slipstream Parameters
The common parameters for all services need to be created and mapped properly.

* Agent

Input parameter net.i2cat.cnsmo.service.dns.server.ready set to default

Output parameter net.services.installed	set to default

* Server

Output parameter net.i2cat.cnsmo.service.dns.server.ready set to default


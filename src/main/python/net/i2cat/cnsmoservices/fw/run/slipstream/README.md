# This directory contains the set of scripts SlipStream runs to deploy the FW service
Currently, the FW requieres a version of Ubuntu 14.04 in order to run properly. We are planning to widen the compatibility requirements in the future.

SlipStream defines the following phases which are run in this order in each VM:
pre-install, install, post-install, deployment and reporting.

In the install phase, the following packages must be installed in both client and server VMs:
curl
cython
git
python-pip
unzip

* About the scripts:
fwdeployment.py is executed by fwdeployment.sh. It contains the deployment instructions.

fwdeployment.sh is meant to run at deployment phase, after post-install.

fwpostinstall.sh is meant to be copied on the SlipStream webApp postinstall field. 

## About Slipstream Parameters
The common parameters for all services need to be created and mapped properly. In the case of LB, VPN has to be configured, together with the corresponding parameters, and the following parameters are the additional ones for the LB service.

* Agent

Input net.i2cat.cnsmo.service.fw.rules: if we don't want to add fw rules at the beggining, the parameter has to be set to an empty list of rules '[]'.

* Server

Input net.i2cat.cnsmo.service.fw.rules:if we don't want to add fw rules at the beggining, the parameter has to be set to an empty list of rules '[]'.

An example of a FW rule is the following:

[{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"src", "ip_range":"0.0.0.0/0", "action":"drop"}, {"direction":"in", "protocol":"tcp", "dst_port":"9091", "dst_src":"src", "ip_range":"0.0.0.0/0", "action":"acpt"}]

Where every rules is enclosed by {}.
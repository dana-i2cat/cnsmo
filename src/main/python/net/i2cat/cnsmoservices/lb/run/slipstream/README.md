# This directory contains the set of scripts SlipStream runs to deploy the LB service
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

* About the scripts:
lborchestratordeployment.py is executed by lborchestratordeployment.sh. It contains the deployment instructions.

lborchestratordeployment.sh is meant to run at deployment phase, after post-install.

lborchestratorpostinstall.sh is meant to be copied on the SlipStream webApp postinstall field. 

## About Slipstream Parameters
The common parameters for all services need to be created and mapped properly. In the case of LB, VPN has to be configured, together with the corresponding parameters, and the following parameters are the additional ones for the LB service.

* Agent

No extra parameters to add.

* Server

Input lb.mode acceptes the values: leastconn/roundrobin/source. Defaults to leastconn

Input lb.node indicates the SlipStream node whose instances will be load balanced

Input lb.port has to be set to the tcp port to load balance


# This directory contains the set of scripts SlipStream runs to deploy the VPN

SlipStream defines the following phases which are run in this order in each VM:
pre-install, install, post-install, deployment and reporting.

In the install phase, the following packages must be installed in both client and server VMs:
curl
cython
git
python-pip

### About the scripts:
* vpn-client-postinstall.sh is meant to run in the VPN-client VM at post-install phase.
* vpn-client-deployment.sh is meant to run in the VPN-client VM at deployment phase, after post-install.
* vpn-client-deployment.py is executed by vpn-client-deployment.sh. It contains the deployment instructions.
* vpn-server-postinstall.sh is meant to run in the VPN-server VM at post-install phase.
* vpn-server-deployment.sh is meant to run in the VPN-server VM at deployment phase, after post-install.
* vpn-server-deployment.py is executed by vpn-server-deployment.sh. It contains the deployment instructions.

These scripts conform the SlipStream application recipe, together with the instruction about which base image should be used. The scripts serve to launch desired services but also as means to interact with the SlipStream application deployment context (run context. . It is through this context, accessed via the slipstream client installed in each machine, that scripts can access a shared state of the run and have access to environment variables. The context also serves as a mean to synchronize the services deployment.

CYCLONE network services are made available to the CYCLONE ecosystem via SlipStream recipes that include scripts in this folder. When run, these scripts launch the CNSMO systemstate and create CNSMOManagers for each required service. Service orchestrator will then manage the overall deployment, sometimes lead by events triggered by the deployment
scripts, specially when synchonization over the run context is required.

## About Slipstream Parameters
The common parameters for all services need to be created and mapped properly. The following parameters are the additional ones for the VPN service.

* Agent

Input parameter vpn.server.address is mapped to output Server:vpn.address

Input parameter vpn.server.nodeinstanceid is mapped to output Server:vpn.server.nodeinstanceid

Output parameter net.i2cat.cnsmo.service.vpn.client.listening set to default

Output parameter net.services.installed	set to default

Output parameter vpn.address set to default

Output parameter vpn.address6 set to default

* Server

Output parameter net.i2cat.cnsmo.service.vpn.configurator.listening set to default

Output parameter net.i2cat.cnsmo.service.vpn.orchestrator.ready	set to default

Output parameter net.i2cat.cnsmo.service.vpn.ready set to default

Output parameter net.i2cat.cnsmo.service.vpn.server.listening set to default

Output parameter net.services.installed set to default

Output parameter vpn.address set to default

Output parameter vpn.address6 set to default

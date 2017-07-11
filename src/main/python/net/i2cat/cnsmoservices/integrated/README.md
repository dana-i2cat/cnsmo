# CNSMO services parameters configuration

Parameters of a SlipStream apllication that need to be created and their values or mappings. 

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



### Some services might need additional parameters to be configured. Read services documentation in /../cnsmoservices/{service}/ for more information
# SDN service

The SDN service consists of 4 different components:
* Orchestrator. Manages in a centralized manner the deployment of the SDN.
* Configurator. Generates configuration files and key-pairs for server and clients.
* Server. Configures and deploys an OVS server.
* Client. Configures and deploys an SDN client, bound to the server.

All these components require an extra 5th component:
* CNSMO systemstate. Used for service discovery.

## How to run

Executable files can be located at:
* src/main/python/net/i2cat/cnsmoservices/sdnoverlay/run directory, for SDN specific components
* src/main/python/net/i2cat/cnsmo/run/systemstate.py, for the CNSMO systemstate

Requirements:
* openvswitch-switch
* unzip
* Have VPN server running and the VPN clients configured

### Run the server
1. Run the VPN server and configure all the VPN clients.
2. Run the installation script in :  ```src/main/python/net/i2cat/cnsmoservices/sdn/run/slpistream/sdnserverpostinstall.sh ```
3. Run the deployment script in :  ```src/main/python/net/i2cat/cnsmoservices/sdn/run/slpistream/sdnserverdeployment.sh ```

### Run the client
4. Run the installation script in :  ```src/main/python/net/i2cat/cnsmoservices/sdn/run/slpistream/sdnclientpostinstall.sh ```
5. Run the installation script in :  ```src/main/python/net/i2cat/cnsmoservices/sdn/run/slpistream/sdnclientpostinstall.sh ```

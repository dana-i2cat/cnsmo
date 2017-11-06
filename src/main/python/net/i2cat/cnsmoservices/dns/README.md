# SDN service

The DNS service consists of 2 different components:
* Server. Configures and deploys DNS server.
* Client. Points to Server in DNS configuration.

All these components require an extra 5th component:
* CNSMO systemstate. Used for service discovery.

## How to run

Executable files can be located at:
* src/main/python/net/i2cat/cnsmoservices/dns/run directory, for DNS specific components
* src/main/python/net/i2cat/cnsmo/run/systemstate.py, for the CNSMO systemstate

Requirements:
* dnsmasq


### Run the server
1. Run the installation script in :  ```src/main/python/net/i2cat/cnsmoservices/dns/run/slpistream/dnsserverpostinstall.sh ```
2. Run the deployment script in :  ```src/main/python/net/i2cat/cnsmoservices/dns/run/slpistream/dnsserverdeployment.sh ```

### Run the client
3. Run the installation script in :  ```src/main/python/net/i2cat/cnsmoservices/dns/run/slpistream/dnsclientpostinstall.sh ```
4. Run the deployment script in :  ```src/main/python/net/i2cat/cnsmoservices/dns/run/slpistream/dnsclientpostinstall.sh ```

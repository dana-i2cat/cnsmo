# VPN service

The VPN service consists of 4 different components:
* Orchestrator. Manages in a centralized manner the deployment of the VPN.
* Configurator. Generates configuration files and key-pairs for server and clients.
* Server. Configures and deploys an openvpn server.
* Client. Configures and deploys an openvpn client, bound to the server.

All these components require an extra 5th component:
* CNSMO systemstate. Used for service discovery.

## How to run

Executable files can be located at:
* src/main/python/net/i2cat/cnsmoservices/vpn/run directory, for VPN specific components
* src/main/python/net/i2cat/cnsmo/run/systemstate.py, for the CNSMO systemstate

Requirements:
* docker (check docker automatic installation instructions for GNU-Linux systems [here](https://docs.docker.com/engine/getstarted/linux_install_help/), or the general [docker installation instructions page](https://docs.docker.com/engine/installation/)).
* python 2.7.X and pip
* openvpn (check [openvpn download page](https://openvpn.net/index.php/download/community-downloads.html))
* redis server installed (check [redis download page](https://redis.io/download))
* a VM to act as the VPN client

### Run the server
1. Run the redis server
2. Keep in mind your IP address (IP_ADDR)
3. Install the dependencies with: ```sudo pip install -r requirements.txt```
(it is recommended to do this in a  python virtual env)
4. Run the system state: ```python src/main/python/net/i2cat/cnsmo/run/systemstate.py```
5. Run the orchestrator: ```python src/main/python/net/i2cat/cnsmoservices/vpn/run/orchestrator.py -r IP_ADDR:6379```.
It will wait for the rest of services to start the VPN deployment.
6. Run the configurator: ```sudo python src/main/python/net/i2cat/cnsmoservices/vpn/run/configurator.py -a IP_ADDR -p 9093 -r IP_ADDR:6379 -s VPNConfigurator --vpn-server-ip IP_ADDR --vpn-server-port 1194 --vpn-address 10.10.10.0 --vpn-mask 255.255.255.0```
7. Run the server: ```sudo python src/main/python/net/i2cat/cnsmoservices/vpn/run/server.py -a IP_ADDR -p 9092 -r IP_ADDR:6379 -s VPNServer```

### Run the client
8. Start de client VM, bridged to the host (must be able to reach IP_ADDR). Run ```vagrant up``` from ```src/main/python/net/i2cat/cnsmoservices/vpn/run/provision/client/``` directory.
9. Login to the vm: ```vagrant ssh```
10. Download CNSMO sources. If using provided Vagrantfile, local sources directory tree is already mounted to ```/cnsmo```.
11. Install software requirements (redis is not required). ```sudo apt-get install -y curl git cython python-pip && curl -fsSL https://get.docker.com/ | sh```
12. Install dependencies, as in step 3 for the server.
13. Keep in mind the client VM IP address (CLIENT_IP_ADDR)
14. Run the client: ```sudo python src/main/python/net/i2cat/cnsmoservices/vpn/run/client.py -a CLIENT_IP_ADDR -p 9091 -r IP_ADDR:6379 -s VPNClient-1```

###Clean up

```
# IN CLIENT VM:
sudo killall python
sudo rm -rf /home/CNSMO
sudo docker rm -f client-vpn
sudo docker rmi client-vpn

# IN SERVER HOST:
sudo killall python
sudo rm -rf /home/CNSMO
sudo docker rm -f server-vpn
sudo docker rmi vpn-server
```
Run ```vagrant destroy``` from ```src/main/python/net/i2cat/cnsmoservices/vpn/run/provision/client/``` directory.
Also, stop the redis server.

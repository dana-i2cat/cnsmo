# LB service

The LB service consists of 3 different components:
* Orchestrator. Manages in a centralized manner the deployment of the LB.
* Configurator. Generates configuration files for the server.
* Server. Configures and deploys an haproxy server.

All these components require an extra component:
* CNSMO systemstate. Used for service discovery.

The LB service additionally requires some backend endpoints, which load should be balanced.
These backend endpoints are completely independent of the LB service itself, and will typically be in different
hosts. 

## How to run

Executable files can be located at:
* src/main/python/net/i2cat/cnsmoservices/lb/run directory, for LB specific components
* src/main/python/net/i2cat/cnsmo/run/systemstate.py, for the CNSMO systemstate
* demo_app.py, as sample backend server.

Requirements:
* docker (check docker automatic installation instructions for GNU-Linux systems [here](https://docs.docker.com/engine/getstarted/linux_install_help/), or the general [docker installation instructions page](https://docs.docker.com/engine/installation/)).
* python 2.7.X and pip
* redis server installed (check [redis download page](https://redis.io/download))


### Run the server
1. Run the redis server
2. Install the dependencies with: ```sudo pip install -r requirements.txt```
(it is recommended to do this in a python virtual env)
3. Keep in mind your IP address (IP_ADDR). Don't use localhost address, even for a single host demonstrator.
4. Run the system state: ```python src/main/python/net/i2cat/cnsmo/run/systemstate.py```
5. Run the orchestrator: ```sudo python src/main/python/net/i2cat/cnsmoservices/lb/run/orchestrator.py -a IP_ADDR -r IP_ADDR:6379 --lb-port=8008 --lb-mode=roundrobin --lb-backend-servers='["IP_ADDR:8081", "IP_ADDR:8082"]'```
It will run configurator and server, wait for them to be registered, and deploy the haproxy.

### Run the clients

6. Start client1 with: ```python demo_app.py IP_ADDR 8081 'Client1 here!'```
7. Start client2 with: ```python demo_app.py IP_ADDR 8082 'Client2 here!'```


### Check the LB
Check the load balancer with: ```curl IP_ADDR:8008```

Check for an experience like the one following:
```
PROMPT>curl IP_ADDR:8008
['Client1 here!']PROMPT> curl IP_ADDR:8008
['Client2 here!']PROMPT> 
```

###Clean up
```
sudo killall python
sudo rm -rf /home/CNSMO
sudo docker rm -f lb-docker-8008
sudo docker rmi lb-server-8008
```
Also, stop the redis server.

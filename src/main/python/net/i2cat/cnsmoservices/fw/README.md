# FW service

The FW service consists of a single component:
* Server. Configures and deploys a management API for local IP-tables daemon.

As any other CNSMo based service, the FW requires requires an extra component:
* CNSMO systemstate. Used for service discovery.


## How to run

Executable files can be located at:
* src/main/python/net/i2cat/cnsmoservices/fw/run directory, for LB specific components
* src/main/python/net/i2cat/cnsmo/run/systemstate.py, for the CNSMO systemstate
* demo_app.py, as sample web server, for demonstration purposes.

Requirements:
* docker (check docker automatic installation instructions for GNU-Linux systems [here](https://docs.docker.com/engine/getstarted/linux_install_help/), or the general [docker installation instructions page](https://docs.docker.com/engine/installation/)).
* python 2.7.X and pip
* redis server installed (check [redis download page](https://redis.io/download))


### Run the server
1. Run the redis server
2. Install the dependencies with: ```sudo pip install -r requirements.txt```
(it is recommended to do this in a python virtual env)
3. Keep in mind your IP address (IP_ADDR). Localhost may serve for this single host demonstrator.
4. Run the system state: ```python src/main/python/net/i2cat/cnsmo/run/systemstate.py```
5. Run the server: ```sudo python src/main/python/net/i2cat/cnsmoservices/fw/run/server.py -a IP_ADDR -p 9095 -r IP_ADDR:6379 -s fw-service-1```
It will deploy the FW service management API.
6. Build the service via the service management API: ```curl -X POST http://IP_ADDR:9095/fw/build/```

### Run the demo apps

7. Start client1 with: ```python demo_app.py IP_ADDR 8081 'Client1 here!'```
8. Start client2 with: ```python demo_app.py IP_ADDR 8082 'Client2 here!'```


### Check access.
Check the FW is NOT filtering traffic.
Check there is access to the apps with curl, looking for an experience like the one following:
```
PROMPT>curl IP_ADDR:8081
['Client1 here!']
PROMPT> curl IP_ADDR:8082
['Client2 here!']
PROMPT> 
```

### Configure FW 
9. Configure FW rules through the API with curl.
 Example given, deny traffic to port 8082 with: ```curl -H "Content-Type: application/json" -X POST -d '{"direction":"in", "protocol":"tcp", "dst_port":"8082", "dst_src":"dst", "ip_range":"0.0.0.0/0", "action":"drop"}' http://IP_ADDR:9095/fw/```

### Check access
Check the FW is filtering traffic.
Check access to the apps is filtered with curl, looking for an experience like the one following:
```
PROMPT>curl IP_ADDR:8081
['Client1 here!']
PROMPT> curl IP_ADDR:8082
...
```

###Clean up
```
sudo killall python
sudo rm -rf /home/CNSMO
sudo docker rm -f fw-docker
sudo docker rmi fw-docker
```
Also, stop the redis server.

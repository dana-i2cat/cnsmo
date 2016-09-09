import getopt
import os
import subprocess

import sys
from flask import Flask
from flask import make_response
from jinja2 import Template
import shlex

###
# This script launches an web application providing configuration files for the load balancer.
# Use the following command in order to invoke the application:
# python configurator.py -a 127.0.0.1 -p 9096 -s LB-ADDRESS -t LB-PORT -m roundrobin/leastconn/source -b "127.0.0.1:8080,127.0.0.1:8081"
###

app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/lb/configs/haproxy/", methods=[GET])
def get_haproxy_config():
    manager = app.config["manager"]
    raw_config = manager.get_config()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=haproxy.cfg"
    return response


@app.route("/lb/configs/docker/", methods=[GET])
def get_dockerfile():
    manager = app.config["manager"]
    raw_config = manager.get_dockerfile()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=Dockerfile"
    return response


class LBConfigManager:

    def __init__(self, lb_ip, lb_port, balance_mode, backend_servers_str):
        self.ip = lb_ip
        self.port = lb_port
        self.balance_mode = balance_mode
        self.backend_servers_str = backend_servers_str
        self.backend_servers = backend_servers_str.split(",")

    def get_config(self):
        """
        Generates an haproxy.cfg file content according to constructor input parameters.
        :return: The content for the haproxy.cfg file.
        """
        template = Template(HAPROXY_CONFIG_TEMPLATE)
        return template.render(ip=self.ip, port=str(self.port), balance_mode=self.balance_mode, backend_servers=self.backend_servers)

    def get_dockerfile(self):
        """
        Generates a Dockerfile content defining a container able to run HAProxy.
        Generated Dockerfile requires a start.bash file in order to run.
        :return: The content for the Dockerfile.
        """
        template = Template(DOCKERFILE_TEMPLATE)
        return template.render(ip=self.ip, port=str(self.port), backend_servers=self.backend_servers_str)


HAPROXY_CONFIG_TEMPLATE = """
defaults
        log     global
        mode    http
        option  httplog
        option  dontlognull
        option redispatch
        retries 3
        maxconn 2000
        timeout connect      5000
        timeout client      50000
        timeout server      50000

frontend lb
        bind 0.0.0.0:{{ port }}
        mode tcp
        option tcplog
        timeout client 3600s
        default_backend servers

backend servers
        mode tcp
        balance {{ balance_mode }}
        {% for backend_server in  backend_servers %}
        {%- if backend_server.strip() -%}
        server server-{{ loop.index }} {{ backend_server.strip() }} check
        {%- endif %}
        {% endfor -%}
        timeout connect 1s
        timeout queue 5s
        timeout server 3600s
"""

DOCKERFILE_TEMPLATE = """
FROM ubuntu:14.04

RUN \
  sed -i 's/^# \(.*-backports\s\)/\\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get install -y haproxy python && \
  sed -i 's/^ENABLED=.*/ENABLED=1/' /etc/default/haproxy && \
  rm -rf /var/lib/apt/lists/*

ADD haproxy.cfg /etc/haproxy/haproxy.cfg
ADD start.bash /haproxy-start

WORKDIR /etc/haproxy

#default value, may be overwritten with docker run -e COUCHDB_SERVERS=ip1:port,ip2:port
ENV COUCHDB_SERVERS="{{ backend_servers }}"

ENV COUCHDB_USERNAME=""
ENV COUCHDB_PASSWORD=""

ENV COUCHDB_HOSTNAME="{{ ip }}:{{ port }}"

CMD ["bash", "/haproxy-start"]

EXPOSE {{ port }}
"""

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:s:t:m:b:", ["lb-address=", "lb-port=", "lb-balance-mode=", "backend-servers="])

    address = "127.0.0.1"
    port = 9096

    for opt, arg in opts:
        print opt, arg
        if opt == "-a":
            address = arg
        elif opt == "-p":
            port = int(arg)
        elif opt in ("-s", "--lb-address"):
            lb_ip = arg
        elif opt in ("-t", "--lb-port"):
            lb_port = arg
        elif opt in ("-m", "--lb-balance-mode"):
            balance_mode = arg
        elif opt in ("-b", "--backend-servers"):
            backend_servers_str = arg

    manager = LBConfigManager(lb_ip, lb_port, balance_mode, backend_servers_str)
    app.config["manager"] = manager

    app.run(host=address, port=port, debug=True)




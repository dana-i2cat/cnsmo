import getopt
import os
import subprocess

import sys
from flask import Flask
from flask import make_response
from jinja2 import Template
import shlex


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/configs/dh/", methods=[GET])
def get_dh():
    manager = app.config["manager"]
    raw_config = manager.get_dh()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/server/", methods=[GET])
def get_server_config():
    manager = app.config["manager"]
    raw_config = manager.get_server_config()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/client/", methods=[GET])
def get_client_config():
    manager = app.config["manager"]
    raw_config = manager.get_client_config()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/cert/ca/", methods=[GET])
def get_ca_cert():
    manager = app.config["manager"]
    raw_config = manager.get_ca_cert()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/certs/client/", methods=[GET])
def get_client_cert():
    manager = app.config["manager"]
    raw_config = manager.get_client_cert()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/keys/client/", methods=[GET])
def get_client_key():
    manager = app.config["manager"]
    raw_config = manager.get_client_key()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/certs/server/", methods=[POST])
def generate_server_cert():
    manager = app.config["manager"]
    manager.generate_server_certs()
    return "", 204


@app.route("/vpn/configs/certs/client/", methods=[POST])
def generate_client_cert():
    manager = app.config["manager"]
    manager.generate_client_certs()
    return "", 204


@app.route("/vpn/configs/certs/server/", methods=[GET])
def get_server_cert():
    manager = app.config["manager"]
    raw_config = manager.get_server_cert()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


@app.route("/vpn/configs/keys/server/", methods=[GET])
def get_server_key():
    manager = app.config["manager"]
    raw_config = manager.get_server_key()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=dh2048.pem"
    return response


class VPNConfigManager:

    def __init__(self, ip, mask, port, server_ip, key_dir):
        self.ip = ip
        self.mask = mask
        self.port = port
        self.server_ip = server_ip
        self.key_dir = key_dir

    def generate_client_certs(self):
        command = "sh %s../build-key client" % self.key_dir
        subprocess.check_call(shlex.split(command))

    def generate_server_certs(self):
        subprocess.Popen("sh %s../build-key server" % self.key_dir)

    def get_client_cert(self):
        f = open(self.key_dir + "client.crt")
        content = f.read()
        f.close()
        return content

    def get_client_key(self):
        f = open(self.key_dir + "client.key")
        content = f.read()
        f.close()
        return content

    def get_client_config(self):
        template = Template(VPN_CLIENT_CONFIG_TEMPLATE)
        return template.render(port=str(self.port), server_ip=self.server_ip)

    def get_server_cert(self):
        f = open(self.key_dir + "server.crt")
        content = f.read()
        f.close()
        return content

    def get_server_key(self):
        f = open(self.key_dir + "server.key")
        content = f.read()
        f.close()
        return content

    def get_server_config(self):
        template = Template(VPN_SERVER_CONFIG_TEMPLATE)
        return template.render(port=str(self.port), ip=self.ip, mask=self.mask)

    def get_ca_cert(self):
        f = open(self.key_dir + "ca.crt")
        content = f.read()
        f.close()
        return content

    def get_dh(self):
        f = open(self.key_dir + "dh2048.pem")
        content = f.read()
        f.close()
        return content


VPN_SERVER_CONFIG_TEMPLATE = """
local 0.0.0.0
port {{ port }}
proto udp
dev tap
ca ca.crt
cert server.crt
key server.key
dh dh2048.pem
server {{ ip }}  {{ mask }}
ifconfig-pool-persist ipp.txt
client-to-client
keepalive 10 120
comp-lzo
persist-key
persist-tun
status openvpn-status.log
verb 3
"""

VPN_CLIENT_CONFIG_TEMPLATE = """
client
dev tun
proto udp
remote {{ server_ip }} {{ port }}
resolv-retry infinite
nobind
persist-key
persist-tun
ca ca.crt
cert client.crt
key client.key
comp-lzo
verb 3
"""

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:s:m:v:o:", ["working-dir="])

    address = "127.0.0.1"
    port = 9093

    for opt, arg in opts:
        print opt
        print opt, arg
        if opt == "-w":
            working_dir = arg
        elif opt == "-a":
            address = arg
        elif opt == "-p":
            port = arg
        elif opt == "-s":
            server_address = arg
        elif opt == "-m":
            vpn_mask = arg
        elif opt == "-v":
            print opt, arg
            vpn_address = arg
        elif opt == "-o":
            vpn_port = arg

    manager = VPNConfigManager(vpn_address, vpn_mask, vpn_port, server_address, working_dir )
    app.config["manager"] = manager

    app.run(host=address, port=int(port), debug=True)




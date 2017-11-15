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


@app.route("/vpn/configs/certs/server/", methods=[POST])
def generate_server_cert():
    manager = app.config["manager"]
    manager.generate_server_certs()
    return "", 204


@app.route("/vpn/configs/certs/client/<client_id>/", methods=[POST])
def generate_client_cert(client_id):
    manager = app.config["manager"]
    manager.generate_client_certs(client_id)
    return "", 204


@app.route("/vpn/configs/certs/ca/", methods=[POST])
def generate_ca_cert():
    print "configurator.py::Generate CA cert..."
    manager = app.config["manager"]
    manager.generate_ca_and_dh()
    print "configurator.py::finished Generating CA cert..."
    return "", 204


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
    response.headers["Content-Disposition"] = "attachment; filename=server.conf"
    return response


@app.route("/vpn/configs/client/<client_id>/", methods=[GET])
def get_client_config(client_id):
    manager = app.config["manager"]
    raw_config = manager.get_client_config()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=client.conf"
    return response


@app.route("/vpn/configs/certs/ca/", methods=[GET])
def get_ca_cert():
    manager = app.config["manager"]
    raw_config = manager.get_ca_cert()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=ca.crt"
    return response


@app.route("/vpn/configs/certs/client/<client_id>/", methods=[GET])
def get_client_cert(client_id):
    manager = app.config["manager"]
    raw_config = manager.get_client_cert(client_id)
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=client.crt"
    return response


@app.route("/vpn/configs/keys/client/<client_id>/", methods=[GET])
def get_client_key(client_id):
    manager = app.config["manager"]
    raw_config = manager.get_client_key(client_id)
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=client.key"
    return response


@app.route("/vpn/configs/certs/server/", methods=[GET])
def get_server_cert():
    manager = app.config["manager"]
    raw_config = manager.get_server_cert()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=server.crt"
    return response


@app.route("/vpn/configs/keys/server/", methods=[GET])
def get_server_key():
    manager = app.config["manager"]
    raw_config = manager.get_server_key()
    response = make_response(raw_config)
    response.headers["Content-Disposition"] = "attachment; filename=server.key"
    return response


@app.route("/vpn/configs/status/", methods=[GET])
def get_status():
    return "Ready", 200


class VPNConfigManager:

    def __init__(self, ip, mask, port, server_ip, key_dir, dns_enabled):
        self.ip = ip
        self.mask = mask
        self.port = port
        self.server_ip = server_ip
        self.key_dir = key_dir
        self.dns_enabled = dns_enabled

    def generate_ca_and_dh(self):
        print "sh %s../gen_ca.sh" % self.key_dir
        command = "sh %s../gen_ca.sh" % self.key_dir
        subprocess.check_call(shlex.split(command), shell=False)

    def generate_client_certs(self, client_id):
        command = "sh %s../gen_client.sh -u %s" % (self.key_dir, client_id)
        subprocess.check_call(shlex.split(command))

    def generate_server_certs(self):
        command = "sh %s../gen_server.sh" % self.key_dir
        subprocess.check_call(shlex.split(command))

    def get_client_cert(self, client_id):
        f = open(self.key_dir + "%s.crt" % client_id)
        content = f.read()
        f.close()
        return content

    def get_client_key(self, client_id):
        f = open(self.key_dir + "%s.key" % client_id)
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
        dns_line
        if self.dns_enabled == "true":
            dns_line = "push dhcp-option DNS 10.10.10.1"
        return template.render(port=str(self.port), ip=self.ip, mask=self.mask, dns_line=dns_line)

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
{{dns_line}}
"""

VPN_CLIENT_CONFIG_TEMPLATE = """
client
dev tap
proto udp
lport {{ port }}
remote {{ server_ip }} {{ port }}
resolv-retry infinite
persist-key
persist-tun
ca ca.crt
cert client.crt
key client.key
comp-lzo
verb 3
"""

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:s:m:v:o:", ["working-dir=","dns-enabled="])

    address = "127.0.0.1"
    port = 9093

    for opt, arg in opts:
        print opt, arg
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            address = arg
        elif opt == "-p":
            port = int(arg)
        elif opt == "-s":
            server_address = arg
        elif opt == "-m":
            vpn_mask = arg
        elif opt == "-v":
            print opt, arg
            vpn_address = arg
        elif opt == "-o":
            vpn_port = arg
        elif opt == "--dns-enabled":
            dns_enabled = arg

    manager = VPNConfigManager(vpn_address, vpn_mask, vpn_port, server_address, working_dir, dns_enabled)
    app.config["manager"] = manager

    app.run(host=address, port=port, debug=True)




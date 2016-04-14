import getopt
import logging
import shlex
import subprocess
import iptools

import sys
from flask import Flask
from flask import json
from flask import request

log = logging.getLogger('cnsmoservices.fw.app.server')


app = Flask(__name__)

GET = "GET"
POST = "POST"
DELETE = "DELETE"

DIRECTION = "direction"
PROTOCOL = "protocol"
DST_PORT = "dst_port"
IP_RANGE = "ip_range"
ACTION = "action"

RULE_FORMAT = '{"direction":"in/out", "protocol":"tcp/udp/...", "dst_port":"[0,65535]", "ip_range":"cidr_notation", "action":"drop/acpt"}'


@app.route("/fw/build/", methods=[POST])
def build_server():
    try:
        if app.config["service_built"]:
            return "Service already built", 409

        log.debug("building docker...")
        subprocess.check_call(shlex.split("docker build -t vpn-server ."))
        log.debug("docker built")
        app.config["service_built"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/fw/", methods=[POST])
def add_rule():
    if not app.config["service_built"]:
        return "Service is not yet built", 409

    rule = json.loads(request.data)
    if not is_valid(rule):
        return "Invalid rule. Expected format is {}".format(RULE_FORMAT), 409

    try:
        log.debug("running docker add...")
        output = subprocess.check_call(shlex.split(
            "docker run -t --rm --net=host --privileged fw-docker add {direction} {protocol} {dst_port} {ip_range} {action}".format(**rule)))
        log.debug("docker run. output: " + output)
        return "", 204
    except Exception as e:
        return str(e), 500


@app.route("/fw/", methods=[DELETE])
def delete_rule():
    if not app.config["service_built"]:
        return "Service is not yet built", 409

    rule = json.loads(request.data)
    if not is_valid(rule):
        return "Invalid rule. Expected format {}".format(RULE_FORMAT), 409

    try:
        log.debug("running docker DEL...")
        output = subprocess.check_call(shlex.split(
            "docker run -t --rm --net=host --privileged fw-docker del {direction} {protocol} {dst_port} {ip_range} {action}".format(
                **rule)))
        log.debug("docker run. output: " + output)
        return "", 204

    except Exception as e:
        return str(e), 500


def is_valid(rule):
    # check rule contains all mandatory fields
    if not {DIRECTION, PROTOCOL, DST_PORT, IP_RANGE, ACTION}.issubset(set(rule.keys())):
        return False

    if rule[DIRECTION] not in ('in', 'out'):
        return False

    if rule[ACTION] not in ('drop', 'acpt'):
        return False

    # port is an int between 0 and 65535
    try:
        dst_port = int(rule[DST_PORT])
        if dst_port < 0 or dst_port > 65535:
            return False
    except ValueError:
        return False

    # ip_range is a valid IP range in CIDR notation (IPv4 or IPv6)
    if not (iptools.ipv4.validate_cidr(rule[IP_RANGE]) or iptools.ipv6.validate_cidr(rule[IP_RANGE])):
        return False

    return True


def prepare_config():
    app.config["service_built"] = False


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:")

    host = "127.0.0.1"
    port = 9095
    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    prepare_config()
    app.run(host=host, port=port, debug=True)

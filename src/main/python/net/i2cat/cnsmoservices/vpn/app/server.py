import getopt
import os
import logging
import shlex
import subprocess

import sys
from flask import Flask, jsonify
from flask import request

log = logging.getLogger('cnsmoservices.vpn.app.server')

call = lambda command: subprocess.check_output(command, shell=True)


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/server/dh/", methods=[POST])
def set_dh():
    try:
        save_file(request.files['file'], "dh2048.pem")
        app.config["config_files"]["dh_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/config/", methods=[POST])
def set_config_file():
    try:
        save_file(request.files['file'], "server.conf")
        app.config["config_files"]["config_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409

# Function to return all the vpn clients with their ID and their @IP
@app.route("/vpn/server/clients/", methods=[GET])
def get_all_vpn_clients():
    all_instances = ss_getinstances()
    # remove slipstream orchestrator instances
    client_instances = [x for x in all_instances if not x.startswith("orchestrator")]
    # remove this instance
    ss_nodename = call('ss-get nodename').rstrip('\n')
    ss_node_instance = call('ss-get id').rstrip('\n')
    instance_id = "%s.%s" % (ss_nodename, ss_node_instance)
    client_instances.remove(instance_id)
    call("echo %s >> /var/tmp/testfile.txt" % client_instances)


# Gets the instances that compose the deployment
# NOTE: Currently there is no way to directly retrieve all nodes intances in a deployment.
#       As of now we have to find them out by parsing the ss:groups, and then the node's
#       <nodename>:<id> runtime parameters.
#       There is an issue to implement this enhancement: https://github.com/slipstream/SlipStreamServer/issues/628
def ss_getinstances():
    # ss:groups  cyclone-fr2:VPN,cyclone-fr1:client2,cyclone-fr2:client1

    groups = call("ss-get ss:groups").rstrip('\n')
    cloud_node_pairs = groups.split(",")

    nodes = list()
    for pair in cloud_node_pairs:
        nodes.append(pair.split(":")[1])

    # nodes = VPN, client2, client1

    indexes = dict()
    # client1:ids     1,2
    for node in nodes:
        indexes[node] = call("ss-get %s:ids" % node).split(",")

    # {"client1":["1","2"]}
    instances = list()
    for node, node_indexes in indexes.iteritems():
        for index in node_indexes:
            instances.append(node + "." + index.rstrip('\n'))

    return instances


@app.route("/vpn/server/cert/ca/", methods=[POST])
def set_ca_cert():
    try:
        save_file(request.files['file'], "ca.crt")
        app.config["config_files"]["ca_cert_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/cert/server/", methods=[POST])
def set_server_cert():
    try:
        save_file(request.files['file'], "server.crt")
        app.config["config_files"]["server_cert_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/key/server/", methods=[POST])
def set_server_key():
    try:
        save_file(request.files['file'], "server.key")
        app.config["config_files"]["server_key_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/build/", methods=[POST])
def build_server():
    try:
        result = reduce(lambda x, y: x and y, app.config["config_files"].values())
        if result:
            log.debug("building docker...")
            subprocess.check_call(shlex.split("docker build -t vpn-server ."))
            log.debug("docker build")
            app.config["service_built"] = True
            return "", 204
        else:
            return "Config is not ready: " + str(app.config["config_files"]), 409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/start/", methods=[POST])
def start_server():
    try:
        if app.config["service_built"]:
            log.debug("running docker...")
            output = subprocess.check_call(shlex.split(
                "docker run --net=host  --privileged -v /dev/net/:/dev/net/ --name server-vpn -d vpn-server"))

            log.debug("docker run. output: " + str(output))
            app.config["service_running"] = True
            return "", 204
        return "Service is not yet built",  409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    try:
        if app.config["service_running"]:
            subprocess.check_call(shlex.split("docker kill server-vpn"))
            subprocess.check_call(shlex.split("docker rm -f server-vpn"))
            app.config["service_running"] = False
            return "", 204
        return "Service is not yet running",  409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/status/", methods=[GET])
def get_status():
    status = dict()
    status["config_files"] = app.config["config_files"]
    status["service_built"] = app.config["service_built"]
    status["service_running"] = app.config["service_running"]
    return jsonify(status), 200


def save_file(file_handler, file_name):
    # filename = secure_filename(file_handler.filename)
    log.debug("saving file to " + app.config['UPLOAD_FOLDER'])
    file_handler.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))


def prepare_config():
    app.config["config_files"] = {"dh_ready": False,
                                  "server_cert_ready": False,
                                  "server_key_ready": False,
                                  "ca_cert_ready": False,
                                  "config_ready": False,
                                  }

    app.config["service_built"] = False
    app.config["service_running"] = False

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:", ["working-dir="])

    host = "127.0.0.1"
    port = 9094
    for opt, arg in opts:
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    app.config["UPLOAD_FOLDER"] = working_dir
    prepare_config()
    app.run(host=host, port=port, debug=True)

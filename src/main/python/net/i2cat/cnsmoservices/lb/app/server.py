import getopt
import os
import logging
import shlex
import subprocess

import sys
from flask import Flask
from flask import json
from flask import request

###
# This script launches an web application running a haproxy inside a docker.
# Use the following command in order to invoke the application:
# python server.py -a 127.0.0.1 -p 9097 -t LB-PORT -w "/tmp/cnsmo/lb/"
###

log = logging.getLogger('cnsmoservices.lb.app.server')

app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/lb/server/docker/", methods=[POST])
def set_docker():
    """
    Puts given Dockerfile in working directory.
    :param request.files: Dockerfile
    :return:
    """
    try:
        save_file(request.files['file'], "Dockerfile")
        app.config["config_files"]["docker_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/lb/server/config/", methods=[POST])
def set_haproxy_config():
    """
    Puts given ha proxy configuration in working directory.
    :param request.files: haproxy.cfg file
    :return:
    """
    try:
        save_file(request.files['file'], "haproxy.cfg")
        app.config["config_files"]["config_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/lb/server/build/", methods=[POST])
def build_lb():
    """
    Builds the docker container from the Dockerfile in working directory.
    Can be executed with the following command:
    curl -X POST http://127.0.0.1:9097/lb/server/build/
    :return:
    """
    try:
        result = reduce(lambda x, y: x and y, app.config["config_files"].values())
        if result:
            log.debug("building docker...")
            subprocess.check_call(shlex.split("docker build -t lb-server ."))
            log.debug("docker build")
            app.config["service_built"] = True
            return "", 204
        else:
            return "Config is not ready: " + str(app.config["config_files"]), 409
    except Exception as e:
        return str(e), 409


@app.route("/lb/server/start/", methods=[POST])
def start_lb():
    """
    Starts the load balancer by running the docker container.
    It specifies the port the container publishes and its mapping to exposed ports,
    and the list of servers to balance between.
    Can be executed with the following command:
    curl -X POST -H "Content-Type: application/json" -d '["123.45.67.89:9999","123.45.67.99:9999"]' http://127.0.0.1:9097/lb/server/start/
    :param request.data: a json with the list of the servers to balance, in the form ["ip:port", "ip:port",...]
    :return:
    """
    try:
        if not app.config["service_built"]:
            return "Service is not yet built", 409

        # retrieving lb_port from config
        if not app.config["lb_port"]:
            return "An LB port needs to be specified", 409
        lb_port = app.config["lb_port"]

        # retrieving backend_servers from request.data
        lb_backend_servers = json.loads(request.data)
        lb_backend_servers_str = ""
        for server in lb_backend_servers:
            lb_backend_servers_str = lb_backend_servers_str + server + ","
        lb_backend_servers_str = lb_backend_servers_str[:-1]    # removing last ','

        log.debug("running docker...")
        command = "docker run -t -d -p {}:{} -e COUCHDB_SERVERS={} --name lb-docker lb-server".format(lb_port, lb_port, lb_backend_servers_str)
        log.debug(command)
        output = subprocess.check_call(shlex.split(command))

        log.debug("docker run. output: " + str(output))
        app.config["service_running"] = True
        return "", 204

    except Exception as e:
        log.error(e)
        return str(e), 409


@app.route("/lb/server/stop/", methods=[POST])
def stop_lb():
    """
    Stops the load balancer by killing and removing the docker container.
    Can be executed with the following command:
    curl -X POST http://127.0.0.1:9097/lb/server/stop/
    :return:
    """
    try:
        if app.config["service_running"]:
            subprocess.check_call(shlex.split("docker kill lb-docker"))
            subprocess.check_call(shlex.split("docker rm -f lb-docker"))
            app.config["service_running"] = False
            return "", 204
        return "Service is not yet running", 409
    except Exception as e:
        return str(e), 409


def save_file(file_handler, file_name):
    # filename = secure_filename(file_handler.filename)
    log.debug("saving file to " + app.config['UPLOAD_FOLDER'])
    file_handler.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))


def prepare_config():
    app.config["config_files"] = {"docker_ready": False,
                                  "config_ready": False,
                                  }
    app.config["service_built"] = False
    app.config["service_running"] = False


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:t:", ["working-dir="])

    host = "127.0.0.1"
    port = 9097
    for opt, arg in opts:
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)
        elif opt == "-t":
            lbport = arg

    app.config["UPLOAD_FOLDER"] = working_dir
    prepare_config()
    app.config["lb_port"] = lbport
    app.run(host=host, port=port, debug=True)

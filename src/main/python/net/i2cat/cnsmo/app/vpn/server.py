import getopt
import os
import logging
import shlex
import subprocess

import sys
from flask import Flask
from flask import request

log = logging.getLogger('cnsmo.vpn.server.app')


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
            subprocess.Popen(shlex.split("docker build -t vpn-server ."))
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
            output = subprocess.check_output(shlex.split(
                "docker run --net=host  --privileged -v /dev/net/:/dev/net/ --name server-vpn -d vpn-server"))

            log.debug("docker run. output: " + output)
            app.config["service_running"] = True
            return "", 204
        return "Service is not yet built",  409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    try:
        if app.config["service_running"]:
            subprocess.Popen(shlex.split("docker kill server-vpn"))
            subprocess.Popen(shlex.split("docker rm -f server-vpn"))
            app.config["service_running"] = False
            return "", 204
        return "Service is not yet running",  409
    except Exception as e:
        return str(e), 409


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
    port = 9092
    for opt, arg in opts:
        if opt == "-w" or "--working-dir":
            working_dir = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = arg

    app.config["UPLOAD_FOLDER"] = working_dir
    prepare_config()
    app.run(host=host, port=port, debug=True)

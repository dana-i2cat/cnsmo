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


@app.route("/vpn/client/config/", methods=[POST])
def set_config_file():
    try:
        save_file(request.files['file'], "client.conf")
        app.config["config_files"]["config_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/cert/ca/", methods=[POST])
def set_ca_cert():
    try:
        save_file(request.files['file'], "ca.crt")
        app.config["config_files"]["ca_cert_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/cert/", methods=[POST])
def set_client_cert():
    try:
        save_file(request.files['file'], "server.crt")
        app.config["config_files"]["server_cert_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/key/", methods=[POST])
def set_client_key():
    try:
        save_file(request.files['file'], "server.key")
        app.config["config_files"]["server_key_ready"] = True
        return "", 204
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/build/", methods=[POST])
def build_client():
    try:
        result = reduce(lambda x, y: x and y, app.config["config_files"].values())
        if result:
            log.debug("building docker...")
            app.config["service_built"] = True
            return "dockerBuilt", 204
        else:
            return "Config is not ready: " + str(app.config["config_files"]), 409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/start/", methods=[POST])
def start_client():
    try:
        if app.config["service_built"]:
            app.config["service_running"] = True
            return "DockerRunning", 204
        return "Service is not yet built",  409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/client/stop/", methods=[POST])
def stop_client():
    try:
        if app.config["service_running"]:
            app.config["service_running"] = False
            return "DockerRunning", 204
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
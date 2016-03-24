import getopt
import os

import subprocess

import sys
from flask import Flask
from flask import request
import shlex


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/client/config/", methods=[POST])
def set_config_file():
    save_file(request.files['file'], "client.conf")
    app.config["config_files"]["config_ready"] = True
    return "", 204


@app.route("/vpn/client/cert/ca/", methods=[POST])
def set_ca_cert():
    save_file(request.files['file'], "ca.crt")
    app.config["config_files"]["ca_cert_ready"] = True
    return "", 204


@app.route("/vpn/client/cert/", methods=[POST])
def set_client_cert():
    save_file(request.files['file'], "client.crt")
    app.config["config_files"]["client_cert_ready"] = True
    return "", 204


@app.route("/vpn/client/key/", methods=[POST])
def set_client_key():
    save_file(request.files['file'], "client.key")
    app.config["config_files"]["client_key_ready"] = True
    return "", 204


@app.route("/vpn/client/build/", methods=[POST])
def build_client():
    result = reduce(lambda x, y: x and y, app.config["config_files"].values())
    if result:
        subprocess.check_call(shlex.split("docker build -t client-vpn ."))
        app.config["service_built"] = True
        return "", 204
    else:
        return "Config is not ready", 409


@app.route("/vpn/client/start/", methods=[POST])
def start_client():
    if app.config["service_built"]:
        subprocess.check_call(
            shlex.split("docker run --net=host  --privileged -v /dev/net/:/dev/net/ --name client-vpn -d client-vpn"))
        app.config["service_running"] = True
        return "", 204
    return "", 409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_client():
    if app.config["service_running"]:
        subprocess.check_call(shlex.split("docker kill client-vpn"))
        subprocess.check_call(shlex.split("docker rm client-vpn"))
        return "",204
    return "",409


def save_file(file, file_name):
    # filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))


def prepare_config():
    app.config["config_files"] = {"client_cert_ready": False,
                                  "client_key_ready": False,
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
        if opt in ("-w", "--working-dir"):
            app.config["UPLOAD_FOLDER"] = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    prepare_config()
    app.run(host=host, port=port, debug=True)

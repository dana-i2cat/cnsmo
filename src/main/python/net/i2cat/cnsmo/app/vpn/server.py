import getopt
import os

import subprocess

import sys
from flask import Flask
from flask import request


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/server/dh/", methods=[POST])
def set_dh():
    save_file(request.files['file'], "dh2048.pem")
    app.config["config_files"]["dh_ready"] = True
    return 204, ""


@app.route("/vpn/server/config/", methods=[POST])
def set_config_file():
    save_file(request.files['file'], "server.conf")
    app.config["config_files"]["config_ready"] = True
    return 204, ""


@app.route("/vpn/server/cert/ca/", methods=[POST])
def set_ca_cert():
    save_file(request.files['file'], "ca.crt")
    app.config["config_files"]["ca_ready"] = True
    return 204, ""


@app.route("/vpn/server/cert/server/", methods=[POST])
def set_server_cert():
    save_file(request.files['file'], "server.crt")
    app.config["config_files"]["server_cert_ready"] = True
    return 204, ""


@app.route("/vpn/server/key/server/", methods=[POST])
def set_server_cert():
    save_file(request.files['file'], "server.key")
    app.config["config_files"]["server_key_ready"] = True
    return 204, ""


@app.route("/vpn/server/build/", methods=[POST])
def build_server(server_name):
    result = reduce(lambda x, y: x and y, app.config["config_files"].values())
    if result:
        subprocess.Popen("docker build -t vpn-server .")
        app.config["service_build"] = True
        return 204, ""
    else:
        return 409, "Config is not ready"


@app.route("/vpn/server/start/", methods=[POST])
def start_server():
    if app.config["service_built"]:
        subprocess.Popen(
            "docker run -t --net=host  --privileged -v /dev/net/:/dev/net/ --name server-vpn -d vpn-server")
        app.config["service_running"] = True
        return 204, ""
    return 409, ""


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    if app.config["service_running"]:
        subprocess.Popen("docker kill server-vpn")
        subprocess.Popen("docker rm server-vpn")
        return 204, ""
    return 409, ""


def save_file(file, file_name):
    # filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))


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
            app.config["UPLOAD_FOLDER"] = arg
        elif opt == "-a":
            host = arg
        elif opt == "p":
            port = arg

    prepare_config()
    app.run(host=host, port=port, debug=False)

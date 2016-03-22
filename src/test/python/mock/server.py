import getopt
import logging

import sys
from flask import Flask

log = logging.getLogger('cnsmo.vpn.server.app')


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/server/dh/", methods=[POST])
def set_dh():
    app.config["config_files"]["dh_ready"] = True
    return "ServerDHSet", 200


@app.route("/vpn/server/config/", methods=[POST])
def set_config_file():
    app.config["config_files"]["config_ready"] = True
    return "ServerConfigSet", 200


@app.route("/vpn/server/cert/ca/", methods=[POST])
def set_ca_cert():
    app.config["config_files"]["ca_cert_ready"] = True
    return "ServerCASet", 200


@app.route("/vpn/server/cert/server/", methods=[POST])
def set_server_cert():
    app.config["config_files"]["server_cert_ready"] = True
    return "ServerCertSet", 200


@app.route("/vpn/server/key/server/", methods=[POST])
def set_server_key():
    app.config["config_files"]["server_key_ready"] = True
    return "ServerKeySet", 200


@app.route("/vpn/server/build/", methods=[POST])
def build_server():
        result = reduce(lambda x, y: x and y, app.config["config_files"].values())
        if result:
            app.config["service_built"] = True
            return "ServerBuilt", 200
        else:
            return "Config is not ready: " + str(app.config["config_files"]), 409


@app.route("/vpn/server/start/", methods=[POST])
def start_server():
    if app.config["service_built"]:
        app.config["service_running"] = True
        return "ServerRunning", 200
    return "Service is not yet built",  409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    if app.config["service_running"]:
        app.config["service_running"] = False
        return "Server Stopped", 200
    return "Service is not yet running",  409


def prepare_config():
    app.config["config_files"] = {"dh_ready": False,
                                  "server_cert_ready": False,
                                  "server_key_ready": False,
                                  "ca_cert_ready": False,
                                  "config_ready": False,
                                  }

    app.config["service_built"] = False
    app.config["service_running"] = False


def main(my_host, my_port):
    prepare_config()
    app.run(host=my_host, port=my_port, debug=True)

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

    main(host, port)

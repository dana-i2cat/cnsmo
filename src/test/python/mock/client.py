import getopt

import sys
from flask import Flask

app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/client/config/", methods=[POST])
def set_config_file():
    app.config["config_files"]["config_ready"] = True
    return "ClientConfigSet", 200


@app.route("/vpn/client/cert/ca/", methods=[POST])
def set_ca_cert():
    app.config["config_files"]["ca_cert_ready"] = True
    return "ClientCASet", 200


@app.route("/vpn/client/cert/", methods=[POST])
def set_server_cert():
    app.config["config_files"]["client_cert_ready"] = True
    return "ClientCertSet", 200


@app.route("/vpn/client/key/", methods=[POST])
def set_server_key():
    app.config["config_files"]["client_key_ready"] = True
    return "ClientKeySet", 200


@app.route("/vpn/client/build/", methods=[POST])
def build_client():
    result = reduce(lambda x, y: x and y, app.config["config_files"].values())
    if result:
        app.config["service_built"] = True
        return "ClientBuilt", 200
    else:
        return "Config is not ready", 409


@app.route("/vpn/client/start/", methods=[POST])
def start_server():
    if app.config["service_built"]:
        app.config["service_running"] = True
        return "ClientStarted", 200
    return "Client is not yet built", 409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    if app.config["service_running"]:
        return "ClientStopped", 200
    return "Client is not yet running", 409


def prepare_config():
    app.config["config_files"] = {"client_cert_ready": False,
                                  "client_key_ready": False,
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
    port = 9092
    for opt, arg in opts:
        if opt in ("-w", "--working-dir"):
            app.config["UPLOAD_FOLDER"] = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    main(host, port)

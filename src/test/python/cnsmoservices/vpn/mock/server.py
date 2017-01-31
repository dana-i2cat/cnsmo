import getopt
import os
import logging
import signal
import time
import sys
from flask import Flask, jsonify
from flask import request
from multiprocessing import Process

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
            app.config["service_built"] = True
            return "dockerBuilt", 204
        else:
            return "Config is not ready: " + str(app.config["config_files"]), 409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/start/", methods=[POST])
def start_server():
    try:
        if app.config["service_built"]:
            app.config["service_running"] = True
            return "DockerRunning", 204
        return "Service is not yet built",  409
    except Exception as e:
        return str(e), 409


@app.route("/vpn/server/stop/", methods=[POST])
def stop_server():
    try:
        if app.config["service_running"]:
            app.config["service_running"] = False
            return "DockerRunning", 204
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


def launch_flask_app(host, port):
    signal_flag = SignalFlag()
    server = Process(target=app.run, args=(host, port, {"debug": True}))
    server.start()
    while not signal_flag.signal_received():
        time.sleep(0.5)
    print("Terminating...")
    server.terminate()
    server.join(2)


class SignalFlag:
    """
    A single-use flag for SIGINT and SIGTERM signals.
    """
    __signal_received = False

    def __init__(self):
        """
        Registers callback for SIGINT and SIGTERM
        """
        signal.signal(signal.SIGINT, self.flag_signal)
        signal.signal(signal.SIGTERM, self.flag_signal)

    def flag_signal(self, signum, frame):
        """
        Flags
        :param signum:
        :param frame:
        :return:
        """
        self.__signal_received = True

    def signal_received(self):
        return self.__signal_received


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
    launch_flask_app(host, port)

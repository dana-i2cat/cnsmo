import getopt
import signal
import time
import sys
import requests
from flask import Flask
from flask import request
from multiprocessing import Process


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/configs/certs/server/", methods=[POST])
def generate_server_cert():
    return "ServerCert", 200


@app.route("/vpn/configs/certs/client/<client_id>/", methods=[POST])
def generate_client_cert(client_id):
    return "ClientCert " + client_id, 200


@app.route("/vpn/configs/certs/ca/", methods=[POST])
def generate_ca_cert():
    return "CaCert", 200


@app.route("/vpn/configs/dh/", methods=[GET])
def get_dh():
    return "GotDH", 200


@app.route("/vpn/configs/server/", methods=[GET])
def get_server_config():
    return "GotServerConfig", 200


@app.route("/vpn/configs/client/<client_id>/", methods=[GET])
def get_client_config(client_id):
    return "GotClientConfig " + client_id, 200


@app.route("/vpn/configs/certs/ca/", methods=[GET])
def get_ca_cert():
    return "GotCACert", 200


@app.route("/vpn/configs/certs/client/<client_id>/", methods=[GET])
def get_client_cert(client_id):
    return "GotClientCert " + client_id, 200


@app.route("/vpn/configs/keys/client/<client_id>/", methods=[GET])
def get_client_key(client_id):
    return "GotClientKey " + client_id, 200


@app.route("/vpn/configs/certs/server/", methods=[GET])
def get_server_cert():
    return "GotServerCert", 200


@app.route("/vpn/configs/keys/server/", methods=[GET])
def get_server_key():
    return "GotServerKey", 200


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

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:s:m:v:o:", ["working-dir="])

    address = "127.0.0.1"
    port = 9093

    for opt, arg in opts:
        print opt, arg
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            address = arg
        elif opt == "-p":
            port = int(arg)
        elif opt == "-s":
            server_address = arg
        elif opt == "-m":
            vpn_mask = arg
        elif opt == "-v":
            vpn_address = arg
        elif opt == "-o":
            vpn_port = arg

    launch_flask_app(address, port)

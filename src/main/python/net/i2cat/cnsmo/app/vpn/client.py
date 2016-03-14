from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
import json

app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/server/<client_name>/dh/", methods=[POST])
def set_dh(client_name):
    pass


@app.route("/vpn/server/<client_name>/config/", methods=[POST])
def set_config_file(client_name):
    pass


@app.route("/vpn/server/<client_name>/cert/ca/", methods=[POST])
def set_ca_cert(client_name):
    pass


@app.route("/vpn/server/<client_name>/cert/server/", methods=[POST])
def set_server_cert(client_name):
    pass


@app.route("/vpn/server/<client_name>/build/", methods=[POST])
def build_server(client_name):
    pass


@app.route("/vpn/server/<client_name>/start/", methods=[POST])
def start_server(client_name):
    pass


@app.route("/vpn/server/<client_name>/stop/", methods=[POST])
def stop_server(client_name):
    pass


if __name__ == "__main__":

    app.run(host="127.0.0.1", port=9092, debug=True)
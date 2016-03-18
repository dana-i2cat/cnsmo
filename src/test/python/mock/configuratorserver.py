from flask import Flask


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/vpn/configs/certs/server/", methods=[POST])
def generate_server_cert():

    return "CaCert", 200


@app.route("/vpn/configs/certs/client/", methods=[POST])
def generate_client_cert():
    return "ClientCert", 200


@app.route("/vpn/configs/certs/ca/", methods=[POST])
def generate_ca_cert():
    return "CaCert", 200


@app.route("/vpn/configs/dh/", methods=[GET])
def get_dh():
    return "GotDH", 200


@app.route("/vpn/configs/server/", methods=[GET])
def get_server_config():
    return "GotServerConfig", 200


@app.route("/vpn/configs/client/", methods=[GET])
def get_client_config():
    return "GotClientConfig", 200


@app.route("/vpn/configs/certs/ca/", methods=[GET])
def get_ca_cert():
    return "GotCACert", 200


@app.route("/vpn/configs/certs/client/", methods=[GET])
def get_client_cert():
    return "GotClientCert", 200


@app.route("/vpn/configs/keys/client/", methods=[GET])
def get_client_key():
    return "GotClientKey", 200


@app.route("/vpn/configs/certs/server/", methods=[GET])
def get_server_cert():
    return "GotServerCert", 200


@app.route("/vpn/configs/keys/server/", methods=[GET])
def get_server_key():
    return "GotServerKey", 200


def main(host, port):
    app.run(host, port, debug=False)

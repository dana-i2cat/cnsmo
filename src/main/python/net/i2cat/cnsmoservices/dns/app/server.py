import getopt
import os
import logging
import shlex
import subprocess
import requests

import sys
from flask import Flask, jsonify
from flask import request
from requests.auth import HTTPBasicAuth

log = logging.getLogger('cnsmoservices.dns.app.server')

call = lambda command: subprocess.check_output(command, shell=True)

app = Flask(__name__)

GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"

# Returns a list of strings with the id of the nodes
@app.route("/sdn/server/status/", methods=[GET])
def get_status():
    return jsonify({}),200


if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:", ["working-dir="])

    host = "127.0.0.1"
    port = 9099
    for opt, arg in opts:
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    app.config["UPLOAD_FOLDER"] = working_dir
    app.config["host"] = host
    app.config["port"] = port
    app.run(host=host, port=port, debug=True)

    


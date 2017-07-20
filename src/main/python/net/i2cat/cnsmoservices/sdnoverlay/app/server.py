import getopt
import os
import logging
import shlex
import subprocess

import sys
from flask import Flask, jsonify
from flask import request

log = logging.getLogger('cnsmoservices.sdn.app.server')


app = Flask(__name__)

GET = "GET"
POST = "POST"


@app.route("/sdn/server/flows", methods=[GET])
def get_flows():
    status = dict()
    status["Content"] = json.loads(request.data)
    return jsonify(status), 200

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:w:", ["working-dir="])

    host = "127.0.0.1"
    port = 9098
    for opt, arg in opts:
        if opt in ("-w", "--working-dir"):
            working_dir = arg
        elif opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    app.config["UPLOAD_FOLDER"] = working_dir
    app.config["host"] = host
    app.run(host=host, port=port, debug=True)

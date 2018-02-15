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

logging.basicConfig(filename='cnsmo-api-service-calls.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG,
                    disable_existing_loggers=False)
                    
log = logging.getLogger('cnsmoservices.dns.app.server')

call = lambda command: subprocess.check_output(command, shell=True)

app = Flask(__name__)

GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"


# Returns a list of strings with the id of the nodes
@app.route("/dns/server/record/", methods=[GET])
def get_dns_records():
    logger = logging.getLogger(__name__)
    logger.debug("get_dns_records GET invocation")
    content = read_lines("/etc/hosts")
    return jsonify({"dns_records":content}),200

@app.route("/dns/server/record/", methods=[POST])
def add_dns_record():
    data = request.json
    dnsrecords = [str(data["dnsrecords"])]
    update_records(dnsrecords)
    response = ""
    response = call("service dnsmasq restart")
    return str(response),200

def update_records(records):
    for record in records:
        l = str(record+"\n")
        add_line("/etc/hosts", l)

def add_line(file_name,line):
    with open(file_name, 'a') as file:
        file.writelines(line) 

def read_lines(file_name): 
    with open(file_name, 'r') as file:
        return file.readlines()


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

    


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

log = logging.getLogger('cnsmoservices.sdn.app.server')


app = Flask(__name__)

GET = "GET"
POST = "POST"

# Practice call, does nothing
@app.route("/sdn/server/flows/", methods=[GET])
def get_flows():
    status = dict()
    status["host"] = app.config["host"]
    status["port"] = app.config["port"]
    return jsonify(status), 200

# Returns a list of strings with the id of the nodes
@app.route("/sdn/server/nodes/", methods=[GET])
def get_nodes():
    r = requests.get('http://134.158.74.110:8080/restconf/operational/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    nodes = {}
    for key in j['nodes']['node']:
        nodes[str(key['id'])] = str(key['flow-node-inventory:ip-address'])

    return str(nodes),200

#la crida sera del format: /blockbyport/SlipstreamInstanceId:port
#@app.route("/sdn/server/filter/blockbyport/", methods=[PUT])
#def add_filter_by_port():


# Returns the last flowId manually added to the filter
# to access flowID use: print j['nodes']['node'][0]['flow-node-inventory:table'][0]['flow'][0]['id'] 
@app.route("/sdn/server/filter/flowcount/", methods=[GET])
def get_flowcount():
    r = requests.get('http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    max = 0
    for key in j['nodes']['node']:
        for idKey in key['flow-node-inventory:table']:
            for flowId in idKey['flow']:
                aux = flowId['id']
                if aux>max:
                    max = aux
                    
            
    return max
   
    

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
    app.config["port"] = port
    call("echo %s >> /var/tmp/SDNservice.txt" % port)
    app.run(host=host, port=port, debug=True)

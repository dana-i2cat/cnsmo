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

call = lambda command: subprocess.check_output(command, shell=True)

app = Flask(__name__)

GET = "GET"
POST = "POST"
PUT = "PUT"

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

    return jsonify(nodes),200

#la crida sera del format: /blockbyport/SlipstreamInstanceId:port
@app.route("/sdn/server/filter/blockbyport/<ssinstanceid>", methods=[PUT])
def add_filter_by_port(ssinstanceid):
    #problema del ssinstanceid???
    newflowCount = get_flowcount()
    call("echo 1: %s>> /var/tmp/SDNservice.txt" % (newflowCount))
    vpnAddr = get_corresp_vpn(ssinstanceid)
    call("echo 2: %s>> /var/tmp/SDNservice.txt" % (vpnAddr))
    flowID = get_flowID(vpnAddr)
    call("echo 4: %s>> /var/tmp/SDNservice.txt" % (flowID))
    # URL has to follow this format: http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:274973442922995/table/0/flow/12
    url = str("http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/node/"+flowID+"/table/0/flow/"+str(newflowCount))
    xml = """
    <flow xmlns="urn:opendaylight:flow:inventory">
        <strict>false</strict>
        <instructions>
            <instruction>
                <order>0</order>
                <apply-actions>
                    <action>
                        <order>0</order>
                        <drop-action/>
                    </action>
                </apply-actions>
            </instruction>
        </instructions>
        <table_id>0</table_id>
        <id>"""+str(newflowCount)+"""</id>
        <cookie_mask>255</cookie_mask>
        <installHw>false</installHw>
        <match>
            <ethernet-match>
                <ethernet-type>
                    <type>2048</type>
                </ethernet-type>
            </ethernet-match>
            <ip-match>
                <ip-protocol>6</ip-protocol>
            </ip-match>
            <ipv4-destination>134.158.0.0/16</ipv4-destination>
            <tcp-destination-port>8080</tcp-destination-port>
        </match>
        <cookie>8</cookie>
        <idle-timeout>3400</idle-timeout>
        <flow-name>portweb-drop</flow-name>
        <priority>650</priority>
        <barrier>false</barrier>
    </flow>"""
    header = {'Content-Type': 'application/xml'}
    r = requests.put(url, data = xml, auth=HTTPBasicAuth('admin', 'admin'), headers=header)
    return str(r.headers),r.status_code

def get_corresp_vpn(ssinstanceid):
    vpnClients = requests.get('http://127.0.0.1:20092/vpn/server/clients/')
    vpnClients = vpnClients.json()
    return str(vpnClients[str(ssinstanceid)]["VPN address:"])

def get_flowID(vpnaddress):
    nodes = get_nodes()
    nodes = nodes.json()
    call("echo 3.1: %s >> /var/tmp/SDNservice.txt" % (nodes))
    auxi = ""
    for key,value in nodes.iteritems():
        if str(value)==str(vpnaddress):
            auxi=str(key)
    call("echo 3.2: %s >> /var/tmp/SDNservice.txt" % (auxi))
    return auxi

# Returns the last flowId manually added to the filter
# to access flowID use: print j['nodes']['node'][0]['flow-node-inventory:table'][0]['flow'][0]['id'] 
def get_flowcount():
    r = requests.get('http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    max = 0
    flows = {}
    for key in j['nodes']['node']:
        for idKey in key['flow-node-inventory:table']:
            for flowId in idKey['flow']:
                aux = flowId['id']
                if int(aux)>int(max):
                    max = aux
                    
            
    return int(max)+1

    

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
    app.run(host=host, port=port, debug=True)

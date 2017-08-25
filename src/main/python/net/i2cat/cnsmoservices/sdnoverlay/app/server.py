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

# Returns a list of strings with the id of the nodes
@app.route("/sdn/server/nodes/", methods=[GET])
def get_nodes():
    r = requests.get('http://127.0.0.1:8080/restconf/operational/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    nodes = {}
    for key in j['nodes']['node']:
        nodes[str(key['id'])] = str(key['flow-node-inventory:ip-address'])

    return jsonify(nodes),200

@app.route("/sdn/server/flows/", methods=[GET])
def get_flows():
    data = request.json
    if data:
        instanceID = str(data["ssinstanceid"])
        call("echo %s >> /var/tmp/sdntest.txt" % instanceID)
        vpnAddr = get_corresp_vpn(instanceID)
        if vpnAddr!="":
            flowID = get_flowID(vpnAddr)
            if flowID!="":
                url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/"+str(flowID))
                r = requests.get(url , auth=HTTPBasicAuth('admin', 'admin'))
                j = r.json()
                nodes = {}
                nodes[str(flowID)] = {}
                nodes[str(flowID)]['vpnIP']=str(vpnAddr)
                if "node" in j:
                    for key in j['node'][0]["flow-node-inventory:table"]:
                        nodes[str(flowID)]['flows'] = key['flow']
                return jsonify(nodes),200
        else:
            return "Node doesn't exist",404
    else:
        # Get all sdn clients
        r = requests.get('http://127.0.0.1:8080/restconf/operational/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
        j = r.json()
        clients = {}
        for key in j['nodes']['node']:
            clients[str(key['id'])] = str(key['flow-node-inventory:ip-address'])

        # get all flows from every sdn client
        url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/")
        r = requests.get(url , auth=HTTPBasicAuth('admin', 'admin'))
        j = r.json()
        nodes = {}
        for key in j['nodes']['node']:
            if key['id']!='':
                nodes[str(key['id'])] = {}
                nodes[str(key['id'])]['vpnID']=str(clients[str(key['id'])])
                if key["flow-node-inventory:table"]:
                    for tables in key["flow-node-inventory:table"]:
                        nodes[str(key['id'])]['flows'] = tables['flow']
        if not nodes:
            return "List is empty",404
        return jsonify(nodes),200


#la crida sera del format: /blockbyport/SlipstreamInstanceId:port
@app.route("/sdn/server/filter/blockbyport/", methods=[PUT])
def add_filter_by_port():
    #problema del ssinstanceid???
    newflowCount = get_flowcount()
    data = request.json
    ssinstanceid = str(data["ssinstanceid"])
    vpnAddr = get_corresp_vpn(ssinstanceid)
    if vpnAddr!="":
        flowID = get_flowID(vpnAddr)
        if flowID!="":
            # URL has to follow this format: http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:274973442922995/table/0/flow/12
            url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/"+flowID+"/table/0/flow/"+str(newflowCount))
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
                    <ipv4-destination>"""+str(data["ip4-destination"])+"""</ipv4-destination>
                    <tcp-destination-port>"""+str(data["tcp-destination-port"])+"""</tcp-destination-port>
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
        else:
            return "Node doesn't exist", 404
    else:
        return "Node doesn't exist", 404

def get_corresp_vpn(ssinstanceid):
    vpnClients = requests.get('http://127.0.0.1:20092/vpn/server/clients/')
    vpnClients = vpnClients.json()
    if vpnClients.get(str(ssinstanceid)):
        return str(vpnClients[str(ssinstanceid)]["VPN address:"])
    return ""

def get_flowID(vpnaddress):
    r = requests.get('http://127.0.0.1:8080/restconf/operational/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    nodes = {}
    for key in j['nodes']['node']:
        nodes[str(key['id'])] = str(key['flow-node-inventory:ip-address'])
    auxi = ""
    for key,value in nodes.iteritems():
        if str(value)==str(vpnaddress):
            auxi=str(key)
    return auxi

# Returns the last flowId manually added to the filter
# to access flowID use: print j['nodes']['node'][0]['flow-node-inventory:table'][0]['flow'][0]['id'] 
def get_flowcount():
    r = requests.get('http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    max = 0
    if "errors" not in j:
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

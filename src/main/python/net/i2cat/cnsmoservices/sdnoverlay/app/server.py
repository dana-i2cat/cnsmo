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
    return jsonify(get_nodeDict()),200

@app.route("/sdn/server/flows/", methods=[GET])
def get_flows():
    data = request.json
    if data:
        instanceID = str(data["ssinstanceid"])
        vpnAddr = get_corresp_vpn(instanceID)
        if vpnAddr!="":
            openflowID = get_nodeOpenflowID(vpnAddr)
            if openflowID!="":
                url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/"+str(openflowID))
                r = requests.get(url , auth=HTTPBasicAuth('admin', 'admin'))
                j = r.json()
                nodeList = {}
                nodeList[str(openflowID)] = {}
                nodeList[str(openflowID)]['vpnIP']=str(vpnAddr)
                if 'node' in j:
                    for node in j['node']:
                        if 'flow-node-inventory:table' in node:
                            for table in node['flow-node-inventory:table']:
                                if 'id' in table and table['id'] == 0 :
                                    nodeList[str(openflowID)]['flows'] = []
                                    if 'flow' in table:
                                        nodeList[str(openflowID)]['flows'] = table['flow']
                return jsonify(nodeList),200
        else:
            return "Node doesn't exist\n",404
    else:
        # Get all sdn clients  
        clients = get_nodeDict()

        # get all flows from every sdn client
        url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/")
        r = requests.get(url , auth=HTTPBasicAuth('admin', 'admin'))
        j = r.json()
        
        if "errors" in j:
            return jsonify({}),200

        nodeList = {}
        for node in j['nodes']['node']:
            if 'id' in node:
                nodeList[str(node['id'])] = {}
                nodeList[str(node['id'])]['vpnID']=str(clients[str(node['id'])])
                if 'flow-node-inventory:table' in node:
                    for table in node['flow-node-inventory:table']:
                        if 'id' in table and table['id'] == 0 : 
                            nodeList[str(node['id'])]['flows'] = []
                            if 'flow' in table:
                                nodeList[str(node['id'])]['flows'] = table['flow']
        return jsonify(nodeList),200

@app.route("/sdn/server/filter/blockbyport/", methods=[PUT])
def add_filter_by_port():
    newflowCount = get_flowcount()
    data = request.json
    ssinstanceid = str(data["ssinstanceid"])
    vpnAddr = get_corresp_vpn(ssinstanceid)
    if vpnAddr!="":
        openflowID = get_nodeOpenflowID(vpnAddr)
        if openflowID!="":
            # URL has to follow this format: http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:274973442922995/table/0/flow/12
            url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/"+openflowID+"/table/0/flow/"+str(newflowCount))
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
            return "Node doesn't exist\n", 404
    else:
        return "Node doesn't exist\n", 404

@app.route("/sdn/server/filter/blockbyport/instance/<str:ssinstanceid>/flow/<int:flowID>", methods=[DELETE])
def delete_filter_by_port():
    vpnAddr = get_corresp_vpn(ssinstanceid)
    if vpnAddr!="":
        openflowID = get_nodeOpenflowID(vpnAddr)
        if openflowID!="":
            # URL has to follow this format: http://134.158.74.110:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:274973442922995/table/0/flow/12
            url = str("http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/"+openflowID+"/table/0/flow/"+str(flowID))
            header = {'Content-Type': 'application/xml'}
            r = requests.delete(url, data=json.dumps({}), auth=HTTPBasicAuth('admin', 'admin'), headers=header)
            return str(r.headers),r.status_code
        else:
            return "Node doesn't exist\n", 404
    else:
        return "Node doesn't exist\n", 404

def get_nodeDict():
    r = requests.get('http://127.0.0.1:8080/restconf/operational/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    nodes = {}
    for key in j['nodes']['node']:
        nodes[str(key['id'])] = str(key['flow-node-inventory:ip-address'])

    return nodes

def get_corresp_vpn(ssinstanceid):
    vpnClients = requests.get('http://127.0.0.1:20092/vpn/server/clients/')
    vpnClients = vpnClients.json()
    if vpnClients.get(str(ssinstanceid)):
        return str(vpnClients[str(ssinstanceid)]["vpnAddress"])
    return ""

def get_nodeOpenflowID(vpnaddress):
    # call to obtain all the sdn clients
    nodes = get_nodeDict()
    auxi = ""
    for key,value in nodes.iteritems():
        if str(value)==str(vpnaddress):
            auxi=str(key)
    return auxi

# Returns the last flowId manually added to the filter
def get_flowcount():
    r = requests.get('http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/' , auth=HTTPBasicAuth('admin', 'admin'))
    j = r.json()
    max = 10
    if "errors" not in j:
        flows = {}
        for node in j['nodes']['node']:
            if 'flow-node-inventory:table' in node:
                for table in node['flow-node-inventory:table']:
                    if 'id' in table and table['id'] == 0 : 
                        if 'flow' in table:
                            for flow in table['flow']:
                                aux = flow['id']
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

    


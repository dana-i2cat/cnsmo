# SDN app: How to use

## Server

SDN server runs on port 20199. This port has to be specified in the URL.

Methods:

+ http://127.0.0.1:20199/sdn/server/flows/ , methods=[GET] : Get all the SDN configured flows. If no paramater is passed, it will return all configured flows for each one of the nodes subscribed in the SDN controller. If we want the flows from a concrete client, the user should specify the client ID using the parameter "ssinstanceid" from the body.


+ http://127.0.0.1:20199/sdn/server/nodes/ , methods=[GET] : Returns a list of pairs with the nodeid and his corresponding vpn address. No parameters need to be configured (GET -d '{}')

+ http://127.0.0.1:20199/sdn/server/filter/blockbyport/ , methods=[PUT] : Adds a new rule to filter flows by port. We need to specify the destination port, the address and the node name following the format: 
{"tcp-destination-port":1919,"ip4-destination":"134.157.24.35/16","ssinstanceid":"Agent.1"}
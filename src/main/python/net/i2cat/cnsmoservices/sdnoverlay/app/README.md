# SDN app: How to use?

## Server

SDN server runs on port 20199. This port has to be specified in the URL.

Methods:

+ http://127.0.0.1:20199/sdn/server/flows/ , methods=[GET] : Get all the SDN configured flows. If no paramater is passed in the call, then it will return all configured flows for each one of the nodes subscribed in the SDN controller. If we want the flows from a concrete client, the user should specify the client ID using the parameter "ssinstanceid" from the body.


+ http://127.0.0.1:20199/sdn/server/nodes/ , methods=[GET] :

+ http://127.0.0.1:20199/sdn/server/filter/blockbyport/ , methods=[PUT] :
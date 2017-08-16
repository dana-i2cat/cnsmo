# SDN app: How to use?

## Server

SDN server runs on port 20199. This port has to be specified in the URL.

Methods:

+ http://127.0.0.1:20199/sdn/server/flows/ , methods=[GET] : Get all the VPN clients with their ClientID and their VPN address.


+ http://127.0.0.1:20199/sdn/server/nodes/ , methods=[GET])

+ http://127.0.0.1:20199/sdn/server/filter/blockbyport/ , methods=[PUT])
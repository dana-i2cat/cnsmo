# VPN app: How to use?

## Server

VPN server runs on port 20092. This port has to be specified in the URL.

Methods:

+ http://127.0.0.1:20092/vpn/server/clients/ , methods=[GET] : Get all the VPN clients with their ClientID and their VPN address. No extra parameters are needed in the body message.

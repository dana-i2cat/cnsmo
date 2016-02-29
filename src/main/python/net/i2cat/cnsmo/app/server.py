from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
import json

app = Flask(__name__)

GET = "GET"

@app.route("/server/<server_name>/", methods=[GET])
def start(server_name):
    return "I'm a server %s" % server_name

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9092, debug=True)
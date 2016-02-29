from flask import Flask
from flask import request
from flask import make_response
from flask import jsonify
import json

app = Flask(__name__)

GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"


@app.route("/dh/", methods=[GET])
def get_dh():
    return "I'm a DH"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9091, debug=True)
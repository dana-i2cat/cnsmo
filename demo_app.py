from flask import Flask
import sys

app = Flask(__name__)


@app.route('/')
def hello_world():
    return app.config.get("data")

if __name__ == '__main__':
    host = str(sys.argv[1])
    port = int(sys.argv[2])
    data = str(sys.argv[3:])
    app.config["data"] = data
    app.run(host=host, port=port)

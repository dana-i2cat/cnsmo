import getopt
import sys

from flask import Flask
from flask import make_response
from flask import jsonify
from flask import request

app = Flask(__name__)

GET = "GET"
POST = "POST"
DELETE = "DELETE"


@app.route("/sample/basic/", methods=[GET])
def get_basic():
    return "", 204


@app.route("/sample/params/<param1>/<param2>/", methods=[GET])
def get_with_url_params(param1, param2):
    params_dict = {'param1': param1, 'param2': param2}
    return jsonify(params_dict)


@app.route("/sample/json/", methods=[GET])
def get_with_json():
    rcv_json_dict = request.get_json()
    rcv_json_str = request.data
    return jsonify(rcv_json_dict)


@app.route("/sample/params/json/<param1>/<param2>/", methods=[GET])
def get_with_url_params_and_json(param1, param2):
    rcv_json_dict = request.get_json()
    params_dict = {'param1': param1, 'param2': param2}
    complete_dict = {'parameters': params_dict, 'input_json': rcv_json_dict}
    return jsonify(complete_dict)


@app.route("/sample/basic/", methods=[POST])
def post_basic():
    return "", 204


@app.route("/sample/params/<param1>/<param2>/", methods=[POST])
def post_with_url_params(param1, param2):
    params_dict = {'param1': param1, 'param2': param2}
    return jsonify(params_dict)


@app.route("/sample/json/", methods=[POST])
def post_with_json():
    rcv_json_dict = request.get_json()
    rcv_json_str = request.data
    return jsonify(rcv_json_dict)


@app.route("/sample/params/json/<param1>/<param2>/", methods=[POST])
def post_with_url_params_and_json(param1, param2):
    rcv_json_dict = request.get_json()
    params_dict = {'param1': param1, 'param2': param2}
    complete_dict = {'parameters': params_dict, 'input_json': rcv_json_dict}
    print(complete_dict)
    return jsonify(complete_dict)


@app.route("/sample/file/", methods=[POST])
def post_with_files():
    rcv_file = request.files['file']
    response = make_response(rcv_file.read())
    response.headers["Content-Disposition"] = "attachment; filename=file.txt"
    return response


class TestApp(object):

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_app_request(self, service_id):
        """
        The app request is an important part of CNSMO, that serves as a description for the application.
        CNSMOManager delegates to the deployment driver the parsing of it, followed by the creation of the environment,
        downloading of 'resources', installation of 'dependencies', and executing the 'trigger'.
        The app request is also advertised via the CNSMO system state. It is retrieved by registered listeners
        and parsed by the service maker in order to build a class that is a representation of the remote service.
        'Endpoints' are used for such purpose.
        :param service_id: 
        :return:
        """
        host = self.host
        port = self.port
        d = dict(service_id=service_id,
                 trigger='python testapp.py -a %s -p %s' % (host, port),
                 resources=[],
                 dependencies=[],
                 endpoints=[{"uri": "http://%s:%s/sample/basic/" % (host, port), "driver": "REST", "logic": "get",
                             "name": "get_basic"},
                            {"uri": "http://%s:%s/sample/params/{param}/{param}/" % (host, port), "driver": "REST",
                             "logic": "get", "name": "get_with_url_params"},
                            {"uri": "http://%s:%s/sample/json/" % (host, port), "driver": "REST", "logic": "get",
                             "name": "get_with_json"},
                            {"uri": "http://%s:%s/sample/params/json/{param}/{param}/" % (host, port), "driver": "REST",
                             "logic": "get", "name": "get_with_url_params_and_json"},

                            {"uri": "http://%s:%s/sample/basic/" % (host, port), "driver": "REST", "logic": "post",
                             "name": "post_basic"},
                            {"uri": "http://%s:%s/sample/params/{param}/{param}/" % (host, port), "driver": "REST",
                             "logic": "post", "name": "post_with_url_params"},
                            {"uri": "http://%s:%s/sample/json/" % (host, port), "driver": "REST", "logic": "post",
                             "name": "post_with_json"},
                            {"uri": "http://%s:%s/sample/params/json/{param}/{param}/" % (host, port), "driver": "REST",
                             "logic": "post", "name": "post_with_url_params_and_json"},
                            {"uri": "http://%s:%s/sample/params/json/{param}/{param}/" % (host, port), "driver": "REST",
                             "logic": "upload", "name": "post_with_files"}, ])
        return d

    def launch_app(self):
        app.run(host=self.host, port=self.port, debug=True)


def main(host, port):
    test_app = TestApp(host, port)
    test_app.launch_app()

if __name__ == "__main__":

    opts, _ = getopt.getopt(sys.argv[1:], "a:p:", [])

    host = "127.0.0.1"
    port = 9090
    for opt, arg in opts:
        if opt == "-a":
            host = arg
        elif opt == "-p":
            port = int(arg)

    main(host, port)

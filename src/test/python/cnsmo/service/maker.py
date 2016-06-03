import json

import sys

import time

import os
import requests
import unittest

from multiprocessing import Process

path = os.path.dirname(os.path.abspath(__file__))
src_dir = path + "/../../../../../"
if src_dir not in sys.path:
    sys.path.append(src_dir)

from src.main.python.net.i2cat.cnsmo.service.maker import ServiceMaker
from src.test.python.cnsmo.service.testapp import TestApp


class ServiceMakerTest(unittest.TestCase):

    def setUp(self):

        # given this app
        test_app = TestApp('127.0.0.1', 9090)
        self.server = Process(target=test_app.launch_app)
        self.server.start()

        # with these uris
        self.url_basic = "http://127.0.0.1:9090/sample/basic/"
        self.url_params = "http://127.0.0.1:9090/sample/params/{}/{}/"
        self.url_json = "http://127.0.0.1:9090/sample/json/"
        self.url_params_json = "http://127.0.0.1:9090/sample/params/json/{}/{}/"
        self.url_file = "http://127.0.0.1:9090/sample/file/"

        # and generated service client for that app
        self.service = ServiceMaker().make_service("Sample", test_app.get_app_request("Sample").get('endpoints'))

        # and these sample values
        self.sample_params = {'param1': 'abc', 'param2': 'def'}
        self.sample_json = {'a': 'abc', 'b': 'def', 'c': ['ccc', 'ddd']}
        self.sample_file = "THIS IS A SAMPLE FILE \n"

        time.sleep(1)

    def tearDown(self):
        self.server.terminate()
        self.server.join()

    def test_expected_behaviour_with_requests(self):

        sample_params = self.sample_params
        sample_json = self.sample_json
        sample_file = self.sample_file

        print("SAMPLES:")
        print(sample_params)
        print(sample_json)
        print(sample_file)

        print("OUTPUTS:")
        r = requests.get(self.url_basic)
        r.raise_for_status()

        r = requests.get(self.url_params.format(sample_params.get('param1'), sample_params.get('param2')))
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_params, sort_keys=True), json.dumps(json.loads(r.content), sort_keys=True))

        r = requests.get(self.url_json, json=sample_json)
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_json, sort_keys=True), json.dumps(json.loads(r.content), sort_keys=True))

        r = requests.get(self.url_params_json.format(sample_params.get('param1'), sample_params.get('param2')),
                         json=sample_json)
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_json, sort_keys=True),
                         json.dumps(json.loads(r.content).get('input_json'), sort_keys=True))
        self.assertEqual(json.dumps(sample_params, sort_keys=True),
                         json.dumps(json.loads(r.content).get('parameters'), sort_keys=True))

        r = requests.post(self.url_basic)
        r.raise_for_status()

        r = requests.post(self.url_params.format(sample_params.get('param1'), sample_params.get('param2')))
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_params, sort_keys=True), json.dumps(json.loads(r.content), sort_keys=True))

        r = requests.post(self.url_json, json=sample_json)
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_json, sort_keys=True), json.dumps(json.loads(r.content), sort_keys=True))

        r = requests.post(self.url_params_json.format(sample_params.get('param1'), sample_params.get('param2')),
                          json=sample_json)
        r.raise_for_status()
        print(r.content)
        self.assertEqual(json.dumps(sample_json, sort_keys=True),
                         json.dumps(json.loads(r.content).get('input_json'), sort_keys=True))
        self.assertEqual(json.dumps(sample_params, sort_keys=True),
                         json.dumps(json.loads(r.content).get('parameters'), sort_keys=True))

        r = requests.post(self.url_file, data={}, files={'file': ('sample.txt', sample_file)})
        r.raise_for_status()
        print(r.content)
        self.assertEqual(sample_file, r.content)

    def test_expected_json_arrives_correctly_in_post_with_json(self):

        r = self.service.post_with_json(self.sample_json)
        print(r.content)
        self.assertEqual(json.dumps(self.sample_json, sort_keys=True), json.dumps(json.loads(r.content), sort_keys=True))


if __name__ == "__main__":
    unittest.main()

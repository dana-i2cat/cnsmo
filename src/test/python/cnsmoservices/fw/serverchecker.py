import os
import requests
import sys
import unittest


class FirewallServerAppTest(unittest.TestCase):

    rule1 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"src","ip_range":"127.0.0.1/32", "action":"drop"}'
    rule2 = '{"direction":"out", "protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"drop"}'
    rule3 = '{"direction":"in", "protocol":"udp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"acpt"}'

    bad_rule1 = '{"protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"drop"}'
    bad_rule2 = '{"direction":"in", "protocol":"tcp", "dst_port":"9999999", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"drop"}'
    bad_rule3 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1/33", "action":"drop"}'
    bad_rule4 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1.1/32", "action":"drop"}'
    bad_rule5 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.0", "action":"drop"}'
    bad_rule6 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"bad_action"}'
    bad_rule7 = '{"direction":"in", "protocol":"tcp", "dst_port":"bad_port", "dst_src":"dst", "ip_range":"127.0.0.1/32", "action":"drop"}'
    bad_rule8 = '{"direction":"in", "protocol":"tcp", "dst_port":"8080", "dst_src":"BAD", "ip_range":"127.0.0.1/32", "action":"drop"}'

    good_rules = {rule1, rule2, rule3}
    bad_rules = {bad_rule1, bad_rule2, bad_rule3, bad_rule4, bad_rule5, bad_rule6, bad_rule7, bad_rule8}

    def test_unbuilt_server_does_not_allow_rules_but_build_does(self):

        # Simulate the server is not yet build
        requests.delete("http://127.0.0.1:9095/fw/build/")

        for rule in self.good_rules:
            r = requests.post("http://127.0.0.1:9095/fw/", data=rule)
            self.assertEquals(409, r.status_code)

        r = requests.post("http://127.0.0.1:9095/fw/build/")
        self.assertEquals(204, r.status_code)

        for rule in self.good_rules:
            r = requests.post("http://127.0.0.1:9095/fw/", data=rule)
            self.assertEquals(204, r.status_code)

    def test_rules_validation(self):

        requests.post("http://127.0.0.1:9095/fw/build/")

        for rule in self.good_rules:
            print rule
            r = requests.post("http://127.0.0.1:9095/fw/", data=rule)
            print r
            self.assertEquals(204, r.status_code)

        for rule in self.good_rules:
            print rule
            r = requests.delete("http://127.0.0.1:9095/fw/", data=rule)
            print r
            self.assertEquals(204, r.status_code)

        for bad_rule in self.bad_rules:
            print bad_rule
            r = requests.post("http://127.0.0.1:9095/fw/", data=bad_rule)
            print r
            print r.content
            self.assertEquals(409, r.status_code)

        for bad_rule in self.bad_rules:
            print bad_rule
            r = requests.delete("http://127.0.0.1:9095/fw/", data=bad_rule)
            print r
            print r.content
            self.assertEquals(409, r.status_code)

    def test_removing_existing_rules(self):

        requests.post("http://127.0.0.1:9095/fw/build/")

        for rule in self.good_rules:
            r = requests.post("http://127.0.0.1:9095/fw/", data=rule)
            self.assertEquals(204, r.status_code)

        for existing_rule in self.good_rules:
            r = requests.delete("http://127.0.0.1:9095/fw/", data=existing_rule)
            self.assertEquals(204, r.status_code)
        

if __name__ == "__main__":

    configurator_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = configurator_path + "/../../../../../"
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    unittest.main()

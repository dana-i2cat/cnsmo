import requests
import time

url_dh = "http://127.0.0.1:9092/vpn/server/dh/"
url_server_conf = "http://127.0.0.1:9092/vpn/server/config/"
url_ca_cert = "http://127.0.0.1:9092/vpn/server/cert/ca/"
url_server_cert = "http://127.0.0.1:9092/vpn/server/cert/server/"
url_server_key = "http://127.0.0.1:9092/vpn/server/key/server/"
url_build = "http://127.0.0.1:9092/vpn/server/build/"
url_start = "http://127.0.0.1:9092/vpn/server/start/"
url_stop = "http://127.0.0.1:9092/vpn/server/stop/"


def main():

    # cheat configuration
    print "Configuring server..."
    r = requests.post(url_dh, data={}, files={'file': ('dh2048.pem', 'SAMPLE_DH\n')})
    print "Response" + r
    r.raise_for_status()
    r = requests.post(url_server_conf, data={}, files={'file': ('server.conf', 'SAMPLE_CONF\n')})
    print "Response" + r
    r.raise_for_status()
    r = requests.post(url_ca_cert, data={}, files={'file': ('ca.crt', 'SAMPLE_CA_CRT\n')})
    print "Response" + r
    r.raise_for_status()
    r = requests.post(url_server_cert, data={}, files={'file': ('server.crt', 'SAMPLE_CRT\n')})
    print "Response" + r
    r.raise_for_status()
    r = requests.post(url_server_key, data={}, files={'file': ('server.key', 'SAMPLE_KEY\n')})
    print "Response" + r
    r.raise_for_status()
    print "Configuration done"

    # build the vpn server
    print "Sending build request..."
    r = requests.post(url_build)
    print "Build response: " + r.text
    r.raise_for_status()
    time.sleep(1)
    print "Sending start request..."
    r = requests.post(url_start)
    print "Start response: " + r.text
    r.raise_for_status()

    # time.sleep(60)
    # r = requests.post(url_stop)


if __name__== "__main__":
    main()

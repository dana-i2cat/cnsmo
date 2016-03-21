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
    print r
    r.raise_for_status()
    r = requests.post(url_server_conf, data={}, files={'file': ('server.conf', 'SAMPLE_CONF\n')})
    print r
    r.raise_for_status()
    r = requests.post(url_ca_cert, data={}, files={'file': ('ca.crt', 'SAMPLE_CA_CRT\n')})
    print r
    r.raise_for_status()
    r = requests.post(url_server_cert, data={}, files={'file': ('server.crt', 'SAMPLE_CRT\n')})
    print r
    r.raise_for_status()
    r = requests.post(url_server_key, data={}, files={'file': ('server.key', 'SAMPLE_KEY\n')})
    print r
    r.raise_for_status()
    print "Configuration done"

    # build the vpn server
    print "Sending build request..."
    r = requests.post(url_build)
    print r
    print r.content
    r.raise_for_status()
    time.sleep(3)

    print "Sending start request..."
    r = requests.post(url_start)
    print r
    print r.content
    r.raise_for_status()
    time.sleep(3)

    print "Sending stop request..."
    r = requests.post(url_stop)
    print r
    print r.content
    r.raise_for_status()


if __name__ == "__main__":
    main()

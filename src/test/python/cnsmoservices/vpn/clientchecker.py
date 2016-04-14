import requests
import time

f = "This is the content of a file\n with multiple lines in it"
r1 = requests.post("http://127.0.0.1:9092/vpn/client/config/", files={"file":("f.conf", f)})
time.sleep(0.3)
print r1
r2 = requests.post("http://127.0.0.1:9092/vpn/client/cert/ca/", files={"file":("f", f)})
time.sleep(0.3)
print r2
r3 = requests.post("http://127.0.0.1:9092/vpn/client/cert/", files={"file":("f", f)})
time.sleep(0.3)
print r3
r4 = requests.post("http://127.0.0.1:9092/vpn/client/key/", files={"file":("f", f)})
time.sleep(0.3)
print r4
r5 = requests.post("http://127.0.0.1:9092/vpn/client/build/", json={})
print r5
r6 = requests.post("http://127.0.0.1:9092/vpn/client/start/", json={})
print r6
print r6.content

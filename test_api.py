import urllib.request
import json

url = "http://127.0.0.1:5000/api/login"
payload = {"username": "Justina", "password": "justy1996."}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as f:
        print(f"Status Code: {f.getcode()}")
        print(f"Response: {f.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"Status Code: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")

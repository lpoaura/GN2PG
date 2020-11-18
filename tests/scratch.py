import requests
import json
from pprint import pprint

root_url = "https://demo.geonature.fr/geonature"
login_url = "/api/auth/login"

payload = {"login": "admin", "password": "admin", "id_application": 3}
json_payload = json.dumps(payload)
headers = {"Content-Type": "application/json"}

with requests.Session() as s:
    r = s.post(
        "https://demo.geonature.fr/geonature/api/auth/login",
        data=json_payload,
        headers=headers,
    )
    print(r.url, r.status_code, r.reason)
    pprint(json.loads(r.content))
    print("headers", r.headers)
    print("cookies", requests.utils.dict_from_cookiejar(s.cookies))
    print("html", r.text)

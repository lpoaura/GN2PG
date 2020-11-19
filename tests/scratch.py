import json
from pprint import pprint

import requests

root_url = "https://demo.geonature.fr/geonature"
login_url = "/api/auth/login"

payload = json.dumps({"login": "admin", "password": "admin", "id_application": 3})
headers = {"Content-Type": "application/json"}

s = requests.Session()
s.headers = headers


r = s.post(root_url + login_url, data=payload)
print(r.url, r.status_code, r.reason)
print(f"User is {json.loads(r.content)}")


m = s.get(root_url + "/api/gn_commons/modules")
modules = json.loads(m.content)


for item in modules:
    if item["module_code"] == "EXPORTS":
        pprint(f">> Export Module Path is {item['module_path']}")
        export_path = item["module_path"]
        break
id_export = 2

try:
    source = s.get(root_url + f"/api/{export_path}/api/{id_export}")
    print(source.url, source.status_code, source.reason)
    source_dict = json.loads(source.content)
    # pprint(source_dict)
except Exception as e:
    raise

for i in source_dict.keys():
    print(f"{i}")


def qs_params(dico: dict = {}):
    return dico


from urllib import parse

qs_params
payload = parse.urlencode(params)
"""Authentication test crashpad"""

# pylint: skip-file
import json
import logging

import requests

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)


class GnSession:
    """Requests session class"""

    def __init__(self, config):
        self._user = config["login"]
        self._pwd = config["password"]
        self._id_application = config["id_application"]
        self._auth_payload = {
            "login": config["login"],
            "password": config["password"],
            # "id_application": config["id_application"],
        }
        self._header = {"Content-Type": "application/json"}
        self._root_url = config["url"]
        self._session = requests.Session()
        self._session.headers = self._header
        # try:
        #     self._session.post(login_url, data=self._auth_payload)
        # except Exception as e:
        #     print(str(e))

    def login(self) -> None:
        """init login function"""
        login_url = self._root_url + "/api/auth/login"
        try:
            r = self._session.post(login_url, json=self._auth_payload)
            logging.info(f"login {r.url} {r.status_code} {r.content} {r.cookies.get_dict()}")
        except Exception as e:
            logging.error(f"<login error> {str(e)}")
        return None

    def get_query(self, path):
        url = self._root_url + path
        try:
            r = self._session.get(url)
            logging.info(f"get_query {r.url} {r.status_code}")
            return json.loads(r.content)
        except Exception as e:
            logging.error(str(e))
            raise e


modules_path = "/api/gn_commons/modules"

test_config = {
    "login": "admin",
    "password": "admin",
    "id_application": 3,
    "url": "https://demo.geonature.fr/geonature",
}

sc = GnSession(config=test_config)
sc.login()
# print("before", sc.cookies.get_dict())
modules = sc.get_query(modules_path)
logging.info("modules %s", modules)

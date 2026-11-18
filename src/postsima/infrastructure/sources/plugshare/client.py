from typing import Any

from curl_cffi import requests


class PlugShareClient:
    BASE_URL = "https://api.plugshare.com/v3/locations/"

    def __init__(self, token: str, auth: str) -> None:
        self._session = requests.Session(impersonate="chrome120")
        self._headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "es",
            "authorization": auth,
            "cognito-authorization": token,
            "referer": "https://www.plugshare.com/",
            "origin": "https://www.plugshare.com",
        }

    def get_location(self, external_id: str) -> dict[str, Any] | None:
        try:
            response = self._session.get(self.BASE_URL + external_id,
                                         headers=self._headers, timeout=30)
        except requests.RequestsError:
            return None

        if response.status_code != 200:
            return None

        return response.json()


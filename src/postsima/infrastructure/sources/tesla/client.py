from typing import Any

from curl_cffi import requests


class TeslaClient:
    BASE_API_URL = "https://www.tesla.com/api/findus/get-location-details"

    def __init__(self, cookie: str) -> None:
        self._session = requests.Session(impersonate="chrome120")
        self._headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-419,es;q=0.6",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Brave";v="152"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "cookie": cookie
        }

    def get_destination(self, external_id: str) -> dict[str, Any] | None:
        type_slug: str = "destination_charger"
        self._headers["referer"] = \
            (f"https://www.tesla.com/es_mx/findus?location={external_id}"
             f"&functionType={type_slug}")
        params = {
            "locationSlug": external_id,
            "functionTypes": type_slug,
            "locale": "es_MX",
            "isInHkMoTw": "false"
        }
        return self._get(self.BASE_API_URL, params)

    def get_supercharger(self, external_id: str) -> dict[str, Any] | None:
        type_slug: str = "supercharger"
        self._headers["referer"] = \
            (f"https://www.tesla.com/es_mx/findus?location={external_id}"
             f"&functionType={type_slug}")
        params = {
            "locationSlug": external_id,
            "functionTypes": type_slug,
            "locale": "es_MX",
            "isInHkMoTw": "false"
        }
        return self._get(self.BASE_API_URL, params)

    def _get(self, url: str, params: dict[str, Any]) -> dict[str, Any] | None:
        try:
            response = self._session.get(
                url,
                params=params,
                headers=self._headers,
                timeout=20
            )
        except requests.RequestsError:
            return None

        if response.status_code != 200:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        if not isinstance(data, dict):
            return None

        return data

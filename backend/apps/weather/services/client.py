from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class WeatherProviderClient:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def get(self, url: str, *, params: dict | None = None, api_key: str | None = None):
        query = urlencode({k: v for k, v in (params or {}).items() if v is not None})
        target = f"{url}{'&' if '?' in url else '?'}{query}" if query else url
        headers = {"Accept": "application/json", "User-Agent": "SIH-Floods/1.0"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = Request(target, headers=headers, method="GET")
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))

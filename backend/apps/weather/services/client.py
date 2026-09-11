from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class WeatherProviderClient:
    def __init__(self, timeout: int = 30):
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")
        self.timeout = timeout

    def get(
        self,
        url: str,
        *,
        params: dict | None = None,
        api_key: str | None = None,
        api_key_param: str | None = None,
    ):
        request_params = dict(params or {})
        headers = {"Accept": "application/json", "User-Agent": "SIH-Floods/1.0"}
        if api_key:
            api_key = api_key.strip()
            if api_key_param:
                request_params[api_key_param] = api_key
            else:
                headers["Authorization"] = f"Bearer {api_key}"

        query = urlencode({k: v for k, v in request_params.items() if v is not None})
        target = f"{url}{'&' if '?' in url else '?'}{query}" if query else url
        request = Request(target, headers=headers, method="GET")
        with urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("Weather provider returned invalid JSON") from exc

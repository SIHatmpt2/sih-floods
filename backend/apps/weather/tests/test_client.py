from unittest.mock import patch
from urllib.error import HTTPError

from django.test import SimpleTestCase

from apps.weather.services.client import WeatherProviderClient


class WeatherProviderClientTests(SimpleTestCase):
    @patch("apps.weather.services.client.urlopen")
    def test_get_returns_json(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b'{"data": []}'
        self.assertEqual(WeatherProviderClient().get("https://example.com"), {"data": []})

    @patch("apps.weather.services.client.urlopen", side_effect=HTTPError("https://example.com", 500, "error", {}, None))
    def test_get_propagates_http_errors(self, urlopen):
        with self.assertRaises(HTTPError):
            WeatherProviderClient().get("https://example.com")

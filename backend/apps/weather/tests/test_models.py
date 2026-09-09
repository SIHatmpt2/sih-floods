from django.test import SimpleTestCase

from apps.weather.models import WeatherStation


class WeatherStationModelTests(SimpleTestCase):
    def test_index_names_are_valid_for_django(self):
        indexes = WeatherStation._meta.indexes
        for index in indexes:
            self.assertLessEqual(len(index.name), 30, index.name)

from django.test import SimpleTestCase

from apps.core.views import EVENT_ID_BY_LOCATION, LOCATIONS, get_event_tile_data


class EventTileMappingTests(SimpleTestCase):
    def test_all_locations_map_to_distinct_dataset_events(self):
        self.assertEqual(set(EVENT_ID_BY_LOCATION), set(LOCATIONS))
        self.assertEqual(len(set(EVENT_ID_BY_LOCATION.values())), len(LOCATIONS))

    def test_known_locations_use_the_correct_event_ids(self):
        self.assertEqual(EVENT_ID_BY_LOCATION["location1"], "AR24-016")
        self.assertEqual(EVENT_ID_BY_LOCATION["location5"], "AR26-001")
        self.assertEqual(EVENT_ID_BY_LOCATION["location30"], "SK22-033")
        self.assertEqual(EVENT_ID_BY_LOCATION["location39"], "UK26-007")

    def test_tile_data_comes_from_the_mapped_event(self):
        data = get_event_tile_data("location1")
        self.assertEqual(data["event_id"], "AR24-016")
        self.assertEqual(data["river_distance"], "0m")

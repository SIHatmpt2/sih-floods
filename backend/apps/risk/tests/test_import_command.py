from io import StringIO
from tempfile import NamedTemporaryFile
from django.core.management import call_command
from django.test import TestCase
from backend.apps.risk.models import FloodEvent


class ImportFloodsCommandTests(TestCase):
    def test_imports_valid_csv(self):
        data = (
            "name,event_date,latitude,longitude,severity,source,district\n"
            "Test Flood,2026-01-02,20.1,78.2,60,gov,Demo\n"
        )
        with NamedTemporaryFile("w+", suffix=".csv", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            call_command("import_floods", f.name)
        self.assertEqual(FloodEvent.objects.count(), 1)

    def test_malformed_rows_are_skipped(self):
        data = (
            "name,event_date,latitude,longitude,severity,source,district\n"
            "Bad,not-a-date,20.1,78.2,60,gov,Demo\n"
        )
        with NamedTemporaryFile("w+", suffix=".csv", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            output = StringIO()
            call_command("import_floods", f.name, stdout=output)
        self.assertEqual(FloodEvent.objects.count(), 0)

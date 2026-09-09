from django.test import SimpleTestCase


class RiskMigrationSyncV4Tests(SimpleTestCase):
    def test_migration_module_imports(self):
        import importlib
        importlib.import_module("apps.risk.migrations.0002_sync_riskzone_and_indexes")

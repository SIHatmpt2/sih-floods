from django.test import SimpleTestCase


class RiskMigrationSyncV3Tests(SimpleTestCase):
    def test_migration_has_expected_operations(self):
        import importlib
        migration = importlib.import_module("apps.risk.migrations.0002_sync_riskzone_and_indexes")
        self.assertEqual(len(migration.Migration.operations), 13)

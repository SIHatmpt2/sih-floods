from django.test import SimpleTestCase


class RiskMigrationSyncTests(SimpleTestCase):
    def test_risk_migration_file_exists(self):
        import importlib

        migration = importlib.import_module("apps.risk.migrations.0002_sync_riskzone_and_indexes")
        self.assertEqual(migration.Migration.dependencies, [("risk", "0001_initial")])
        self.assertEqual(len(migration.Migration.operations), 13)

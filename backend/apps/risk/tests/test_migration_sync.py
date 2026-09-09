from django.test import SimpleTestCase


class RiskMigrationSyncTests(SimpleTestCase):
    def test_expected_migration_operations_are_documented(self):
        from apps.risk.migrations import _0002_sync_riskzone_and_indexes

        operations = _0002_sync_riskzone_and_indexes.Migration.operations
        self.assertEqual(len(operations), 13)

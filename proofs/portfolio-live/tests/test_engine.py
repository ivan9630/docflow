import unittest

from engine.capacity import project_months
from engine.document_migration import audit_records
from engine.olympics_pipeline import run_pipeline
from engine.workflow import transition


class PortfolioEngineTests(unittest.TestCase):
    def test_document_migration_accepts_clean_and_rejects_duplicate(self):
        rows = [
            {"document_id": "D-1", "owner": "Team A", "document_type": "CONTRAT", "updated_at": "2026-01-02"},
            {"document_id": "D-1", "owner": "Team B", "document_type": "FACTURE", "updated_at": "2026-01-02"},
            {"document_id": "D-2", "owner": "", "document_type": "NOTE", "updated_at": "bad"},
        ]
        result = audit_records(rows)
        self.assertEqual(len(result["accepted"]), 0)
        self.assertIn("duplicate_document_id", result["rejected"][0]["issues"])
        self.assertEqual(len(result["rejected"][2]["issues"]), 3)

    def test_workflow_rejects_invalid_transition(self):
        self.assertEqual(transition("submitted", "approve"), "approved")
        with self.assertRaises(ValueError):
            transition("draft", "approve")

    def test_capacity_zero_and_overload(self):
        result = project_months([{"month": "Jan", "demand_days": 5, "capacity_days": 0}])
        self.assertIsNone(result[0]["utilization_pct"])
        self.assertEqual(result[0]["gap_days"], 5)

    def test_sql_pipeline_quarantines_duplicate_and_bad_medal(self):
        rows = [
            {"athlete_id": "A1", "country": "Synthetic", "event": "Relay", "year": 2024, "medal": "Gold"},
            {"athlete_id": "A1", "country": "Synthetic", "event": "Relay", "year": 2024, "medal": "Gold"},
            {"athlete_id": "A2", "country": "Imaginary", "event": "Sprint", "year": 2024, "medal": "Wood"},
        ]
        result = run_pipeline(rows)
        self.assertEqual(result["accepted_count"], 1)
        self.assertEqual(len(result["rejected"]), 2)
        self.assertEqual(result["by_country"][0]["gold_medals"], 1)


if __name__ == "__main__":
    unittest.main()

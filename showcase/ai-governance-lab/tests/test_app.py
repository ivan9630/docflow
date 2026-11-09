import json
import tempfile
import unittest
from pathlib import Path
from sys import path
path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import analyze_case, detect_pii, export_reports


class GovernanceTests(unittest.TestCase):
    def test_safe_use_case(self):
        case = analyze_case({"name": "Analyse interne", "human_oversight": True})
        self.assertEqual(case["score"], 0)
        self.assertEqual(case["priority"], "FAIBLE")

    def test_high_priority(self):
        case = analyze_case({"name": "Décision automatisée", "personal_data": True,
                             "sensitive_data": True, "impactful_decision": True,
                             "third_party_llm": True, "human_oversight": False})
        self.assertEqual(case["priority"], "ÉLEVÉE")
        self.assertTrue(case["recommended_actions"])

    def test_pii_detection(self):
        self.assertEqual(detect_pii("Écrire à alice@example.com ou au 06 12 34 56 78."),
                         {"emails": 1, "phones": 1})

    def test_invalid_name(self):
        with self.assertRaises(ValueError):
            analyze_case({"name": ""})

    def test_files_are_created(self):
        with tempfile.TemporaryDirectory() as temp:
            result = export_reports([{"name": "Test", "human_oversight": True}], Path(temp))
            self.assertEqual(len(result), 1)
            self.assertTrue((Path(temp) / "report.md").exists())
            self.assertEqual(len(json.loads((Path(temp) / "results.json").read_text())), 1)


if __name__ == "__main__":
    unittest.main()

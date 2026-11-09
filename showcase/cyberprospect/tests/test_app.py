import csv
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import score_contact, deduplicate, draft_message, run

class ProspectTests(unittest.TestCase):
    def test_priority(self):
        c = score_contact({"company":"X","role":"RSSI","sector":"finance","employees":"300","signal":"nouveau_rssi","email":"x@example.invalid"})
        self.assertEqual(c["priority"], "A")

    def test_deduplication(self):
        items = [{"company":"X","email":"a@x.fr"},{"company":"x","email":"A@X.FR"}]
        self.assertEqual(len(deduplicate(items)), 1)

    def test_invalid_company(self):
        with self.assertRaises(ValueError):
            score_contact({"company":""})

    def test_no_real_outreach(self):
        self.assertIn("Seriez-vous disponible", draft_message({"company":"X","signal":"projet_cloud"}))

    def test_exports(self):
        with tempfile.TemporaryDirectory() as temp:
            rows = run([{"company":"X","role":"RSSI","employees":"150"}], Path(temp))
            self.assertEqual(len(rows), 1)
            with (Path(temp)/"qualified.csv").open(encoding="utf-8") as f:
                self.assertEqual(len(list(csv.DictReader(f))), 1)
            self.assertTrue((Path(temp)/"report.md").exists())

if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
import sqlite3
from pathlib import Path
from pipeline import clean_campaigns, build_star_schema, metrics

class MarketingPipelineTest(unittest.TestCase):
    def test_quality_schema_and_metrics(self):
        clean, anomalies = clean_campaigns()
        self.assertEqual((len(clean), len(anomalies)), (600, 5))
        self.assertTrue((clean["clics"] <= clean["impressions"]).all())
        self.assertTrue((clean["conversions"] <= clean["clics"]).all())
        self.assertGreater(metrics(clean)["impressions"], metrics(clean)["clics"])
        with tempfile.TemporaryDirectory() as temp:
            facts = build_star_schema(clean, Path(temp))
            self.assertEqual(len(facts), 600)
            with sqlite3.connect(Path(temp) / "marketing_demo.sqlite") as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM fact_performance").fetchone()[0], 600)

if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"python"))
import pipeline_marketing as p

class TestsPilotage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=pd.read_csv(p.RAW)
        cls.good,cls.bad=p.validate(cls.raw)

    def test_quality_counts(self):
        self.assertEqual((len(self.raw),len(self.good),len(self.bad)),(605,600,5))
        self.assertSetEqual(set(self.bad.motif_rejet),{
            "DOUBLON_ID","REGION_INCONNUE","DATE_INVALIDE",
            "CLICS_IMPRESSIONS_INCOHERENTS","COUT_NEGATIF"})

    def test_integrity(self):
        self.assertTrue((self.good.clics<=self.good.impressions).all())
        self.assertTrue((self.good.rdv<=self.good.contacts).all())
        self.assertEqual(self.good.record_id.nunique(),600)
    
    def test_metrics(self):
        m=p.metrics(self.good)
        self.assertGreater(m["impressions"],m["clics"])
        self.assertGreater(m["clics"],m["contacts"])
        self.assertGreater(m["contacts"],m["rdv"])
        self.assertGreaterEqual(m["ctr_pct"],0)
        self.assertIsNotNone(p.impact_did(self.good)["difference_de_differences"])
    
    def test_schema(self):
        with tempfile.TemporaryDirectory() as d:
            fact=p.create_star_schema(self.good,Path(d))
            self.assertEqual(len(fact),600)
            self.assertTrue((Path(d)/"pilotage_campagnes.sqlite").exists())

if __name__=="__main__":
    unittest.main()

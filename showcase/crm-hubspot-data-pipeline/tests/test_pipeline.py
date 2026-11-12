import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from crm_pipeline.generate_demo import build
from crm_pipeline.pipeline import load_clean, enrich, write_sqlite, run
from crm_pipeline.hubspot_adapter import read_fixture, get_contacts

class PipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=Path(__file__).resolve().parents[1]/'data/leads_demo.csv'
        cls.clean,cls.errors,cls.raw=load_clean(cls.data)
    def test_quality(self):
        self.assertEqual((self.raw,len(self.clean),len(self.errors)),(260,240,20))
        self.assertEqual((self.errors.motif_rejet=='DOUBLON_EMAIL').sum(),12)
    def test_dedup(self):
        self.assertEqual(self.clean.email.nunique(),240)
        self.assertTrue((self.clean.contacts_convertis<=self.clean.contacts_livres).all())
    def test_ml_and_segments(self):
        enriched,metrics=enrich(self.clean)
        self.assertEqual(len(enriched),240)
        self.assertGreaterEqual(enriched.score_qualite.mean(),0)
        self.assertEqual(len(set(enriched.segment)),3)
        self.assertIn('roc_auc_synthetique',metrics)
    def test_sqlite_idempotence(self):
        enriched,_=enrich(self.clean)
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'db.sqlite'
            write_sqlite(enriched,db)
            write_sqlite(enriched,db)
            import sqlite3
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute('SELECT count(*) FROM fact_leads').fetchone()[0],240)
    def test_hubspot_fixture(self):
        fixture=Path(__file__).resolve().parents[1]/'data/hubspot_fixture.json'
        self.assertEqual(len(read_fixture(fixture)),2)
        with self.assertRaises(RuntimeError):get_contacts(limit=2,token='')
    def test_main_outputs(self):
        with tempfile.TemporaryDirectory() as folder:
            res=run(self.data,Path(folder))
            self.assertEqual(res['contacts_uniques'],240)
            self.assertEqual(res['segments'],3)
            self.assertTrue((Path(folder)/'hubspot_demo.sqlite').exists())
if __name__=='__main__':unittest.main()

class DeliveryTest(unittest.TestCase):
    def test_export_filters(self):
        from crm_pipeline.delivery import prepare_delivery
        clean,_,_=load_clean()
        scored,_=enrich(clean)
        delivery=prepare_delivery(scored)
        self.assertLessEqual(len(delivery),25)
        self.assertTrue(delivery['secteur'].isin(['BTP','Services','Logiciels']).all())
        self.assertTrue((delivery['score_qualite']>=70).all())

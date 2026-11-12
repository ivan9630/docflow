import unittest,tempfile,sqlite3
from pathlib import Path
from code.llm_enrichment import enrich
from code.scraper import scrape_local
from code.bot_handler import Support
from code.storage import store
from code.pipeline import run
class Tests(unittest.TestCase):
    def test_scraping(self):
        x=scrape_local(Path("examples/exemple_fiche.html"))
        self.assertIn("Bosch",x["nom"])
    def test_enrich(self):
        x=enrich({"produit_id":"A","nom":"Four Brandt","prix_reference_eur":200,"etat":"bon"})
        self.assertEqual(x["valeur_estimee_eur"],150)
    def test_bot(self):
        self.assertTrue(Support().respond("Il y a une surchauffe")["escalade"])
        self.assertTrue(Support().respond("question sur une fusée spatiale")["escalade"])
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"db.sqlite"
            x=enrich({"produit_id":"A","nom":"Four Brandt","prix_reference_eur":200})
            store(x,p);store(x,p)
            with sqlite3.connect(p) as conn:self.assertEqual(conn.execute("SELECT COUNT(*) FROM fiches").fetchone()[0],1)
    def test_50(self):
        self.assertEqual(len(run()[1]),50)
if __name__=="__main__":unittest.main()

import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import tokens,search,recall_at_k
D=[{"id":"a","text":"documentation GitLab CI et tests"},{"id":"b","text":"analyse des données Python"}]
class Tests(unittest.TestCase):
 def test_tokens(self):self.assertIn("données",tokens("Données"))
 def test_rank(self):self.assertEqual(search("GitLab tests",D)[0]["id"],"a")
 def test_empty(self):self.assertEqual(search("inconnu",D),[])
 def test_recall(self):self.assertEqual(recall_at_k([{"question":"analyse Python","relevant_id":"b"}],D,k=1),1.0)
 def test_invalid(self):
  with self.assertRaises(ValueError):recall_at_k([],D)

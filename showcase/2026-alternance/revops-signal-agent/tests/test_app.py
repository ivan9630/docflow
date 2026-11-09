import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import Account,score,pipeline
class Tests(unittest.TestCase):
 def test_score(self):self.assertEqual(score(Account("A",800,"education",True,True)),100)
 def test_order(self):self.assertEqual(pipeline([Account("B",2,"other"),Account("A",700,"tech")])[0]["name"],"A")
 def test_dedup(self):self.assertEqual(len(pipeline([Account("A",4,"other"),Account("a",5,"other")])),1)
 def test_invalid(self):
  with self.assertRaises(ValueError):score(Account("",1,"other"))

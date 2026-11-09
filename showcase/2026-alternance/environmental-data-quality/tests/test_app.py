import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import ingest,summary
class Tests(unittest.TestCase):
 def test_valid(self):
  rows,err=ingest("site,month,metric,value\nA,2026-10,electricite_kwh,100\n")
  self.assertEqual((len(rows),len(err)),(1,0))
 def test_duplicate(self):
  rows,err=ingest("site,month,metric,value\nA,X,diesel_l,1\nA,X,diesel_l,2\n")
  self.assertEqual(len(err),1)
 def test_negative(self):
  rows,err=ingest("site,month,metric,value\nA,X,diesel_l,-2\n")
  self.assertEqual(len(rows),0)
 def test_aggregation(self):
  rows,_=ingest("site,month,metric,value\nA,X,diesel_l,1\nA,Y,diesel_l,1\n")
  self.assertAlmostEqual(summary(rows)["A"],5.36)

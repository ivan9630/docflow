import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import metrics,validate
class Tests(unittest.TestCase):
 def test_counts(self):self.assertEqual(metrics([{"station":"A","status":"open"}])["open"],1)
 def test_valid(self):self.assertTrue(validate({"station":"A","severity":"low","description":"test"}))
 def test_missing(self):
  with self.assertRaises(ValueError):validate({"station":"","severity":"low","description":"test"})
 def test_bad_severity(self):
  with self.assertRaises(ValueError):validate({"station":"A","severity":"wrong","description":"test"})

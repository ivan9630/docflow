import sys, unittest, sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import load_events,kpis
class Tests(unittest.TestCase):
 def setUp(self): self.db=sqlite3.connect(":memory:")
 def test_valid(self):
  a,b=load_events(self.db,[{"id":"a","zone":"Z","ts":"2026-11-07T08:00","delay_min":4}])
  self.assertEqual((a,b),(1,[]))
 def test_duplicate(self):
  e={"id":"a","zone":"Z","ts":"2026-11-07T08:00","delay_min":4}
  a,b=load_events(self.db,[e,e]);self.assertEqual((a,len(b)),(1,1))
 def test_invalid(self):
  a,b=load_events(self.db,[{"id":"a","zone":"Z","ts":"wrong","delay_min":-1}]);self.assertEqual(a,0)
 def test_kpi(self):
  load_events(self.db,[{"id":"a","zone":"Z","ts":"2026-11-07T08:00","delay_min":4}])
  self.assertEqual(kpis(self.db)[0]["avg_delay_min"],4)

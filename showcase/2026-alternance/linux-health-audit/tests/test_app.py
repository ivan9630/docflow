import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import audit,summary
class Tests(unittest.TestCase):
 def test_ok(self):self.assertEqual(audit([{"host":"X","disk_pct":40,"backups_enabled":True,"last_patch":"2026-11-01"}]),[])
 def test_disk(self):self.assertEqual(audit([{"host":"X","disk_pct":99,"backups_enabled":True,"last_patch":"2026-11-01"}])[0]["severity"],"high")
 def test_old(self):self.assertGreater(len(audit([{"host":"X","disk_pct":40,"backups_enabled":True,"last_patch":"2026-01-01"}])),0)
 def test_invalid(self):self.assertEqual(audit([{"host":"X","disk_pct":140}])[0]["severity"],"error")

import unittest
import csv
from pathlib import Path
from scripts.generate_demo import ROOT
from scripts.monthly_report import load_sessions,metrics
from scripts.seo_audit import audit,build
from scripts.benchmark import build as benchmark
class TestProject(unittest.TestCase):
 def test_720_sessions_and_3_sources(self):
  rows=load_sessions();self.assertEqual(len(rows),720)
  self.assertEqual(set(r['source'] for r in rows),{'organic','paid_search','direct'})
 def test_131_pages(self):
  with (ROOT/'data/pages_demo.csv').open(encoding='utf-8') as f:self.assertEqual(len(list(csv.DictReader(f))),131)
 def test_analytics_rates(self):
  m=metrics([{'pageviews':'1','bounced':'1','lead_converted':'1','duration_seconds':'0'},{'pageviews':'3','bounced':'0','lead_converted':'0','duration_seconds':'60'}]);self.assertEqual(m['taux_conversion_pct'],50)
  self.assertEqual(m['taux_rebond_pct'],50);self.assertEqual(m['pages_vues'],4)
 def test_site_crawl(self):
  results=audit();self.assertEqual(len(results),131);self.assertTrue(any(r['anomalies'] for r in results))
 def test_html_tracking(self):
  h=(ROOT/'demo/assets/tracking.js').read_text(encoding='utf-8');self.assertIn('trackPageView',h);self.assertIn('trackEvent',h);self.assertIn('trackGoal',h);self.assertIn('setConsentGiven',h)
 def test_benchmark(self):self.assertEqual(benchmark(),4)
 def test_monthly_rows(self):self.assertEqual(metrics([r for r in load_sessions() if r['date'].startswith('2026-10')])['sessions'],400)
if __name__=='__main__':unittest.main()

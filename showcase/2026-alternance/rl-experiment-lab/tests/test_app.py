import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app import simulate,baseline
class Tests(unittest.TestCase):
 def test_reproducible(self):self.assertEqual(simulate([.2,.9],100),simulate([.2,.9],100))
 def test_steps(self):self.assertEqual(sum(simulate([.2,.9],100)["counts"]),100)
 def test_invalid(self):
  with self.assertRaises(ValueError):simulate([-1],10)
 def test_learning(self):self.assertGreater(simulate([.1,.9],4000,seed=10)["mean_reward"],.6)

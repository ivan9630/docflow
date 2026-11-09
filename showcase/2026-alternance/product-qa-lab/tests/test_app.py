import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import priority, test_story, report
class Tests(unittest.TestCase):
    def test_priority(self):
        self.assertGreater(priority({"severity":"bloquant","affected_users":300}), priority({"severity":"mineur","affected_users":800}))
    def test_release_blocker(self):
        t={"severity":"majeur","affected_users":100}
        self.assertLess(priority(t), priority({**t,"release_blocker":True}))
    def test_acceptance(self):
        self.assertFalse(test_story({"name":"A","criteria":[{"passed":False}]})["ready"])
    def test_empty(self):
        with self.assertRaises(ValueError): test_story({"name":"A","criteria":[]})
    def test_report(self):
        self.assertEqual(report([{"name":"A","criteria":[{"passed":True}]}],[])["status"]["OK"],1)

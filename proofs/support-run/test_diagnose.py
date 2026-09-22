import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from diagnose import SERVICES, diagnose


class TriageTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = dict.fromkeys(SERVICES, True)

    def test_healthy_is_not_end_to_end_proof(self):
        result = diagnose(self.snapshot)
        self.assertEqual(result["severity"], "OK")
        self.assertIn("does not prove", result["next_steps"][0])

    def test_api_outage(self):
        self.snapshot["api"] = False
        self.assertEqual(diagnose(self.snapshot)["severity"], "P1")

    def test_worker_outage(self):
        self.snapshot["worker"] = False
        self.assertEqual(diagnose(self.snapshot)["severity"], "P2")

    def test_dependencies_before_worker(self):
        self.snapshot.update(database=False, worker=False)
        result = diagnose(self.snapshot)
        self.assertIn("database", result["next_steps"][0])
        self.assertEqual(result["failed"], ["database", "worker"])

    def test_missing_key(self):
        del self.snapshot["queue"]
        with self.assertRaises(ValueError):
            diagnose(self.snapshot)

    def test_wrong_types(self):
        for invalid in ("false", None, 0, [], {}):
            with self.subTest(invalid=invalid):
                self.snapshot["queue"] = invalid
                with self.assertRaises(ValueError):
                    diagnose(self.snapshot)

    def test_no_mutation(self):
        before = self.snapshot.copy()
        diagnose(self.snapshot)
        self.assertEqual(self.snapshot, before)

    def test_cli_valid_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            sample = Path(temp) / "sample.json"
            for content, exit_code in ((json.dumps(self.snapshot), 0), ("{", 2)):
                sample.write_text(content, encoding="utf-8")
                run = subprocess.run([sys.executable, str(Path(__file__).with_name("diagnose.py")),
                                      str(sample)], capture_output=True, text=True, timeout=5)
                self.assertEqual(run.returncode, exit_code)
                if exit_code == 0:
                    self.assertEqual(json.loads(run.stdout)["severity"], "OK")


if __name__ == "__main__":
    unittest.main(verbosity=2)

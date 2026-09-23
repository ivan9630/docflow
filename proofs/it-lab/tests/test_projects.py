"""Unit, CLI and real localhost HTTP integration tests (no external services)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run import load

NAMES = sorted(p.name for p in ROOT.iterdir() if (p / "project.py").is_file())

def sample(name):
    return json.loads((ROOT / name / "sample.json").read_text(encoding="utf-8"))

def check(name, data=None):
    return load(name).analyze(sample(name) if data is None else data)

class Examples(unittest.TestCase):
    def test_exactly_ten_distinct_projects(self):
        self.assertEqual(len(NAMES), 10)

def example_test(name):
    def test(self):
        data = sample(name)
        before = copy.deepcopy(data)
        expected = load(name).analyze(data)
        self.assertEqual(data, before)
        process = subprocess.run([sys.executable, str(ROOT / "run.py"), name],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout), expected)
    return test

for name in NAMES:
    setattr(Examples, "test_cli_" + name.replace("-", "_"), example_test(name))

class BusinessRules(unittest.TestCase):
    def test_requirements_pending_and_uncovered(self):
        data = sample("requirements-traceability")
        self.assertFalse(check("requirements-traceability")["release_ready"])
        data["tests"] = []
        self.assertEqual(check("requirements-traceability", data)["requirements"][0]["status"], "uncovered")

    def test_requirements_fail_and_accept(self):
        data = sample("requirements-traceability")
        data["tests"][1]["status"] = "pass"
        self.assertTrue(check("requirements-traceability", data)["release_ready"])
        data["tests"][0]["status"] = "fail"
        self.assertEqual(check("requirements-traceability", data)["requirements"][0]["status"], "failed")

    def test_requirements_invalid_reference_and_duplicate(self):
        data = sample("requirements-traceability")
        data["tests"][0]["requirement"] = "missing"
        with self.assertRaises(ValueError):
            check("requirements-traceability", data)
        data = sample("requirements-traceability")
        data["requirements"].append(data["requirements"][0])
        with self.assertRaises(ValueError):
            check("requirements-traceability", data)

    def test_workstation_review_and_healthy(self):
        self.assertEqual(check("workstation-audit")["review_count"], 2)
        data = sample("workstation-audit")
        data["devices"][0]["disk_free_gb"] = 100
        data["devices"][1]["encrypted"] = True
        self.assertEqual(check("workstation-audit", data)["review_count"], 0)

    def test_workstation_invalid_snapshot(self):
        for field, value in [("encrypted", "false"), ("disk_total_gb", 0), ("disk_free_gb", 1000),
                             ("ram_gb", True), ("ram_gb", float("nan"))]:
            data = sample("workstation-audit")
            data["devices"][0][field] = value
            with self.assertRaises(ValueError):
                check("workstation-audit", data)

    def test_incident_priority_and_boundary(self):
        report = check("incident-triage")["tickets"]
        self.assertEqual(report[0]["priority"], "P1")
        self.assertTrue(report[0]["escalate"])
        data = sample("incident-triage")
        data["now"] = "2026-09-23T11:30:00+00:00"
        self.assertTrue(check("incident-triage", data)["tickets"][0]["escalate"])

    def test_incident_invalid_time(self):
        for now in ["2026-09-23T10:00:00+00:00", "2026-09-23T12:00:00"]:
            data = sample("incident-triage")
            data["now"] = now
            with self.assertRaises(ValueError):
                check("incident-triage", data)

    def test_reporting_quarantine_and_sql(self):
        report = check("claims-reporting")
        self.assertEqual(report["accepted"], 2)
        self.assertEqual(len(report["rejected"]), 2)
        self.assertEqual(report["kpis"], [{"team": "A", "count": 2, "amount_eur": 200,
                                         "average_delay_days": 3}])

    def test_reporting_sql_values_not_executed(self):
        data = {"claims": [{"id": "X", "team": "'; DROP TABLE claims;--", "amount_eur": 2, "delay_days": 1}]}
        self.assertEqual(check("claims-reporting", data)["accepted"], 1)
        self.assertEqual(check("claims-reporting", {"claims": []})["kpis"], [])

    def test_transaction_baseline_separate_from_candidates(self):
        report = check("transaction-alerts")
        self.assertEqual(report["baseline_median"], 100)
        self.assertEqual([t["review"] for t in report["transactions"]], [False, True])

    def test_transaction_zero_mad_and_threshold(self):
        data = {"history": [100] * 5, "transactions": [{"id": "X", "amount": 106}]}
        report = check("transaction-alerts", data)
        self.assertEqual(report["scale"], 1)
        self.assertFalse(report["transactions"][0]["review"])
        data["transactions"][0]["amount"] = 107
        self.assertTrue(check("transaction-alerts", data)["transactions"][0]["review"])

    def test_transaction_bad_history(self):
        data = sample("transaction-alerts")
        data["history"] = [100]
        with self.assertRaises(ValueError):
            check("transaction-alerts", data)

    def test_retail_no_join_fanout(self):
        self.assertEqual(check("retail-bi")["categories"],
                         [{"category": "books", "revenue_cents": 5000, "stock_units": 4,
                           "out_of_stock_skus": 1}])

    def test_retail_unknown_sku_and_noninteger(self):
        data = sample("retail-bi")
        data["sales"][0]["sku"] = "missing"
        with self.assertRaises(ValueError):
            check("retail-bi", data)
        data = sample("retail-bi")
        data["sales"][0]["quantity"] = 1.5
        with self.assertRaises(ValueError):
            check("retail-bi", data)

    def test_network_dependency_order(self):
        self.assertEqual(check("network-path")["check_order"], ["gateway", "switch", "workstation"])

    def test_network_cycle_missing_dependency_and_bad_ip(self):
        for change in ("cycle", "missing", "ip"):
            data = sample("network-path")
            if change == "cycle":
                data["nodes"][0]["depends_on"] = ["workstation"]
            elif change == "missing":
                data["nodes"][0]["depends_on"] = ["unknown"]
            else:
                data["nodes"][0]["ip"] = "not-an-ip"
            with self.assertRaises(ValueError):
                check("network-path", data)

    def test_warehouse_four_acceptance_cases(self):
        self.assertTrue(check("warehouse-recette")["release_ready"])
        data = sample("warehouse-recette")
        data["scenarios"][0]["expected"]["stock"] = 999
        self.assertFalse(check("warehouse-recette", data)["release_ready"])

    def test_warehouse_end_to_end_transitions(self):
        transition = load("warehouse-recette").transition
        state, stock = transition("new", "reserve", 8, 3)
        state, stock = transition(state, "pick", stock, 3)
        state, stock = transition(state, "ship", stock, 3)
        self.assertEqual((state, stock), ("shipped", 5))
        with self.assertRaises(ValueError):
            transition(state, "ship", stock, 3)

    def test_erp_stock_and_invoice_delta(self):
        report = check("erp-reconciliation")
        self.assertEqual(report["closing_stock"], {"SKU1": 12})
        self.assertEqual(report["invoice_discrepancies"][0]["difference_cents"], -100)

    def test_erp_duplicate_and_negative_stock(self):
        data = sample("erp-reconciliation")
        data["movements"].append(data["movements"][0])
        with self.assertRaises(ValueError):
            check("erp-reconciliation", data)
        data = sample("erp-reconciliation")
        data["movements"][1]["quantity"] = 16
        with self.assertRaises(ValueError):
            check("erp-reconciliation", data)

class HTTPIntegration(unittest.TestCase):
    def setUp(self):
        self.server = load("service-desk-web").make_server()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.server.database.close()

    def test_actual_http_creation_and_readback(self):
        with urlopen(self.base + "/", timeout=3) as response:
            self.assertIn("Mini Service Desk", response.read().decode())
        title = "<script>alert(1)</script>'"
        request = Request(self.base + "/api/tickets", data=json.dumps({"title": title}).encode(),
                          headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=3) as response:
            self.assertEqual(response.status, 201)
            self.assertEqual(json.load(response)["id"], 1)
        with urlopen(self.base + "/api/tickets", timeout=3) as response:
            self.assertEqual(json.load(response), [{"id": 1, "title": title, "status": "open"}])

    def test_http_invalid_input_and_not_found(self):
        for body in [b"{", b'{"title":""}', b'{"title":42}']:
            request = Request(self.base + "/api/tickets", data=body)
            with self.assertRaises(HTTPError) as raised:
                urlopen(request, timeout=3)
            self.assertEqual(raised.exception.code, 400)
            raised.exception.close()
        with self.assertRaises(HTTPError) as raised:
            urlopen(self.base + "/missing", timeout=3)
        self.assertEqual(raised.exception.code, 404)
        raised.exception.close()

class CLIValidation(unittest.TestCase):
    def test_bad_json_unknown_project_missing_field(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "input.json"
            for content in ["{", "{}"]:
                path.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, str(ROOT / "run.py"), "retail-bi", str(path)],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertNotIn("Traceback", result.stderr)
        result = subprocess.run([sys.executable, str(ROOT / "run.py"), "../escape"],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)

if __name__ == "__main__":
    unittest.main()


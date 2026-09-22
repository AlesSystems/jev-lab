import importlib.util
import json
import math
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("repro_coach.py")
SPEC = importlib.util.spec_from_file_location("repro_coach", SCRIPT)
assert SPEC and SPEC.loader
repro_coach = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = repro_coach
SPEC.loader.exec_module(repro_coach)


class PolicyTests(unittest.TestCase):
    def test_thresholds_and_middle_values(self):
        ready = repro_coach.decide({"steps_present": 0.2, "result_present": 0.8, "environment_present": 1.0})
        self.assertEqual(ready.status, "ready")
        self.assertEqual(ready.checklist, (repro_coach.QUESTIONS["steps_present"].template,))

        review = repro_coach.decide({"steps_present": 0.21, "result_present": 0.8, "environment_present": 0.8})
        self.assertEqual((review.status, review.checklist), ("review", ()))

    def test_invalid_answer_is_unavailable(self):
        for invalid in (True, math.nan, -0.1, 1.1, "0.9"):
            with self.subTest(invalid=invalid):
                result = repro_coach.decide({"steps_present": invalid, "result_present": 0.8, "environment_present": 0.8})
                self.assertEqual(result.status, "unavailable")
                self.assertEqual(result.checklist, ())

    def test_empty_ready_checklist_is_automatic(self):
        result = repro_coach.decide({key: 0.8 for key in repro_coach.QUESTIONS})
        self.assertEqual((result.status, result.checklist), ("ready", ()))


class BoundaryTests(unittest.TestCase):
    def test_response_parser_requires_every_typed_noul(self):
        payload = {
            "answers": {key: {"type": "noul", "noul": 0.8} for key in repro_coach.QUESTIONS},
            "model": "jev-1.13.0",
            "usage": {"input_tokens": 12},
        }
        parsed = repro_coach.parse_response(payload)
        self.assertEqual(parsed.values["steps_present"], 0.8)
        self.assertEqual(parsed.returned_model, "jev-1.13.0")

        payload["answers"]["steps_present"]["type"] = "choice"
        with self.assertRaises(repro_coach.ResponseError):
            repro_coach.parse_response(payload)

    def test_whole_checklist_metrics_keep_all_inputs_in_denominator(self):
        rows = [
            {"expected_checklist": ["a"], "baseline": {"checklist": []}, "jev": {"status": "ready", "checklist": ["a"]}},
            {"expected_checklist": [], "baseline": {"checklist": []}, "jev": {"status": "ready", "checklist": []}},
            {"expected_checklist": ["a"], "baseline": {"checklist": []}, "jev": {"status": "review", "checklist": []}},
            {"expected_checklist": [], "baseline": {"checklist": []}, "jev": {"status": "unavailable", "checklist": []}},
        ]
        metrics = repro_coach.metrics(rows)
        self.assertEqual(metrics["eligible"], 4)
        self.assertEqual(metrics["automatic"], 2)
        self.assertEqual(metrics["correct_automatic"], 2)
        self.assertEqual(metrics["coverage"], 0.5)
        self.assertEqual(metrics["selective_accuracy"], 1.0)


class CliTests(unittest.TestCase):
    def test_blank_report_requests_description_without_live_configuration(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "report", "   ", "--live"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "request_description")

    def test_baseline_run_records_not_run(self):
        fixture = [{
            "fixture_id": "one",
            "split": "dev",
            "report": "Export is broken.",
            "expected_present": {"steps_present": False, "result_present": False, "environment_present": False},
            "disputed": False,
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_path = root / "fixtures.json"
            evidence_path = root / "evidence.jsonl"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "fixtures", "--fixtures", str(fixture_path), "--split", "dev", "--evidence", str(evidence_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            row = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(row["jev"]["status"], "not_run")
            self.assertEqual(row["provenance"], "baseline_only")
            self.assertFalse(json.loads(result.stdout)["jev_acceptance_evaluable"])


if __name__ == "__main__":
    unittest.main()

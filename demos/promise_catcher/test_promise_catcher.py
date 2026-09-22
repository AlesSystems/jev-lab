import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import promise_catcher


class DecisionTests(unittest.TestCase):
    def test_policy_routes_clear_uncertain_and_contradictory_answers(self):
        cases = [
            ((0.8, 0.2), "proposed"),
            ((0.2, 0.8), "no_suggestion"),
            ((0.1, 0.1), "no_suggestion"),
            ((0.5, 0.1), "review"),
            ((0.1, 0.5), "review"),
            ((0.9, 0.9), "review"),
        ]
        self.assertEqual(
            [promise_catcher.decide(*probabilities).status for probabilities, _ in cases],
            [expected for _, expected in cases],
        )

    def test_response_parser_rejects_invalid_required_answers(self):
        valid = {
            "model": "jev-1.13.0",
            "answers": {
                "commitment": {"type": "noul", "noul": 0.9},
                "completed": {"type": "noul", "noul": 0.1},
            },
            "usage": {"input_tokens": 10},
        }
        self.assertEqual(
            promise_catcher.parse_jev_response(valid).commitment,
            0.9,
        )
        for bad_value in [True, float("nan"), -0.1, 1.1, "0.9"]:
            broken = json.loads(json.dumps(valid))
            broken["answers"]["commitment"]["noul"] = bad_value
            with self.subTest(bad_value=bad_value):
                with self.assertRaises(promise_catcher.ResponseError):
                    promise_catcher.parse_jev_response(broken)


class PreviewTests(unittest.TestCase):
    def test_preview_is_durable_idempotent_and_conflict_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previews.jsonl"
            item = promise_catcher.PromiseInput("note-17", "Ada", "I will send it.")
            self.assertEqual(promise_catcher.save_preview(path, item), "created")
            self.assertEqual(promise_catcher.save_preview(path, item), "duplicate")
            self.assertEqual(
                promise_catcher.save_preview(
                    path,
                    promise_catcher.PromiseInput("note-17", "Ada", "I will send that."),
                ),
                "conflict",
            )
            self.assertEqual(
                json.loads(path.read_text()),
                {
                    "source_id": "note-17",
                    "source_sentence": "I will send it.",
                    "author": "Ada",
                    "owner": None,
                    "due_date": None,
                    "confirmation_required": ["owner", "due_date"],
                },
            )

    def test_corrupt_preview_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previews.jsonl"
            path.write_text("not-json\n")
            with self.assertRaises(promise_catcher.PreviewError):
                promise_catcher.save_preview(
                    path,
                    promise_catcher.PromiseInput("note-17", "Ada", "I will send it."),
                )
            self.assertEqual(path.read_text(), "not-json\n")


class CliTests(unittest.TestCase):
    def test_offline_catch_reports_not_run_and_requires_preview_opt_in(self):
        script = Path(__file__).with_name("promise_catcher.py")
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "previews.jsonl"
            command = [
                sys.executable,
                str(script),
                "catch",
                "--source-id",
                "note-17",
                "--author",
                "Ada",
                "--sentence",
                "I will send it.",
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            output = json.loads(result.stdout)
            self.assertEqual(output["jev_status"], "not_run")
            self.assertEqual(output["baseline_action"], "proposed")
            self.assertFalse(preview.exists())

            result = subprocess.run(
                [*command, "--preview", str(preview)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(result.stdout)["preview_status"], "created")
            self.assertTrue(preview.exists())


if __name__ == "__main__":
    unittest.main()

import json
import os
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

import promise_catcher


class DecisionTests(unittest.TestCase):
    def test_live_cli_exposes_the_returned_envelope(self):
        payload = {
            "model": "jev-1.13.0",
            "answers": {key: {"type": "noul", "noul": 0.9} for key in promise_catcher.QUESTIONS},
            "rationale": "A returned field",
        }
        output = StringIO()
        with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": "cli-secret"}), mock.patch("urllib.request.urlopen") as urlopen, redirect_stdout(output):
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            self.assertEqual(promise_catcher.main(["catch", "--source-id", "id", "--author", "Ada", "--sentence", "I will send it.", "--live"]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(result["inspection"]["response"], payload)
        self.assertNotIn("cli-secret", output.getvalue())

    def test_inspection_preserves_response_and_excludes_credentials(self):
        payload = {
            "model": "jev-1.13.0",
            "answers": {key: {"type": "noul", "noul": 0.9} for key in promise_catcher.QUESTIONS},
            "reasoning": {"text": "Returned explanation"},
            "usage": {"input_tokens": 12},
        }
        inspection = promise_catcher.inspection_record()
        self.assertIsNone(inspection["request"])
        self.assertIsNone(inspection["response"])
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(payload).encode()
            promise_catcher.call_jev(promise_catcher.PromiseInput("id", "Ada", "I will send it."), "inspection-test-secret", inspection)
            sent = urlopen.call_args.args[0]
        self.assertEqual(inspection["request"], json.loads(sent.data))
        self.assertEqual(inspection["response"], payload)
        self.assertNotIn("inspection-test-secret", json.dumps(inspection))
        self.assertNotIn("Authorization", json.dumps(inspection))

    def test_invalid_response_is_visible_but_still_an_error(self):
        inspection = promise_catcher.inspection_record()
        with mock.patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value.__enter__.return_value.read.return_value = b'{"answers": {}}'
            with self.assertRaises(promise_catcher.ResponseError):
                promise_catcher.call_jev(promise_catcher.PromiseInput("id", "Ada", "I will send it."), "secret", inspection)
        self.assertEqual(inspection["response"], {"answers": {}})

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
        for bad_value in [True, float("nan"), -0.1, 1.1, "0.9", 10**400]:
            broken = json.loads(json.dumps(valid))
            broken["answers"]["commitment"]["noul"] = bad_value
            with self.subTest(bad_value=bad_value), self.assertRaises(
                promise_catcher.ResponseError
            ):
                    promise_catcher.parse_jev_response(broken)

        for bad_tokens in (True, -1, 1.5, "10"):
            broken = json.loads(json.dumps(valid))
            broken["usage"]["input_tokens"] = bad_tokens
            with self.subTest(bad_tokens=bad_tokens), self.assertRaises(
                promise_catcher.ResponseError
            ):
                promise_catcher.parse_jev_response(broken)


class PreviewTests(unittest.TestCase):
    def test_preview_is_durable_idempotent_and_conflict_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previews.jsonl"
            item = promise_catcher.PromiseInput("note-17", "Ada", "I will send it.")
            self.assertEqual(promise_catcher.save_preview(path, item), "created")
            self.assertEqual(promise_catcher.save_preview(path, item), "duplicate")
            self.assertEqual(promise_catcher.save_preview(path, item, "live_jev"), "duplicate")
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
                    "engine": "offline_baseline",
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

    def test_shaped_invalid_preview_is_rejected_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previews.jsonl"
            for invalid in ("{}\n", "[]\n"):
                with self.subTest(invalid=invalid):
                    path.write_text(invalid)
                    with self.assertRaises(promise_catcher.PreviewError):
                        promise_catcher.save_preview(
                            path,
                            promise_catcher.PromiseInput("note-17", "Ada", "I will send it."),
                        )
                    self.assertEqual(path.read_text(), invalid)

    def test_failed_atomic_replace_preserves_existing_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "previews.jsonl"
            first = promise_catcher.PromiseInput("note-1", "Ada", "I will send it.")
            promise_catcher.save_preview(path, first)
            before = path.read_text()
            with mock.patch.object(
                promise_catcher.os, "replace", side_effect=OSError("disk")
            ), self.assertRaises(OSError):
                promise_catcher.save_preview(
                    path,
                    promise_catcher.PromiseInput("note-2", "Ben", "I will review it."),
                )
            self.assertEqual(path.read_text(), before)


class CliTests(unittest.TestCase):
    def test_dev_evaluation_summarizes_the_selected_ten_rows(self):
        fixtures = Path(__file__).with_name("fixtures.jsonl")
        with tempfile.TemporaryDirectory() as directory:
            summary = promise_catcher.evaluate(
                fixtures,
                Path(directory) / "evidence.jsonl",
                live=False,
                split="dev",
            )
            self.assertEqual(summary["eligible"], 10)
            self.assertEqual(summary["not_run"], 10)
            self.assertEqual(summary["baseline_correct"], 9)
            self.assertEqual(summary["acceptance"], "not_measured")

    def test_live_metrics_require_balanced_heldout_labels_and_price_known_usage(self):
        fixtures = Path(__file__).with_name("fixtures.jsonl")
        answer = promise_catcher.JevAnswers(0.9, 0.1, "jev-1.13.0", {"input_tokens": 100})
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TYPESAFE_API_KEY": "test-key"}
        ), mock.patch.object(
            promise_catcher, "call_jev", return_value=answer
        ):
            dev = promise_catcher.evaluate(
                fixtures,
                Path(directory) / "dev.jsonl",
                live=True,
                split="dev",
            )
            self.assertEqual(dev["input_tokens_known"], 1_000)
            self.assertEqual(dev["usage_missing_count"], 0)
            self.assertEqual(dev["estimated_input_cost_usd"], 0.000042)

            rows = [json.loads(line) for line in fixtures.read_text().splitlines()]
            for row in rows:
                if row["split"] == "heldout":
                    row["expected"] = "proposed"
            unbalanced = Path(directory) / "unbalanced.jsonl"
            unbalanced.write_text("".join(json.dumps(row) + "\n" for row in rows))
            summary = promise_catcher.evaluate(
                unbalanced,
                Path(directory) / "heldout.jsonl",
                live=True,
                split="heldout",
            )
            self.assertFalse(summary["jev_acceptance_evaluable"])
            self.assertEqual(summary["acceptance"], "not_measured")
            self.assertEqual(summary["acceptance_reason"], "heldout_labels_not_10_and_10")

    def test_live_metrics_count_empty_usage_as_missing(self):
        fixtures = Path(__file__).with_name("fixtures.jsonl")
        answer = promise_catcher.JevAnswers(0.9, 0.1, "jev-1.13.0", {})
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TYPESAFE_API_KEY": "test-key"}
        ), mock.patch.object(
            promise_catcher, "call_jev", return_value=answer
        ):
            summary = promise_catcher.evaluate(
                fixtures,
                Path(directory) / "dev.jsonl",
                live=True,
                split="dev",
            )
            self.assertEqual(summary["usage_missing_count"], 10)
            self.assertEqual(summary["input_tokens_known"], 0)
            self.assertTrue(summary["cost_partial"])

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
            self.assertIsNone(output["inspection"]["request"])
            self.assertIsNone(output["inspection"]["response"])
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

            replay = subprocess.run(
                [*command, "--preview", str(preview)],
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(replay.stdout)["preview_status"], "duplicate")
            self.assertEqual(len(preview.read_text().splitlines()), 1)

    def test_live_failure_never_writes_a_baseline_preview(self):
        script = Path(__file__).with_name("promise_catcher.py")
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory) / "previews.jsonl"
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "catch",
                    "--source-id",
                    "note-17",
                    "--author",
                    "Ada",
                    "--sentence",
                    "I will send it.",
                    "--live",
                    "--preview",
                    str(preview),
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "TYPESAFE_API_KEY": ""},
                check=True,
            )
            output = json.loads(result.stdout)
            self.assertEqual(output["jev_action"], "unavailable")
            self.assertEqual(output["preview_status"], "not_requested")
            self.assertFalse(preview.exists())

    def test_request_failure_never_writes_a_baseline_preview(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            os.environ, {"TYPESAFE_API_KEY": "test-key"}
        ), mock.patch.object(
            promise_catcher, "call_jev", side_effect=promise_catcher.ResponseError("failed")
        ):
            preview = Path(directory) / "previews.jsonl"
            output = StringIO()
            args = Namespace(
                source_id="note-17",
                author="Ada",
                sentence="I will send it.",
                live=True,
                preview=str(preview),
            )
            with redirect_stdout(output):
                promise_catcher._catch(args)
            self.assertEqual(json.loads(output.getvalue())["jev_action"], "unavailable")
            self.assertFalse(preview.exists())


if __name__ == "__main__":
    unittest.main()

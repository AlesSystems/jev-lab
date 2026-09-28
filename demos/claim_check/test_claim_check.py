import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).with_name("claim_check.py")
SPEC = importlib.util.spec_from_file_location("claim_check", SCRIPT)
assert SPEC and SPEC.loader
claim_check = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = claim_check
SPEC.loader.exec_module(claim_check)


class ClaimTests(unittest.TestCase):
    def test_overlap_marks_every_shared_word_as_supported(self):
        narrow = claim_check.baseline("CSV exports are faster")
        wide = claim_check.baseline("All exports are faster")
        slower = claim_check.baseline("Exports are slower now")
        self.assertEqual(narrow["verdict"], "supported")
        self.assertEqual(narrow["reason"], "shared words: csv, exports")
        self.assertEqual(wide["verdict"], "supported")
        self.assertEqual(slower["verdict"], "supported")

    def test_wider_claim_keeps_the_evidence_and_changes_the_label(self):
        narrow = claim_check.board_payload("csv_faster")
        wide = claim_check.board_payload("all_faster")
        slower = claim_check.board_payload("slower")
        self.assertEqual(narrow["evidence"], wide["evidence"])
        self.assertEqual(narrow["decision"], "SUPPORTED")
        self.assertFalse(narrow["split"])
        self.assertEqual(wide["decision"], "INSUFFICIENT")
        self.assertTrue(wide["split"])
        self.assertEqual(slower["label"]["verdict"], "contradicted")
        self.assertEqual(slower["baseline"]["verdict"], "supported")

    def test_unknown_claim_is_rejected(self):
        status, payload, _media = claim_check.route("GET", "/api/board?id=missing")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "unknown_scenario")

    def test_missing_key_stays_on_the_baseline(self):
        def transport(body: bytes, api_key: str) -> bytes:
            raise AssertionError("Jev was called")

        board = claim_check.board_payload("all_faster", api_key=None, transport=transport)
        self.assertEqual(board["engine"], "offline_baseline")
        self.assertIsNone(board["jev"])
        self.assertEqual(board["decision"], "INSUFFICIENT")

    def test_live_choice_is_the_reading_and_the_key_stays_out_of_the_body(self):
        seen: dict[str, object] = {}

        def transport(body: bytes, api_key: str) -> bytes:
            seen["key"] = api_key
            seen["body"] = json.loads(body)
            return json.dumps({
                "model": "jev-1.13.0",
                "answers": {
                    "verdict": {
                        "type": "choice",
                        "choice": "insufficient_evidence",
                        "probabilities": {
                            "supported": 0.04,
                            "contradicted": 0.06,
                            "insufficient_evidence": 0.9,
                        },
                        "confidence": 0.86,
                    }
                },
            }).encode()

        board = claim_check.board_payload("all_faster", api_key="secret", transport=transport)
        self.assertEqual(seen["key"], "secret")
        request = seen["body"]
        assert isinstance(request, dict)
        self.assertEqual(request["model"], "jev-1.13.0")
        self.assertEqual(request["state"]["claim"], "All exports are faster")
        self.assertIn("evidence", request["state"])
        self.assertNotIn("secret", body_text(request))
        self.assertEqual(board["engine"], "live_jev")
        self.assertEqual(board["decision"], "INSUFFICIENT")
        self.assertEqual(board["jev"]["verdict"], "insufficient_evidence")
        self.assertEqual(board["jev"]["confidence"], 0.86)
        self.assertTrue(board["split"])

    def test_low_confidence_stays_in_review(self):
        board = claim_check.board_payload("csv_faster", api_key="secret", transport=lambda _body, _key: choice_body("supported", 0.41))
        self.assertEqual(board["engine"], "live_jev")
        self.assertEqual(board["decision"], "REVIEW")
        self.assertIsNone(board["jev"]["verdict"])

    def test_a_bad_response_is_unavailable_and_is_not_replaced_by_the_baseline(self):
        board = claim_check.board_payload("csv_faster", api_key="secret", transport=lambda _body, _key: b"{}")
        self.assertEqual(board["engine"], "unavailable")
        self.assertEqual(board["decision"], "UNAVAILABLE")
        self.assertIsNone(board["jev"])
        self.assertEqual(board["baseline"]["verdict"], "supported")

    def test_route_forwards_the_env_key(self):
        with mock.patch.object(claim_check, "board_payload", return_value={"ok": True}) as board:
            with mock.patch.dict("os.environ", {"TYPESAFE_API_KEY": "secret"}):
                status, payload, _media = claim_check.route("GET", "/api/board?id=csv_faster")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        board.assert_called_once_with("csv_faster", api_key="secret")


def choice_body(choice: str, confidence: float) -> bytes:
    probabilities = {"supported": 0.0, "contradicted": 0.0, "insufficient_evidence": 0.0}
    probabilities[choice] = 1.0
    return json.dumps({
        "model": "jev-1.13.0",
        "answers": {
            "verdict": {
                "type": "choice",
                "choice": choice,
                "probabilities": probabilities,
                "confidence": confidence,
            }
        },
    }).encode()


def body_text(request: dict) -> str:
    return json.dumps(request)

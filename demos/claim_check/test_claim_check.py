import importlib.util
import sys
import unittest
from pathlib import Path

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

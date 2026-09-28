import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("interruption_budget.py")
SPEC = importlib.util.spec_from_file_location("interruption_budget", SCRIPT)
assert SPEC and SPEC.loader
budget = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = budget
SPEC.loader.exec_module(budget)


def placed(payload: dict, event_id: str) -> dict:
    for column in payload["columns"]:
        for event in column["events"]:
            if event["id"] == event_id:
                return event
    raise AssertionError(event_id)


class InboxTests(unittest.TestCase):
    def test_lookup_and_label_disagree_on_smoke_and_checkout(self):
        page = budget.inbox(False)
        smoke = placed(page, "smoke")
        checkout = placed(page, "checkout")
        self.assertEqual(smoke["lane"], "digest")
        self.assertEqual(smoke["baseline"], "attention_now")
        self.assertTrue(smoke["split"])
        self.assertEqual(checkout["lane"], "attention_now")
        self.assertEqual(checkout["baseline"], "digest")
        self.assertEqual(page["decision"], "SPLIT")

    def test_quiet_hours_digest_everything_except_the_page_flag(self):
        page = budget.inbox(True)
        self.assertEqual(page["decision"], "QUIET")
        self.assertEqual(placed(page, "checkout")["lane"], "digest")
        self.assertEqual(placed(page, "handoff")["lane"], "digest")
        edge = placed(page, "edge")
        self.assertEqual(edge["lane"], "attention_now")
        self.assertFalse(edge["split"])
        self.assertEqual(edge["note"], "Priority flag holds this in attention now.")

    def test_quiet_flag_must_be_yes_or_no(self):
        status, payload, _media = budget.route("GET", "/api/inbox?quiet=maybe")
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_quiet")

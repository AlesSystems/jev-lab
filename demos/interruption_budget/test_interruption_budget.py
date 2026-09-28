import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

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
    def test_custom_event_reaches_jev_and_page_flag_stays_in_code(self):
        sent = []

        def transport(body: bytes, _key: str) -> bytes:
            sent.append(json.loads(body))
            return score_body({"custom": 1.9})

        event = budget.custom_event("My build is blocked by a missing approval", False)
        page = budget.inbox(False, api_key="secret", transport=transport, events=(event,), custom=True)
        self.assertEqual(sent[0]["state"]["events"][0]["text"], event.text)
        self.assertEqual(placed(page, "custom")["lane"], "attention_now")
        self.assertEqual(page["engine"], "live_jev")

        sent.clear()
        page = budget.inbox(False, api_key="secret", transport=transport,
                            events=(budget.custom_event("Page me", True),), custom=True)
        self.assertEqual(sent, [])
        self.assertEqual(placed(page, "custom")["source"], "code_rule")
        self.assertEqual(budget.inbox(False, events=(budget.custom_event("Page me", True),),
                                      custom=True)["engine"], "code_rule")

    def test_custom_route_validates_input(self):
        for body in (b"{}", b'{"text":"","quiet":false,"page":false}',
                     b'{"text":"Hi","quiet":"no","page":false}'):
            status, _payload, _media = budget.route("POST", "/api/sort", body)
            self.assertEqual(status, 400)
        status, payload, _media = budget.route(
            "POST", "/api/sort", b'{"text":"Custom alert","quiet":false,"page":false}'
        )
        self.assertEqual(status, 200)
        self.assertEqual(placed(payload, "custom")["text"], "Custom alert")

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

    def test_score_maps_onto_the_three_lanes(self):
        self.assertEqual(budget.lane_from_score(0.2, 0.9), "digest")
        self.assertEqual(budget.lane_from_score(1.1, 0.91), "review")
        self.assertEqual(budget.lane_from_score(1.8, 0.93), "attention_now")
        self.assertEqual(budget.lane_from_score(2.0, 0.4), "review")

    def test_missing_key_does_not_call_jev(self):
        def transport(body: bytes, api_key: str) -> bytes:
            raise AssertionError("Jev was called")

        page = budget.inbox(False, api_key=None, transport=transport)
        self.assertEqual(page["engine"], "offline_baseline")
        self.assertEqual(placed(page, "smoke")["lane"], "digest")

    def test_live_scores_place_events_and_the_page_flag_skips_jev(self):
        seen: dict[str, object] = {}

        def transport(body: bytes, api_key: str) -> bytes:
            seen["key"] = api_key
            seen["body"] = json.loads(body)
            request = seen["body"]
            assert isinstance(request, dict)
            return score_body({event_id: 0.1 for event_id in request["questions"]})

        page = budget.inbox(False, api_key="secret", transport=transport)
        request = seen["body"]
        assert isinstance(request, dict)
        self.assertEqual(seen["key"], "secret")
        self.assertEqual(request["model"], "jev-1.13.0")
        self.assertNotIn("edge", request["questions"])
        self.assertNotIn("secret", json.dumps(request))
        self.assertEqual(page["engine"], "live_jev")
        self.assertEqual(placed(page, "smoke")["lane"], "digest")
        self.assertEqual(placed(page, "smoke")["source"], "live_jev")
        edge = placed(page, "edge")
        self.assertEqual(edge["lane"], "attention_now")
        self.assertEqual(edge["source"], "code_rule")
        self.assertEqual(edge["note"], "Priority flag holds this in attention now.")

    def test_quiet_hours_do_not_call_jev_even_with_a_key(self):
        def transport(body: bytes, api_key: str) -> bytes:
            raise AssertionError("Jev was called")

        page = budget.inbox(True, api_key="secret", transport=transport)
        self.assertEqual(page["engine"], "code_rule")
        self.assertEqual(placed(page, "handoff")["lane"], "digest")
        self.assertEqual(placed(page, "edge")["lane"], "attention_now")

    def test_a_bad_response_lands_in_review_without_using_the_fixture_lane(self):
        page = budget.inbox(False, api_key="secret", transport=lambda _body, _key: b"{}")
        self.assertEqual(page["engine"], "unavailable")
        self.assertEqual(page["decision"], "UNAVAILABLE")
        smoke = placed(page, "smoke")
        self.assertEqual(smoke["lane"], "review")
        self.assertEqual(smoke["source"], "unavailable")
        self.assertEqual(placed(page, "edge")["lane"], "attention_now")

    def test_route_forwards_the_env_key(self):
        with mock.patch.object(budget, "inbox", return_value={"ok": True}) as inbox:
            with mock.patch.dict("os.environ", {"TYPESAFE_API_KEY": "secret"}):
                status, payload, _media = budget.route("GET", "/api/inbox?quiet=0")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        inbox.assert_called_once_with(False, api_key="secret")


def score_body(scores: dict[str, float]) -> bytes:
    answers = {
        event_id: {
            "type": "score",
            "score": score,
            "confidence": 0.9,
            "probabilities": {"0": 1.0},
            "legend": {"0": "Informational", "1": "Can wait", "2": "Blocked"},
        }
        for event_id, score in scores.items()
    }
    return json.dumps({"model": "jev-1.13.0", "answers": answers}).encode()

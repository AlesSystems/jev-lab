import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("demo_dashboard.py")
SPEC = importlib.util.spec_from_file_location("demo_dashboard", SCRIPT)
assert SPEC and SPEC.loader
demo_dashboard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = demo_dashboard
SPEC.loader.exec_module(demo_dashboard)

EXPECTED_IDS = (
    "field_matchmaker",
    "claim_check",
    "interruption_budget",
    "festival_control_room",
    "launch_lab",
    "feedback_kitchen",
    "jev_habitat",
    "repro_coach",
    "promise_catcher",
)


def answer_leaves(node):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "type":
                continue
            yield from answer_leaves(value)
    elif isinstance(node, list):
        for item in node:
            yield from answer_leaves(item)
    else:
        yield node


class DemoDashboardTests(unittest.TestCase):
    def test_catalog_matches_the_demo_directories(self):
        ids = [item["id"] for item in demo_dashboard.catalog()]
        self.assertEqual(ids, list(EXPECTED_IDS))
        demos = Path(__file__).parents[1]
        for demo_id in ids:
            self.assertTrue((demos / demo_id).is_dir(), demo_id)

    def test_field_match_trace_uses_the_real_targets_and_a_blank_choice(self):
        demo = next(item for item in demo_dashboard.catalog() if item["id"] == "field_matchmaker")
        targets = [target["id"] for target in demo["request"]["state"]["targets"]]
        self.assertEqual(
            targets,
            ["company_name", "contact_email", "account_id", "country", "annual_revenue"],
        )
        self.assertIsNone(demo["response"]["answers"]["c0"]["choice"])
        self.assertIsNone(demo["response"]["answers"]["c0"]["confidence"])

    def test_answer_leaves_stay_unmeasured(self):
        for demo in demo_dashboard.catalog():
            leaves = list(answer_leaves(demo["response"]["answers"]))
            self.assertTrue(leaves, demo["id"])
            self.assertTrue(all(value is None for value in leaves), demo["id"])

    def test_shared_ports_are_named(self):
        demos = {item["id"]: item for item in demo_dashboard.catalog()}
        self.assertIn("8766", demos["launch_lab"]["port_note"])
        self.assertIn("Claim check", demos["launch_lab"]["port_note"])
        self.assertIn("8767", demos["feedback_kitchen"]["port_note"])
        self.assertIn("Interruption budget", demos["feedback_kitchen"]["port_note"])
        self.assertEqual(demos["repro_coach"]["open"], "")
        self.assertEqual(demos["field_matchmaker"]["open"], "http://127.0.0.1:8765")

    def test_routes_serve_the_page_catalog_and_warm_sheet(self):
        status, payload, media = demo_dashboard.route("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", media)
        html = payload.decode() if isinstance(payload, bytes) else payload
        self.assertIn("/api/demos", html)
        self.assertNotIn("Prototype variants", html)

        status, payload, media = demo_dashboard.route("GET", "/api/demos")
        self.assertEqual(status, 200)
        self.assertIn("application/json", media)
        self.assertEqual([item["id"] for item in payload["demos"]], list(EXPECTED_IDS))

        status, css, media = demo_dashboard.route("GET", "/app.css")
        self.assertEqual(status, 200)
        self.assertIn("text/css", media)
        text = css.decode() if isinstance(css, bytes) else css
        self.assertIn("#3f2a1d", text)
        self.assertNotIn("#1d4ed8", text)
        self.assertNotIn("#b7c6e0", text)

        status, _, _ = demo_dashboard.route("GET", "/missing")
        self.assertEqual(status, 404)

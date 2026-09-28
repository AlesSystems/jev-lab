import importlib.util
import json
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("field_matchmaker.py")
SPEC = importlib.util.spec_from_file_location("field_matchmaker", SCRIPT)
assert SPEC and SPEC.loader
field_matchmaker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = field_matchmaker
SPEC.loader.exec_module(field_matchmaker)


def choices(scenario_id: str, use_label: bool = True) -> list[dict[str, str | None]]:
    board = field_matchmaker.board_payload(scenario_id)
    return [
        {"header": column["header"], "target_id": column["label"] if use_label else column["baseline"]}
        for column in board["columns"]
    ]


class MappingTests(unittest.TestCase):
    def test_alias_baseline_misses_trading_name_and_hits_account(self):
        self.assertIsNone(field_matchmaker.baseline_target("Trading name"))
        self.assertEqual(field_matchmaker.baseline_target("Account"), "account_id")
        self.assertEqual(field_matchmaker.baseline_target("Country"), "country")

    def test_vendor_file_labels_the_alias_misses(self):
        board = field_matchmaker.board_payload("vendor_csv")
        by_header = {column["header"]: column for column in board["columns"]}
        self.assertEqual(by_header["Trading name"]["label"], "company_name")
        self.assertIsNone(by_header["Trading name"]["baseline"])
        self.assertIsNone(by_header["Account"]["label"])
        self.assertEqual(by_header["Account"]["baseline"], "account_id")

    def test_unique_picks_preview_and_duplicate_picks_stay_closed(self):
        clear = field_matchmaker.assess("clean_headers", choices("clean_headers"))
        self.assertEqual(clear["decision"], "CLEAR")
        self.assertEqual(clear["preview"][0]["target"], "company_name")
        self.assertEqual(len(clear["preview"]), 5)

        conflict = field_matchmaker.assess("name_conflict", choices("name_conflict"))
        self.assertEqual(conflict["decision"], "CONFLICT")
        self.assertEqual(conflict["conflicts"], ["company_name"])
        self.assertEqual(conflict["preview"], [])

    def test_vendor_labels_split_from_the_baseline_and_still_preview(self):
        result = field_matchmaker.assess("vendor_csv", choices("vendor_csv"))
        self.assertEqual(result["decision"], "SPLIT")
        self.assertEqual(result["preview"][0], {
            "header": "Trading name",
            "target": "company_name",
            "samples": ["Northwind", "Acme Ltd", "Bright Studio"],
        })
        self.assertEqual(result["preview"][2]["target"], "unmapped")

    def test_unknown_target_is_rejected_at_the_boundary(self):
        status, payload, _media = field_matchmaker.route(
            "POST",
            "/api/preview",
            json.dumps({"scenario_id": "vendor_csv", "choices": [{"header": "Trading name", "target_id": "password"}]}).encode(),
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "unknown_target")

    def test_static_paths_stay_inside_the_page(self):
        self.assertIsNone(field_matchmaker.resolve_static("../repro_coach.py"))
        self.assertEqual(field_matchmaker.resolve_static("index.html").name, "index.html")

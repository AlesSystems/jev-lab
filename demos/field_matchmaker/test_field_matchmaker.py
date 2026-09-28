import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

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

    def test_missing_key_does_not_call_jev(self):
        def transport(body: bytes, api_key: str) -> bytes:
            raise AssertionError("Jev was called")

        board = field_matchmaker.board_payload("vendor_csv", api_key=None, transport=transport)
        self.assertEqual(board["engine"], "offline_baseline")
        self.assertTrue(all(column["jev"] is None for column in board["columns"]))

    def test_live_choices_fill_confident_columns_and_leave_the_key_out_of_the_body(self):
        seen: dict[str, object] = {}

        def transport(body: bytes, api_key: str) -> bytes:
            seen["key"] = api_key
            seen["body"] = json.loads(body)
            return column_body({
                "c0": ("company_name", 0.91),
                "c1": ("contact_email", 0.4),
                "c2": ("unmapped", 0.88),
                "c3": ("country", 0.93),
                "c4": ("annual_revenue", 0.9),
            })

        board = field_matchmaker.board_payload("vendor_csv", api_key="secret", transport=transport)
        request = seen["body"]
        assert isinstance(request, dict)
        self.assertEqual(seen["key"], "secret")
        self.assertEqual(request["model"], "jev-1.13.0")
        self.assertNotIn("secret", json.dumps(request))
        self.assertIn("unmapped", request["questions"]["c0"]["criteria"])
        by_header = {column["header"]: column["jev"] for column in board["columns"]}
        self.assertEqual(by_header["Trading name"], {"status": "suggested", "target": "company_name", "confidence": 0.91})
        self.assertEqual(by_header["Work email"]["status"], "review")
        self.assertIsNone(by_header["Work email"]["target"])
        self.assertEqual(by_header["Account"], {"status": "suggested", "target": None, "confidence": 0.88})
        self.assertEqual(board["engine"], "live_jev")

    def test_duplicate_jev_targets_still_conflict_in_code(self):
        board = field_matchmaker.board_payload(
            "name_conflict",
            api_key="secret",
            transport=lambda _body, _key: column_body({
                "c0": ("company_name", 0.9),
                "c1": ("company_name", 0.92),
                "c2": ("contact_email", 0.95),
            }),
        )
        picks = [
            {"header": column["header"], "target_id": column["jev"]["target"]}
            for column in board["columns"]
        ]
        result = field_matchmaker.assess("name_conflict", picks)
        self.assertEqual(result["decision"], "CONFLICT")
        self.assertEqual(result["conflicts"], ["company_name"])

    def test_a_bad_response_does_not_invent_mappings(self):
        board = field_matchmaker.board_payload("clean_headers", api_key="secret", transport=lambda _body, _key: b"{}")
        self.assertEqual(board["engine"], "unavailable")
        self.assertTrue(all(column["jev"]["status"] == "unavailable" for column in board["columns"]))
        self.assertTrue(all(column["jev"]["target"] is None for column in board["columns"]))

    def test_route_forwards_the_env_key(self):
        with mock.patch.object(field_matchmaker, "board_payload", return_value={"ok": True}) as board:
            with mock.patch.dict("os.environ", {"TYPESAFE_API_KEY": "secret"}):
                status, payload, _media = field_matchmaker.route("GET", "/api/board?id=vendor_csv")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"ok": True})
        board.assert_called_once_with("vendor_csv", api_key="secret")

    def test_custom_csv_uses_samples_without_fixture_labels(self):
        csv_text = 'Organisation,Email\n"Acme, Inc",person@example.test\nOther,other@example.test'
        scenario = field_matchmaker.parse_csv(csv_text)
        board = field_matchmaker.board_payload(scenario, api_key="secret", transport=lambda raw, key: column_body({
            "c0": ("company_name", 0.9), "c1": ("contact_email", 0.95),
        }))
        self.assertFalse(board["has_labels"])
        self.assertEqual(board["columns"][0]["samples"], ("Acme, Inc", "Other"))
        self.assertIsNone(board["columns"][0]["label"])
        self.assertEqual(board["columns"][0]["jev"]["target"], "company_name")
        body = {"csv": csv_text, "choices": [
            {"header": "Organisation", "target_id": "company_name"},
            {"header": "Email", "target_id": "contact_email"},
        ]}
        status, result, _ = field_matchmaker.route("POST", "/api/preview", json.dumps(body).encode())
        self.assertEqual(status, 200)
        self.assertEqual(result["preview"][0]["samples"], ["Acme, Inc", "Other"])
        body["choices"][1]["target_id"] = "company_name"
        _, result, _ = field_matchmaker.route("POST", "/api/preview", json.dumps(body).encode())
        self.assertEqual(result["decision"], "CONFLICT")
        self.assertEqual(result["preview"], [])
        self.assertNotIn("custom", field_matchmaker.SCENARIOS)

    def test_custom_input_bounds_and_invalid_shapes(self):
        for value in [None, "", "Header", "A,A\n1,2", "A,B\n1", 'A\n"unfinished',
                      "A\n" + "x" * 501, "A\n" + "1\n" * 21,
                      ",".join(str(i) for i in range(11)) + "\n" + ",".join("1" for _ in range(11)),
                      "x" * 12001]:
            with self.subTest(value=str(value)[:40]):
                status, _, _ = field_matchmaker.route("POST", "/api/board", json.dumps({"csv": value}).encode())
                self.assertEqual(status, 400)
        status, _, _ = field_matchmaker.route("POST", "/api/board", b"x" * 64001)
        self.assertEqual(status, 413)
        status, _, _ = field_matchmaker.route("POST", "/api/board", b"\xff")
        self.assertEqual(status, 400)

    def test_fixture_loading_never_calls_jev_and_round_trips_csv(self):
        with mock.patch.object(field_matchmaker, "post_jev", side_effect=AssertionError("called Jev")):
            status, result, _ = field_matchmaker.route("GET", "/api/fixture?id=vendor_csv")
        self.assertEqual(status, 200)
        parsed = field_matchmaker.parse_csv(result["csv"])
        self.assertEqual(parsed.columns[0].header, "Trading name")
        self.assertEqual(parsed.columns[0].samples, ("Northwind", "Acme Ltd", "Bright Studio"))

    def test_custom_board_route_keeps_credentials_server_side(self):
        with mock.patch.dict("os.environ", {"TYPESAFE_API_KEY": "secret"}):
            with mock.patch.object(field_matchmaker, "post_jev", return_value=(json.loads(column_body({"c0": ("country", 0.9)})), None)) as post:
                status, result, _ = field_matchmaker.route("POST", "/api/board", b'{"csv":"Nation\\nDK"}')
        self.assertEqual(status, 200)
        self.assertEqual(result["engine"], "live_jev")
        self.assertEqual(post.call_args.args[1], "secret")
        self.assertNotIn("secret", json.dumps(result))


def column_body(readings: dict[str, tuple[str, float]]) -> bytes:
    answers = {}
    for key, (choice, confidence) in readings.items():
        answers[key] = {
            "type": "choice",
            "choice": choice,
            "probabilities": {choice: 1.0},
            "confidence": confidence,
        }
    return json.dumps({"model": "jev-1.13.0", "answers": answers}).encode()

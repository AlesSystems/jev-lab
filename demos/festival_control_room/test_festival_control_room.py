import importlib.util
import json
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

path = Path(__file__).with_name("festival_control_room.py")


def input_crews():
    return [{k: c[k] for k in ("id", "x", "y", "enabled")} for c in room.CREWS]


spec = importlib.util.spec_from_file_location("festival_control_room", path)
assert spec and spec.loader
room = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = room
spec.loader.exec_module(room)


class ControlRoomTests(unittest.TestCase):
    def test_queue_waits_and_never_double_books(self):
        crews = [{**c, "enabled": c["id"] == "med_a"} for c in input_crews()]
        plan = room.make_plan("fixture", crews)
        medical = [
            a
            for a in plan["assignments"]
            if plan["judgments"][a["report_id"]]["team"] == "medical"
        ]
        assigned = [a for a in medical if a["status"] == "assigned"]
        self.assertGreaterEqual(len(assigned), 2)
        self.assertTrue(
            all(
                assigned[i + 1]["dispatch_at"] >= assigned[i]["clear_at"]
                for i in range(len(assigned) - 1)
            )
        )

    def test_default_east_medical_report_moves_while_waiting_for_crew(self):
        default = room.make_plan("fixture", input_crews())
        report = next(r for r in default["reports"] if r["id"] == "medical_east")
        assignment = next(a for a in default["assignments"] if a["report_id"] == report["id"])
        self.assertGreater(assignment["dispatch_at"], report["move_until"])
        self.assertNotEqual(room.position(report, 70), room.position(report, 100))
        staffed = input_crews()
        next(c for c in staffed if c["id"] == "med_b")["enabled"] = True
        enabled = room.make_plan("fixture", staffed)
        prompt = next(a for a in enabled["assignments"] if a["report_id"] == report["id"])
        self.assertEqual(prompt["dispatch_at"], report["at"])
        self.assertLess(prompt["arrive_at"], assignment["arrive_at"])
        self.assertEqual(default["judgments"], enabled["judgments"])

    def test_staffing_changes_schedule_not_judgments(self):
        original = room.make_plan("fixture", input_crews())
        crews = [{**c, "enabled": False} for c in input_crews()]
        empty = room.make_plan("fixture", crews)
        self.assertEqual(original["reports"], empty["reports"])
        self.assertEqual(original["judgments"], empty["judgments"])
        self.assertEqual(empty["summary"]["assigned"], 0)
        self.assertGreater(original["summary"]["assigned"], 0)

    def test_boundary_and_static_allowlist(self):
        bad = {"mode": "fixture", "crews": input_crews()}
        bad["crews"][0]["x"] = True
        self.assertEqual(
            room.route("POST", "/api/plan", json.dumps(bad).encode())[0], 400
        )
        self.assertEqual(room.route("GET", "/../field_matchmaker.py")[0], 404)
        self.assertEqual(room.route("POST", "/api/plan", b"{}")[0], 400)

    def test_missing_key_and_malformed_model_fail_closed(self):
        request = {"mode": "live", "crews": input_crews()}
        self.assertEqual(
            room.make_plan("live", request["crews"], api_key=None)["error"],
            "Live Jev requires TYPESAFE_API_KEY.",
        )
        with self.assertRaises(room.ResponseError):
            room.parse_jev({"model": "jev-latest", "answers": {}}, room.REPORTS)

    def test_live_success_is_cached_and_staffing_replays(self):
        room.LIVE_CACHE = None
        calls = []

        def transport(body, key):
            calls.append((json.loads(body), key))
            answers = {}
            for report in room.REPORTS:
                rid = report["id"]
                answers[rid + "_urgency"] = {
                    "type": "score",
                    "score": 2.5,
                    "confidence": 0.9,
                    "probabilities": {"0": 0, "1": 0, "2": 0.5, "3": 0.5},
                }
                answers[rid + "_team"] = {
                    "type": "choice",
                    "choice": "medical",
                    "confidence": 0.9,
                    "probabilities": {
                        "medical": 1,
                        "security": 0,
                        "welfare": 0,
                        "operations": 0,
                        "none": 0,
                    },
                }
                answers[rid + "_evidence"] = {"type": "noul", "noul": 0.9}
            return json.dumps({"model": "jev-1.13.0", "answers": answers}).encode()

        try:
            first = room.make_plan("live", input_crews(), "secret", transport)
            second = room.make_plan(
                "live",
                [{**c, "enabled": False} for c in input_crews()],
                "secret",
                transport,
            )
            self.assertEqual(len(calls), 1)
            self.assertEqual(first["judgments"], second["judgments"])
            self.assertGreater(
                first["summary"]["assigned"], second["summary"]["assigned"]
            )
            self.assertEqual(calls[0][1], "secret")
            self.assertNotIn("secret", json.dumps(calls[0][0]))
            self.assertEqual(len(calls[0][0]["questions"]), 24)
            self.assertNotIn("reports", calls[0][0]["state"])
            self.assertNotIn("secret", json.dumps(first))
        finally:
            room.LIVE_CACHE = None

    def test_bad_live_values_and_transport_fail_closed(self):
        with self.assertRaises(room.ResponseError):
            room.parse_jev(
                {
                    "model": "jev",
                    "answers": {
                        "medical_north_urgency": {"type": "score", "score": True}
                    },
                }
            )
        room.LIVE_CACHE = None
        with self.assertRaises(room.ResponseError):
            room.live_judgments("secret", lambda _body, _key: b"{}")
        self.assertIsNone(room.LIVE_CACHE)

    def test_pending_urgency_and_review_do_not_dispatch(self):
        judgments = {k: dict(v) for k, v in room.FIXTURE.items()}
        judgments["smoke_rumor"]["team_confidence"] = 0.3
        assignments, _ = room.simulate(room.validate_crews(input_crews()), judgments)
        by_id = {a["report_id"]: a for a in assignments}
        self.assertEqual(by_id["smoke_rumor"]["status"], "review")
        self.assertIsNone(by_id["smoke_rumor"]["crew_id"])
        self.assertEqual(by_id["medical_north"]["escalation"], "escalate")
        self.assertEqual(by_id["smoke_rumor"]["escalation"], "not_supported")

    def test_queued_reports_choose_urgency_at_release_not_future(self):
        from unittest import mock

        base = room.REPORTS[0]
        reports = (
            {
                **base,
                "id": "first",
                "at": 0,
                "service_seconds": 100,
                "x": 430,
                "y": 300,
                "end_x": 430,
                "end_y": 300,
            },
            {
                **base,
                "id": "low",
                "at": 1,
                "service_seconds": 10,
                "x": 430,
                "y": 300,
                "end_x": 430,
                "end_y": 300,
            },
            {
                **base,
                "id": "high",
                "at": 2,
                "service_seconds": 10,
                "x": 430,
                "y": 300,
                "end_x": 430,
                "end_y": 300,
            },
            {
                **base,
                "id": "future",
                "at": 111,
                "service_seconds": 10,
                "x": 430,
                "y": 300,
                "end_x": 430,
                "end_y": 300,
            },
        )
        reads = {
            rid: {
                "urgency": urgency,
                "urgency_confidence": 0.9,
                "team": "medical",
                "team_confidence": 0.9,
                "evidence": 0.9,
            }
            for rid, urgency in [("first", 3), ("low", 1), ("high", 2), ("future", 3)]
        }
        crews = room.validate_crews(
            [{**c, "enabled": c["id"] == "med_a"} for c in input_crews()]
        )
        with mock.patch.object(room, "REPORTS", reports):
            assignments, _ = room.simulate(crews, reads)
        by_id = {a["report_id"]: a for a in assignments}
        self.assertLess(by_id["high"]["dispatch_at"], by_id["low"]["dispatch_at"])
        self.assertLess(by_id["high"]["dispatch_at"], by_id["future"]["dispatch_at"])

    def test_same_plan_replays_and_repositioning_shortens_real_travel(self):
        first = room.make_plan("fixture", input_crews())
        self.assertEqual(first, room.make_plan("fixture", input_crews()))
        moved = input_crews()
        moved[0].update(x=180, y=145)
        shorter = room.make_plan("fixture", moved)
        original = next(
            a for a in first["assignments"] if a["report_id"] == "medical_north"
        )
        closer = next(
            a for a in shorter["assignments"] if a["report_id"] == "medical_north"
        )
        self.assertEqual(closer["arrive_at"] - closer["dispatch_at"], 10)
        self.assertGreater(original["arrive_at"], closer["arrive_at"])
        self.assertEqual(first["judgments"], shorter["judgments"])

    def test_full_live_response_rejects_nonfinite_bool_and_huge_numbers(self):
        answers = {}
        for report in room.REPORTS:
            rid = report["id"]
            answers[rid + "_urgency"] = {
                "type": "score",
                "score": 2.5,
                "confidence": 0.9,
                "probabilities": {"0": 0, "1": 0, "2": 0.5, "3": 0.5},
            }
            answers[rid + "_team"] = {
                "type": "choice",
                "choice": "medical",
                "confidence": 0.9,
                "probabilities": {
                    "medical": 1,
                    "security": 0,
                    "welfare": 0,
                    "operations": 0,
                    "none": 0,
                },
            }
            answers[rid + "_evidence"] = {"type": "noul", "noul": 0.9}
        for invalid in (float("nan"), float("inf"), True, 10**1000):
            with self.subTest(value=str(invalid)[:20]):
                answers["medical_north_urgency"]["score"] = invalid
                with self.assertRaises(room.ResponseError):
                    room.parse_jev({"model": "jev-1.13.0", "answers": answers})
        room.LIVE_CACHE = None
        with self.assertRaises(room.ResponseError):
            room.live_judgments(
                "secret", lambda _body, _key: (_ for _ in ()).throw(TimeoutError())
            )
        self.assertIsNone(room.LIVE_CACHE)

    def test_live_choice_and_score_must_agree_with_distributions(self):
        answers = {}
        for report in room.REPORTS:
            rid = report["id"]
            answers[rid + "_urgency"] = {
                "type": "score",
                "score": 2.5,
                "confidence": 0.9,
                "probabilities": {"0": 0, "1": 0, "2": 0.5, "3": 0.5},
            }
            answers[rid + "_team"] = {
                "type": "choice",
                "choice": "medical",
                "confidence": 0.9,
                "probabilities": {
                    "medical": 1,
                    "security": 0,
                    "welfare": 0,
                    "operations": 0,
                    "none": 0,
                },
            }
            answers[rid + "_evidence"] = {"type": "noul", "noul": 0.9}
        payload = {"model": "jev-1.13.0", "answers": answers}
        self.assertEqual(room.parse_jev(payload)[1]["medical_north"]["team"], "medical")
        answers["medical_north_team"]["probabilities"] = {
            "medical": 0,
            "security": 1,
            "welfare": 0,
            "operations": 0,
            "none": 0,
        }
        with self.assertRaises(room.ResponseError):
            room.parse_jev(payload)
        answers["medical_north_team"]["probabilities"] = {
            "medical": 1,
            "security": 0,
            "welfare": 0,
            "operations": 0,
            "none": 0,
        }
        answers["medical_north_urgency"].update(
            score=3, probabilities={"0": 1, "1": 0, "2": 0, "3": 0}
        )
        with self.assertRaises(room.ResponseError):
            room.parse_jev(payload)

    def test_http_handler_rejects_cross_origin_and_plain_text(self):
        server = room.ThreadingHTTPServer(("127.0.0.1", 0), room.Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/api/plan"
            data = json.dumps({"mode": "fixture", "crews": input_crews()}).encode()
            good = urllib.request.Request(
                url, data, {"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(good, timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.load(response)["mode"], "fixture")
            for headers in (
                {"Content-Type": "text/plain"},
                {"Content-Type": "application/json", "Origin": "https://other.example"},
            ):
                with (
                    self.subTest(headers=headers),
                    self.assertRaises(urllib.error.HTTPError) as caught,
                ):
                    urllib.request.urlopen(
                        urllib.request.Request(url, data, headers), timeout=3
                    )
                self.assertEqual(caught.exception.code, 400)
                caught.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)

    def test_scenario_contract(self):
        status, body, _ = room.route("GET", "/api/scenario")
        self.assertEqual(status, 200)
        self.assertEqual(len(body["reports"]), 8)
        self.assertEqual(len(body["crews"]), 6)
        self.assertEqual(body["duration"], 1200)

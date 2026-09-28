from __future__ import annotations

import argparse
import json
import math
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, TypedDict, cast
from urllib.parse import urlparse


class Report(TypedDict):
    id: str
    at: int
    title: str
    text: str
    zone: str
    x: int
    y: int
    end_x: int
    end_y: int
    move_until: int
    service_seconds: int


class Crew(TypedDict):
    id: str
    name: str
    specialty: str
    x: float
    y: float
    enabled: bool


class Judgment(TypedDict):
    urgency: float
    urgency_confidence: float
    team: str
    team_confidence: float
    evidence: float


class Assignment(TypedDict):
    report_id: str
    crew_id: str | None
    dispatch_at: float | None
    arrive_at: float | None
    clear_at: float | None
    from_x: float | None
    from_y: float | None
    to_x: float
    to_y: float
    status: str
    reason: str
    escalation: str


STATIC = Path(__file__).with_name("static")
FILES = {
    "index.html": "text/html; charset=utf-8",
    "app.css": "text/css; charset=utf-8",
    "app.js": "text/javascript; charset=utf-8",
}
MODEL = "jev-latest"
ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MAX_REQUEST = 16_384
MAX_RESPONSE = 1_000_000
SPECIALTIES = ("medical", "security", "welfare", "operations")
ZONES = (
    {"id": "north", "name": "North stage", "x": 225, "y": 150},
    {"id": "east", "name": "East lawn", "x": 740, "y": 180},
    {"id": "center", "name": "Main concourse", "x": 505, "y": 360},
    {"id": "south", "name": "South gate", "x": 510, "y": 585},
    {"id": "west", "name": "West market", "x": 235, "y": 420},
    {"id": "lake", "name": "Waterfront", "x": 790, "y": 500},
)
CREWS: tuple[Crew, ...] = (
    {
        "id": "med_a",
        "name": "Medical A",
        "specialty": "medical",
        "x": 430,
        "y": 300,
        "enabled": True,
    },
    {
        "id": "med_b",
        "name": "Medical B",
        "specialty": "medical",
        "x": 750,
        "y": 330,
        "enabled": True,
    },
    {
        "id": "sec_a",
        "name": "Security A",
        "specialty": "security",
        "x": 380,
        "y": 560,
        "enabled": True,
    },
    {
        "id": "sec_b",
        "name": "Security B",
        "specialty": "security",
        "x": 700,
        "y": 250,
        "enabled": True,
    },
    {
        "id": "welfare",
        "name": "Welfare",
        "specialty": "welfare",
        "x": 270,
        "y": 380,
        "enabled": True,
    },
    {
        "id": "ops",
        "name": "Operations",
        "specialty": "operations",
        "x": 580,
        "y": 490,
        "enabled": True,
    },
)
REPORTS: tuple[Report, ...] = (
    {
        "id": "medical_north",
        "at": 0,
        "title": "Guest collapses near stage",
        "text": "Steward reports a guest collapsed and is unresponsive beside the North stage barrier.",
        "zone": "north",
        "x": 180,
        "y": 145,
        "end_x": 195,
        "end_y": 155,
        "move_until": 110,
        "service_seconds": 240,
    },
    {
        "id": "medical_east",
        "at": 52,
        "title": "Breathing difficulty",
        "text": "Guest at East lawn is struggling to breathe; companion requests medical help.",
        "zone": "east",
        "x": 780,
        "y": 175,
        "end_x": 750,
        "end_y": 195,
        "move_until": 120,
        "service_seconds": 210,
    },
    {
        "id": "smoke_rumor",
        "at": 175,
        "title": "Possible smoke",
        "text": "A guest heard someone say there might be smoke near the West market. No smell or visible smoke reported.",
        "zone": "west",
        "x": 225,
        "y": 395,
        "end_x": 255,
        "end_y": 410,
        "move_until": 240,
        "service_seconds": 150,
    },
    {
        "id": "lost_child",
        "at": 265,
        "title": "Child separated",
        "text": "Steward is with a child separated from their guardian at the South gate. Child is safe and waiting.",
        "zone": "south",
        "x": 490,
        "y": 590,
        "end_x": 510,
        "end_y": 580,
        "move_until": 335,
        "service_seconds": 180,
    },
    {
        "id": "water",
        "at": 390,
        "title": "Guest near water edge",
        "text": "Eyewitness sees a guest slip into shallow water at the waterfront and calls for immediate help.",
        "zone": "lake",
        "x": 800,
        "y": 510,
        "end_x": 820,
        "end_y": 525,
        "move_until": 440,
        "service_seconds": 230,
    },
    {
        "id": "barrier",
        "at": 510,
        "title": "Barrier leaning into crowd",
        "text": "Two stewards see a temporary crowd barrier leaning into the North stage walkway.",
        "zone": "north",
        "x": 255,
        "y": 175,
        "end_x": 245,
        "end_y": 185,
        "move_until": 570,
        "service_seconds": 170,
    },
    {
        "id": "spill",
        "at": 700,
        "title": "Slippery food spill",
        "text": "Vendor reports a large drink spill across the Main concourse path; guests are walking around it.",
        "zone": "center",
        "x": 540,
        "y": 375,
        "end_x": 545,
        "end_y": 375,
        "move_until": 740,
        "service_seconds": 150,
    },
    {
        "id": "smoke_seen",
        "at": 890,
        "title": "Visible smoke at market",
        "text": "Two stewards see smoke rising from behind a West market food stall and smell burning plastic.",
        "zone": "west",
        "x": 285,
        "y": 440,
        "end_x": 290,
        "end_y": 445,
        "move_until": 940,
        "service_seconds": 240,
    },
)
FIXTURE: dict[str, Judgment] = {
    "medical_north": {
        "urgency": 2.95,
        "urgency_confidence": 0.96,
        "team": "medical",
        "team_confidence": 0.97,
        "evidence": 0.94,
    },
    "medical_east": {
        "urgency": 2.85,
        "urgency_confidence": 0.93,
        "team": "medical",
        "team_confidence": 0.95,
        "evidence": 0.91,
    },
    "smoke_rumor": {
        "urgency": 1.35,
        "urgency_confidence": 0.71,
        "team": "security",
        "team_confidence": 0.66,
        "evidence": 0.18,
    },
    "lost_child": {
        "urgency": 1.8,
        "urgency_confidence": 0.87,
        "team": "welfare",
        "team_confidence": 0.93,
        "evidence": 0.83,
    },
    "water": {
        "urgency": 2.9,
        "urgency_confidence": 0.91,
        "team": "security",
        "team_confidence": 0.82,
        "evidence": 0.95,
    },
    "barrier": {
        "urgency": 2.5,
        "urgency_confidence": 0.89,
        "team": "operations",
        "team_confidence": 0.88,
        "evidence": 0.9,
    },
    "spill": {
        "urgency": 1.3,
        "urgency_confidence": 0.84,
        "team": "operations",
        "team_confidence": 0.91,
        "evidence": 0.88,
    },
    "smoke_seen": {
        "urgency": 2.7,
        "urgency_confidence": 0.88,
        "team": "security",
        "team_confidence": 0.9,
        "evidence": 0.96,
    },
}
LIVE_CACHE: tuple[str, dict[str, Judgment], float] | None = None
CACHE_LOCK = threading.Lock()  # ponytail: one global call lock; split by source if concurrent live throughput matters.


class ResponseError(ValueError):
    pass


def number(value: object, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ResponseError("invalid numeric value")
    try:
        result = float(value)
    except OverflowError as error:
        raise ResponseError("numeric value out of range") from error
    if not math.isfinite(result) or not low <= result <= high:
        raise ResponseError("numeric value out of range")
    return result


def validate_crews(value: object) -> list[Crew]:
    if not isinstance(value, list) or len(value) != len(CREWS):
        raise ValueError("Include each crew exactly once.")
    catalog = {crew["id"]: crew for crew in CREWS}
    seen = set()
    result: list[Crew] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"id", "x", "y", "enabled"}:
            raise ValueError("Each crew needs id, x, y and enabled.")
        crew_id = item["id"]
        if not isinstance(crew_id, str) or crew_id not in catalog or crew_id in seen:
            raise ValueError("Unknown or duplicate crew.")
        seen.add(crew_id)
        if not isinstance(item["enabled"], bool):
            raise TypeError("Crew enabled must be boolean.")
        try:
            x = number(item["x"], 0, 1000)
            y = number(item["y"], 0, 700)
        except ResponseError as error:
            raise ValueError(str(error)) from error
        result.append({**catalog[crew_id], "x": x, "y": y, "enabled": item["enabled"]})
    return [next(crew for crew in result if crew["id"] == c["id"]) for c in CREWS]


def questions() -> dict[str, Any]:
    result = {}
    for report in REPORTS:
        rid = report["id"]
        context = {"report": {"title": report["title"], "text": report["text"]}}
        result[rid + "_urgency"] = {
            "type": "score",
            "instructions": {
                **context,
                "question": "How urgently does `report` need a festival team response based only on the report text?",
            },
            "criteria": [
                "No team response is justified by this report.",
                "A routine amenity or service issue can wait while the festival continues.",
                "A credible safety or welfare problem needs a team soon, but no immediate danger is described.",
                "A person faces immediate serious harm or a hazard is actively threatening guests.",
            ],
        }
        result[rid + "_team"] = {
            "type": "choice",
            "instructions": {
                **context,
                "question": "Which single festival team specialty best handles `report`, or none if no team is justified?",
            },
            "criteria": {
                "medical": "Illness or injury",
                "security": "Crowd, access, or immediate safety",
                "welfare": "Separated people or guest support",
                "operations": "Site equipment, cleaning, or infrastructure",
                "none": "No supported team selection",
            },
        }
        result[rid + "_evidence"] = {
            "type": "noul",
            "instructions": {
                **context,
                "question": "Does `report` contain sufficiently direct, concrete evidence of a safety hazard to escalate to a supervisor now?",
            },
            "criteria": {
                "true": "Direct witness or clear observed hazard",
                "false": "Rumor, uncertain claim, or no safety hazard",
            },
        }
    return result


def validate_distribution(value: object, keys: tuple[str, ...]) -> None:
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ResponseError("Invalid Jev distribution.")
    total = sum(number(value[key], 0, 1) for key in keys)
    if not 0.98 <= total <= 1.02:
        raise ResponseError("Invalid Jev distribution.")


def parse_jev(
    payload: object, reports: tuple[Report, ...] = REPORTS
) -> tuple[str, dict[str, Judgment]]:
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("model"), str)
        or not payload["model"].strip()
        or not isinstance(payload.get("answers"), dict)
    ):
        raise ResponseError("Invalid Jev response.")
    answers = payload["answers"]
    result = {}
    for report in reports:
        rid = report["id"]
        score, choice, noul = (
            answers.get(rid + suffix) for suffix in ("_urgency", "_team", "_evidence")
        )
        if (
            not all(isinstance(a, dict) for a in (score, choice, noul))
            or score.get("type") != "score"
            or choice.get("type") != "choice"
            or noul.get("type") != "noul"
        ):
            raise ResponseError("Invalid Jev answer.")
        team = choice.get("choice")
        if team not in (*SPECIALTIES, "none"):
            raise ResponseError("Invalid Jev team.")
        validate_distribution(score.get("probabilities"), ("0", "1", "2", "3"))
        validate_distribution(choice.get("probabilities"), (*SPECIALTIES, "none"))
        result[rid] = {
            "urgency": number(score.get("score"), 0, 3),
            "urgency_confidence": number(score.get("confidence"), 0, 1),
            "team": team,
            "team_confidence": number(choice.get("confidence"), 0, 1),
            "evidence": number(noul.get("noul"), 0, 1),
        }
    return cast(str, payload["model"]), cast(dict[str, Judgment], result)


def live_judgments(
    api_key: str, transport=None
) -> tuple[str, dict[str, Judgment], float]:
    global LIVE_CACHE
    with CACHE_LOCK:
        if LIVE_CACHE is not None:
            return LIVE_CACHE
        body = json.dumps(
            {
                "model": MODEL,
                "state": {
                    "context": "Synthetic festival incident reports. Judge each report from its own supplied text only; later reports are independent."
                },
                "questions": questions(),
            }
        ).encode()
        started = time.perf_counter()
        try:
            if transport is None:
                request = urllib.request.Request(
                    ENDPOINT,
                    body,
                    {
                        "Authorization": "Bearer " + api_key,
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=30) as response:
                    raw = response.read(MAX_RESPONSE + 1)
            else:
                raw = transport(body, api_key)
            if not isinstance(raw, bytes) or len(raw) > MAX_RESPONSE:
                raise ResponseError("Jev response is too large.")
            model, judgments = parse_jev(json.loads(raw))
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
            UnicodeError,
        ) as error:
            raise ResponseError(
                "Live Jev is unavailable or returned an invalid response."
            ) from error
        LIVE_CACHE = (model, judgments, (time.perf_counter() - started) * 1000)
        return LIVE_CACHE


def position(report: Report, at: float) -> tuple[float, float]:
    span = report["move_until"] - report["at"]
    progress = min(1.0, max(0.0, (at - report["at"]) / span)) if span > 0 else 1.0
    return (
        report["x"] + (report["end_x"] - report["x"]) * progress,
        report["y"] + (report["end_y"] - report["y"]) * progress,
    )


def simulate(
    crews: list[Crew], judgments: dict[str, Judgment]
) -> tuple[list[Assignment], int]:
    state = {
        c["id"]: {"x": c["x"], "y": c["y"], "free": 0.0} for c in crews if c["enabled"]
    }
    pending = list(REPORTS)
    result: dict[str, Assignment] = {}
    now = 0.0
    while pending:
        future = [r["at"] for r in pending if r["at"] > now]
        if not any(r["at"] <= now for r in pending):
            now = min(future)
        available_reports = sorted(
            (r for r in pending if r["at"] <= now),
            key=lambda r: (-judgments[r["id"]]["urgency"], r["at"], r["id"]),
        )
        progress = False
        for report in available_reports:
            judgment = judgments[report["id"]]
            rid = report["id"]
            escalation = (
                "escalate"
                if judgment["evidence"] >= 0.8
                else "review"
                if judgment["evidence"] >= 0.4
                else "not_supported"
            )
            to_x, to_y = position(report, now)
            base: Assignment = {
                "report_id": rid,
                "crew_id": None,
                "dispatch_at": None,
                "arrive_at": None,
                "clear_at": None,
                "from_x": None,
                "from_y": None,
                "to_x": to_x,
                "to_y": to_y,
                "status": "unassigned",
                "reason": "No enabled specialist available.",
                "escalation": escalation,
            }
            if (
                judgment["team"] == "none"
                or min(judgment["team_confidence"], judgment["urgency_confidence"])
                < 0.6
            ):
                result[rid] = cast(
                    Assignment,
                    {
                        **base,
                        "status": "review",
                        "reason": "Team or urgency needs review.",
                    },
                )
                pending.remove(report)
                progress = True
                continue
            candidates = [
                c
                for c in crews
                if c["enabled"]
                and c["specialty"] == judgment["team"]
                and state[c["id"]]["free"] <= now
            ]
            if not candidates:
                continue
            crew = min(
                candidates,
                key=lambda c: (
                    math.hypot(state[c["id"]]["x"] - to_x, state[c["id"]]["y"] - to_y),
                    c["id"],
                ),
            )
            here = state[crew["id"]]
            travel = max(10.0, math.hypot(here["x"] - to_x, here["y"] - to_y) / 2)
            arrive = now + travel
            clear = arrive + report["service_seconds"]
            result[rid] = cast(
                Assignment,
                {
                    **base,
                    "crew_id": crew["id"],
                    "dispatch_at": now,
                    "arrive_at": arrive,
                    "clear_at": clear,
                    "from_x": here["x"],
                    "from_y": here["y"],
                    "status": "assigned",
                    "reason": "Nearest available specialist.",
                },
            )
            here.update(x=to_x, y=to_y, free=clear)
            pending.remove(report)
            progress = True
        if not pending:
            break
        if progress:
            continue
        next_times = [r["at"] for r in pending if r["at"] > now] + [
            s["free"] for s in state.values() if s["free"] > now
        ]
        if next_times:
            now = min(next_times)
        else:
            for report in pending:
                judgment = judgments[report["id"]]
                x, y = position(report, now)
                result[report["id"]] = {
                    "report_id": report["id"],
                    "crew_id": None,
                    "dispatch_at": None,
                    "arrive_at": None,
                    "clear_at": None,
                    "from_x": None,
                    "from_y": None,
                    "to_x": x,
                    "to_y": y,
                    "status": "unassigned",
                    "reason": "No enabled specialist available.",
                    "escalation": "escalate"
                    if judgment["evidence"] >= 0.8
                    else "review"
                    if judgment["evidence"] >= 0.4
                    else "not_supported",
                }
            break
    assignments = [result[r["id"]] for r in REPORTS]
    duration = max(
        1200, math.ceil(max((a["clear_at"] or 0 for a in assignments), default=0))
    )
    return assignments, duration


def make_plan(
    mode: str, crews: object, api_key: str | None = None, transport=None
) -> dict[str, Any]:
    if mode not in ("fixture", "live"):
        raise ValueError("Choose fixture or live mode.")
    parsed_crews = validate_crews(crews)
    if mode == "live":
        key = api_key.strip() if isinstance(api_key, str) else ""
        if not key:
            return {"error": "Live Jev requires TYPESAFE_API_KEY."}
        model, judgments, elapsed = live_judgments(key, transport)
    else:
        model, judgments, elapsed = None, FIXTURE, None
    assignments, duration = simulate(parsed_crews, judgments)
    assigned = [a for a in assignments if a["status"] == "assigned"]
    arrival = {r["id"]: r["at"] for r in REPORTS}
    return {
        "mode": mode,
        "model": model,
        "reports": list(REPORTS),
        "crews": parsed_crews,
        "judgments": judgments,
        "assignments": assignments,
        "duration": duration,
        "summary": {
            "assigned": len(assigned),
            "unassigned": len(assignments) - len(assigned),
            "mean_response_seconds": round(
                sum(
                    cast(float, a["arrive_at"]) - arrival[a["report_id"]]
                    for a in assigned
                )
                / len(assigned),
                1,
            )
            if assigned
            else 0,
        },
        "elapsed_ms": round(elapsed, 1) if elapsed is not None else None,
    }


def route(
    method: str, path: str, body: bytes | None = None
) -> tuple[int, dict[str, Any] | bytes, str]:
    pathname = urlparse(path).path
    if method == "GET" and pathname == "/api/scenario":
        return (
            200,
            {
                "title": "Northline Festival",
                "duration": 1200,
                "live_available": bool(os.environ.get("TYPESAFE_API_KEY", "").strip()),
                "reports": list(REPORTS),
                "crews": list(CREWS),
                "zones": list(ZONES),
            },
            "application/json",
        )
    if method == "POST" and pathname == "/api/plan":
        if body is None or len(body) > MAX_REQUEST:
            return 400, {"error": "Invalid request size."}, "application/json"
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict) or set(payload) != {"mode", "crews"}:
                raise ValueError("Provide mode and crews.")
            plan = make_plan(
                payload["mode"], payload["crews"], os.environ.get("TYPESAFE_API_KEY")
            )
            return (503 if "error" in plan else 200), plan, "application/json"
        except (ValueError, TypeError, ResponseError) as error:
            if isinstance(error, ResponseError):
                return 503, {"error": str(error)}, "application/json"
            return (
                400,
                {
                    "error": str(error)
                    if isinstance(error, ValueError)
                    and not isinstance(error, json.JSONDecodeError)
                    else "Invalid JSON request."
                },
                "application/json",
            )
    if method == "GET":
        name = "index.html" if pathname == "/" else pathname.removeprefix("/")
        if name in FILES and (STATIC / name).is_file():
            return 200, (STATIC / name).read_bytes(), FILES[name]
        return 404, {"error": "Not found."}, "application/json"
    return 405, {"error": "Method not allowed."}, "application/json"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.respond(*route("GET", self.path))

    def do_POST(self) -> None:
        host = self.headers.get("Host", "")
        origin = self.headers.get("Origin")
        allowed = {
            f"127.0.0.1:{cast(tuple[str, int], self.server.server_address)[1]}",
            f"localhost:{cast(tuple[str, int], self.server.server_address)[1]}",
        }
        media = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if (
            host not in allowed
            or (
                origin is not None
                and origin not in {f"http://{name}" for name in allowed}
            )
            or media != "application/json"
        ):
            self.respond(
                400,
                {"error": "Invalid request origin or content type."},
                "application/json",
            )
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 <= length <= MAX_REQUEST:
                raise ValueError()
        except ValueError:
            self.respond(400, {"error": "Invalid request size."}, "application/json")
            return
        self.respond(*route("POST", self.path, self.rfile.read(length)))

    def respond(self, status: int, payload: dict[str, Any] | bytes, media: str) -> None:
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args: object) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["serve"])
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print("http://127.0.0.1:" + str(args.port), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

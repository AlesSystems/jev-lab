#!/usr/bin/env python3
"""Preview CSV header mappings against an alias baseline and fixture labels."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

STATIC = Path(__file__).with_name("static")
ALLOWED_FILES = {"index.html": "text/html; charset=utf-8", "app.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
TARGETS: tuple[tuple[str, str], ...] = (
    ("company_name", "Company name"),
    ("contact_email", "Contact email"),
    ("account_id", "Account id"),
    ("country", "Country"),
    ("annual_revenue", "Annual revenue"),
)
TARGET_IDS = {target_id for target_id, _label in TARGETS}
ALIASES: dict[str, frozenset[str]] = {
    "company_name": frozenset({"company name", "company", "legal name"}),
    "contact_email": frozenset({"email", "e-mail", "email address"}),
    "account_id": frozenset({"account id", "account", "acct"}),
    "country": frozenset({"country", "nation"}),
    "annual_revenue": frozenset({"revenue", "annual revenue"}),
}


@dataclass(frozen=True)
class Column:
    header: str
    samples: tuple[str, str, str]
    baseline: str | None
    label: str | None


@dataclass(frozen=True)
class Scenario:
    id: str
    title: str
    columns: tuple[Column, ...]


def normalize(header: str) -> str:
    return " ".join("".join(character.lower() if character.isalnum() else " " for character in header).split())


def baseline_target(header: str) -> str | None:
    key = normalize(header)
    for target_id, aliases in ALIASES.items():
        if key == target_id.replace("_", " ") or key in aliases:
            return target_id
    return None


def _column(header: str, samples: tuple[str, str, str], label: str | None) -> Column:
    return Column(header, samples, baseline_target(header), label)


SCENARIOS: dict[str, Scenario] = {
    "vendor_csv": Scenario(
        "vendor_csv",
        "Vendor file",
        (
            _column("Trading name", ("Northwind", "Acme Ltd", "Bright Studio"), "company_name"),
            _column("Work email", ("a@acme.test", "b@acme.test", "c@acme.test"), "contact_email"),
            _column("Account", ("4412", "north", "88"), None),
            _column("Country", ("US", "DE", "JP"), "country"),
            _column("Revenue", ("1200000", "400000", "90000"), "annual_revenue"),
        ),
    ),
    "name_conflict": Scenario(
        "name_conflict",
        "Two names",
        (
            _column("Legal name", ("Northwind", "Acme Ltd", "Bright Studio"), "company_name"),
            _column("Company", ("Northwind", "Acme Ltd", "Bright Studio"), "company_name"),
            _column("Email", ("a@acme.test", "b@acme.test", "c@acme.test"), "contact_email"),
        ),
    ),
    "clean_headers": Scenario(
        "clean_headers",
        "Clean headers",
        (
            _column("Company name", ("Northwind", "Acme Ltd", "Bright Studio"), "company_name"),
            _column("Email", ("a@acme.test", "b@acme.test", "c@acme.test"), "contact_email"),
            _column("Account id", ("4412", "4413", "4414"), "account_id"),
            _column("Country", ("US", "DE", "JP"), "country"),
            _column("Annual revenue", ("1200000", "400000", "90000"), "annual_revenue"),
        ),
    ),
}


def scenario_list() -> list[dict[str, str]]:
    return [{"id": scenario.id, "title": scenario.title} for scenario in SCENARIOS.values()]


def board_payload(scenario_id: str) -> dict[str, Any]:
    scenario = SCENARIOS[scenario_id]
    return {
        "id": scenario.id,
        "title": scenario.title,
        "targets": [{"id": target_id, "label": label} for target_id, label in TARGETS],
        "columns": [asdict(column) for column in scenario.columns],
        "note": "Scenario labels are fixtures. This page does not call Jev.",
    }


def assess(scenario_id: str, choices: object) -> dict[str, Any]:
    scenario = SCENARIOS[scenario_id]
    parsed = _choices(scenario, choices)
    picked = [target_id for _header, target_id in parsed]
    conflicts = tuple(sorted(target_id for target_id, count in Counter(target for target in picked if target).items() if count > 1))
    by_header = {header: target_id for header, target_id in parsed}
    split = any(by_header[column.header] != column.baseline for column in scenario.columns)
    if conflicts:
        decision = "CONFLICT"
        preview: list[dict[str, Any]] = []
    else:
        decision = "SPLIT" if split else "CLEAR"
        preview = [
            {
                "header": column.header,
                "target": by_header[column.header] or "unmapped",
                "samples": list(column.samples),
            }
            for column in scenario.columns
        ]
    return {"decision": decision, "conflicts": list(conflicts), "preview": preview}


def _choices(scenario: Scenario, choices: object) -> tuple[tuple[str, str | None], ...]:
    if not isinstance(choices, list):
        raise TypeError("invalid_choices")
    expected = [column.header for column in scenario.columns]
    parsed: list[tuple[str, str | None]] = []
    for item in choices:
        if not isinstance(item, Mapping):
            raise TypeError("invalid_choices")
        header = item.get("header")
        target_id = item.get("target_id")
        if not isinstance(header, str) or header not in expected:
            raise ValueError("unknown_header")
        if target_id is not None and (not isinstance(target_id, str) or target_id not in TARGET_IDS):
            raise ValueError("unknown_target")
        parsed.append((header, target_id))
    if [header for header, _target in parsed] != expected:
        raise ValueError("unknown_header")
    return tuple(parsed)


def resolve_static(name: str) -> Path | None:
    media = ALLOWED_FILES.get(name)
    if media is None:
        return None
    return STATIC / name


def route(method: str, path: str, body: bytes | None = None) -> tuple[int, dict[str, Any] | bytes, str]:
    parsed = urlparse(path)
    if method == "GET" and parsed.path == "/api/scenarios":
        return 200, {"scenarios": scenario_list()}, "application/json"
    if method == "GET" and parsed.path == "/api/board":
        scenario_id = (parse_qs(parsed.query).get("id") or [""])[0]
        try:
            return 200, board_payload(scenario_id), "application/json"
        except KeyError:
            return 404, {"error": "unknown_scenario"}, "application/json"
    if method == "POST" and parsed.path == "/api/preview":
        try:
            payload = json.loads(body or b"")
        except json.JSONDecodeError:
            return 400, {"error": "invalid_json"}, "application/json"
        if not isinstance(payload, Mapping):
            return 400, {"error": "invalid_json"}, "application/json"
        raw_id = payload.get("scenario_id")
        if not isinstance(raw_id, str) or raw_id not in SCENARIOS:
            return 404, {"error": "unknown_scenario"}, "application/json"
        try:
            return 200, assess(raw_id, payload.get("choices")), "application/json"
        except (TypeError, ValueError) as error:
            return 400, {"error": str(error)}, "application/json"
    if method == "GET":
        name = "index.html" if parsed.path == "/" else parsed.path.removeprefix("/")
        static = resolve_static(name)
        if static is None or not static.is_file():
            return 404, {"error": "not_found"}, "application/json"
        return 200, static.read_bytes(), ALLOWED_FILES[name]
    return 405, {"error": "method_not_allowed"}, "application/json"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._respond(*route("GET", self.path))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        self._respond(*route("POST", self.path, self.rfile.read(length)))

    def _respond(self, status: int, payload: dict[str, Any] | bytes, content_type: str) -> None:
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(port: int) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"http://127.0.0.1:{port}", flush=True)
    server.serve_forever()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview a CSV field mapping.")
    sub = parser.add_subparsers(dest="command", required=True)
    board = sub.add_parser("board")
    board.add_argument("scenario")
    preview = sub.add_parser("preview")
    preview.add_argument("scenario")
    preview.add_argument("choices")
    server = sub.add_parser("serve")
    server.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(args.port)
        return 0
    if args.command == "board":
        print(json.dumps(board_payload(args.scenario), indent=2))
        return 0
    print(json.dumps(assess(args.scenario, json.loads(args.choices)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

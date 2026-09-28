#!/usr/bin/env python3
"""Sort synthetic events into attention, review, and digest."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

STATIC = Path(__file__).with_name("static")
ALLOWED_FILES = {"index.html": "text/html; charset=utf-8", "app.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
LOOKUP = {
    "export_completed": "digest",
    "export_failed": "attention_now",
    "maintenance": "digest",
}
LANES = ("attention_now", "review", "digest")
LANE_TITLES = {"attention_now": "Attention now", "review": "Review", "digest": "Digest"}


@dataclass(frozen=True)
class Event:
    id: str
    event_type: str
    flag: str
    text: str
    baseline: str
    label: str


EVENTS = (
    Event("completed", "export_completed", "normal", "Your export completed.", "digest", "digest"),
    Event("handoff", "export_failed", "normal", "Your export failed. Your team cannot finish today's handoff.", "attention_now", "attention_now"),
    Event("smoke", "export_failed", "normal", "Nightly smoke export failed. No customer is waiting on it.", "attention_now", "digest"),
    Event("checkout", "maintenance", "normal", "Migration blocked. Checkout cannot take orders.", "digest", "attention_now"),
    Event("warnings", "export_completed", "normal", "Export finished with warnings.", "digest", "review"),
    Event("window", "maintenance", "normal", "Deploy finished. This is the expected maintenance window.", "digest", "digest"),
    Event("edge", "maintenance", "page", "Packet loss on the edge.", "digest", "digest"),
)


def shown_lane(raw: str, flag: str, quiet: bool) -> str:
    if flag == "page":
        return "attention_now"
    if quiet:
        return "digest"
    return raw


def inbox(quiet: bool) -> dict[str, Any]:
    columns: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
    for event in EVENTS:
        lane = shown_lane(event.label, event.flag, quiet)
        baseline = shown_lane(event.baseline, event.flag, quiet)
        note = "Priority flag holds this in attention now." if event.flag == "page" else f"baseline: {LANE_TITLES[baseline]}"
        columns[lane].append({
            "id": event.id,
            "text": event.text,
            "lane": lane,
            "baseline": baseline,
            "split": baseline != lane,
            "note": note,
        })
    splits = [event["id"] for column in columns.values() for event in column if event["split"]]
    if quiet:
        decision = "QUIET"
    elif splits:
        decision = "SPLIT"
    else:
        decision = "CLEAR"
    return {
        "quiet": quiet,
        "decision": decision,
        "preference": "Interrupt for blocked work. Otherwise digest.",
        "note": "Scenario lanes are fixtures. This page does not call Jev.",
        "columns": [
            {"id": lane, "title": LANE_TITLES[lane], "events": columns[lane]}
            for lane in LANES
        ],
    }


def resolve_static(name: str) -> Path | None:
    if name not in ALLOWED_FILES:
        return None
    return STATIC / name


def route(method: str, path: str) -> tuple[int, dict[str, Any] | bytes, str]:
    parsed = urlparse(path)
    if method != "GET":
        return 405, {"error": "method_not_allowed"}, "application/json"
    if parsed.path == "/api/inbox":
        raw = (parse_qs(parsed.query).get("quiet") or ["0"])[0]
        if raw not in {"0", "1"}:
            return 400, {"error": "invalid_quiet"}, "application/json"
        return 200, inbox(raw == "1"), "application/json"
    name = "index.html" if parsed.path == "/" else parsed.path.removeprefix("/")
    static = resolve_static(name)
    if static is None or not static.is_file():
        return 404, {"error": "not_found"}, "application/json"
    return 200, static.read_bytes(), ALLOWED_FILES[name]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status, payload, content_type = route("GET", self.path)
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
    parser = argparse.ArgumentParser(description="Sort events into an interruption budget.")
    sub = parser.add_subparsers(dest="command", required=True)
    board = sub.add_parser("inbox")
    board.add_argument("--quiet", action="store_true")
    server = sub.add_parser("serve")
    server.add_argument("--port", type=int, default=8767)
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(args.port)
        return 0
    print(json.dumps(inbox(args.quiet), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

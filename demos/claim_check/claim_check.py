#!/usr/bin/env python3
"""Compare a release claim with one evidence passage."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Sequence
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

STATIC = Path(__file__).with_name("static")
ALLOWED_FILES = {"index.html": "text/html; charset=utf-8", "app.css": "text/css; charset=utf-8", "app.js": "text/javascript; charset=utf-8"}
EVIDENCE = (
    "The CSV export path now writes rows in batches. Internal timing on the CSV fixture "
    "dropped from 4.2s to 1.1s. PDF and API exports were not measured."
)
STOP = frozenset(["a", "an", "the", "is", "are", "was", "were", "now", "from", "to", "of", "and", "or", "on", "in", "for", "with", "not"])
WORDS = {"supported": "SUPPORTED", "insufficient_evidence": "INSUFFICIENT", "contradicted": "CONTRADICTED"}


def tokens(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2 and token not in STOP)


def baseline(claim: str, evidence: str = EVIDENCE) -> dict[str, str]:
    overlap = sorted(set(tokens(claim)) & set(tokens(evidence)))
    if overlap:
        return {"verdict": "supported", "reason": "shared words: " + ", ".join(overlap)}
    return {"verdict": "insufficient_evidence", "reason": "no shared words"}


SCENARIOS: dict[str, dict[str, str]] = {
    "csv_faster": {
        "title": "CSV exports",
        "claim": "CSV exports are faster",
        "verdict": "supported",
        "reason": "The passage times the CSV export path.",
    },
    "all_faster": {
        "title": "All exports",
        "claim": "All exports are faster",
        "verdict": "insufficient_evidence",
        "reason": "The passage does not measure PDF or API exports.",
    },
    "slower": {
        "title": "Slower exports",
        "claim": "Exports are slower now",
        "verdict": "contradicted",
        "reason": "The passage reports a shorter CSV timing, not a slowdown.",
    },
}


def scenario_list() -> list[dict[str, str]]:
    return [{"id": scenario_id, "title": scenario["title"]} for scenario_id, scenario in SCENARIOS.items()]


def board_payload(scenario_id: str) -> dict[str, Any]:
    scenario = SCENARIOS[scenario_id]
    reading = baseline(scenario["claim"])
    return {
        "id": scenario_id,
        "title": scenario["title"],
        "claim": scenario["claim"],
        "evidence": EVIDENCE,
        "baseline": reading,
        "label": {"verdict": scenario["verdict"], "reason": scenario["reason"]},
        "decision": WORDS[scenario["verdict"]],
        "split": reading["verdict"] != scenario["verdict"],
        "note": "Scenario labels are fixtures. This page does not call Jev.",
    }


def resolve_static(name: str) -> Path | None:
    if name not in ALLOWED_FILES:
        return None
    return STATIC / name


def route(method: str, path: str) -> tuple[int, dict[str, Any] | bytes, str]:
    parsed = urlparse(path)
    if method != "GET":
        return 405, {"error": "method_not_allowed"}, "application/json"
    if parsed.path == "/api/scenarios":
        return 200, {"scenarios": scenario_list()}, "application/json"
    if parsed.path == "/api/board":
        scenario_id = (parse_qs(parsed.query).get("id") or [""])[0]
        try:
            return 200, board_payload(scenario_id), "application/json"
        except KeyError:
            return 404, {"error": "unknown_scenario"}, "application/json"
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
    parser = argparse.ArgumentParser(description="Check one release claim against one passage.")
    sub = parser.add_subparsers(dest="command", required=True)
    board = sub.add_parser("board")
    board.add_argument("scenario")
    server = sub.add_parser("serve")
    server.add_argument("--port", type=int, default=8766)
    args = parser.parse_args(argv)
    if args.command == "serve":
        serve(args.port)
        return 0
    print(json.dumps(board_payload(args.scenario), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

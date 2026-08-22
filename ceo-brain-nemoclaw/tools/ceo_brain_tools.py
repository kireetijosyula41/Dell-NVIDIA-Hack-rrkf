#!/usr/bin/env python3
"""Read-only CLI facade for a NemoClaw sandbox to query CEO Brain evidence."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request


BASE_URL = os.getenv("CEO_BRAIN_API_URL", "http://host.docker.internal:8080").rstrip("/")


def post(path: str, payload: dict) -> None:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        print(json.dumps(json.loads(response.read().decode("utf-8")), indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Query the CEO Brain read-only evidence API.")
    parser.add_argument("tool", choices=("search-projects", "search-emails", "get-graph-neighborhood", "get-github-evidence", "create-audit-warning"))
    parser.add_argument("--query", required=True)
    parser.add_argument("--project-id", action="append", default=[])
    parser.add_argument("--warning-json", help="Path to final agent warning JSON for create-audit-warning.")
    args = parser.parse_args()
    if args.tool == "create-audit-warning":
        if not args.warning_json:
            parser.error("--warning-json is required for create-audit-warning")
        payload = json.loads(open(args.warning_json, encoding="utf-8").read())
    else:
        payload = {"query": args.query, "projectIds": args.project_id}
    post(f"/tools/{args.tool}", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

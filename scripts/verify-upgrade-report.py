#!/usr/bin/env python3
import pathlib
import re
import sys


def main() -> int:
    report = pathlib.Path(sys.argv[1])
    text = report.read_text(encoding="utf-8")
    required = (
        "# Xiaozhi Server v0.9.6 Upgrade Report",
        "## Current state",
        "## Compatibility boundary",
        "## Model recommendation",
        "## Rollout",
        "## Observation gates",
        "## Rollback",
        "xiaozhi-server:0.9.6-candidate-20260814",
        "xiaozhi-server:20260813-secure",
        "manager web/API",
        "0.9.1",
        "v0.9.6",
    )
    missing = [item for item in required if item not in text]
    if missing:
        raise SystemExit(f"missing report evidence: {missing}")
    if not re.search(r"sha256:[0-9a-f]{64}", text):
        raise SystemExit("missing immutable candidate image id")
    if "docker compose" not in text or "docker image inspect" not in text:
        raise SystemExit("missing executable rollout or rollback verification")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

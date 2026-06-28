#!/usr/bin/env python3
"""Resolve a PetHatch event to a pet animation.

Usage:
  python3 examples/event-resolver.py pets/xiaochai/pet.json quota.limit
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


FALLBACKS = {
    "agent.idle": "idle",
    "agent.running": "running",
    "agent.waiting": "waiting",
    "agent.review": "review",
    "agent.failed": "failed",
}


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: event-resolver.py PET_JSON EVENT_NAME", file=sys.stderr)
        return 2

    pet = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    event_name = sys.argv[2]
    event = pet.get("events", {}).get(event_name)
    if event:
        print(json.dumps(event, ensure_ascii=False, indent=2))
        return 0

    print(json.dumps({"animation": FALLBACKS.get(event_name, "idle"), "tone": "neutral"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

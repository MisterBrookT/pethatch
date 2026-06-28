#!/usr/bin/env python3
"""Validate the static gallery has the local files it references."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import sys


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for key in ("src", "href"):
            value = attr_map.get(key)
            if value:
                self.refs.append(value)


def local_ref(value: str) -> bool:
    parsed = urlparse(value)
    return not parsed.scheme and not parsed.netloc and not value.startswith("#")


def main() -> int:
    if not INDEX.exists():
        print("error: missing index.html", file=sys.stderr)
        return 1
    parser = RefParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    missing = []
    for ref in parser.refs:
        if not local_ref(ref):
            continue
        path = ROOT / ref.split("#", 1)[0]
        if not path.exists():
            missing.append(ref)
    if missing:
        for ref in missing:
            print(f"error: missing local site reference: {ref}", file=sys.stderr)
        return 1
    print("ok: validated static site")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate PetHatch pet packs without third-party dependencies."""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ANIMATIONS = [
    "idle",
    "running-right",
    "running-left",
    "waving",
    "jumping",
    "failed",
    "waiting",
    "running",
    "review",
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path}: {exc}")


def webp_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        fail(f"{path} is not a WebP file")
    chunk = data[12:16]
    if chunk == b"VP8X":
        if len(data) < 30:
            fail(f"{path} has a truncated VP8X header")
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 ":
        if len(data) < 30:
            fail(f"{path} has a truncated VP8 header")
        width, height = struct.unpack_from("<HH", data, 26)
        return width & 0x3FFF, height & 0x3FFF
    if chunk == b"VP8L":
        if len(data) < 25:
            fail(f"{path} has a truncated VP8L header")
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height
    fail(f"{path} uses unsupported WebP chunk {chunk!r}")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path} is not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def image_size(path: Path) -> tuple[int, int]:
    suffix = path.suffix.lower()
    if suffix == ".webp":
        return webp_size(path)
    if suffix == ".png":
        return png_size(path)
    fail(f"unsupported spritesheet extension: {path}")


def validate_pet(pet_dir: Path) -> dict:
    pet_json = pet_dir / "pet.json"
    pet = load_json(pet_json)

    for field in ("schemaVersion", "id", "displayName", "description", "spritesheet", "animations"):
        if field not in pet:
            fail(f"{pet_json} missing required field {field!r}")

    if not pet.get("license", {}).get("assets"):
        fail(f"{pet_json} missing required field 'license.assets'")

    if pet["id"] != pet_dir.name:
        fail(f"{pet_json} id must match folder name {pet_dir.name!r}")

    sheet_info = pet["spritesheet"]
    sheet_path = pet_dir / sheet_info.get("path", "")
    if not sheet_path.exists():
        fail(f"{pet_json} references missing spritesheet {sheet_path}")

    if sheet_info["cellWidth"] != 192 or sheet_info["cellHeight"] != 208:
        fail(f"{pet_json} cell size must be 192x208")

    width, height = image_size(sheet_path)
    expected_width = sheet_info["columns"] * sheet_info["cellWidth"]
    expected_height = sheet_info["rows"] * sheet_info["cellHeight"]
    if (width, height) != (expected_width, expected_height):
        fail(f"{sheet_path} is {width}x{height}, expected {expected_width}x{expected_height}")

    if sheet_info.get("width") and sheet_info["width"] != width:
        fail(f"{pet_json} spritesheet.width is {sheet_info['width']}, actual {width}")
    if sheet_info.get("height") and sheet_info["height"] != height:
        fail(f"{pet_json} spritesheet.height is {sheet_info['height']}, actual {height}")

    animations = pet["animations"]
    by_name = {item.get("name"): item for item in animations}
    for row, name in enumerate(REQUIRED_ANIMATIONS):
        item = by_name.get(name)
        if not item:
            fail(f"{pet_json} missing animation {name!r}")
        if item.get("row") != row:
            fail(f"{pet_json} animation {name!r} row is {item.get('row')}, expected {row}")
        frames = item.get("frames")
        if not isinstance(frames, int) or frames < 1 or frames > sheet_info["columns"]:
            fail(f"{pet_json} animation {name!r} has invalid frame count {frames!r}")

    animation_names = set(by_name)
    for event_name, event in pet.get("events", {}).items():
        animation = event.get("animation")
        if animation not in animation_names:
            fail(f"{pet_json} event {event_name!r} references unknown animation {animation!r}")

    for preview_key in ("contactSheet", "animation"):
        preview_path = pet.get("preview", {}).get(preview_key)
        if preview_path:
            path = pet_dir / preview_path
            if not path.exists():
                fail(f"{pet_json} preview {preview_key!r} references missing file {preview_path}")
            if path.stat().st_size == 0:
                fail(f"{pet_json} preview {preview_key!r} is empty: {preview_path}")
            if path.suffix.lower() in (".png", ".webp"):
                preview_width, preview_height = image_size(path)
                if preview_width < 1 or preview_height < 1:
                    fail(f"{pet_json} preview {preview_key!r} has invalid size")

    return pet


def validate_manifest(pets: dict[str, dict]) -> None:
    manifest_path = ROOT / "manifest.json"
    manifest = load_json(manifest_path)
    ids = set()
    for entry in manifest.get("pets", []):
        pet_id = entry.get("id")
        if not pet_id:
            fail(f"{manifest_path} has pet entry without id")
        if pet_id in ids:
            fail(f"{manifest_path} has duplicate pet id {pet_id!r}")
        ids.add(pet_id)
        if pet_id not in pets:
            fail(f"{manifest_path} references missing pet {pet_id!r}")
        for key in ("manifest", "spritesheet", "preview", "contactSheet"):
            rel = entry.get(key)
            if rel and not (ROOT / rel).exists():
                fail(f"{manifest_path} entry {pet_id!r} references missing {key}: {rel}")

    missing = set(pets) - ids
    if missing:
        fail(f"{manifest_path} missing pets: {', '.join(sorted(missing))}")


def main() -> None:
    pets_root = ROOT / "pets"
    if not pets_root.exists():
        fail("missing pets directory")

    pets = {}
    for pet_dir in sorted(path for path in pets_root.iterdir() if path.is_dir()):
        pet = validate_pet(pet_dir)
        pets[pet["id"]] = pet

    validate_manifest(pets)
    print(f"ok: validated {len(pets)} pet pack(s)")


if __name__ == "__main__":
    main()

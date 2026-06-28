#!/usr/bin/env python3
"""Small local PetHatch CLI.

This intentionally stays dependency-free. It installs pets from this checkout
into a Codex/OpenPets-compatible local pets directory.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DEST = Path.home() / ".codex" / "pets"


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


def manifest() -> dict:
    return load_json(ROOT / "manifest.json")


def pet_entries() -> list[dict]:
    return list(manifest().get("pets", []))


def find_pet(pet_id: str) -> dict:
    for entry in pet_entries():
        if entry.get("id") == pet_id:
            return entry
    known = ", ".join(sorted(entry.get("id", "") for entry in pet_entries()))
    fail(f"unknown pet {pet_id!r}. Known pets: {known or 'none'}")


def cmd_list(_: argparse.Namespace) -> int:
    for entry in pet_entries():
        pet_id = entry["id"]
        name = entry.get("displayName", pet_id)
        description = entry.get("description", "")
        print(f"{pet_id}\t{name}\t{description}")
    return 0


def cmd_validate(_: argparse.Namespace) -> int:
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / "scripts" / "run-pet.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-pets.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-site.py")], check=True)
    return 0


def copy_required(src: Path, dest: Path) -> None:
    if not src.exists():
        fail(f"missing source file: {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def cmd_install(args: argparse.Namespace) -> int:
    entry = find_pet(args.pet_id)
    pet_dir = ROOT / entry["path"]
    pet_manifest = load_json(pet_dir / "pet.json")
    sheet_path = pet_dir / pet_manifest["spritesheet"]["path"]

    dest_root = Path(args.dest).expanduser()
    dest_dir = dest_root / pet_manifest["id"]
    if dest_dir.exists() and not args.force:
        fail(f"{dest_dir} already exists. Use --force to overwrite.")

    dest_dir.mkdir(parents=True, exist_ok=True)
    copy_required(pet_dir / "pet.json", dest_dir / "pet.json")
    copy_required(sheet_path, dest_dir / sheet_path.name)

    if args.with_previews:
        for key in ("contactSheet", "animation"):
            rel = pet_manifest.get("preview", {}).get(key)
            if rel:
                copy_required(pet_dir / rel, dest_dir / rel)

    print(f"installed {pet_manifest['id']} to {dest_dir}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    entry = find_pet(args.pet_id)
    pet_dir = ROOT / entry["path"]
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run-pet.py"),
        str(pet_dir),
    ]
    if args.demo:
        command.append("--demo")
    if args.minute_seconds is not None:
        command.extend(["--minute-seconds", str(args.minute_seconds)])
    if args.quota_remaining is not None:
        command.extend(["--quota-remaining", str(args.quota_remaining)])
    if args.duration:
        command.extend(["--duration", str(args.duration)])
    if args.log_events:
        command.append("--log-events")
    if args.x is not None:
        command.extend(["--x", str(args.x)])
    if args.y is not None:
        command.extend(["--y", str(args.y)])
    if args.pin:
        command.append("--pin")
    return subprocess.run(command, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pethatch",
        description="Install and validate local PetHatch pet packs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List pets in this checkout.")
    list_parser.set_defaults(func=cmd_list)

    validate_parser = sub.add_parser("validate", help="Validate all pet packs.")
    validate_parser.set_defaults(func=cmd_validate)

    install_parser = sub.add_parser("install", help="Install a pet into a local runtime directory.")
    install_parser.add_argument("pet_id", help="Pet id from manifest.json, e.g. xiaochai.")
    install_parser.add_argument(
        "--dest",
        default=str(DEFAULT_DEST),
        help=f"Destination pets directory. Default: {DEFAULT_DEST}",
    )
    install_parser.add_argument("--force", action="store_true", help="Overwrite an existing installed pet.")
    install_parser.add_argument(
        "--with-previews",
        action="store_true",
        help="Also copy contact-sheet and preview assets.",
    )
    install_parser.set_defaults(func=cmd_install)

    run_parser = sub.add_parser("run", help="Run a pet as a tiny macOS desktop companion.")
    run_parser.add_argument("pet_id", help="Pet id from manifest.json, e.g. xiaochai.")
    run_parser.add_argument("--demo", action="store_true", help="Compress behavior thresholds for a quick local demo.")
    run_parser.add_argument("--minute-seconds", type=float, default=None, help="Seconds per pet minute.")
    run_parser.add_argument("--quota-remaining", type=float, default=None, help="Quota remaining fraction, e.g. 0.15.")
    run_parser.add_argument("--duration", type=float, default=0.0, help="Exit after this many seconds.")
    run_parser.add_argument("--log-events", action="store_true", help="Print event transitions to stdout.")
    run_parser.add_argument("--x", type=float, default=None, help="Initial window x position.")
    run_parser.add_argument("--y", type=float, default=None, help="Initial window y position.")
    run_parser.add_argument("--pin", action="store_true", help="Use a higher always-on-top level.")
    run_parser.set_defaults(func=cmd_run)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

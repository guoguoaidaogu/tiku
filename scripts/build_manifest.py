#!/usr/bin/env python3
"""Rebuild assets/manifest.json from the .json files found under assets/.

The manifest lists every JSON file and records which one the webpage should
open by default:

    {
      "default": { "chapter": "chapter2", "file": "test2_2.json" },
      "files": ["chapter1/test1_1.json", ...]
    }

Usage:
    python3 scripts/build_manifest.py
    python3 scripts/build_manifest.py --default chapter2/test2_2.json
    python3 scripts/build_manifest.py --clear-default

Without --default, an existing valid default is preserved; otherwise the first
file in sorted order becomes the default.
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
MANIFEST = ASSETS / "manifest.json"


def split_path(path: str) -> tuple[str, str]:
    """'chapter2/test2_2.json' -> ('chapter2', 'test2_2.json'); root file -> ('', name)."""
    head, sep, tail = path.partition("/")
    return (head, tail) if sep else ("", head)


def read_existing_default() -> dict | None:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    default = data.get("default") if isinstance(data, dict) else None
    if not isinstance(default, dict):
        return None

    chapter = default.get("chapter")
    file = default.get("file")
    if not isinstance(chapter, str) or not isinstance(file, str):
        return None
    return {"chapter": chapter, "file": file}


def as_path(default: dict) -> str:
    chapter = default["chapter"]
    return f"{chapter}/{default['file']}" if chapter else default["file"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--default", metavar="PATH",
                       help="file to open by default, e.g. chapter2/test2_2.json")
    group.add_argument("--clear-default", action="store_true",
                       help="do not record a default file")
    args = parser.parse_args()

    if not ASSETS.is_dir():
        print(f"error: {ASSETS} does not exist", file=sys.stderr)
        return 1

    files = sorted(
        p.relative_to(ASSETS).as_posix()
        for p in ASSETS.rglob("*.json")
        if p.is_file() and p.name != MANIFEST.name
    )

    if not files:
        print("error: no .json files found under assets/", file=sys.stderr)
        return 1

    # Work out the default.
    if args.clear_default:
        default = None
        note = "default cleared on request"
    elif args.default:
        requested = args.default.strip().lstrip("./")
        if requested not in files:
            print(f"error: {requested!r} is not one of the known files:", file=sys.stderr)
            for name in files:
                print(f"  - {name}", file=sys.stderr)
            return 1
        chapter, name = split_path(requested)
        default = {"chapter": chapter, "file": name}
        note = "default set on request"
    else:
        existing = read_existing_default()
        if existing and as_path(existing) in files:
            default = existing
            note = "kept the existing default"
        else:
            if existing:
                print(f"note: previous default {as_path(existing)!r} no longer exists",
                      file=sys.stderr)
            chapter, name = split_path(files[0])
            default = {"chapter": chapter, "file": name}
            note = "fell back to the first file"

    payload: dict = {}
    if default is not None:
        payload["default"] = default
    payload["files"] = files

    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {MANIFEST.relative_to(ROOT)} with {len(files)} file(s) ({note}):")
    for name in files:
        marker = "  <- default" if default and as_path(default) == name else ""
        print(f"  - {name}{marker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

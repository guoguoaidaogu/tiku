#!/usr/bin/env python3
"""Check that every locale in i18n/ has the same message keys as the base locale.

Usage:
    python3 scripts/check_i18n.py

index.html treats i18n/en.json as the base: a key missing from another locale
falls back to English, and a key present only in the base is reported here so
the gap is visible during review rather than at runtime. Exits non-zero when
anything is wrong, so it can be wired into CI.

Also verifies that the {placeholders} of each message match between locales —
a dropped {n} is easy to miss and shows up as a literal "{n}" on screen.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
BASE = "en"
PLACEHOLDER = re.compile(r"\{(\w+)\}")


def placeholders(value) -> set:
    """Placeholders of a message, which is a string or a CLDR plural object."""
    if isinstance(value, dict):
        found = set()
        for form in value.values():
            found |= set(PLACEHOLDER.findall(str(form)))
        return found
    return set(PLACEHOLDER.findall(str(value)))


def load(path: pathlib.Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"error: cannot read {path.relative_to(ROOT)}: {err}")
        raise SystemExit(1)
    if not isinstance(data, dict):
        print(f"error: {path.relative_to(ROOT)} must contain a JSON object")
        raise SystemExit(1)
    return data


def main() -> int:
    if not I18N.is_dir():
        print(f"error: {I18N} does not exist")
        return 1

    catalogs = {p.stem: load(p) for p in sorted(I18N.glob("*.json"))}
    if BASE not in catalogs:
        print(f"error: the base locale i18n/{BASE}.json is missing")
        return 1

    base = catalogs[BASE]
    problems = 0

    print(f"base locale: {BASE} ({len(base)} messages)")
    for code, messages in catalogs.items():
        if code == BASE:
            continue

        missing = sorted(set(base) - set(messages))
        extra = sorted(set(messages) - set(base))
        mismatch = sorted(
            k for k in set(base) & set(messages)
            if placeholders(base[k]) != placeholders(messages[k])
        )

        if not (missing or extra or mismatch):
            print(f"  {code}: ok ({len(messages)} messages)")
            continue

        problems += 1
        print(f"  {code}: {len(messages)} messages")
        for k in missing:
            print(f"    missing key: {k}")
        for k in extra:
            print(f"    unknown key (not in {BASE}): {k}")
        for k in mismatch:
            print(f"    placeholder mismatch: {k} "
                  f"({BASE}={sorted(placeholders(base[k]))} {code}={sorted(placeholders(messages[k]))})")

    if problems:
        print(f"\n{problems} locale(s) need attention")
        return 1

    print("\nall locales are in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Is every config entry in the section the code actually binds it to?

    python3 code/cfgaudit.py

BepInEx resolves a setting by **(section, key)**, not by key. An entry under the wrong section is
not cosmetic: `Bind()` does not find it, the plugin silently runs on its coded default, and the
next launch writes a *second* copy under the right section. The hand-placed one stays in the file
forever, looking authoritative, read by nobody.

That is exactly what happened to `DebugHotkeysIgnoreHeldKeys` (CHANGELOG 47, fixed in 49): bound
under "Tools", hand-written into [Gameplay]. It went unnoticed because its default is `true` and
the file said `true`, so nothing misbehaved - it would only have shown up the first time somebody
set it to `false` and nothing happened.

This is unavoidable rather than sloppy: code/README.md instructs adding new settings to the config
**by hand**, because BepInEx only rewrites the file on a clean run. So the check has to exist.
Same principle as `[ALIAS-GAP]`, `[AI-AUDIT]` and `[KEYBIND]` - a gap must announce itself rather
than look plausible.

Exits non-zero if anything is wrong, so it can gate a release.
"""
import glob
import os
import re
import sys

import pncpaths as P

ROOT = P.ROOT
SRC = os.path.join(ROOT, "code/edimod/PncEdi")
CFGS = ["BepInEx/config/com.edi.pnc.cfg"]

# Config.Bind<T>("Section", "Key", default, "description")
BIND = re.compile(r'\.Bind<[^>]+>\(\s*"([^"]+)"\s*,\s*"([^"]+)"')


def bound_pairs():
    """(section, key) -> source file. Keyed on the PAIR: `Enabled` is legitimately bound four
    times, under Ambient, Gameplay, Imp and Interactive. Keying on the name alone reports three
    of those four as misplaced."""
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, "*.cs"))):
        for sec, key in BIND.findall(open(f, encoding="utf-8").read()):
            out[(sec, key)] = os.path.basename(f)
    return out


def file_pairs(path):
    out, cur = [], None
    text = open(path, encoding="utf-8-sig", newline="").read().replace("\r\n", "\n")
    for i, line in enumerate(text.split("\n"), 1):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
        elif "=" in s and not s.startswith("#"):
            out.append((cur, s.split("=", 1)[0].strip(), i))
    return out


def main():
    bound = bound_pairs()
    print(f"{len(bound)} (section, key) pairs bound in {os.path.relpath(SRC, ROOT)}")
    rc = 0
    for name in CFGS:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            print(f"\n{name}: MISSING")
            rc = 1
            continue
        got = file_pairs(path)
        seen, bad = set(), []
        for sec, key, ln in got:
            if (sec, key) in seen:
                bad.append(f"  DUPLICATE  [{sec}] {key}  line {ln}")
            seen.add((sec, key))
            if (sec, key) not in bound:
                elsewhere = sorted(s for s, k in bound if k == key)
                bad.append(f"  NOT BOUND  [{sec}] {key}  line {ln}" +
                           (f"  -> the code binds it under {elsewhere}; the game ignores this line"
                            if elsewhere else "  (no such key anywhere in the source)"))
        for sec, key in sorted(set(bound) - seen):
            bad.append(f"  ABSENT     [{sec}] {key}  bound in {bound[(sec, key)]}, not in the file")
        print(f"\n{name}: {len(got)} entries")
        if bad:
            print("\n".join(bad))
            rc = 1
        else:
            print("  ok - every entry sits in the section the code binds it to")
    return rc


if __name__ == "__main__":
    sys.exit(main())

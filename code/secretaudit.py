#!/usr/bin/env python3
"""Is anything tracked that should not be public?

    python3 code/secretaudit.py           the working tree: tracked, and untracked-but-not-ignored
    python3 code/secretaudit.py --history every blob in every commit (slow, before a push)

**Why this exists.** The repo is public (§183), and `.gitignore` already reasons carefully about
this: `EdiConfig.json` is untracked *on purpose* because its device names embed per-user Handy
connection keys, "which are effectively credentials for controlling that hardware". That rule
protected the file and nothing else. A real key - this machine's - had been pasted into
`code/README.md` as a config example, and sat there through eleven commits and every audit this
project has, because no check has ever looked at file *content* for anything but correctness.

The general shape of the failure is that a credential's home is guarded while a copy of it is
quoted somewhere as an illustration. So this does not check `EdiConfig.json`. It checks
everything else, three ways:

  - **the keys this machine actually has** - read out of the same per-user configs
    `handystate.py` probes, and searched for verbatim in every tracked file. This is the check
    that would have caught the README, and it needs no pattern to be right, only the key to be
    real. It is skipped, loudly, on a machine with no Edi config: a clone with nothing to leak
    cannot perform it, and a skip that is announced is not the same as a pass;
  - **the shape of a key**, `The Handy [........]`, wherever it appears in a tracked file. This
    catches a key that came from somebody else's paste, or from a machine this one has never
    been. Three values are allowed to wear the shape, because a document has to be able to show
    it: a run of `x`, a `<named>` slot, and an ellipsis;
  - **a populated `Handy.Key` or `Handy.ApiKey`** in tracked JSON. `code/dist/EdiConfig.json` is
    a template that ships in the release archive; the day someone regenerates it by copying a
    working config, it stops being one.

Keys are never printed, here or in a failure: the finding is the file and the line, and the
value is masked the way `handystate.py` masks it. A check that leaks the secret it found in CI
output has moved the problem rather than solved it.

`--history` asks the same first two questions of every blob ever committed: a working tree can be
clean while three commits back is not. It is not in `check.py`'s fast tier because it reads the
whole object database.

**Since the push, this gate is the only line.** §182's redaction worked because nothing had been
pushed and the history could be rewritten for free. That is spent: a key that reaches a commit now
is public whether or not it is later removed, and the remedy stops being `git filter-branch` and
becomes revoking the credential at the device end. The fast-tier run is what keeps that from ever
being the question.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

import handystate as H
import pncpaths as P

ROOT = P.ROOT

# The documents' own placeholders. A template has to show the shape of a device name, so the shape
# alone cannot be the finding - these are the two values allowed to wear it: a run of `x`, which is
# what the archive README and the config examples use, a `<named>` slot, which is how the prose in
# `code/README.md` and `release.py` describes the field rather than showing one, and an ellipsis,
# which is how `learnings/` quotes the shape while talking about it. Anything else in the brackets
# is a finding, including an invented key: a document with a plausible one in it teaches the next
# reader to paste a real one.
PLACEHOLDER = re.compile(r"^(x+|<[^>]*>|\.{2,}|…)$", re.IGNORECASE)
# The device-name shape Edi writes, and HandyHttpClient parses. Deliberately looser than
# `handystate.HANDY_NAME`: anything inside the brackets is a finding here unless it is the
# placeholder, including a truncated or invented key, because a document with a plausible-looking
# key in it teaches the next reader to paste a real one.
DEVICE_NAME = re.compile(r"The Handy \[([^\]\n]{2,})\]")
# A connection key is 8 URL-safe characters. Bare, with no device name around it, that is too
# short to search for on its own without matching English - so a bare key is only ever found by
# the verbatim search below, never by shape.
JSON_KEY_FIELDS = ("Key", "ApiKey")

# This file quotes the patterns it hunts for, so it would report itself forever.
SELF = os.path.relpath(os.path.abspath(__file__), ROOT)


def mask(value):
    """Never print a key. Same masking as `handystate.mask`, for the same reason."""
    return H.mask(value)


def scannable_files():
    """Every file a push could publish: tracked, **and untracked-but-not-ignored**.

    The second half is not padding. `.gitignore` here is an allowlist, and §180 is the case where
    eleven files sat in the tree unignored and unadded while every gate passed, because every gate
    reads the working tree and git was the only thing that knew. A file in that state is one
    `git add -A` from being committed, so scanning only `ls-files` would clear a key the moment
    before it became public rather than after."""
    files = []
    for args in (["git", "ls-files", "-z"],
                 ["git", "ls-files", "-z", "--others", "--exclude-standard"]):
        out = subprocess.run(args, cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, check=True).stdout
        files += [p for p in out.split("\0") if p]
    return files


def read_text(path):
    """Text of a tracked file, or None if it is binary or unreadable. No binary is tracked here
    (`.gitignore` says so and `release.py` enforces it), so this is belt and braces."""
    try:
        with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return None


def local_keys():
    """Every Handy key this machine holds, from the per-user configs `handystate.py` reads.

    Returns (keys, sources). Unlike `handystate.candidates()` this keeps a key with no API key
    beside it - an unusable credential is still a credential once it is published - and it never
    exits: a machine with no Edi config is a legitimate place to run this."""
    keys, sources = set(), []
    for path in H.CONFIG_PATHS:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8-sig") as fh:
                handy = (json.load(fh) or {}).get("Handy") or {}
        except (json.JSONDecodeError, OSError):
            continue
        sources.append(path)
        for field in JSON_KEY_FIELDS:
            value = handy.get(field)
            if value:
                keys.add(str(value))
    for path in H.EDI_CONFIGS:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8-sig") as fh:
                devices = ((json.load(fh) or {}).get("Devices") or {}).get("Devices") or {}
        except (json.JSONDecodeError, OSError):
            continue
        sources.append(path)
        if isinstance(devices, dict):
            for name in devices:
                hit = H.HANDY_NAME.search(name)
                if hit:
                    keys.add(hit.group(1))
    return keys, sources


def scan_text(path, text, keys):
    """Findings in one file's text, as [(line number, what, masked value)]."""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        for key in keys:
            if key in line:
                found.append((number, "a connection key this machine holds", mask(key)))
        for hit in DEVICE_NAME.finditer(line):
            value = hit.group(1)
            if not PLACEHOLDER.match(value):
                found.append((number, "a device name with a key in it", mask(value)))
    return found


def scan_json(path, text):
    """A populated `Handy.Key` / `Handy.ApiKey` in a tracked config. Template configs are the
    point of this one: they are copied from working configs, which is how they get filled in."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return []
    handy = (data or {}).get("Handy") if isinstance(data, dict) else None
    if not isinstance(handy, dict):
        return []
    return [(0, f"a populated Handy.{field}", mask(str(handy[field])))
            for field in JSON_KEY_FIELDS if handy.get(field)]


def scan_worktree(keys):
    findings = []
    for path in scannable_files():
        if path == SELF:
            continue
        text = read_text(path)
        if text is None:
            continue
        for number, what, value in scan_text(path, text, keys):
            findings.append((path, number, what, value))
        if path.endswith(".json"):
            for number, what, value in scan_json(path, text):
                findings.append((path, number, what, value))
    return findings


def scan_history(keys):
    """The same questions asked of every blob in every commit.

    `git rev-list --objects --all` names each blob and the path it was last seen at, which is
    enough to point a reader at what to rewrite. A blob is reported once, not once per commit
    that reaches it."""
    listing = subprocess.run(["git", "rev-list", "--objects", "--all"], cwd=ROOT, text=True,
                             stdout=subprocess.PIPE, check=True).stdout.splitlines()
    findings = []
    for entry in listing:
        sha, _, path = entry.partition(" ")
        if not path or path == SELF:
            continue
        kind = subprocess.run(["git", "cat-file", "-t", sha], cwd=ROOT, text=True,
                              stdout=subprocess.PIPE).stdout.strip()
        if kind != "blob":
            continue
        blob = subprocess.run(["git", "cat-file", "blob", sha], cwd=ROOT,
                              stdout=subprocess.PIPE).stdout
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            continue
        for number, what, value in scan_text(path, text, keys):
            findings.append((f"{sha[:10]} {path}", number, what, value))
    return findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--history", action="store_true",
                    help="scan every blob in every commit, not only the tracked working tree")
    args = ap.parse_args()

    keys, sources = local_keys()
    if keys:
        print(f"{len(keys)} local key(s) from {len(sources)} config(s) searched for verbatim")
    else:
        print("SKIPPED: no Edi config on this machine - only the shape checks ran")

    findings = scan_history(keys) if args.history else scan_worktree(keys)
    for where, number, what, value in sorted(findings):
        place = f"{where}:{number}" if number else where
        print(f"FAIL {place}: {what} ({value})")

    if findings:
        print(f"\n{len(findings)} finding(s). A tracked key is public the moment the repo is;"
              " redact it, and rewrite the history that carries it.")
        return 1
    scope = "every blob in every commit" if args.history else "the working tree"
    print(f"ok - no key in {scope}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Every check this project has, in one run.

    python3 code/check.py               the fast gates (~7 s) - run this after any change
    python3 code/check.py --full        + the asset sweeps (~25 s) - before a release
    python3 code/check.py --deploy      deploy first (build + patch both installs), then check
    python3 code/check.py --list        what would run, and why each step is in its tier
    python3 code/check.py -k alias      only steps whose name contains `alias`
    python3 code/check.py -v            print every step's output, not only the failures

**Why this exists.** PROJECT.md's "Checking your work" table is fifteen checks (and four
instruments) with four different invocations (`python3`, `.venv/bin/python`, `dotnet test`,
`dotnet run --project`), three different ideas of what failure looks like, and one entry that needs
the hardware plugged in. A session that has just changed one file either runs all fifteen by hand
or - what actually happened - runs the two it remembers. This runs them, in dependency order, and gives one exit code.

**The three ways a tool here reports failure**, all of which this has to understand:

  `gate`   exit code is the verdict:  patchaudit, cfgaudit, versionaudit, ladders --check,
           deploy --check, release --check, dotnet test.
  `grep`   exit code is always 0 and the verdict is a word in the output: slugharness prints
           `UNMAPPED` per unmapped pair, animsweep prints `OFF` in its time column. A tool like
           this cannot be wrapped by exit code alone, and wrapping it wrong is worse than not
           wrapping it - it would report green forever.
  `report` no verdict exists to compute: gallerydiff and speedcheck answer a question a human
           reads (which rows differ, which are too fast for which device). They run under --full,
           their summary is printed, and they fail the run only if the tool itself crashes.

Only `handystate.py` is left out entirely: it polls your Handy over the network for as long as you
let it, which is not a check, it is an instrument.

Steps are ordered cheapest-and-most-fundamental first, so a broken build or a bad config is
reported in the first two seconds rather than after the asset sweeps.

`code/refvideo.py` is deliberately not here. Rendering and verifying the per-scene reference
videos was a one-off for other scripters (§88); it is still a working tool, run by hand.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import time

import pncpaths as P

ROOT = P.ROOT
VENV = os.path.join(ROOT, ".venv/bin/python")


class Step:
    def __init__(self, name, argv, why, tier="fast", kind="gate",
                 bad=None, needs=(), tail=3):
        self.name = name        # what -k matches, and what the summary line says
        self.argv = argv        # argv list, run from ROOT
        self.why = why          # the question this step answers (--list, and the summary)
        self.tier = tier        # "fast" (always) or "full" (--full only)
        self.kind = kind        # gate | grep | report  - see the module docstring
        self.bad = bad          # kind="grep": a regex whose presence in stdout means failure
        self.needs = needs      # executables/paths that must exist, else the step is skipped
        self.tail = tail        # lines of output to show for a passing report step


PY = sys.executable or "python3"

STEPS = [
    Step("tests", ["dotnet", "test", "code/tests/PncEdi.Tests.csproj"],
         "does the naming, alias and config layer still behave?",
         needs=("dotnet",)),
    Step("cfgaudit", [PY, "code/cfgaudit.py"],
         "is every config entry in the section its Bind() names?"),
    Step("versionaudit", [PY, "code/versionaudit.py"],
         "does every place that states the mod version agree?"),
    Step("bridgeaudit", [PY, "code/bridgeaudit.py"],
         "is the custom-enemy seam still wired at both ends?"),
    Step("patchaudit", [PY, "code/patchaudit.py"],
         "does the mod still bind to the game, and is every patch class registered?",
         needs=("game",)),
    Step("ladders", [PY, "code/ladders.py", "--check"],
         "do the filler and hypnosis rows still share their grid and anchor?"),
    Step("slugharness",
         ["dotnet", "run", "--project", "code/slugharness", "--",
          "BepInEx/config/com.edi.pnc.cfg"],
         "does every animator state resolve to a script?",
         kind="grep", bad=r"\bUNMAPPED\b", needs=("dotnet",)),
    Step("webmify", [PY, "code/webmify.py", "--check"],
         "does every custom-enemy video have a WebM, so it plays on Linux?"),
    Step("packageaudit", [PY, "code/packageaudit.py"],
         "does every package that declares an assembly ship a current one?"),
    Step("deploy", [PY, "code/deploy.py", "--check"],
         "are the game installs current?",
         needs=("game",)),
    Step("release", [PY, "code/release.py", "--check"],
         "would a release build succeed?"),

    Step("animsweep", [VENV, "code/animsweep.py"],
         "every scene's timing and polarity against its animation",
         tier="full", kind="grep", bad=r"^\S.*\bOFF\b", needs=("venv", "game")),
    Step("dioramaaudit", [VENV, "code/dioramaaudit.py"],
         "does every ambient Patterns entry still match a clip or a looping source?",
         tier="full", needs=("venv", "game")),
    Step("gallerydiff", [VENV, "code/gallerydiff.py"],
         "does the gallery play a different-length clip than gameplay?",
         tier="full", kind="report", needs=("venv", "game"), tail=3),
    Step("speedcheck", [PY, "code/speedcheck.py"],
         "is each script playable on the target device?",
         tier="full", kind="report", tail=4),
]


def missing(step):
    """Why this step cannot run here, or None. Skips are reported, never silent - a check that
    quietly does not run is the failure mode this whole file exists to remove."""
    for need in step.needs:
        if need == "venv" and not os.path.exists(VENV):
            return "no .venv (python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt)"
        if need == "game" and not os.path.isdir(P.game_dir()):
            return f"no game install at {os.path.relpath(P.game_dir(), ROOT)}"
        if need == "dotnet" and not shutil.which(need):
            return f"{need} not on PATH"
    return None


def run(step, verbose):
    """Run one step. Returns (verdict, seconds, output) with verdict in ok/FAIL/skip."""
    why = missing(step)
    if why:
        return "skip", 0.0, why
    t0 = time.time()
    proc = subprocess.run(step.argv, cwd=ROOT, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    secs = time.time() - t0
    out = proc.stdout or ""
    if proc.returncode != 0:
        return "FAIL", secs, out
    if step.kind == "grep":
        hits = [ln for ln in out.splitlines() if re.search(step.bad, ln)]
        if hits:
            return "FAIL", secs, "\n".join(hits)
    return "ok", secs, out


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--full", action="store_true",
                    help="also run the asset sweeps (needs .venv and the game)")
    ap.add_argument("--deploy", action="store_true",
                    help="build and patch both game installs before checking")
    ap.add_argument("--list", action="store_true", help="print the steps and exit")
    ap.add_argument("-k", metavar="TEXT", default="", help="only steps whose name contains TEXT")
    ap.add_argument("-v", "--verbose", action="store_true", help="print every step's output")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help:
        print(__doc__)
        return 0

    steps = [s for s in STEPS
             if (a.full or s.tier == "fast") and a.k.lower() in s.name.lower()]
    if a.list:
        for s in steps:
            print(f"  {s.name:<13}{s.tier:<6}{s.kind:<7}{s.why}")
        return 0
    if not steps:
        sys.exit(f"check: no step matches -k {a.k!r}")

    if a.deploy:
        # Before, not after: every step below reads either the working tree or an install, and
        # `deploy --check` is one of them - checking a tree you are about to deploy answers a
        # question nobody asked.
        print("== deploy")
        if subprocess.run([PY, "code/deploy.py"], cwd=ROOT).returncode != 0:
            print("\ndeploy failed - nothing else run")
            return 1

    results = []
    for s in steps:
        verdict, secs, out = run(s, a.verbose)
        results.append((s, verdict, secs))
        mark = {"ok": "ok  ", "FAIL": "FAIL", "skip": "skip"}[verdict]
        print(f"{mark} {s.name:<13}{secs:>6.1f}s  {s.why}")
        if verdict == "skip":
            print(f"       {out}")
        elif verdict == "FAIL" or a.verbose or (s.kind == "report" and verdict == "ok"):
            body = out.rstrip().splitlines()
            if not a.verbose and verdict == "ok":
                body = body[-s.tail:]
            for ln in body:
                print(f"     | {ln}")

    bad = [s.name for s, v, _ in results if v == "FAIL"]
    skipped = [s.name for s, v, _ in results if v == "skip"]
    total = sum(t for _, _, t in results)
    print(f"\n{len(results) - len(bad) - len(skipped)}/{len(results)} ok in {total:.0f}s"
          + (f", skipped: {', '.join(skipped)}" if skipped else "")
          + (f", FAILED: {', '.join(bad)}" if bad else ""))
    if not a.full and not bad:
        print("fast tier only - `--full` adds the asset sweeps before a release")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())

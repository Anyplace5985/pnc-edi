#!/usr/bin/env python3
"""Hand-authored scenes: the ones no proxy can find.

    .venv/bin/python code/authored.py [--write]

Three scenes were flagged on the feel pass with cues about how they should *feel*, not about
what moves. A proxy can time them and can say what is on screen, but it cannot decide that a
wrapped tongue should read as a vibration rather than as head position. The curves live here, with
the frame evidence and the cue that produced each, so they are reproducible and arguable instead
of being an unexplained edit to a JSON file.

Everything obeys the same conventions as the derived scenes: >=100 ms between points, speeds
inside the reference band, seams considered. See ../learnings/funscript-authoring.md "Writing for
the hardware".
"""
import sys, os, csv, json

import pncpaths as P

ROOT = P.ROOT
DIRS = [P.DETAILED]
CSVS = [P.DEFINITIONS]


def baphomet_start():
    """Gallery_Baphomet_Grabbed_BJ_Start - 20 frames @8fps = 2500 ms.

    CUE: vibrate near the top while she wraps her tongue round it, rather than following her
    head; then refocus on her head as she goes down and takes it in one go.

    The frames back this exactly. 0-1: approaching in darkness, nothing touching. 2-10
    (250-1250 ms): the tongue is visibly coiled around the shaft while her head stays put -
    there is no head motion to follow here, which is why the old curve's 100/50/100 wander had
    nothing behind it. 11 (1375 ms): mouth opens wide. 11-14 (to 1750 ms): she descends and takes
    it in one motion. 15-19: held at the base.

    The guide prescribes this case directly: "switch up/down direction when she reaches the left
    or right and circles back with her tongue - that creates constant movement even if she isn't
    really moving up and down." So the tongue phase is a 70<->100 oscillation, high and shallow,
    and the descent is one clean 100->0 stroke over 375 ms (267 u/s - inside even a Handy 1).

    Ends at 0, held. Baphomet_Loop starts at 0, so that is also the right handoff; Edi's loop
    fixup turns the open seam into a 750 ms pull-off at 133 u/s rather than a jump."""
    acts = [(0, 100), (250, 100)]                       # approaching, nothing touching yet
    for k, t in enumerate(range(375, 1251, 125)):       # tongue coiled: shallow, high, constant
        acts.append((t, 70 if k % 2 == 0 else 100))
    acts += [(1375, 100),                               # mouth opens
             (1750, 0),                                 # takes it in one go
             (2500, 0)]                                 # held at the base
    return "Baphomet_Start", acts, 2500


def baphomet_cum():
    """Gallery_Baphomet_Grabbed_BJ_Cum - 20 frames @8fps = 2500 ms.

    CUE: the stroker travels far up for no apparent reason - reduce that excursion.

    Confirmed: her face never leaves the base for the whole clip. Signed displacement stays inside
    +-33 through frames 0-13, is exactly 0.00 for 14-16, then goes large negative for 17-19, which
    is the scene fading out rather than anyone moving. There is no upstroke in this animation, so
    the old curve's climb to 100 at 366 ms was invented.

    Scripted as what it is: locked deep, pulsing. 0<->35 every 125 ms (280 u/s) while there is
    motion, then still from 1750 ms as the animation goes static and fades. Peak 35 instead of
    100 is the excursion reduction asked for."""
    acts = [(t, 0 if k % 2 == 0 else 35) for k, t in enumerate(range(0, 1626, 125))]
    acts += [(1750, 0), (2500, 0)]                      # static frames 14-16, then the fade
    return "Baphomet_Cum", acts, 2500


def gravy_loop2():
    """Gallery_Gravy_Grabbed_Loop2 - 7 frames @9fps = 778 ms, script is 2 cycles.

    CUE: would benefit from some bounce at the bottom.

    Measured first, because the shape was also wrong. The pale shaft below her is visible only in
    frames 1-3 (904, 725, 259 px) and completely hidden in 0 and 4-6. So she is seated for over
    half the cycle: up fast on frame 1, down through 2-3, then a long bottom dwell. The old curve
    peaked at 248 ms against an animation peaking at 111 ms.

    The bounce goes in that dwell. It is an authored addition - nothing in the sprites rebounds -
    but bottoming out is a real event and the dwell is otherwise 444 ms of nothing. Kept small
    and quick (0->25->0 at 111 ms, 225 u/s) so it reads as impact, not as a second stroke."""
    cyc = [(0, 0), (111, 100), (222, 80), (333, 29),    # measured: hidden, then exposed 904/725/259
           (444, 0), (555, 25), (666, 0)]               # seated; the bounce is the 25
    acts = [(c * 778 + t, p) for c in range(2) for t, p in cyc]
    acts.append((1556, 0))
    return "Gravy_Loop2", acts, 1556


def write(name, acts, total, note, min_gap=100):
    """`min_gap` is the >=100 ms authoring convention, relaxable for a derived scene.

    100 ms is the rule for a curve written from scratch, not a property of the corpus: 24 of the
    59 scripts have points closer than that, `imp_3` down to 53 ms, because the fastest scenes are
    genuinely that fast. A scene generated by replaying one of those at a slower clock inherits
    its spacing and cannot be held to a standard its own master fails - so callers doing that pass
    the master's floor, which the scaling can only improve on."""
    stem = name.lower()
    assert acts[-1][0] == total, (name, acts[-1], total)
    gaps = [b[0] - a[0] for a, b in zip(acts, acts[1:])]
    assert min(gaps) >= min_gap, (name, f"gap under {min_gap}ms", min(gaps))
    fast = max(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000 for a, b in zip(acts, acts[1:]))
    doc = {"actions": [{"at": t, "pos": p} for t, p in acts], "inverted": False, "range": 100,
           "version": "1.0", "metadata": {
               "bookmarks": [], "chapters": [], "creator": "", "performers": [], "tags": [],
               "notes": "", "license": "", "script_url": "", "video_url": "", "type": "basic",
               "duration": round(total / 1000), "title": name, "description": note}}
    for d in DIRS:
        json.dump(doc, open(os.path.join(d, stem + ".funscript"), "w", encoding="utf-8"), indent=2)
    for c in CSVS:                                       # keep EndTime in step
        raw = open(c, encoding="utf-8-sig", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for i, l in enumerate(lines):
            f = l.split(",")
            if len(f) >= 4 and f[0] == name:
                f[3] = str(total); lines[i] = ",".join(f)
        open(c, "w", encoding="utf-8", newline="").write("﻿" + nl.join(lines))
    print(f"{name:<16}{len(acts):>3} acts  end={total:<5} range {min(p for _, p in acts)}-"
          f"{max(p for _, p in acts):<4} min gap={min(gaps)}ms  peak={fast:.0f} u/s")


if __name__ == "__main__":
    for fn in (baphomet_start, baphomet_cum, gravy_loop2):
        name, acts, total = fn()
        if "--write" in sys.argv:
            write(name, acts, total, fn.__doc__.strip().split("\n")[0] + " Hand-authored from the "
                  "feel-pass cue; see code/authored.py for the reasoning.")
        else:
            print(f"{name:<16}{len(acts):>3} acts  end={total}   {acts[:6]} ...")

#!/usr/bin/env python3
"""Generate a speed-limited gallery variant for slower hardware.

    .venv/bin/python code/variants.py            # report what would change
    .venv/bin/python code/variants.py --write    # write Edi/Gallery/<variant>/

Edi picks a script by variant, and the variant is the FOLDER NAME under Gallery/. So shipping a
second folder is all that is needed - no mod change, no config setting. Point a device at it in
`Edi/EdiConfig.json`:

    "The Handy [xxxx]": { "Variant": "handy1", ... }

WHY A SEPARATE VARIANT INSTEAD OF ONE SAFE SCRIPT

A stroker cannot exceed its firmware speed cap. Asked for more, it does not fail loudly - it
simply fails to arrive, reaching part of the commanded travel before the next command lands. The
stroke silently shortens and fast sections turn to mush. Handy 1 caps near 400 mm/s over a 110 mm
stroke (364 units/s); a Handy 2 Pro at max overclock manages 1200 mm/s over 125 mm (960 units/s), which
is well over double. One script cannot serve both without wasting one of them.

HOW: SLEW LIMITING, NOT GLOBAL SCALING

Scaling the whole script down by one factor also shrinks the slow sections, which had headroom
and did not need it. Instead each transition is clipped to what the device can actually cover in
the time available:

    reachable = limit_units_per_s * dt / 1000
    pos = previous + clamp(target - previous, -reachable, +reachable)

Timing is untouched - it is the sync to the animation and must not move. Slow strokes keep their
full range; only the ones the device could never have completed get shorter. That is the same
outcome the hardware would reach on its own, except the positions stay coherent instead of
drifting wherever the motor happened to stop.
"""
import glob, shutil, sys, os, csv, json

import pncpaths as P
import speedcheck as S

ROOT = P.ROOT
TREES = [P.GALLERY]
SRC = "detailed"


def slew(acts, lim, passes=6):
    """Clip each transition to what the device can cover, cyclically.

    Every row here is Loop=true, and Edi's InproveLoopDetection rewrites the last action to match
    the first at load. So a limiter that simply runs start-to-end leaves the wrap unclipped: the
    tail lags, gets forced back to the head position, and that jump is over the limit again -
    which is exactly what a first attempt produced, 10 transitions up to 1633 u/s all sitting on
    the final segment. Running repeatedly, each pass starting where the last ended, converges to a
    position where the loop closes on its own and no segment (the wrap included) exceeds `lim`."""
    cur = float(acts[0]["pos"])
    for _ in range(passes):
        out, c = [{"at": acts[0]["at"], "pos": cur}], cur
        for a, b in zip(acts, acts[1:]):
            reach = lim * (b["at"] - a["at"]) / 1000.0
            c += max(-reach, min(reach, b["pos"] - c))
            out.append({"at": b["at"], "pos": max(0.0, min(100.0, c))})
        if abs(out[-1]["pos"] - cur) < 0.05:
            break
        cur = out[-1]["pos"]
    return [{"at": p["at"], "pos": int(round(p["pos"]))} for p in out]


def rng(a):
    return max(x["pos"] for x in a) - min(x["pos"] for x in a)


# Only ONE variant is generated, and only one is warranted. Measured against `detailed`:
#   Handy 1 (364 u/s) - the median transition across the whole set is 363 u/s, so half of
#     everything sits at or over the cap. That is sustained excess, and it mushes. Limit it.
#   Handy 2 Pro at max overclock (1200 mm/s = 960 u/s, off the device's own menu; review articles
#     say 800 and are low) - `detailed` runs p95 872 u/s, under the cap, and exactly one script
#     (`imp_3`) has a median above it.
#     11 others only exceed on isolated accents, which scripters write deliberately: the best
#     reference script here, shared_zombie, has a 1538 u/s (1923 mm/s) jolt that no device can
#     literally reach and that reads as a snap. Clipping those would remove intended punch from
#     the one device fast enough to enjoy it. `detailed` IS the Handy 2 Pro script; do not limit it.
VARIANTS = {"handy1": "handy1"}


def emit(variant, dev, rows, write):
    lim = S.limit(dev)
    if write:
        for t in TREES:
            os.makedirs(os.path.join(t, variant), exist_ok=True)
    print(f"variant '{variant}' <- '{SRC}' at {lim:.0f} units/s ({dev})\n")
    print(f"{'scene':<28}{'range':>7}{'->':>4}{'':<3}{'p90 u/s':>9}{'->':>4}{'':<3}{'changed':>8}")
    n_changed = 0
    copied = []
    for r in rows:
        # Per-axis siblings (`<row>.<axis>.funscript`) are COPIED, not limited. The slew limit is a
        # stroke length in mm over a firmware speed cap - arithmetic that means nothing on an axis
        # measured in degrees - and the device this variant exists for has one axis and ignores the
        # rest anyway. Copying rather than skipping keeps the variant folders in parity, so a device
        # pointed at `handy1` never finds a row that is missing an axis the master has.
        for axis, src in S.axis_files(os.path.join(TREES[0], SRC), r["FileName"]):
            if axis == "default":
                continue
            copied.append(os.path.basename(src))
            if write:
                for t in TREES:
                    shutil.copyfile(src, os.path.join(t, variant, os.path.basename(src)))
        fp = os.path.join(TREES[0], SRC, r["FileName"] + ".funscript")
        doc = json.load(open(fp, encoding="utf-8-sig"))
        a = doc["actions"]
        b = slew(a, lim)
        sa, sb = S.analyse(a), S.analyse(b)
        pa = sorted(x[3] for x in sa["segs"]); pb = sorted(x[3] for x in sb["segs"])
        p90a, p90b = pa[int(len(pa) * .9)], pb[int(len(pb) * .9)]
        ch = sum(1 for x, y in zip(a, b) if x["pos"] != y["pos"])
        if ch: n_changed += 1
        print(f"{r['Name']:<28}{rng(a):>7}{'->':>4}{rng(b):<3}{p90a:>9.0f}{'->':>4}{p90b:<3.0f}"
              f"{ch:>8}")
        if write:
            doc = dict(doc); doc["actions"] = b
            m = dict(doc.get("metadata") or {})
            m["title"] = r["Name"]
            m["description"] = (f"{variant} variant of '{SRC}': slew-limited to {lim:.0f} units/s "
                                f"({S.DEV[dev][1]} mm/s over {S.DEV[dev][0]} mm). Timing identical; "
                                f"only strokes the device could not complete are shortened.")
            doc["metadata"] = m
            for t in TREES:
                json.dump(doc, open(os.path.join(t, variant, r["FileName"] + ".funscript"),
                                    "w", encoding="utf-8"), indent=2)
    print(f"\n{n_changed} of {len(rows)} scripts differ from '{SRC}'")
    if copied:
        print(f"{len(copied)} per-axis script(s) copied unchanged (no stroke cap applies to a "
              f"non-linear axis): {', '.join(copied)}")
    stale = [os.path.basename(f) for f in sorted(glob.glob(
                os.path.join(TREES[0], variant, "*.*.funscript")))
             if os.path.basename(f) not in copied]
    if stale:
        print(f"{len(stale)} per-axis script(s) in '{variant}' with no master in '{SRC}': "
              f"{', '.join(stale)}")
    print()


def main():
    write = "--write" in sys.argv
    rows = P.definitions_rows(os.path.join(TREES[0], "Definitions.csv"))
    for variant, dev in VARIANTS.items():
        emit(variant, dev, rows, write)
    if not write:
        print("re-run with --write to emit the variants")


if __name__ == "__main__":
    main()

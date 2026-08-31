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
SRC = "handy2pro"


def slew(acts, hard, soft=None, budget=0.0, passes=6):
    """Clip each transition to what the device can cover, cyclically, under two caps.

    ONE CAP OR TWO. `hard` is a wall: no transition may ever demand more, because past it the
    motor simply fails to arrive. `soft` is the speed the script should *sustain*; the eroscripts
    multi-axis guide quotes both for every device (The Handy 2: 600 soft, 700 hard) and
    this project's own rule says the same thing from the other end - judge a script by its median,
    never its maximum, because a deliberate snap is an artistic choice and sustained excess is what
    turns a stroke to mush. A single-cap limiter cannot express that: set it to the soft figure and
    every accent is flattened, set it to the hard one and nothing is limited at all.

    THE BUCKET. Between the two caps sits a token bucket, measured in *position units of travel*.
    Every segment earns `soft * dt` units of credit and spends `|step|`; the balance is capped at
    `budget` and never goes below zero. A segment may therefore travel up to
    `min(hard * dt, soft * dt + bucket)`. A script that has been idling banks a full budget and can
    spend it on one fast accent at the hard cap; a script that is already running flat out has an
    empty bucket, so every further segment is held at the soft cap. That is exactly the
    soft/hard distinction, and it is one line of arithmetic rather than a special case for accents.

    `soft=None` (or `budget=0`) collapses this to the old single-cap slew limiter, which is what
    `handy1` still uses: 364 u/s there is a firmware ceiling read off the device, not a taste, so
    there is no softer figure to sustain and nothing to bank.

    CYCLIC. Every row here is Loop=true, and Edi's InproveLoopDetection rewrites the last action to
    match the first at load. So a limiter that simply runs start-to-end leaves the wrap unclipped:
    the tail lags, gets forced back to the head position, and that jump is over the limit again -
    which is exactly what a first attempt produced, 10 transitions up to 1633 u/s all sitting on
    the final segment. Running repeatedly, each pass starting where the last ended, converges to a
    position where the loop closes on its own and no segment (the wrap included) exceeds `hard`.
    The bucket carries across a pass boundary the same way the position does, for the same reason.
    """
    if soft is None:
        soft, budget = hard, 0.0
    cur, bank = float(acts[0]["pos"]), budget
    for _ in range(passes):
        out, c, bucket = [{"at": acts[0]["at"], "pos": cur}], cur, bank
        for a, b in zip(acts, acts[1:]):
            dt = (b["at"] - a["at"]) / 1000.0
            # A non-monotonic pair - two actions at the same millisecond, or a tail that runs
            # backwards - has no speed to limit, and a negative dt inverts the clamp below and
            # drags every position after it. Pass it through and let `nonmonotonic()` report the
            # file: it is a defect in the master, not something a limiter should quietly repair.
            if dt <= 0:
                c = float(b["pos"])
                out.append({"at": b["at"], "pos": max(0.0, min(100.0, c))})
                continue
            reach = min(hard * dt, soft * dt + bucket)
            step = max(-reach, min(reach, b["pos"] - c))
            bucket = max(0.0, min(budget, bucket + soft * dt - abs(step)))
            c += step
            out.append({"at": b["at"], "pos": max(0.0, min(100.0, c))})
        if abs(out[-1]["pos"] - cur) < 0.05:
            break
        cur, bank = out[-1]["pos"], bucket
    return [{"at": p["at"], "pos": int(round(p["pos"]))} for p in out]


def nonmonotonic(acts):
    """[(i, at_prev, at)] for every pair whose timestamps do not advance.

    Three of the femboy-witch masters end `61128 ms` then `60000 ms` - a tail written out of order,
    past the row's own 60 s duration. Nothing had ever reported it: `speedcheck.analyse` drops
    `dt <= 0` segments before it measures anything, and packages are not in `speedcheck` at all."""
    return [(i, a["at"], b["at"]) for i, (a, b) in enumerate(zip(acts, acts[1:]))
            if b["at"] <= a["at"]]


def rng(a):
    return max(x["pos"] for x in a) - min(x["pos"] for x in a)


# WHICH VARIANTS EXIST, AND WHY EACH ONE IS WARRANTED. Measured against the master:
#
#   handy1 - 364 u/s (110 mm @ 400 mm/s, firmware). The median transition across the whole master
#     set is 363 u/s, so half of everything sits at or over the cap. That is sustained excess and
#     it mushes. One cap, not two: 364 is a firmware ceiling read off the device, not a taste, so
#     there is no softer figure to sustain. (The eroscripts guide quotes 400 soft / 500 hard in
#     *units* for a Handy 1, which is above the firmware's own mm/s ceiling; the device wins.)
#
#   handy2 - 600 soft / 700 hard, the eroscripts multi-axis guide's figures for "The Handy 2".
#     Its next row up, "The Handy 2 Overclocked" (700/800), was the first choice and is not used:
#     overclocking is a 2 Pro feature, so that row is most likely about the same device the master
#     is authored for - and the guide's author says outright he owns neither and took the numbers
#     from forum searching. A folder named after a device should carry that device's own row.
#     Against the master this clips 16 rows, all of them the loud ones: `imp_3` goes from a
#     1041 u/s median to under 600 with its full 0-100 range intact, and the whole set gives up
#     107 position units of range in total.
#
#   handy2pro - the master itself, not generated. A 2 Pro at max overclock manages 1200 mm/s over
#     125 mm = 960 u/s off the device's own slider-overclocking menu (review articles say 800 mm/s
#     and are low by a third; the guide has no 2 Pro row at all, and the one figure its comments
#     offer - 1200 units/s - is *higher* than ours). Against that the master runs p95 901 u/s,
#     under the cap, and exactly one script (`imp_3`) has a median above it. Eleven others exceed
#     only on isolated accents, which scripters write deliberately: the best reference script here,
#     shared_zombie, has a 1538 u/s (1923 mm/s) jolt that no device can literally reach and that
#     reads as a snap. Clipping those would remove intended punch from the one device fast enough
#     to enjoy it. The master IS the Handy 2 Pro script; do not limit it.
#
# `budget` is the token bucket in `slew` - position units of travel that may be spent above the
# soft cap. 20 units at a 100 u/s excess rate is ~0.2 s of accent at the hard cap before the soft
# cap takes over, which is a snap rather than a section. Raising it to 40 buys 0.4 s and recovers
# 7 more of the master's 157 over-soft transitions; past 80 nothing changes, because the master
# has no sustained run long enough to spend it.
VARIANTS = {
    "handy1": dict(hard=S.limit("handy1"), note="110 mm @ 400 mm/s firmware cap"),
    "handy2": dict(hard=700.0, soft=600.0, budget=20.0,
                   note="eroscripts multi-axis guide, The Handy 2"),
}


def caps(spec):
    """(hard, soft, budget) for a variant spec, with the single-cap case filled in."""
    return spec["hard"], spec.get("soft"), spec.get("budget", 0.0)


def describe(spec):
    hard, soft, budget = caps(spec)
    if soft is None:
        return f"{hard:.0f} units/s"
    return f"{soft:.0f} units/s sustained, {hard:.0f} peak (bucket {budget:.0f} units)"


def emit(variant, spec, rows, write, trees=None):
    trees = trees or TREES
    hard, soft, budget = caps(spec)
    if write:
        for t in trees:
            os.makedirs(os.path.join(t, variant), exist_ok=True)
    print(f"variant '{variant}' <- '{SRC}' at {describe(spec)} - {spec['note']}\n")
    print(f"{'scene':<28}{'range':>7}{'->':>4}{'':<3}{'p90 u/s':>9}{'->':>4}{'':<3}{'changed':>8}")
    n_changed = 0
    copied = []
    for r in rows:
        # Per-axis siblings (`<row>.<axis>.funscript`) are COPIED, not limited. The slew limit is a
        # stroke length in mm over a firmware speed cap - arithmetic that means nothing on an axis
        # measured in degrees - and the device this variant exists for has one axis and ignores the
        # rest anyway. Copying rather than skipping keeps the variant folders in parity, so a device
        # pointed at `handy1` never finds a row that is missing an axis the master has.
        for axis, src in S.axis_files(os.path.join(trees[0], SRC), r["FileName"]):
            if axis == "default":
                continue
            copied.append(os.path.basename(src))
            if write:
                for t in trees:
                    shutil.copyfile(src, os.path.join(t, variant, os.path.basename(src)))
        fp = os.path.join(trees[0], SRC, r["FileName"] + ".funscript")
        doc = json.load(open(fp, encoding="utf-8-sig"))
        a = doc["actions"]
        for i, t0, t1 in nonmonotonic(a):
            WARNINGS.append(f"NONMONOTONIC {SRC}/{r['FileName']}.funscript: action {i + 1} at "
                            f"{t0} ms is followed by {t1} ms")
        b = slew(a, hard, soft, budget)
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
            m["description"] = (f"{variant} variant of '{SRC}': slew-limited to {describe(spec)}. "
                                f"{spec['note']}. Timing identical; only strokes the device could "
                                f"not complete are shortened.")
            doc["metadata"] = m
            for t in trees:
                json.dump(doc, open(os.path.join(t, variant, r["FileName"] + ".funscript"),
                                    "w", encoding="utf-8"), indent=2)
    print(f"\n{n_changed} of {len(rows)} scripts differ from '{SRC}'")
    if copied:
        print(f"{len(copied)} per-axis script(s) copied unchanged (no stroke cap applies to a "
              f"non-linear axis): {', '.join(copied)}")
    stale = [os.path.basename(f) for f in sorted(glob.glob(
                os.path.join(trees[0], variant, "*.*.funscript")))
             if os.path.basename(f) not in copied]
    if stale:
        print(f"{len(stale)} per-axis script(s) in '{variant}' with no master in '{SRC}': "
              f"{', '.join(stale)}")
    print()


# Custom-enemy packages carry their own gallery, so they need the same variant folders the main
# gallery has - a device pointed at `handy2` that finds no `handy2/` under a package plays nothing
# for that enemy, the same parity failure §89 found for per-axis files. They have no
# Definitions.csv (the manifest declares their rows), so this walks the files instead.
#
# `handy1` is NOT regenerated here. Those package variants were authored by hand against the Handy
# 1, not slew-limited from the master, and overwriting them would throw that work away. Only
# variants this tool owns - currently `handy2` alone - are emitted for a package.
PACKAGES = os.path.join(ROOT, "BepInEx/custom-enemies")
WARNINGS = []
GENERATED_FOR_PACKAGES = ["handy2"]


def emit_packages(write):
    for pkg in sorted(os.listdir(PACKAGES)):
        src_dir = os.path.join(PACKAGES, pkg, "funscripts", SRC)
        if not os.path.isdir(src_dir):
            continue
        masters = sorted(glob.glob(os.path.join(src_dir, "*.funscript")))
        if not masters:
            continue
        for variant in GENERATED_FOR_PACKAGES:
            spec = VARIANTS[variant]
            hard, soft, budget = caps(spec)
            out_dir = os.path.join(PACKAGES, pkg, "funscripts", variant)
            if write:
                os.makedirs(out_dir, exist_ok=True)
            changed = 0
            for fp in masters:
                doc = json.load(open(fp, encoding="utf-8-sig"))
                a = doc["actions"]
                for i, t0, t1 in nonmonotonic(a):
                    WARNINGS.append(f"NONMONOTONIC {pkg}/{SRC}/{os.path.basename(fp)}: action "
                                    f"{i + 1} at {t0} ms is followed by {t1} ms")
                b = slew(a, hard, soft, budget)
                if any(x["pos"] != y["pos"] for x, y in zip(a, b)):
                    changed += 1
                if write:
                    doc = dict(doc)
                    doc["actions"] = b
                    m = dict(doc.get("metadata") or {})
                    m["description"] = (f"{variant} variant of '{SRC}': slew-limited to "
                                        f"{describe(spec)}. {spec['note']}. Timing identical; only "
                                        f"strokes the device could not complete are shortened.")
                    doc["metadata"] = m
                    json.dump(doc, open(os.path.join(out_dir, os.path.basename(fp)), "w",
                                        encoding="utf-8"), indent=2)
            print(f"package '{pkg}' -> {variant}: {len(masters)} script(s), {changed} limited")


def main():
    write = "--write" in sys.argv
    rows = P.definitions_rows(os.path.join(TREES[0], "Definitions.csv"))
    for variant, spec in VARIANTS.items():
        emit(variant, spec, rows, write)
    emit_packages(write)
    if WARNINGS:
        # Deduplicated: a master is read once per variant, so every warning would otherwise
        # appear as many times as there are variants generated from it.
        print(f"\n{len(set(WARNINGS))} master(s) with timestamps that do not advance - the limiter "
              f"passes these through untouched, and the FILE is what needs fixing:")
        for w in sorted(set(WARNINGS)):
            print(f"  {w}")
    if not write:
        print("\nre-run with --write to emit the variants")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Device-compliance check: is a script physically playable, and by what?

    .venv/bin/python code/speedcheck.py [--variant detailed|handy1]

Funscript positions are 0-100 over the device's full stroke, so the speed a transition demands is
  |dpos| / dt  ->  units/s,  and  units/s * stroke_mm / 100 -> mm/s.

Device ceilings (mm/s -> units/s at that device's stroke length). The 125 mm figures are read off
the slider-overclocking menu of the Handy 2 Pro this project is authored against, not from review
articles - those quote 800 mm/s for the overclock, which is wrong:

    Handy 1              110 mm, 400 mm/s firmware cap    -> 364 units/s
    Handy 2 Pro          125 mm, 450 mm/s stock           -> 360 units/s
    Handy 2 Pro max OC   125 mm, 1200 mm/s                -> 960 units/s
    (motor absolute      125 mm, 1600 mm/s                -> 1280 units/s - not selectable)

Those two keys were called `handy2` / `handy2_oc` until the device was identified properly; the
numbers never changed, only the name they were filed under.

The same menu sets a MINIMUM speed: 32 mm/s stock, 15 mm/s at max overclock. Below that the
motor will not track smoothly, so a very slow ramp is as unplayable as a very fast one - it just
fails in the other direction.

Past the cap the device does not fail loudly - it *collapses the stroke*, reaching a fraction of
the commanded travel before the next command arrives. Fast sections turn to mush and amplitude
quietly disappears, which is exactly the failure a script cannot show you on screen.

Multi-axis: a row may carry `<row>.<axis>.funscript` files beside its own script (Edi's `Axis`
enum, `AXES` below). Each is listed on its own line as `<row>.<axis>`. The device ceilings are a
travel in mm and apply to the linear axes only; the others are reported for point spacing alone.

Command rate matters separately: eroscripts' guide asks for >=100 ms between points (10/s), and
the original Handy guarantees only ~2 commands/s with ~6/s the practical ceiling. Points closer
than that are not reproduced, they are averaged away.
"""
import sys, os, csv, glob, json

import pncpaths as P

ROOT = P.ROOT

# Edi's `Axis` enum (`Edi.Core/Funscript/FileJson/FunscriptAxis.cs`), which is also its list of
# reserved filename tokens. A file is `<row>.<axis>.funscript` beside the row's own script, in the
# same variant folder, and Edi joins it to the row by name - `FunscriptRepository.ReadGallery`
# files each one into `gallery.AxesCommands[axis]`. No Definitions.csv row and no mod change.
AXES = ["default", "surge", "sway", "twist", "roll", "pitch", "vibrate", "valve", "suction",
        "rotate", "frequency", "volume", "pulseWidth"]

# The stroke caps below are a linear travel over a stroke length in mm. That arithmetic means
# nothing on an axis measured in degrees, so only these two are checked against a device ceiling.
LINEAR_AXES = {"default", "surge"}
DEV = {"handy1": (110, 400), "handy2pro": (125, 450), "handy2pro_oc": (125, 1200)}
DEV_MIN = {"handy1": 32, "handy2pro": 32, "handy2pro_oc": 15}   # mm/s floor, same menu
MIN_GAP = 100
# Positions are integers, so a transition can land a shade over the cap purely from rounding -
# 1 unit across a 16 ms gap is 62 u/s. Count only excess that could not be rounding.
TOL = 1.05


def axis_files(tree, stem):
    """[(axis, path)] for one row: its own script first, then any per-axis siblings.

    Edi decides the axis from the last dot-separated token of the filename, so a stem carrying a
    reserved token IS an axis file - which is also why row filenames must not contain a dot for any
    other purpose (`learnings/edi-integration.md`)."""
    out = []
    base = os.path.join(tree, stem + ".funscript")
    if os.path.exists(base):
        out.append(("default", base))
    known = {a.lower() for a in AXES if a != "default"}
    for f in sorted(glob.glob(os.path.join(tree, stem + ".*.funscript"))):
        tok = os.path.basename(f)[len(stem) + 1:-len(".funscript")]
        if tok.lower() in known:
            out.append((tok.lower(), f))
    return out


def limit(dev):
    mm, mms = DEV[dev]
    return mms / mm * 100.0


def floor(dev):
    """The device's MINIMUM tracking speed, in units/s. Below it the motor does not move smoothly,
    so a crawling ramp fails the same way an impossible one does - it just fails downward."""
    mm = DEV[dev][0]
    return DEV_MIN[dev] / mm * 100.0


def analyse(acts):
    segs = []
    for a, b in zip(acts, acts[1:]):
        dt = b["at"] - a["at"]
        dp = abs(b["pos"] - a["pos"])
        if dt > 0:
            segs.append((a["at"], dt, dp, dp / dt * 1000.0))
    if not segs:
        return None
    sp = sorted(s[3] for s in segs)
    return dict(n=len(acts), segs=segs,
                gaps=[s[1] for s in segs],
                mingap=min(s[1] for s in segs),
                short=sum(1 for s in segs if s[1] < MIN_GAP),
                peak=sp[-1], p95=sp[int(len(sp) * 0.95)],
                over={d: sum(1 for s in segs if s[3] > limit(d) * TOL) for d in DEV},
                # A hold is 0 u/s and is not a floor violation - the device is asked for no
                # motion at all. Only commanded motion too slow to track counts.
                under={d: sum(1 for s in segs if 0 < s[3] < floor(d)) for d in DEV})


def main():
    variant = "detailed"
    if "--variant" in sys.argv:
        variant = sys.argv[sys.argv.index("--variant") + 1]
    rows = P.definitions_rows()
    tree = os.path.join(P.GALLERY, variant)
    out, extra = [], []
    for r in rows:
        for axis, fp in axis_files(tree, r["FileName"]):
            a = json.load(open(fp, encoding="utf-8-sig"))["actions"]
            st = analyse(a)
            if not st:
                continue
            (out if axis in LINEAR_AXES else extra).append(
                (r["Name"] if axis == "default" else f"{r['Name']}.{axis}", axis, st))
    out.sort(key=lambda x: -x[2]["peak"])
    print(f"variant: {variant}")
    print(f"{'scene':<28}{'pts':>5}{'mingap':>7}{'<100ms':>7}{'peak u/s':>10}{'p95':>7}"
          f"{'>H1':>5}{'>Proc':>7}")
    for n, axis, s in out:
        print(f"{n:<28}{s['n']:>5}{s['mingap']:>7}{s['short']:>7}{s['peak']:>10.0f}{s['p95']:>7.0f}"
              f"{s['over']['handy1']:>5}{s['over']['handy2pro_oc']:>7}")
    if extra:
        # A degrees-per-second axis has no stroke length, so the mm/s ceilings do not apply and are
        # not printed. Point spacing still does: every device averages away points it cannot reach.
        print(f"\nnon-linear axes ({len(extra)}) - no stroke ceiling applies; spacing still does")
        print(f"{'scene':<28}{'pts':>5}{'mingap':>7}{'<100ms':>7}{'peak u/s':>10}{'p95':>7}")
        for n, axis, s in sorted(extra, key=lambda x: -x[2]["peak"]):
            print(f"{n:<28}{s['n']:>5}{s['mingap']:>7}{s['short']:>7}{s['peak']:>10.0f}"
                  f"{s['p95']:>7.0f}")
    print(f"\nlimits: handy1 {limit('handy1'):.0f} u/s | handy2pro {limit('handy2pro'):.0f}"
          f" | handy2pro max OC {limit('handy2pro_oc'):.0f}   (min gap {MIN_GAP} ms, tol x{TOL})")
    bad_h1 = [n for n, _, s in out if s["over"]["handy1"]]
    bad_oc = [n for n, _, s in out if s["over"]["handy2pro_oc"]]
    slow_oc = [n for n, _, s in out if s["under"]["handy2pro_oc"]]
    bad_gap = [n for n, _, s in (out + extra) if s["short"]]
    print(f"exceed Handy 1     : {len(bad_h1)}/{len(out)}  {bad_h1[:12]}")
    # The line that matters for the device this project is authored against. It was missing until
    # the 2 Pro was identified, so the per-row `>Proc` column had no summary and nobody read it.
    print(f"exceed 2 Pro OC    : {len(bad_oc)}/{len(out)}  {bad_oc[:12]}")
    print(f"under 2 Pro OC min : {len(slow_oc)}/{len(out)}  {slow_oc[:12]}")
    print(f"points <100 ms     : {len(bad_gap)}/{len(out)}  {bad_gap[:12]}")


if __name__ == "__main__":
    main()

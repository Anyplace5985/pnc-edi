#!/usr/bin/env python3
"""Rebuild the 3-imp grapple scenes from their animations.

    .venv/bin/python code/impgrab.py

The trio has two imps doing different things, and a whole-frame proxy averages them into mush.
Both scripts are measured from a colour mask instead: the shaft is tan (R>150,G>100,B>80) where
the imps are deep red (G~54), so counting tan pixels in a row band says how much of the shaft is
uncovered there.

  tip   rows 100-120, x 180-300 - the imp on the tip. More tan = exposed = withdrawn = 100.
  balls rows 180-200, x 180-300 - the imp on the balls.

In Imp_Grab_Cum the tip imp descends over cycle 0, stays down through cycles 1-2 and releases in
cycle 3, while the balls imp repeats its 875 ms bob all four times - which is why `stroke_period`
reports reps=4 for what is really a single 3500 ms arc. Trust the region, not the frame.

CONVENTIONS (from eroscripts' scripting guide and the OFS-authored scripts in _reference):

- **>=100 ms between points.** The original Handy guarantees ~2 commands/s and tops out near 6;
  anything denser is averaged away rather than reproduced. `shared_plantasha` - the best script
  in this set, verified to 0.3% - puts 90% of its gaps at >=100 ms, with the mode at 125-150.
- **Buzz is a half-range oscillation, not a tremor.** `shared_zombie`'s cum section alternates
  0<->50 every ~100-120 ms (410-540 u/s). A +-7 wiggle is imperceptible on the hardware; 50 units is
  what actually reads as vibration on a stroker, which has no vibrator motor to use instead.
- **Speed** = |dpos|/dt -> units/s. Handy 1 caps near 364 u/s, a Handy 2 Pro at max overclock 960.
  Bursts above are normal (shared_plantasha peaks at 644, median 274); sustained excess is what
  makes a Handy 1 collapse its stroke. See code/speedcheck.py.
"""
import sys, os, json

import animcheck as A
import pncpaths as P

ROOT = P.ROOT
DIRS = [P.DETAILED]
TIP, BALLS, XS = (100, 120), (180, 200), (180, 300)
BUZZ_LO, BUZZ_HI, BUZZ_STEP = 0, 50, 104     # 0<->50 every ~104 ms, as shared_zombie does
HOLD_ENTER = 0.15                             # tip below this = the imp is down and staying


def bands(sprites):
    import numpy as np
    tip, balls = [], []
    for s in sprites:
        a = np.array(s.read().image.convert("RGB")).astype(int)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R > 150) & (G > 100) & (B > 80)
        tip.append(int(m[TIP[0]:TIP[1], XS[0]:XS[1]].sum()))
        balls.append(int(m[BALLS[0]:BALLS[1], XS[0]:XS[1]].sum()))
    return tip, balls


def norm(v):
    lo, hi = min(v), max(v)
    return [(x - lo) / (hi - lo) for x in v] if hi > lo else [0.0] * len(v)


def thin(items, min_gap=100):
    """Enforce the >=100 ms floor on a merged list of (at, pos, priority).

    Needed because the buzz runs on its own ~104 ms grid and the descend/release run on the
    animation's 125 ms frame grid, so the two collide wherever they meet - the first version put
    a buzz point 4 ms before a frame point, which reads as a 15000 u/s jump. Structural points
    (priority 1) win; a buzz point that crowds one is dropped, not the other way round."""
    out = []
    for at, pos, pri in sorted(items, key=lambda x: x[0]):
        if out and at - out[-1][0] < min_gap:
            if pri > out[-1][2]:
                out[-1] = (at, pos, pri)          # structural point displaces the buzz
            continue                              # else drop this one
        out.append((at, pos, pri))
    return [{"at": a, "pos": p} for a, p, _ in out]


def write(stem, acts, clip, note, total):
    doc = {"actions": acts, "inverted": False, "range": 100, "version": "1.0", "metadata": {
        "bookmarks": [], "chapters": [], "creator": "", "performers": [], "tags": [], "notes": "",
        "license": "", "script_url": "", "video_url": "", "type": "basic",
        "duration": round(total / 1000), "title": stem,
        "description": f"Rebuilt from {clip} by code/impgrab.py. {note} {total}ms."}}
    for d in DIRS:
        json.dump(doc, open(os.path.join(d, stem + ".funscript"), "w", encoding="utf-8"), indent=2)


def build_loop(env):
    """Pure stroke, one point per animation frame (125 ms) - already above the 100 ms floor."""
    sp, dur, fps = A.clip_frames(env, "Imp_Grab_Loop")
    tip, _ = bands(sp)
    base = norm(tip)
    n, step, cycles = len(tip), dur / len(tip), 2
    acts = thin([(int(round(c * dur + i * step)), int(round(base[i] * 100)), 1)
                 for c in range(cycles) for i in range(n)])
    total = int(round(dur * cycles))
    acts.append({"at": total, "pos": acts[0]["pos"]})
    write("imp_grab_loop", acts, "Imp_Grab_Loop",
          "Stroke follows the imp on the tip, one point per frame (125ms). No buzz - the balls "
          "imp bobs at the same 875ms as the stroke here, so a second rhythm would only fight it.",
          total)
    print(f"imp_grab_loop   {len(acts):>3} actions  {total}ms   tip {tip}")


def build_cum(env):
    """Descend -> buzz while held deep -> release. The buzz is the balls imp, and it is the
    point of the scene: the tip imp is locked down for 2.1 s of the 3.5 s, so without it the
    script is a slow dip and nothing else."""
    sp, dur, fps = A.clip_frames(env, "Imp_Grab_Cum")
    tip, balls = bands(sp)
    base, amp = norm(tip), norm(balls)
    n, step = len(tip), dur / len(tip)
    held = [i for i, v in enumerate(base) if v < HOLD_ENTER]
    h0, h1 = held[0] * step, (held[-1] + 1) * step
    items = []
    for i in range(n):                                   # descend + release, per frame
        t = i * step
        if h0 <= t < h1: continue
        items.append((int(round(t)), int(round(base[i] * 100)), 1))
    t, k = h0, 0                                         # buzz through the hold
    while t < h1:
        f = min(n - 1, int(t / step))
        hi = BUZZ_HI * (0.75 + 0.25 * amp[f])            # swell with the balls imp
        items.append((int(round(t)), int(round(hi if k % 2 else BUZZ_LO)), 0))
        t += BUZZ_STEP; k += 1
    acts = thin(items)
    total = int(round(dur))
    if total - acts[-1]["at"] < 100: acts.pop()
    acts.append({"at": total, "pos": acts[0]["pos"]})
    write("imp_grab_cum", acts, "Imp_Grab_Cum",
          f"Tip imp descends, is held deep from {h0:.0f}-{h1:.0f}ms, then releases. The hold is "
          f"scripted as a {BUZZ_LO}<->{BUZZ_HI} buzz every {BUZZ_STEP}ms (the technique "
          f"shared_zombie uses), amplitude swelling with the balls imp.", total)
    print(f"imp_grab_cum    {len(acts):>3} actions  {total}ms   hold {h0:.0f}-{h1:.0f}ms")


if __name__ == "__main__":
    env = A.load_env()
    build_loop(env); build_cum(env)

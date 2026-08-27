#!/usr/bin/env python3
"""Retiming pass: every script's length against its own animation's timing.

    .venv/bin/python code/retime.py                 # report only
    .venv/bin/python code/retime.py --apply         # fix everything <= 5% off
    .venv/bin/python code/retime.py --apply --max-pct 2

Timing here is objective: an AnimationClip is a sprite list at a fixed sample rate, so the
duration comes straight out of the shipped assets - none of ../learnings/funscript-timing.md's
measurement traps.

**Every Definitions.csv row is Loop=true**, so a script whose length is not a whole number of
animation periods slips a little on every repeat.  The period is the clip duration, unless the
clip itself holds N identical repeats (`stroke_period`), in which case it is the sub-period.

Fixing means *scaling* the whole script to the target, not trimming: trimming costs real content
and desyncs the shape (CHANGELOG "Tried and reverted").  A scale under ~5% is well below the
just-noticeable difference for stroke timing, so it removes the drift without changing the feel.
Anything larger is a rate or authoring problem and is reported, never auto-applied.

WARN flags a clip with a near-miss sub-repeat (aligned ratio 0.5-0.9).  A genuine repeat scores
far lower - `imp gangbang 2` is 0.12 - but the column exists because that one hid for a day.

a.strk / s.strk / rate compare the animation's stroke period against the script's.  **This is a
ranking aid, not a verdict** - the same standing as polarity.  s.strk is solid (it reads the
script's own actions); a.strk divides the cycle by the maxima a silhouette proxy can see, and
that proxy does not resolve individual strokes inside a long varied clip - `Gravy_Cum` reports
one 7000 ms "stroke" for a 56-frame sequence.  Trust it where the cycle plausibly IS one stroke
(short clips, few frames); elsewhere use it to pick what to look at.  It is worth having because
length and rate fail independently: `imp_1` was exactly 11.000 cycles while stroking 1.56x
slower than its animation, and only the rate column showed it (CHANGELOG 34b).
"""
import sys, os, csv, json

import animcheck as A
import pncpaths as PATHS
import proxies as P
from animsweep import MAP

ROOT = PATHS.ROOT
CSVS = [PATHS.DEFINITIONS]
DIRS = [PATHS.DETAILED]


def near_miss(sprites, dur):
    """Sub-repeats that scored between the detection threshold and 'clearly not a repeat'."""
    import numpy as np
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.size[0] for i in ims); H = max(i.size[1] for i in ims)
    st = []
    for im in ims:
        a = np.zeros((H, W, 4), np.float32); arr = np.array(im).astype(np.float32)
        a[H - arr.shape[0]:H, :arr.shape[1]] = arr; st.append(a)
    st = np.stack(st); lum = st[..., :3].mean(3) * (st[..., 3] / 255.0); n = len(st)

    def d(a, b, span=3):
        best = None
        for dx in range(-span, span + 1):
            x = a[:, max(0, dx):]; y = b[:, max(0, -dx):]
            w = min(x.shape[1], y.shape[1])
            v = float(np.abs(x[:, :w] - y[:, :w]).mean())
            if best is None or v < best: best = v
        return best

    base = float(np.mean([d(lum[i], lum[(i + 1) % n]) for i in range(n)]))
    hits = []
    for k in range(2, n):                       # k=1 is "one frame", never a stroke
        if n % k: continue
        v = float(np.mean([d(lum[i], lum[i + k]) for i in range(n - k)])) / max(base, 1e-9)
        if 0.5 <= v < 0.9: hits.append(f"{n//k}x@{dur*k/n:.0f}ms={v:.2f}")
    return hits


def _peaks(vals, frac=0.25):
    """Indices of local maxima at least `frac` of the full range above the minimum."""
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-9:
        return []
    bar = lo + (hi - lo) * frac
    return [i for i in range(len(vals))
            if vals[i] >= bar
            and vals[i] >= vals[i - 1 if i else len(vals) - 1]
            and vals[i] > vals[(i + 1) % len(vals)]]


def script_stroke(acts):
    """The script's OWN stroke period: median spacing of prominent position maxima."""
    pos = [a["pos"] for a in acts]; at = [a["at"] for a in acts]
    pk = [at[i] for i in _peaks(pos)]
    if len(pk) < 2:
        return None
    gaps = sorted(pk[i + 1] - pk[i] for i in range(len(pk) - 1))
    return gaps[len(gaps) // 2]


def anim_stroke(sprites, period, reps, scene=None):
    """The animation's stroke period - its cycle divided by the strokes visible inside it.

    `stroke_period` only finds *identical* repeats, so a long varied clip reports reps=1 and its
    "period" is the whole sequence, not a stroke: `Gravy_Cum` is one 7000 ms cycle containing
    dozens of strokes.  Comparing a script's stroke against that is meaningless, so count the
    proxy's maxima within one cycle first.

    Rate and length are independent failures.  `imp_1` sat at exactly 11.000 cycles of its
    animation while stroking 1.56x slower than it: the length check said 'ok' and the device
    still lagged the picture.  A rate mismatch also voids the polarity correlation, because the
    sweep samples the script at the animation's period and the phase drifts across cycles."""
    n = len(sprites) // reps
    vals = P.proxy_for(scene, sprites, A.motion_proxy)[0][:n]
    k = len(_peaks(vals))
    return (period / k) if k else None


def scan():
    env = A.load_env()
    rows = {r["Name"]: r for r in csv.DictReader(open(CSVS[0], encoding="utf-8-sig"))}
    out = []
    for name, clip in MAP.items():
        sprites, dur, fps = A.clip_frames(env, clip)
        fp = os.path.join(DIRS[0], name.lower() + ".funscript")
        if not sprites or not os.path.exists(fp):
            continue
        period, reps = A.stroke_period(sprites, dur)
        if name in P.ONESHOT:
            period, reps = dur, 1                    # a single arc has no cycle to align to
        acts = json.load(open(fp, encoding="utf-8-sig"))["actions"]
        end = acts[-1]["at"]
        sstroke = script_stroke(acts)
        astroke = anim_stroke(sprites, period, reps, name)
        n = max(1, round(end / period))
        target = int(round(n * period))
        out.append(dict(name=name, clip=clip, dur=dur, reps=reps, period=period, end=end,
                        units=end / period, target=target,
                        err=(end - target) / target * 100 if target else 0.0,
                        sstroke=sstroke, astroke=astroke,
                        rate=(sstroke / astroke) if (sstroke and astroke) else None,
                        csv_end=int(rows.get(name, {}).get("EndTime", 0) or 0),
                        warn=near_miss(sprites, dur)))
    out.sort(key=lambda r: -abs(r["err"]))
    return out


def apply(rec):
    """Scale a script to its target length and update Definitions.csv."""
    s = rec["target"] / rec["end"]
    for d in DIRS:
        fp = os.path.join(d, rec["name"].lower() + ".funscript")
        doc = json.load(open(fp, encoding="utf-8-sig"))
        acts, seen, new = doc["actions"], set(), []
        for a in acts:
            at = int(round(a["at"] * s))
            if at in seen: continue
            seen.add(at); new.append({"at": at, "pos": int(a["pos"])})
        if len(new) > 1 and rec["target"] <= new[-2]["at"]:
            new.pop()                                  # scaling collapsed it onto its neighbour
        new[-1]["at"] = rec["target"]                  # exact, no rounding slop
        new[-1]["pos"] = new[0]["pos"]                 # keep the loop seam closed
        doc["actions"] = new
        doc.setdefault("metadata", {})["duration"] = round(rec["target"] / 1000)
        json.dump(doc, open(fp, "w", encoding="utf-8"), indent=2)
    for c in CSVS:
        raw = open(c, encoding="utf-8-sig", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.split(nl)
        for i, l in enumerate(lines):
            f = l.split(",")
            if len(f) >= 4 and f[0] == rec["name"]:
                f[3] = str(rec["target"]); lines[i] = ",".join(f)
        open(c, "w", encoding="utf-8", newline="").write("﻿" + nl.join(lines))


def main():
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    cap = 5.0
    if "--max-pct" in sys.argv:
        cap = float(sys.argv[sys.argv.index("--max-pct") + 1])
    recs = scan()
    print(f"{'scene':<28}{'clip':>7}{'rep':>4}{'period':>8}{'script':>8}{'units':>8}"
          f"{'target':>8}{'err%':>8}{'a.strk':>8}{'s.strk':>8}{'rate':>7}  flags")
    for r in recs:
        f = []
        if r["csv_end"] != r["end"]: f.append(f"CSV={r['csv_end']}")
        if r["warn"]: f.append("WARN " + ",".join(r["warn"]))
        aa = f"{r['astroke']:.0f}" if r["astroke"] else "-"
        ss = f"{r['sstroke']}" if r["sstroke"] else "-"
        rt = f"{r['rate']:.2f}x" if r["rate"] else "-"
        print(f"{r['name']:<28}{r['dur']:>7.0f}{r['reps']:>4}{r['period']:>8.1f}{r['end']:>8}"
              f"{r['units']:>8.3f}{r['target']:>8}{r['err']:>+8.2f}{aa:>8}{ss:>8}{rt:>7}  {' '.join(f)}")

    # Floor at 0.1%: several periods are not a whole number of ms (555.6, 666.7, 888.9), so the
    # target is itself rounded and a 1 ms "error" is that rounding, not drift.
    todo = [r for r in recs if 0.1 < abs(r["err"]) <= cap]
    over = [r for r in recs if abs(r["err"]) > cap]
    print(f"\n{len(todo)} scene(s) fixable at <= {cap}%; {len(over)} beyond it (report only)")
    if "--apply" not in flags:
        print("re-run with --apply to scale the fixable ones")
        return 0
    for r in todo:
        apply(r)
        print(f"  {r['name']:<28} {r['end']:>6} -> {r['target']:<6} ({r['err']:+.2f}%)")
    print(f"applied {len(todo)}; still out of range:")
    for r in over:
        print(f"  {r['name']:<28} {r['end']:>6} vs {r['target']:<6} ({r['err']:+.2f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Validate funscripts against the game's own sprite animations.

    .venv/bin/python code/animcheck.py <clip name> <funscript stem> [--sheet] [--motion]

These are 2D sprite animations: an AnimationClip is an ordered list of Sprite references at a
fixed sample rate, so the exact frame sequence *and* the exact duration are readable from the
shipped assets. No video capture, no autocorrelation, none of the measurement traps in
PROJECT.md.

Motion proxy: every sprite in a sheet is alpha-trimmed from the top and shares a bottom edge, so
the trimmed height is the silhouette's top edge. That tracks the moving mass directly and is a
*signed* signal, unlike a frame-difference magnitude (which peaks twice per stroke - see
../learnings/funscript-timing.md "magnitude signals give the half-period").

The proxy has no idea which end is "deep". Run with --sheet, look at the contact sheet, and pass
--invert if the mass being low means deep. `--motion` draws a variance map, which answers "what
moves at all" before you pick anything to measure - see motion_map.
Convention: deep / enveloped = pos 0.
"""
import json, os, sys, tempfile

import pncpaths as P

# Re-exported: `refvideo` and the sweeps reach the repo and the assets through this module, which
# is the one they already import. `pncpaths` is where both actually live.
ROOT = P.ROOT
FILES = P.ASSET_FILES


def game_data_dir():
    """The `*_Data` folder of a game install. Not in this repo - the repo holds the mod only.

    Default is whatever `game-windows` points at. `PNC_GAME_DIR` overrides it, which is how you
    measure against a different build: every number in TIMING-AUDIT.md and the 63/63 sweep came
    from 0.2.1, now at `../Archive/PNC 0.2.1 Win`."""
    return P.game_data_dir("animcheck")


def load_env():
    import UnityPy
    data = game_data_dir()
    return UnityPy.load(*[os.path.join(data, f) for f in FILES])


def _first_pptr_curve(sprites):
    """The leading run whose frame numbers strictly increase - i.e. the first of several curves.

    A clip can animate more than one SpriteRenderer, and `pptrCurveMapping` then holds the curves
    back to back with nothing marking the boundary.  A real sequence never counts backwards, so
    the boundary is the first frame number that does not increase on its predecessor:

        GooperGrabScreen     blowjob_1-Sheet_0..7   then Goop_overlay-Sheet_0  -> cut at 8
        GooperGrabScreenCum  blowjob_CUM-Sheet_0..13 then Goop_overlay-Sheet_0 -> cut at 14

    This is only ever reached when `genericBindings` reports more than one PPtr curve, which is
    what makes the plain rule safe.  `GhoulGrabCum` is the clip that looks like a counter-example -
    one curve whose sprites run `Nun Sex CUM-Sheet_1_0..21` and then `Nun Sex CUM-Sheet_3_0..10`,
    a restart at _0 that this rule would cut - but it declares **one** PPtr curve, so it never
    arrives here.  The earlier version tried to tell the two apart by sheet name and could not:
    names cannot separate "a second object" from "page 2 of the same atlas", and trying made it
    let one frame of the second curve through (§69).
    """
    def num(s):
        head, _, tail = s.rpartition("_")
        return int(tail) if tail.isdigit() else None

    out = []
    prev = None
    for s in sprites:
        k = num(s.read().m_Name)
        if k is not None and prev is not None and k <= prev:
            break                                   # counted backwards: a new curve starts here
        if k is not None:
            prev = k
        out.append(s)
    return out


def clip_frames(env, clip_name):
    """(sprites, clip length in ms, sample rate).

    The clip length is `m_StopTime` - what the animator loops on - and is NOT always
    len(sprites)/rate: `GooperGrabScreenCum` is 1500 ms because its overlay curve runs 15 samples
    where the body runs 14, so the body holds its last frame for the final 100 ms.  Frame k plays
    at k/rate, never at k*dur/n; use `frame_times`."""
    # {file basename: {path_id: obj}}. Keying on path_id alone across the three loaded files is
    # wrong and ../learnings/asset-inspection.md says so: `m_FileID` is part of a PPtr's identity.
    # It went unnoticed for
    # a long time because on the two Gooper clips it *helped* - the overlay sprites came back as
    # Texture2D from the wrong file and were filtered out, leaving the body frames by accident.
    # On game 0.3.1 the same bug stops helping: `BlackSerpent GrabScreen` lives in
    # resources.assets, so all 7 of its m_FileID=0 pointers resolved into sharedassets0 and the
    # clip read as **zero frames** (§69).
    by_file = {}
    for o in env.objects:
        by_file.setdefault(os.path.basename(getattr(o.assets_file, "name", "") or ""),
                           {})[o.path_id] = o

    def resolve(owner, pptr):
        """m_FileID 0 means the owning file; n means its externals[n-1]."""
        pid = pptr.get("m_PathID")
        if not pid:
            return None
        fid = pptr.get("m_FileID", 0)
        if fid == 0:
            name = os.path.basename(getattr(owner.assets_file, "name", "") or "")
        else:
            try:
                name = os.path.basename(owner.assets_file.externals[fid - 1].path)
            except (IndexError, AttributeError):
                return None
        return by_file.get(name, {}).get(pid)

    for o in env.objects:
        if o.type.name != "AnimationClip":
            continue
        d = o.read_typetree()
        if d.get("m_Name") != clip_name:
            continue
        bind = d["m_ClipBindingConstant"]
        pm = bind.get("pptrCurveMapping") or []
        got = [resolve(o, p) for p in pm]
        sprites = [s for s in got if s is not None and s.type.name == "Sprite"]
        ncurves = sum(1 for b in (bind.get("genericBindings") or []) if b.get("isPPtrCurve"))
        if ncurves > 1:
            sprites = _first_pptr_curve(sprites)
        return sprites, float(d["m_MuscleClip"]["m_StopTime"]) * 1000.0, float(d["m_SampleRate"])
    return [], 0.0, 0.0


def frame_times(n, dur, fps):
    """When each sprite frame is on screen.  Sprite keyframes sit on the sample grid, so frame k
    starts at k/fps; `dur` is only how long the animator holds the whole clip before looping."""
    return [k * 1000.0 / fps for k in range(n)] if fps else [k * dur / max(n, 1) for k in range(n)]


def stroke_period(sprites, dur):
    """A clip may repeat several times within its own length - ../learnings/funscript-timing.md's
    "compare stroke
    rate, not cycle period". Find the smallest sub-period whose frames match.

    Frames are compared at their best integer x-offset. Sprite sheets are alpha-trimmed per
    frame, so a repeat drawn a pixel to one side is still a repeat - but a uniform 1px shift
    misaligns every edge in the image and dominates a mean-absolute-difference. That is exactly
    how `imp gangbang 2` hid: its two halves are identical at dx=+1 (ratio 0.12) and scored 0.70
    unaligned, just past the threshold, so it read as one 1200ms stroke instead of two 600ms
    ones - and the whole "D5 and D6 are 2x apart" conclusion followed from that."""
    import numpy as np
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.size[0] for i in ims); H = max(i.size[1] for i in ims)
    st = []
    for im in ims:
        a = np.zeros((H, W, 4), np.float32); arr = np.array(im).astype(np.float32)
        a[H - arr.shape[0]:H, :arr.shape[1]] = arr; st.append(a)
    st = np.stack(st); lum = st[..., :3].mean(3) * (st[..., 3] / 255.0)
    n = len(st)

    def diff(a, b, span=3):
        best = None
        for dx in range(-span, span + 1):
            x = a[:, max(0, dx):]; y = b[:, max(0, -dx):]
            w = min(x.shape[1], y.shape[1])
            d = float(np.abs(x[:, :w] - y[:, :w]).mean())
            if best is None or d < best:
                best = d
        return best

    base = float(np.mean([diff(lum[i], lum[(i + 1) % n]) for i in range(n)]))
    for k in range(1, n):
        if n % k:
            continue
        d = float(np.mean([diff(lum[i], lum[i + k]) for i in range(n - k)]))
        if d < base * 0.5:                      # repeats are far closer than neighbours
            return dur * k / n, n // k
    return dur, 1


def signed_shift(sprites):
    import numpy as np
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.size[0] for i in ims); H = max(i.size[1] for i in ims)
    st = []
    for im in ims:
        a = np.zeros((H, W, 4), np.float32); arr = np.array(im).astype(np.float32)
        a[H - arr.shape[0]:H, :arr.shape[1]] = arr; st.append(a)
    st = np.stack(st); lum = st[..., :3].mean(3) * (st[..., 3] / 255.0)
    med = np.median(lum, axis=0); rows = np.arange(H)[:, None].astype(np.float32)
    out = []
    for i in range(len(st)):
        d = lum[i] - med
        pos = np.clip(d, 0, None); neg = np.clip(-d, 0, None)
        if pos.sum() < 1e-6 or neg.sum() < 1e-6:
            out.append(0.0); continue
        cp = float((rows * pos).sum() / pos.sum())     # content appeared here
        cn = float((rows * neg).sum() / neg.sum())     # content vanished from here
        out.append(cn - cp)                            # > 0 : mass moved up
    return out


def top_edges(sprites):
    return [float(s.read().image.size[1]) for s in sprites]   # taller = mass reaches higher


def motion_proxy(sprites):
    """Pick the proxy: silhouette top edge, or signed displacement when the outline is pinned.

    The test is the top edge's range as a FRACTION of sprite height, not whether it is exactly
    zero. Four scenes move 1.4-2.4% (3-5 px on a 127-280 px sprite) - that is alpha-trim jitter,
    not motion, and reading it as signal produces phantom strokes: `ambient_imp_gangbang_2`'s
    3 px wobble made its 600 ms cycle look like two 300 ms strokes. 3% keeps `Gargoyle_Grabbed`
    (5.9%, 16 px) on the silhouette, where it belongs."""
    tops = top_edges(sprites)
    if max(tops) - min(tops) > max(tops) * 0.03:
        return tops, "sil"
    return signed_shift(sprites), "sig"


def motion_map(sprites, path):
    """Per-pixel variance across the clip, drawn in red over frame 0. Returns (busiest x, y, size).

    "What moves?" is the first question for any scene, and ../learnings/funscript-proxies.md's
    answer - describe what is
    on screen - is much easier with one picture than by flipping between frames. It also names the
    *region* to measure, which is the decision a whole-frame proxy gets wrong: the 3-imp grapple,
    `Wendigo_Continued`, and every diorama added in 0.3.1.

    Read it for where the change is concentrated, not for how much there is. A thin outline all
    round a body is that body translating a pixel or two; a bright blob in one place is a part
    moving against the rest, and that is the thing worth a proxy.
    """
    from PIL import Image as _Image
    import numpy as _np
    ims = [s.read().image.convert("RGBA") for s in sprites]
    H = max(i.height for i in ims); W = max(i.width for i in ims)
    stack = _np.zeros((len(ims), H, W, 4), dtype=_np.float32)
    for k, im in enumerate(ims):
        # Sprites are alpha-trimmed per frame and not registered to each other (CHANGELOG 33),
        # so paste onto one canvas against the shared bottom edge before comparing anything.
        stack[k, H - im.height:, :im.width] = _np.asarray(im).astype(_np.float32)
    lum = stack[..., :3].mean(axis=3) * (stack[..., 3] > 128)
    var = lum.std(axis=0)
    base = (lum[0] / max(1e-6, float(lum.max())) * 90).astype(_np.uint8)
    img = _np.dstack([base, base, base])
    img[..., 0] = _np.maximum(img[..., 0], (var / max(1e-6, float(var.max())) * 255).astype(_np.uint8))
    out = _Image.fromarray(img, "RGB").resize((W * 3, H * 3), _Image.NEAREST)
    out.save(path)
    return int(var.sum(axis=0).argmax()), int(var.sum(axis=1).argmax()), out.size


def contact_sheet(sprites, path, cols=4):
    from PIL import Image, ImageDraw
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.size[0] for i in ims)
    H = max(i.size[1] for i in ims)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (W * min(cols, len(ims)), H * rows), (20, 20, 24))
    dr = ImageDraw.Draw(sheet)
    for i, im in enumerate(ims):
        cell = Image.new("RGBA", (W, H), (20, 20, 24, 255))
        cell.paste(im, (0, H - im.size[1]), im)          # bottom-aligned, as in game
        x, y = (i % cols) * W, (i // cols) * H
        sheet.paste(cell.convert("RGB"), (x, y))
        dr.text((x + 6, y + 4), f"{i}", fill=(255, 80, 80))
    sheet.save(path)
    return sheet.size


def sample(actions, t):
    if t <= actions[0]["at"]:
        return float(actions[0]["pos"])
    if t >= actions[-1]["at"]:
        return float(actions[-1]["pos"])
    for i in range(len(actions) - 1):
        a, b = actions[i], actions[i + 1]
        if a["at"] <= t <= b["at"]:
            f = (t - a["at"]) / max(b["at"] - a["at"], 1)
            return a["pos"] + f * (b["pos"] - a["pos"])
    return float(actions[-1]["pos"])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) < 2:
        print(__doc__)
        return 2
    clip_name, stem = args[0], args[1]

    env = load_env()
    sprites, dur, fps = clip_frames(env, clip_name)
    if not sprites:
        print(f"clip {clip_name!r}: not found or has no sprite frames")
        return 1
    tops, pname = motion_proxy(sprites)
    n = len(sprites)
    period, reps = stroke_period(sprites, dur)
    print(f"{clip_name}: {n} frames, {dur:.1f}ms, {fps:.0f}fps")
    if reps > 1:
        print(f"  clip contains {reps} identical strokes -> true period {period:.1f}ms")

    # Both of these are things a person looks at once, so they go to a scratch directory rather
    # than into the tree. PNC_OUT_DIR overrides it; the system temp dir is the default because a
    # hardcoded one is a path that exists on exactly one machine.
    out = os.environ.get("PNC_OUT_DIR") or tempfile.gettempdir()

    if "--sheet" in flags:
        p = os.path.join(out, f"{stem}_frames.png")
        print("  contact sheet:", p, contact_sheet(sprites, p))

    if "--motion" in flags:
        p = os.path.join(out, f"{stem}_motion.png")
        cx, ry, size = motion_map(sprites, p)
        print(f"  motion map: {p} {size}  busiest column x={cx}, row y={ry}")

    lo, hi = min(tops), max(tops)
    if hi - lo < 1e-6:
        print("  nothing measurable moves in this clip")
        return 1
    print(f"  proxy: {'silhouette top edge' if pname == 'sil' else 'signed displacement'}")
    # higher on screen = withdrawn = 100, unless --invert
    want = [(t - lo) / (hi - lo) * 100.0 for t in tops]
    if "--invert" in flags:
        want = [100.0 - w for w in want]

    fp = os.path.join(ROOT, "Edi/Gallery/detailed", stem + ".funscript")
    actions = json.load(open(fp, encoding="utf-8-sig"))["actions"]
    end = actions[-1]["at"]
    cycles = max(1, int(round(end / dur)))
    ft = frame_times(n, dur, fps)
    got = []
    for k in range(n):
        vals = [sample(actions, c * dur + ft[k]) for c in range(cycles)]
        got.append(sum(vals) / len(vals))

    mg = sum(got) / n
    mw = sum(want) / n
    num = sum((g - mg) * (w - mw) for g, w in zip(got, want))
    den = (sum((g - mg) ** 2 for g in got) * sum((w - mw) ** 2 for w in want)) ** 0.5
    corr = num / den if den > 1e-9 else 0.0

    print(f"  script {stem}: {len(actions)} actions, {end}ms = {end/dur:.3f} cycles ({cycles} sampled)")
    print(f"\n  frame  animation  script")
    for i in range(n):
        print(f"    {i:<5}  {want[i]:8.1f}  {got[i]:6.1f}")
    print(f"\n  correlation {corr:+.3f}", end="")
    if corr < -0.3:
        print("   -> INVERTED (pos -> 100-pos fixes it)")
    elif corr > 0.3:
        print("   -> polarity agrees")
    else:
        print("   -> no clear relationship; wrong proxy or a shape problem")
    return 0


if __name__ == "__main__":
    sys.exit(main())

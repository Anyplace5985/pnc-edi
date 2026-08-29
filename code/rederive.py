#!/usr/bin/env python3
"""The six scenes `retime.py` reports and refuses, re-derived from their animations.

    .venv/bin/python code/rederive.py [--write]

`retime.py` only ever scales a script to a whole number of animation cycles, and it caps that at
5% because a larger scale changes how a scene feels. These six sat at 6-27%, so it left them
alone and the TODO carried them as "needs a feel pass: is it too fast or too slow?".

Pulling the frames answered a different question. **Only two of the six were a rate problem at
all**, and for one of those `retime`'s own target was wrong:

  Gooper_Start    the script holds TWO strokes at 1023 ms against an 800 ms animation.  retime
                  rounded 2046/800 to 3 cycles and proposed 2400, i.e. it would have stretched a
                  script that was already 28% too slow.  Two strokes = 1600 ms.
  Plantasha_Cum   two halves of 3566 ms against a 3875 ms cycle - a genuine clean scale, but the
                  spike at the end of each half lands ~600 ms after the animation's lift.
  Gooper_Cum      the animation's two strokes are NOT equal: 800 ms then 600 ms (the second skips
                  the two mid-descent frames), plus a 100 ms tail.  The script has two equal
                  870 ms strokes, so no single scale can fit it.
  Nun_Cum         300 ms descent, 2.7 s motionless, 300 ms lift.  A length problem only by
                  accident; what was wrong is where the events sit.
  Plantasha_Start a clean symmetric 1000 ms stroke in the animation against a wandering 0-60
                  wobble in the script.  A shape problem, not a length one.
  Wendigo_Start   its last 1.8 s is a wipe to black.  Nothing to be in sync with.

See CHANGELOG 48.  Conventions as everywhere else: >=100 ms between points, whole-cycle lengths,
loop seam closed, speeds judged by median rather than peak (PROJECT.md "Writing for the
hardware").  `authored.write` does the writing so there is one writer for the tree and the CSV.
"""
import sys, os

import pncpaths as PATHS
from authored import ROOT, write


def nun_cum():
    """GhoulGrabCum - 33 frames @10fps = 3300 ms.

    Almost nothing happens in this clip and that is the finding.  Measured as distance from the
    medoid (seated) pose - `proxies.nun_cum_motion` - the whole scene is:

        f0-f3    0-300 ms     she comes down onto it   (100, 95, 48, 16)
        f5-f8    500-800      settled, then bit-identical frames
        f9-f12   900-1200     a twitch, peak at f9     (15, 13, 7, 2)
        f13-f20  1300-2000    bit-identical
        f21      2100         the same twitch again, one frame long
        f22-f29  2200-2900    bit-identical
        f30-f32  3000-3200    she lifts off            (13, 60, 78) -> f0 = 100

    17 of the 33 frames are byte-for-byte identical to each other, so the two twitches are the only
    events in a 2.7 s hold.  The old script buzzed in three bursts - 660-1105, 1574-1853,
    3021-3300 - of which the first roughly coincided with the f9 twitch, the second had nothing
    behind it at all, and the third ran on top of the lift instead of leaving room for it.

    Buzz rather than a literal 0->15->0, on the cue that she does move a little here and the
    buzzes should sit on that: a 15-unit stroke is under the guide's 20% floor and would barely
    register, while 0<->40 at 125 ms (320 u/s) reads as a pulse the way `shared_zombie` does.
    Two bursts, not three, and the third one's slot is given back to the lift."""
    acts = [(0, 100), (100, 95), (200, 48), (300, 10), (500, 0),   # descent, frames 0-5
            (900, 40), (1025, 0), (1150, 40), (1275, 0),           # twitch 1, frames 9-12
            (2100, 40), (2225, 0),                                 # twitch 2, frame 21
            (3000, 0), (3100, 60), (3200, 78), (3300, 100)]        # lift off, frames 30-32
    return "Nun_Cum", acts, 3300


# --- the two Gooper grab scenes -------------------------------------------------------------
#
# They are ONE animation used three times.  `GooperGrabScreenCum`'s first 8 frames have the exact
# same silhouette sequence as the whole of `GooperGrabScreen` - 212, 210, 206, 198, 193, 189, 203,
# 211 px in both - redrawn on a separate sheet with the cum added; its frames 8-13 are that same
# stroke with the two mid-descent frames dropped.  So there is one stroke shape here, and it lives
# in one place.
#
# GOOPER is the silhouette top edge normalised 0-100.  The head (the upper blob, the one with the
# eyestalks) is the only thing that moves: row by row, the silhouette below row ~80 is identical in
# every frame and all the variation sits in rows 10-70.
GOOPER = [100, 91, 74, 39, 17, 0, 61, 96]           # frames 0-7, 100 ms apart
GOOPER_FAST = [GOOPER[i] for i in (0, 1, 4, 5, 6, 7)]   # the cum clip's second stroke

# Head-only work, so it does not use the whole range.  The guide makes blowjobs the exception to
# "avoid strokes under 20%" - short strokes are right "when the girl only works the head" - and
# she works the tip here rather than travelling any real depth.  100-50-100 was chosen by feel as
# the middle ground between that 10-20% advice and the "exaggerate rather than be literal" side
# that the first version took.  Change DEEP alone to move it; nothing else depends on the range.
DEEP = 50


def _band(v):
    """Normalised proxy value -> position, inside the DEEP..100 band."""
    return int(DEEP + v * (100 - DEEP) / 100 + 0.5)


def gooper_start():
    """GooperGrabScreen - 8 frames @10fps = 800 ms, scripted as 2 cycles.

    Polarity was confirmed good on an earlier feel pass and is unchanged here: the head
    descends onto it and low is deep.  Note that CHANGELOG 39's sleeve rule does not apply - that
    one inverts a *shaft-exposure* proxy ("shaft showing above the body means it slid to the base,
    which is deep"), and this is a *body-position* proxy.  The shaft rises from the player at the
    bottom of frame either way, so head-low is deep whether she is on the tip or sleeved on it.

    So the shape was never in question; the rate was.  The old script ran 1023 ms per stroke
    against an 800 ms animation, the same failure as `imp_1` (CHANGELOG 34b), and rounding its
    2046 ms to 3 cycles hid it: 2046/800 = 2.557 looks like "nearly 2.5 cycles" when the script
    plainly contains 2 strokes.  Count the script's strokes before trusting a cycle count.

    Derived straight from the frames, so the descent keeps the animation's 500/300 ms asymmetry.
    The old curve's little bounce at the bottom is dropped: nothing in the sprites rebounds, and
    the guide is explicit that skipping a stroke beats inventing one.

    Two cycles rather than one, matching the other grab loops (Nun_Grab 2x600, Mimic_Loop 2x625,
    Gargoyle_Grabbed 2x1000)."""
    cyc = [(i * 100, _band(v)) for i, v in enumerate(GOOPER)]
    acts = [(c * 800 + t, p) for c in range(2) for t, p in cyc] + [(1600, _band(GOOPER[0]))]
    return "Gooper_Start", acts, 1600


def gooper_cum():
    """GooperGrabScreenCum - 14 body frames @10fps, clip 1500 ms.

    Same animation as `gooper_start` plus the cum, so the same stroke shape at the same band - see
    GOOPER above.  Two things about the clip itself are not what they look like.

    First, it has a **second sprite curve** - a `Goop_overlay` drip layer - and it is the only
    clip in the set besides `GooperGrabScreen` that does.  `animcheck.clip_frames` takes every
    Sprite in `pptrCurveMapping` as one sequence, so it should have concatenated body and overlay;
    it got away with it only because the overlay's PPtrs have a fileID that a path_id-keyed dict
    resolves to the wrong file, so they came back as Texture2D and were dropped.  Load-bearing
    luck, now fixed properly.  The overlay is also why the clip is 1500 ms: it runs 15 samples
    where the body runs 14, so the body ends at 1400 and holds its last frame for the final 100 ms.

    Second, its two strokes are **not equal**.  Frames 8-13 reproduce frames 0,1,4,5,6,7 exactly -
    the second stroke skips the two mid-descent frames - so it is 800 ms then 600 ms, not
    2 x 700.  The old script's two equal 870 ms strokes cannot be scaled onto that by any factor,
    which is the whole reason it read as 15.93% off with no sensible target."""
    acts = [(i * 100, _band(v)) for i, v in enumerate(GOOPER)]                  # 0-700, 800 ms
    acts += [(800 + i * 100, _band(v)) for i, v in enumerate(GOOPER_FAST)]      # 800-1300, 600 ms
    acts += [(1400, _band(GOOPER[0])), (1500, _band(GOOPER[0]))]               # overlay's extra sample
    return "Gooper_Cum", acts, 1500


def plantasha_start():
    """PlantashaGrab - 8 frames @8fps = 1000 ms.

    Measured with `proxies.plantasha_shaft`, the shaft between her lips gives a textbook single
    stroke: 0, 262, 2079, 3142, 3222, 2510, 1632, 283 px.  Fully taken at f0, fully withdrawn at
    f4, back down by f7 - symmetric, 500 ms each way, unambiguous.

    Against that the old script was a wander that never left 0-60 and reached its maximum at
    703 ms, two thirds of the way through the return.  Normalising to the full range is the
    "exaggerate rather than be literal" side of the guide's trade-off, and it is the easy call
    here because the animation really does traverse from fully taken to fully clear - this is not
    the head-only case that would argue for a 10-20% band.

    Kept at one cycle.  Since CHANGELOG 41 dropped `Plantasha_Loop` and repointed its aliases
    here, this row is the plantasha grab loop, so a short tight loop is what it wants."""
    acts = [(0, 0), (125, 8), (250, 65), (375, 98), (500, 100),
            (625, 78), (750, 51), (875, 9), (1000, 0)]
    return "Plantasha_Start", acts, 1000


def plantasha_cum():
    """PlantashaCum - 31 frames @8fps = 3875 ms, scripted as 2 cycles.

    The one scene of the six where `retime`'s target was simply right: the script is two halves of
    3566 ms and the animation cycle is 3875, so 2 x 3875 = 7750 and the error is -7.96%.  It is
    rebuilt rather than scaled only because scaling would drag the spike at the end of each half
    from 3566 to 3875 - i.e. onto the loop seam - when the animation's lift is at 3000-3750.

    Structure, from `proxies.plantasha_shaft` plus a count of the cream pixels:

        f0-f23   0-3000 ms    seated, no stroke at all; cum accumulating at her lips
        f24-f29  3000-3625    one full lift, peak at f26 (3250), back down by f29
        f30      3750         seated again -> f0

    The hold is not empty though, and this is the same lesson as `Nun_Cum`: frames 10-16 and 21-22
    are bit-identical, but f6-f9 and f17-f20 are not, and **the twitches land on exactly the
    frames where new cum appears** (750 ms: 0->12->37->66 px; 2125 ms: 66->92->181->219->243).
    So the buzz bursts go there rather than running continuously through 2.4 s of nothing, which
    is what the old curve did with 14 evenly spaced pulses.

    0<->51 is the old script's own buzz level, kept."""
    cyc = [(0, 0),
           (750, 51), (875, 0), (1000, 51), (1125, 0),        # spurt 1, frames 6-9
           (2125, 51), (2250, 0), (2375, 51), (2500, 0),      # spurt 2, frames 17-20
           (3000, 52), (3125, 89), (3250, 100), (3375, 79),   # the lift, frames 24-29
           (3500, 51), (3625, 9), (3750, 6)]
    acts = [(c * 3875 + t, p) for c in range(2) for t, p in cyc] + [(7750, 0)]
    return "Plantasha_Cum", acts, 7750


def wendigo_start():
    """WendigoKiss - 31 frames @6fps = 5167 ms.

    Not a loop and not a sex scene: it is the intro cinematic that hands over to
    `Wendigo_Continued`.  Reading the tongue's pixel area and the amount of pure black in frame:

        f0-f8    0-1333 ms    dark, nothing on screen; she is approaching
        f9-f14   1500-2333    the tongue arrives and grows, 5347 -> 27956 px
        f15-f20  2500-3333    working, while a wipe starts eating the frame
        f21-f30  3500-5167    the wipe takes over; the tongue is gone by f29 and the last frame
                              is 129k pure black pixels, i.e. the whole picture

    So a third of this clip is a transition with nothing in it, and the old script oscillated
    100<->40 straight through to 5373 ms.  CUE: wind down across the wipe so the handoff to
    `Wendigo_Continued` starts from rest rather than mid-stroke.

    Registered in `proxies.AUTHORED`: the wind-down is a decision about a picture that is no
    longer there, so a correlation against any proxy is meaningless by construction.

    Parked at 100 through the dark approach rather than rising 0->100 across it, which is what the
    first version kept from the old script. Two reasons, and the second is the binding one:

    - there is nothing on screen for the first 1333 ms, so a 1.14 s stroke there is invented
      motion, and the top is where a stroke should start from anyway;
    - `Wendigo_Start` hands off to `Wendigo_Continued`, whose animation opens fully withdrawn
      (frame 0 is the top of the stroke), so the handoff is only seamless if this one *ends* at
      100. Every row is `Loop=true` and Edi's `inproveLoopAccion` forces `last.pos = first.pos`,
      so the ending cannot be chosen independently of the opening: to end at 100 it has to start
      at 100. The wind-down therefore settles upward onto 100 instead of decaying to 0."""
    acts = [(0, 100), (1300, 100),                                       # dark approach, parked
            (1500, 40), (1800, 100), (2100, 40), (2400, 100),            # tongue, frames 9-20
            (2700, 40), (3000, 100), (3300, 40),
            (3650, 85), (4000, 60), (4350, 90), (4700, 78), (5167, 100)] # settle onto the handoff
    return "Wendigo_Start", acts, 5167


def wendigo_continued():
    """WendigoSex - 8 frames @8fps = 1000 ms, scripted as 4 cycles.

    **Inverted, and against the wrong subject.** Reported on the feel pass as "seems off -
    the focus should be on the guy who is on top in this scene, unlike most other scenes", and the
    frames agree on both counts.

    Every frame is a full 480x270 with no alpha trim, so the silhouette proxy has nothing to
    measure and the sweep fell back to signed displacement, which tracked the cyan spill rather
    than either body. It scored +0.45 - comfortably "polarity agrees" - against a curve that runs
    exactly backwards. A mid positive correlation from a proxy that is watching the wrong object
    is worth nothing; see `proxies.wendigo_top`.

    Tracking the pale figure's y centroid (`proxies.wendigo_top`) gives an unambiguous stroke:

        frame    0     1     2     3     4     5     6     7
        y-cent  75.7  76.1  81.6  86.6  87.2  88.2  86.5  81.1     larger = lower on screen
        pos      100    96    52    12     8     0    14    57

    He descends over frames 0-5 and returns over 5-7 - a 625 ms descent against a 375 ms return,
    with a dwell at the bottom. The old curve sat at 0 where he is fully withdrawn and peaked at
    90 where he is deepest.

    Starts at 100, which is what makes the handoff from `Wendigo_Start` seamless: in game the
    chain is `WendigoKiss` -> `WendigoSexSceneIntro` -> `WendigoSexScene`, and both of the latter
    dispatch this row, so it is re-triggered from the top at the intro."""
    cyc = [100, 96, 52, 12, 8, 0, 14, 57]
    acts = [(c * 1000 + i * 125, p) for c in range(4) for i, p in enumerate(cyc)]
    acts.append((4000, cyc[0]))
    return "Wendigo_Continued", acts, 4000


# --- gallery variants ------------------------------------------------------------------------
#
# The gallery viewer plays its own `Gallery_*` clips, and 12 of 29 rows are a different length
# from the in-game clip they share a script with (CHANGELOG 51, `code/gallerydiff.py`). One
# funscript cannot be whole-cycle correct for both, which is why the Goopers and `Nun_Cum` were
# reported as right in play and wrong in the gallery.
#
# These six are the rows above the ~1.1x threshold the feel pass established - everything at
# 1.07x and below went unnoticed and is deliberately left sharing one script.
#
# Four of the six are the **same sprite sequence at a slower frame rate**: `Gallery_Gooper_Grab_*`
# and `Gallery_Imp_Grabbed_*` list byte-identical sprites to their in-game clips and differ only
# in `m_SampleRate` (8 vs 10 fps, 6 vs 8 fps). So those need no re-derivation at all, only the
# same shape at the gallery's period. `Gallery_Nun_Cum` is the one with genuinely different
# content: 55 frames against 33, with three twitches instead of two.


SCALED_FLOOR = {}   # row -> the point spacing a derived scene may be held to


def _derived_floor(src_actions, ratio):
    """The `min_gap` a scene replayed from `src_actions` onto a `ratio`-times clock may be held to.

    Not simply the master's own spacing: the gallery clip can be *faster* than the in-game one
    (`Gallery_PlantashaGrab_Start` is 9 fps against 8), and then the remapped points are legitimately
    closer than the master's. What carries over is the master's spacing *scaled by the same clock
    change* - the derived scene should be no worse than its source, measured in frames rather than
    milliseconds. Capped at 100 so this can only ever relax the standard convention, never tighten
    it beyond it."""
    worst = min(b["at"] - a["at"] for a, b in zip(src_actions, src_actions[1:]))
    return min(100, int(worst * ratio))


def _frame_anchors(env, clip):
    """[(first appearance time in ms, sprite name)] plus the clip end.

    A clip's keyframe list can repeat a frame - `DragonFaceSit` opens on `face_sit-Sheet_0` twice,
    `Gallery_Grabbed_Wendigo_Start` holds its final black frame for 13 keyframes - so keyframe
    index and frame index are not the same thing. Anchoring on where each distinct frame *first*
    appears is what makes the two timelines comparable.

    **The anchor is the sprite's name, not its ordinal.** An earlier version numbered the distinct
    frames 0, 1, 2 ... in each clip and joined the two timelines on that number, which is the same
    thing only while the two clips hold the same frames in the same order. `Gallery_BlindedBeast_
    Grab_Cum` breaks it: it inserts `BlindedBeast-Cum2_15`, a frame the in-game clip skips, so from
    there on the ordinals are off by one and every later frame mapped to its neighbour's time - the
    remap came out identical to its master except for the closing point, which is exactly what a
    clip 111 ms longer should *not* look like (§71)."""
    import animcheck as _A
    sp, dur, fps = _A.clip_frames(env, clip)
    names = [s.read().m_Name for s in sp]
    seen, anchors = set(), []
    for j, n in enumerate(names):
        if n not in seen:
            seen.add(n)
            anchors.append((j * 1000.0 / fps, n))
    return anchors, dur


def _remap_by_frame(env, source_row, new_row, play_clip, gal_clip, cycles):
    """Replay a script on the gallery clip's timeline, frame for frame.

    Scaling by the duration ratio is only right when the two clips differ *uniformly*, and three of
    these six do not: the gallery Wendigo runs the same 31 frames faster and then holds the last
    one for 1750 ms, the gallery Dragon drops the doubled opening frame, and the gallery Plantasha
    cum includes a frame gameplay skips. A uniform scale would smear those differences across the
    whole scene instead of putting them where they belong.

    So build a piecewise-linear map between the two timelines from the frames they share, and send
    every action through it. Exact at every frame boundary, and a hold in one clip simply stretches
    that one segment."""
    import json as _json
    pa, pdur = _frame_anchors(env, play_clip)
    ga, gdur = _frame_anchors(env, gal_clip)
    gtime = {u: t for t, u in ga}
    xs = [t for t, u in pa if u in gtime] + [pdur]
    ys = [gtime[u] for t, u in pa if u in gtime] + [gdur]

    def remap(t):
        if t <= xs[0]:
            return ys[0]
        for i in range(len(xs) - 1):
            if xs[i] <= t <= xs[i + 1]:
                f = (t - xs[i]) / max(xs[i + 1] - xs[i], 1e-9)
                return ys[i] + f * (ys[i + 1] - ys[i])
        return ys[-1]

    fp = os.path.join(ROOT, "Edi/Gallery/handy2pro", source_row.lower() + ".funscript")
    src = _json.load(open(fp, encoding="utf-8-sig"))["actions"]
    total = int(round(cycles * gdur))
    acts, seen = [], set()
    for a in src:
        c, within = divmod(a["at"], pdur)
        if a["at"] >= cycles * pdur:            # the closing point
            at = total
        else:
            at = int(round(c * gdur + remap(within)))
        if at in seen:
            continue
        seen.add(at)
        acts.append((at, int(a["pos"])))
    acts[-1] = (total, acts[0][1])
    SCALED_FLOOR[new_row] = _derived_floor(src, gdur / pdur)
    return new_row, acts, total


def _scaled_from(source_row, new_row, cycles, period):
    """Replay an existing script at the gallery clip's period.

    Used for the imp tiers, whose shape cannot be re-derived: all three are 4 frames, and
    `imp_2`/`imp_3` stroke at 263 ms and 130 ms inside a 500 ms cycle because there are more imps
    doing it (CHANGELOG 38). That escalation is authored, not measurable, so the gallery version
    has to be the same curve on a slower clock rather than a fresh derivation.

    Reads the master rather than hardcoding, so the two cannot drift: re-running `--write` after
    editing an imp scene regenerates its gallery twin."""
    import json as _json
    fp = os.path.join(ROOT, "Edi/Gallery/handy2pro", source_row.lower() + ".funscript")
    src = _json.load(open(fp, encoding="utf-8-sig"))["actions"]
    total = int(round(cycles * period))
    scale = total / src[-1]["at"]
    acts, seen = [], set()
    for a in src:
        at = int(round(a["at"] * scale))
        if at in seen:
            continue
        seen.add(at)
        acts.append((at, int(a["pos"])))
    acts[-1] = (total, acts[0][1])          # exact, and the loop seam closed
    SCALED_FLOOR[new_row] = _derived_floor(src, scale)
    return new_row, acts, total


def nun_cum_gallery():
    """Gallery_Nun_Cum - 55 frames @10fps = 5500 ms.

    The only one of the six whose gallery clip is different *content* rather than the same frames
    slowed down. Measured with the same medoid-distance proxy as the in-game version
    (`proxies.nun_cum_motion`), it is the same scene with the hold extended and the twitch
    repeated a third time:

        f0-f3     0-300 ms     she comes down onto it   (100, 95, 48, 16)
        f9-f12    900-1200     twitch
        f21-f24   2100-2400    twitch                   <- the in-game clip has this one as a
        f40-f43   4000-4300    twitch                      single frame and stops after it
        f52-f54   5200-5400    she lifts off            (13, 60, 78) -> f0 = 100

    So it takes the in-game curve and adds a third burst, which is exactly the shape the extra
    2200 ms is spent on. Buzz level and timing match `nun_cum` so the two feel like one scene."""
    acts = [(0, 100), (100, 95), (200, 48), (300, 10), (500, 0),      # descent, frames 0-5
            (900, 40), (1025, 0), (1150, 40), (1275, 0),              # twitch, frames 9-12
            (2100, 40), (2225, 0), (2350, 40), (2475, 0),             # twitch, frames 21-24
            (4000, 40), (4125, 0), (4250, 40), (4375, 0),             # twitch, frames 40-43
            (5100, 0), (5200, 13), (5300, 60), (5400, 78), (5500, 100)]   # lift, frames 52-54
    return "Nun_Cum_Gallery", acts, 5500


def gooper_start_gallery():
    """Gallery_Gooper_Grab_Start - the 8 frames of `GooperGrabScreen` at 8fps = 1000 ms.

    Identical sprites to the in-game clip, so the same GOOPER shape and the same DEEP band; only
    the frame spacing changes, 100 ms to 125 ms. Two cycles, matching `gooper_start`."""
    cyc = [(i * 125, _band(v)) for i, v in enumerate(GOOPER)]
    acts = [(c * 1000 + t, p) for c in range(2) for t, p in cyc] + [(2000, _band(GOOPER[0]))]
    return "Gooper_Start_Gallery", acts, 2000


def gooper_cum_gallery():
    """Gallery_Gooper_Grab_Cum - the 14 frames of `GooperGrabScreenCum` at 8fps = 1750 ms.

    Identical sprites again, so the same two unequal strokes - now 1000 ms and 750 ms. **No tail
    hold here:** 14 frames at 8fps is exactly 1750 ms, whereas the in-game clip runs 100 ms past
    its last body frame because a second sprite curve outlasts it (CHANGELOG 48). The gallery
    version has no overlay curve, so the script ends on the stroke."""
    acts = [(i * 125, _band(v)) for i, v in enumerate(GOOPER)]                  # 0-875, 1000 ms
    acts += [(1000 + i * 125, _band(v)) for i, v in enumerate(GOOPER_FAST)]     # 1000-1625, 750 ms
    acts += [(1750, _band(GOOPER[0]))]
    return "Gooper_Cum_Gallery", acts, 1750


def imp_1_gallery():
    """Gallery_Imp_Grabbed_1 - the 4 frames of `Imp_Grab_One` at 6fps = 666.7 ms."""
    return _scaled_from("imp_1", "imp_1_Gallery", 11, 2000.0 / 3.0)


def imp_2_gallery():
    """Gallery_Imp_Grabbed_2 - the 4 frames of `Imp_Grab_Two` at 6fps = 666.7 ms."""
    return _scaled_from("imp_2", "imp_2_Gallery", 10, 2000.0 / 3.0)


def imp_3_gallery():
    """Gallery_Imp_Grabbed_3 - the 4 frames of `Imp_Grab_Three` at 6fps = 666.7 ms."""
    return _scaled_from("imp_3", "imp_3_Gallery", 10, 2000.0 / 3.0)


# The rest of the gallery mismatches, remapped frame-for-frame off their masters. These sit at
# 0.889x-1.065x - under the ~1.1x the feel pass could tell apart, but far outside the 0.5% the rest
# of the set is held to, and "whole-cycle exact" is the standard everywhere else (CHANGELOG 53).
REMAPPED = (
    # row,             master,            gameplay clip,   gallery clip,                    cycles
    ("Plantasha_Start_Gallery", "Plantasha_Start", "PlantashaGrab",
     "Gallery_PlantashaGrab_Start", 1),
    ("Plantasha_Cum_Gallery", "Plantasha_Cum", "PlantashaCum",
     "Gallery_PlantashaGrab_Cum", 2),
    ("imp_grab_loop_Gallery", "imp_grab_loop", "Imp_Grab_Loop",
     "Gallery_Imp_Gangbang_Loop", 2),
    ("imp_grab_cum_Gallery", "imp_grab_cum", "Imp_Grab_Cum",
     "Gallery_Imp_Gangbang_Cum", 1),
    ("Wendigo_Start_Gallery", "Wendigo_Start", "WendigoKiss",
     "Gallery_Grabbed_Wendigo_Start", 1),
    ("Dragon_Grabbed_Gallery", "Dragon_Grabbed", "DragonFaceSit",
     "Dragon_Gallery_Grabbed", 1),
)


def remapped_scenes():
    """Build the frame-remapped gallery variants. Loads the assets once, so it is a generator
    rather than one function per scene."""
    import animcheck as _A
    env = _A.load_env()
    for row, master, play_clip, gal_clip, cycles in REMAPPED:
        yield _remap_by_frame(env, master, row, play_clip, gal_clip, cycles)


SCENES = (nun_cum, gooper_start, gooper_cum,
          plantasha_start, plantasha_cum, wendigo_start, wendigo_continued,
          nun_cum_gallery, gooper_start_gallery, gooper_cum_gallery,
          imp_1_gallery, imp_2_gallery, imp_3_gallery)

# Rows that rederive.py creates rather than edits. `authored.write` only updates an existing
# Definitions.csv line, so these have to be added first or the funscript would ship unregistered.
NEW_ROWS = ("Nun_Cum_Gallery", "Gooper_Start_Gallery", "Gooper_Cum_Gallery",
            "imp_1_Gallery", "imp_2_Gallery", "imp_3_Gallery") + tuple(r[0] for r in REMAPPED)


def ensure_row(name, total):
    """Add `name` to Definitions.csv if it is not there yet."""
    for c in (PATHS.DEFINITIONS,):
        raw = open(c, encoding="utf-8-sig", newline="").read()
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.replace("\r\n", "\n").split("\n")
        if any(l.split(",")[0] == name for l in lines):
            continue
        while lines and lines[-1] == "":
            lines.pop()
        lines.append(f"{name},{name.lower()},0,{total},gallery,true")
        lines.append("")
        open(c, "w", encoding="utf-8", newline="").write("﻿" + nl.join(lines))
        print(f"  + row {name} added to {os.path.relpath(c, ROOT)}")

if __name__ == "__main__":
    built = [fn() for fn in SCENES] + list(remapped_scenes())
    for name, acts, total in built:
        if "--write" in sys.argv:
            if name in NEW_ROWS:
                ensure_row(name, total)
            write(name, acts, total,
                  "Re-derived from the animation; see code/rederive.py for the reasoning.",
                  min_gap=SCALED_FLOOR.get(name, 100))
        else:
            gaps = [b[0] - a[0] for a, b in zip(acts, acts[1:])]
            fast = max(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000 for a, b in zip(acts, acts[1:]))
            print(f"{name:<17}{len(acts):>3} acts  end={total:<5} min gap={min(gaps):>4}ms  "
                  f"peak={fast:>4.0f} u/s   {acts[:4]} ...")

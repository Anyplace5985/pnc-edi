#!/usr/bin/env python3
"""The scenes game 0.3.1 added, derived from their animations.

    python3 code/scenes031.py            # print what would be written
    python3 code/scenes031.py --write    # write the funscripts and add Definitions rows

Six dioramas (D10-D15) and four peek scenes. Same conventions as everywhere else: >=100 ms between
points, whole-cycle lengths, the loop seam closed, range judged against what is actually on screen,
speeds judged by median rather than peak (../learnings/funscript-authoring.md, "Writing for the
hardware"). `authored.write`
does the writing so there is one writer for the tree and the CSV.

**Every curve here was derived by looking at the frames first.** The numbers in each docstring are
the measured proxy, and the proxy is named because the generic one is wrong for most of these: a
diorama is two characters doing different things in one full-bleed frame, which is exactly the case
../learnings/funscript-proxies.md says a whole-frame silhouette averages into mush. The
measurements are baked as literals
rather than re-measured on import, as in `rederive.py`, so this module runs without the game.

Polarity is the part that cannot be measured. The convention is **deep / enveloped = 0**, and for
each scene the docstring says which way round the geometry puts it. §39's rule - that a body with
the shaft passing *through* it is a sleeve, so visible shaft above it means *deep* - does not apply
to a rider sitting on top of a shaft, where the exposed shaft is *below* the body and means the
rider is high. Ask what an inversion was an inversion *of* before carrying it across.
"""
import os
import sys

from authored import write                                          # noqa: E402
from rederive import ensure_row                                      # noqa: E402

# Dioramas play on a loop while the player stands near them, so a one-cycle file would be a very
# short loop. The existing nine run ~3000-3500 ms at a whole number of cycles (§33), and these
# follow: pick the repeat count that lands nearest 3000 ms without leaving a partial cycle.
TARGET_MS = 3000


def cycles_for(cycle_ms: float) -> int:
    n = max(1, round(TARGET_MS / cycle_ms))
    return n


def loop(values, fps, name, cycles=None, total=None):
    """Per-frame proxy values -> actions, repeated to a whole number of cycles.

    Frame *k* is on screen at `k/fps`, never at `k*duration/n` - ../learnings/asset-inspection.md,
    and the reason the two
    Gooper clips needed `_first_pptr_curve`. The final point closes the loop onto the first
    position: `InproveLoopDetection` would force that anyway, and writing it makes the file say
    what it means."""
    step = 1000.0 / fps
    cycle_ms = len(values) * step
    n = cycles if cycles is not None else cycles_for(cycle_ms)
    acts = []
    for c in range(n):
        for k, v in enumerate(values):
            acts.append((int(round(c * cycle_ms + k * step)), int(round(v))))
    end = int(round(total if total is not None else n * cycle_ms))
    acts.append((end, int(round(values[0]))))
    return name, acts, end


def norm(series, deep_is_max=False):
    """Normalise a measured proxy to 0-100 with deep = 0.

    `deep_is_max=True` where the raw number is *larger* when the scene is deep - a y coordinate
    that grows downward, most often."""
    lo, hi = min(series), max(series)
    if hi - lo < 1e-9:
        return [0] * len(series)
    out = [(v - lo) / (hi - lo) * 100.0 for v in series]
    return [100.0 - v for v in out] if deep_is_max else out


# --------------------------------------------------------------------------------------------
# dioramas


def dragon_squat_ride():
    """D10 `dragon squat ride` - 6 frames @8fps = 750 ms, one stroke.

    A partner on their back with the shaft vertical, and the dragon squatting down onto it from
    above; the dragon fills most of the frame, the partner is a tan figure along the bottom.

    Proxy: the **topmost pale pixel in the shaft band** (x 0.38-0.58 of the sprite, below 0.55 H),
    i.e. where the dragon's underside cuts across the shaft. The generic signed-displacement proxy
    is useless here - it tracks the dragon's wings and horns, which is most of the silhouette and
    none of the act.

        frame      0     1     2     3     4     5
        top y    251   239   229   224   229   245      (27 px of travel)

    Polarity: the exposed shaft is *below* the rider, so more of it showing means the dragon has
    risen = withdrawn. That is the opposite geometry to §39's gooper, where the shaft passed
    through the body and showed above it. Frame 0 is deep.

    Range: full 0-100. The exposed shaft runs ~224-258 px and the dragon covers 27 px of that ~34,
    so this is a near-full-length ride, not a bob that needs exaggerating into one."""
    y = [250, 236, 228, 224, 229, 245]
    return loop(norm(y, deep_is_max=True), 8, "ambient_dragon_squat_ride")


def wendigo_squat_ride():
    """D11 `wendigo squat ride` - 6 frames @8fps = 750 ms, one stroke.

    The same staging as D10 with the wendigo in place of the dragon: partner on their back, shaft
    vertical, rider squatting onto it from above. The rider is near-black here, so the partner and
    the shaft are the only bright things in frame.

    Proxy: topmost pale pixel in a **narrow** central band (x 0.46-0.54), i.e. the shaft tip where
    the wendigo's underside crosses it. A wider band is pinned by the partner's raised thighs,
    which are pale, static and higher than the shaft - it reads 3 px of travel and looks like a
    dead scene.

        frame      0     1     2     3     4     5
        top y    313   308   306   300   300   309      (13 px, 3.7% of sprite height)

    Polarity as D10: exposed shaft below the rider = risen = withdrawn, frame 0 deep."""
    y = [313, 308, 306, 300, 300, 309]
    return loop(norm(y, deep_is_max=True), 8, "ambient_wendigo_squat_ride")


def goonshroom_gangbang():
    """D12 `goonshroom gangbang` - 12 frames @8fps = 1500 ms, holding **two** strokes.

    Three goonshrooms on one partner; the middle one rides, the outer two work the hands. The
    period is the certain part and the shape is not:

    **Two strokes, proven by exact repetition.** The alpha-trimmed sprite heights run
    `179, 181, 176, 180, 177, 178` and then those same six values again, and the cap-top series is
    identical across the halves. So the true period is **750 ms**, not the clip's 1500 - the same
    trap as `imp gangbang` (../learnings/funscript-timing.md, "a clip's own length is not
    necessarily its stroke
    period"). Nothing in `stroke_period`'s output said so; the bounding boxes did.

    **The shape is jitter.** The largest honest travel anywhere in the frame is ~5 px on a 181 px
    sprite (2.8%), under the 3% floor `motion_proxy` uses, and the variance map shows it as a
    1-2 px outline shimmer around *every* body rather than a localised stroke. Reproducing the
    measured 6, 4, 9, 5, 8, 7 would be scripting pixel noise.

    So this one is **authored on a measured period**: a clean stroke at the proven 750 ms, full
    range on the same reasoning that settled `ambient_nun_wall_chain_head` - how far anyone
    actually travels is not readable from the animation, so "exaggerate rather than be literal"
    wins by default. Asymmetric, because a ride drops faster than it lifts."""
    stroke = [0, 8, 45, 100, 78, 34]           # authored: drop, dwell low, lift, fall back
    return loop(stroke, 8, "ambient_goonshroom_gangbang", cycles=4)


def nun_watersports():
    """D13 `nun watersports` - 8 frames @6fps = 1333 ms, and **two poses**.

    Frames 0-3 are one sprite (238x317) and frames 4-7 another (238x316), and the only difference
    is a one-pixel shift in the nun's skirt edge. The partner kneeling below does not move at all.
    The variance map is a hairline around one hem and nothing else.

    There is no stroke here and inventing one would be scripting to something that is not on
    screen - ../learnings/funscript-authoring.md's "better to skip a stroke than add a non-existing
    stroke". But a diorama
    with no row plays nothing at all, and the act is a *continuous* one rather than a rhythmic one.

    So: a slow swell, deliberately not a thrust. 0 -> 100 -> 0 across the clip's own 1333 ms,
    which is ~150 u/s - far below anything that reads as stroking, and about as close to "steady
    pressure that is going somewhere" as a linear device gets. Recorded as authored, not measured,
    because the animation supports the *duration* and nothing else."""
    swell = [0, 29, 71, 100, 100, 71, 29, 0]
    return loop(swell, 6, "ambient_nun_watersports", cycles=2)


def plant_gangbang():
    """D14 `plant gangbang` - 8 frames @8fps = 1000 ms, one stroke. The clearest of the six.

    Plantasha's flower head rides a shaft rising from the vines, with a second bud and a hand at
    the sides. The flower is a sleeve engulfing the tip, so this is §39's *mouth* geometry, not its
    gooper geometry: the exposed shaft is **below** the flower, and more of it showing means the
    flower has lifted = withdrawn.

    Proxy: topmost pale pixel in the shaft band (x 0.54, found by taking the column whose top edge
    travels furthest rather than by eye). The flower's pink interior does not pollute it - pink is
    r-g ~110 and the pale mask requires r-g < 60.

        frame      0     1     2     3     4     5     6     7
        top y    125   113   108   112   117   140   143   138    (40 px, 19.2% of height)

    40 px of travel is the largest in the set by a wide margin, so this one is measured
    end-to-end and needs no exaggeration."""
    y = [125, 113, 108, 112, 117, 140, 143, 138]
    return loop(norm(y, deep_is_max=True), 8, "ambient_plant_gangbang", cycles=3)


def serpent_wall_blowjob():
    """D15 `serpent blowjob wall` - 6 frames @8fps = 750 ms, a hold and a pull.

    The player is pinned upright against a wall and the serpent's head works them from below. The
    serpent's *body* is static - its gold collar moves 1.4 px across the whole clip - so anything
    measured off the coil is noise. The head is the mover, and it moves diagonally.

    Three independent measurements agree on the shape, which is what makes a 17 px motion worth
    trusting at all:

        the pink mouth arc, displaced from frame 0   0.0  1.0  1.4  0.0  5.1  15.6 px
        dark pixels in the head ROI                   14    0   21   14   51   100 (normalised)
        the player's own visible pixel count        13065 13002 12956 13168 13368 13584

    All three say the same thing: **frames 0-3 are a hold and the movement is in 4-5**, with the
    player becoming more exposed as the head draws back. So this is a long dwell and a pull-off,
    and the loop closes by plunging back - the shape of §48's `Nun_Cum` rather than a stroke.

    The 1 px wobble at frames 1-2 is dropped: it is a third of a pixel of centroid and writing it
    would put two direction changes into what the picture shows as a hold.

    **Held to the bottom half of the range (0-50) after a play (§81).** The motion measured is
    17 px of head travel on a scene where the player never moves; run full-range it read as a
    stroke the picture does not contain. Halving keeps the shape - the dwell and the pull are
    unchanged in time and in proportion - and puts it back in the register of a mouth working the
    base. The measured series is untouched; only the band it is written into changed."""
    return loop([0, 0, 0, 0, 18, 50], 8, "ambient_serpent_wall_blowjob", cycles=4)


# --------------------------------------------------------------------------------------------
# peek scenes
#
# These are full-bleed room art seen through a keyhole vignette, so there is no alpha trim and the
# silhouette proxy is dead - ../learnings/funscript-proxies.md's `Wendigo_Continued` problem. What
# they do have that a
# grab screen does not is a **static background**, which makes the median frame a usable
# background plate: subtract it and what is left is exactly the moving bodies. That is the proxy
# used below ("moving mass"), and its centroid is a position, so it gives period and phase rather
# than the half-period a frame difference would.


def gargoyle_fuck_fest():
    """P8 `GargoylePeep_Loop` - 10 frames @9fps = 1111 ms, holding **two** strokes of 555.6 ms.

    A gargoyle taking a kneeling partner from behind in a cell, with more gargoyles watching.

    The repeat is real and the shape is not, and the two findings are the same measurement. Frames
    k and k+5 differ in 1.1-2.5% of pixels at a mean |diff| under 0.5/255, so the halves are the
    same motion - `stroke_period` says reps=2 and it is right. But the moving-mass centroid read
    `65, 96, 96, 86, 100` for the first half and `58, 48, 89, 0, 15` for the second, which cannot
    both be true of two identical halves.

    **That contradiction is what condemns the proxy.** Where the halves are near-identical, the
    median plate sits close to both, so the residual is dominated by the 1-2% of pixels that differ
    rather than by the bodies, and its centroid wanders. Compare `peek_gravy_bath`, where the same
    proxy returned an *exactly* repeating series - a repeat is the evidence that a residual is
    tracking real periodic motion rather than noise, and its absence here is the evidence it is not.

    So: **period measured, shape authored** - one thrust per 555.6 ms, driven in fast and drawn
    back slower, which is the rhythm of the staging."""
    return loop([100, 30, 0, 45, 80], 9, "peek_gargoyle_fuck_fest", cycles=6)


def gravy_bath():
    """P9 `GravyPeep_Loop` - 12 frames @9fps = 1333 ms, holding **two** strokes.

    Gravy in a bath, seen through the keyhole. Like D12 the repeat is exact and it is the thing
    worth trusting: the moving mass's x runs `0, 12, 88, 90, 100, 100` and then those same six
    values again, and y repeats to within a point (`64, 0, 23, 99, 57, 58` / `62, 1, 25, 100, 59,
    59`). True period **666.7 ms**, not the clip's 1333.

    Travel is 36.8 px (13.6% of frame), the largest of the four peeks, so the shape is measured
    rather than authored. Taken on y, which is the larger axis here."""
    return loop([64, 0, 23, 99, 57, 58], 9, "peek_gravy_bath", cycles=5)


def serpent_prison():
    """P10 `Peephole Serpent Loop` - 5 frames @9fps = 556 ms.

    The serpent stretched along a partner on the cell floor. Its motion is **mostly horizontal** -
    the moving mass travels 63.5 px in x against 26.8 px in y - which fits the staging: the serpent
    lies along the body rather than riding it, so x is the depth axis, not y. That alone is worth
    recording, because taking y here would have measured the coil settling.

    Five frames is too few to trust a shape from, though: the measured x reads `0, 92, 8, 6, 100`,
    which is two direction changes in 556 ms and more likely the diff mask catching the fluid that
    appears at frames 2-3 than a real double stroke. So the **period is measured and the shape is
    authored** - one clean horizontal thrust per 556 ms, the same call as D12."""
    return loop([0, 30, 75, 100, 45], 9, "peek_serpent_prison", cycles=6)


def werewolf_ride():
    """P11 `Peephole werewolf Loop` - 5 frames @9fps = 556 ms.

    A werewolf riding a partner, keyhole view. Frame 1 is the top of the lift and 0/4 the bottom;
    the body's own top edge only moves 4 px, but the mass below it opens and closes clearly.

    The moving-mass centroid reads `0, 98, 31, 100, 33`, which would be two lifts in 556 ms. The
    fluid appearing across frames 1-3 is in that mask and is the likelier explanation - the same
    confound as P10. **Period measured, shape authored**: one ride per 556 ms, dropping faster than
    it lifts."""
    return loop([0, 100, 72, 40, 18], 9, "peek_werewolf_ride", cycles=6)


SCENES = [dragon_squat_ride, wendigo_squat_ride, goonshroom_gangbang,
          nun_watersports, plant_gangbang, serpent_wall_blowjob,
          gargoyle_fuck_fest, gravy_bath, serpent_prison, werewolf_ride]


if __name__ == "__main__":
    for fn in SCENES:
        name, acts, total = fn()
        gaps = [b[0] - a[0] for a, b in zip(acts, acts[1:])]
        fast = max(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000 for a, b in zip(acts, acts[1:]))
        median = sorted(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000
                        for a, b in zip(acts, acts[1:]))[len(gaps) // 2]
        if "--write" in sys.argv:
            ensure_row(name, total)
            write(name, acts, total,
                  "Derived from the 0.3.1 animation; see code/scenes031.py for the reasoning.")
        else:
            print(f"{name:<30}{len(acts):>3} acts  end={total:<5} min gap={min(gaps):>4}ms  "
                  f"median={median:>4.0f} peak={fast:>4.0f} u/s   {acts[:4]} ...")

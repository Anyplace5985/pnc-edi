#!/usr/bin/env python3
"""The three enemies game 0.3.1 added, derived from their grab screens.

    .venv/bin/python code/grabs031.py            # print what would be written
    .venv/bin/python code/grabs031.py --write    # write the funscripts and add Definitions rows

Black Serpent, Blinded Beast (two stages) and GoonShroom: eleven in-game scenes plus the eight
gallery twins their viewer clips need. `code/scenes031.py` did the same job for 0.3.1's dioramas
and peek scenes; this is the grab-screen half, and it needs the assets loaded because the gallery
twins are built by replaying a master on the viewer's own timeline (`rederive._remap_by_frame`).

**Every curve here was derived by looking at the frames first**, and each docstring names the proxy
because the generic one is wrong for all of them - three of the four staging types are a creature
filling the frame with a few dozen pixels of shaft doing the actual work. The measurements are
baked as literals so the module runs without the game; only the gallery twins need it.

Polarity is the part that cannot be measured, so each docstring says which way round the geometry
puts it. Two rules from earlier sessions carry the whole set:

  * §39's *sleeve* rule - a body the shaft passes **through** shows more shaft the deeper it is.
    That is the Black Serpent's paizuri: the tip emerges above her cleavage at the top of the
    thrust, so maximum protrusion is position 0.
  * scenes031's *rider* rule - a body sitting **on** a shaft shows more shaft the higher it is.
    That is the Blinded Beast and the GoonShroom, both squat rides seen from behind.

The two look identical to a pixel counter and are exact opposites. Ask what the shaft passes
through before normalising anything.
"""
import os
import sys

from authored import ROOT, write                                           # noqa: E402
from rederive import (SCALED_FLOOR, _remap_by_frame, _scaled_from,    # noqa: E402
                      ensure_row)

# Grab loops are scripted at TWO cycles, everywhere in this set: Nun_Grab 2x600, Mimic_Loop
# 2x625, Gooper_Start 2x800, Gargoyle_Grabbed 2x1000. Every row is Loop=true, so the length is
# only about giving the device a whole cycle to work with, and matching the neighbours costs
# nothing. Cum scenes are one-shots and run their clip's own length exactly once.
LOOP_CYCLES = 2


def cycle(values, fps, name, cycles=LOOP_CYCLES, total=None):
    """Per-frame positions -> actions, repeated to a whole number of cycles.

    Frame *k* is on screen at `k/fps`, never at `k*duration/n` (learnings/asset-inspection.md).
    The closing point puts the loop seam back on the first position: `InproveLoopDetection` would
    force that anyway, and writing it makes the file say what it means."""
    step = 1000.0 / fps
    cycle_ms = len(values) * step
    acts = []
    for c in range(cycles):
        for k, v in enumerate(values):
            acts.append((int(round(c * cycle_ms + k * step)), int(round(v))))
    end = int(round(total if total is not None else cycles * cycle_ms))
    acts.append((end, int(round(values[0]))))
    return name, acts, end


def norm(series, deep_is_max=False):
    """Normalise a measured proxy to 0-100 with deep = 0.

    `deep_is_max=True` where the raw number is *larger* when the scene is deep - a shaft-exposure
    count under §39's sleeve rule, or a y coordinate that grows downward."""
    lo, hi = min(series), max(series)
    if hi - lo < 1e-9:
        return [0] * len(series)
    out = [(v - lo) / (hi - lo) * 100.0 for v in series]
    return [100.0 - v for v in out] if deep_is_max else out


# ---------------------------------------------------------------------------------------------
# Black Serpent - BrawlerEnemyAI, `BlackSerpent GrabScreen` / `_Cum`
#
# A paizuri. She is greyscale from her hood to her breasts (R=G=B throughout: 29, 74, 53, 23) and
# the player is the only warm thing in frame, so `(R > 120) & (R - B > 20)` separates the two
# outright - no threshold hunting, and no chance of catching her. The measurement is the flesh
# area inside the cleavage band, x 0.40-0.53 and y 0.40-0.85 of a 463x270 canvas.
#
# The variance map settles what to measure: one bright blob at the cleavage, her eyelids, and
# otherwise a 1 px outline. Nothing else in this scene moves.


def serpent_loop():
    """`BlackSerpent GrabScreen` - 7 frames @8fps = 875 ms, one stroke.

    Her hood is down and her breasts are around it; the tip emerges from the top of her cleavage.
    Flesh pixels in the cleavage band:

        frame        0     1     2     3     4     5     6
        area        81   262   837  1078  1491  1618   358      (20x range)

    Polarity is §39's sleeve rule and it is worth stating in full, because the picture invites the
    opposite reading. The shaft's total length is fixed; what shows above her cleavage plus what
    is inside plus what is below is constant. So the frame where the most tip protrudes (f5) is
    the frame where the most of it is *inside* her - deep, position 0 - and f0, where a sliver
    shows, is the top of the stroke. Reading "more visible = more withdrawn" gets this scene
    exactly backwards, and it is the same trap the gooper set in §39.

    A 20x range on the proxy is the largest in this file, so the shape is measured end to end and
    nothing is exaggerated.

    **The sleeve reading above was played and rejected (§81).** Played on the device the scene ran
    backwards, so `deep_is_max` is now False: the frames showing the most flesh in the cleavage
    band are the deep ones. The argument for the sleeve rule is left standing above because it is
    the reasoning that has to be re-made for the *next* scene of this staging, not deleted as if
    it had never been made - the measurement is unchanged either way and only the polarity flipped.
    Timing is objective, polarity is not, and the device is the only instrument that reads it."""
    area = [81, 262, 837, 1078, 1491, 1618, 358]
    return cycle(norm(area, deep_is_max=False), 8, "Serpent_Loop")


def serpent_cum():
    """`BlackSerpent GrabScreen_Cum` - 27 frames @8fps = 3375 ms.

    **Three phases with three different geometries**, which is why no single proxy covers it and
    why the cleavage count alone would have read the middle of the scene backwards.

    `f0-f4` (0-500 ms) she opens her mouth wide and rears back; the whole shaft comes clear
    between her breasts rather than just the tip, so the cleavage count leaves the loop's range
    entirely (1078 -> 4646). f0's count is *exactly* the loop's f3, so the cum clip starts
    mid-stroke and the curve starts at that same position.

    `f5-f20` (625-2500 ms) her mouth is on it. The cleavage count collapses to ~340 because her
    head occludes the band - an occlusion, not a depth reading, and taking it as one would put the
    scene at its deepest for the wrong reason. What is real here is a **six-frame sub-loop**:
    frames 8-13 and 14-19 repeat to within 1-2 px on the silhouette top edge and 1% on the count,
    and the whole-frame difference drops to 0.65-1.32 against 22.6 at the start. So the period is
    proven at 750 ms and the travel is her head, 14 px on a 270 px sprite = 5.2%. Written as the
    measured six-frame shape inside a 0-30 band: the guide makes head-only oral the exception to
    "avoid strokes under 20%", and a scene that is 5% on screen has no business using more.

    `f21-f26` (2625-3250 ms) she pulls off - the cleavage count jumps to 12348 at f22, the largest
    of the clip - and then f24, f25 and f26 return counts of 1491, 1618 and 358, which are *the
    loop clip's f4, f5 and f6 exactly*. The cum clip ends by replaying the loop's tail, so the
    curve ends on the loop's own positions and hands back to it without a seam."""
    acts = [(0, 35),                                    # = the loop's f3, where this clip starts
            (125, 70), (250, 100), (375, 100),          # mouth open, shaft clear: withdrawn
            (500, 55),                                  # her head coming down
            (625, 0)]                                   # f5: mouth on it
    # f6-f20, the proven 750 ms sub-loop. Head top edge f9-f14 read 27, 16, 28, 30, 29, 26 px;
    # normalised inside 16..30 and scaled to the 0-30 band that is a fast lift and a slow settle.
    bob = [6, 30, 4, 0, 2, 9]
    for k, t in enumerate(range(750, 2501, 125)):
        acts.append((t, bob[(k + 3) % 6]))              # phase-aligned so f10 is the peak
    acts += [(2625, 85), (2750, 100), (2875, 55),       # she pulls off; f22 is the clip's max
             (3000, 8), (3125, 0), (3250, 82),          # = the loop's f4, f5, f6
             (3375, 100)]                               # = the loop's f0
    return "Serpent_Cum", acts, 3375


# ---------------------------------------------------------------------------------------------
# Blinded Beast - a two-stage miniboss. Both stages' grab screens declare states called exactly
# `Loop` and `Cum`, which is what `GrabVariantSuffixes` exists to tell apart (§66).
#
# Untransformed: a rear view, the beast prone over the player, the shaft a near-white ribbed
# column between its thighs. Her skin is a saturated orange (185,126,97) and the column is
# desaturated (203,189,176), so `(R > 150) & (R - B < 45) & (B > 130)` picks the column alone.
#
# Transformed: the same staging redrawn much larger, and now the shaft is *pink* (160,66,73 to
# 231,126,135) against brown fur (56,43,37). `(R > 140) & (R - G > 55)` separates them; the count
# barely moves between frames, so the signal is the column's position rather than its area.


def beast_start():
    """`Blinded Beast Grabscreen Start` - 5 frames @9fps = 555.56 ms, one stroke.

    Rear view, the beast squatting on the player. Top of the exposed column, in x 0.455-0.545:

        frame        0     1     2     3     4
        top y      210   211   184   151   189      (60 px of travel, 24% of the sprite)

    Polarity is the rider rule, not the sleeve rule: the exposed shaft is *below* the body here,
    so more of it showing means the beast has risen = withdrawn. f3 is the top of the lift and f1
    is fully seated.

    Sprite alpha trim is not registered frame to frame, so every frame is pasted onto one canvas
    against the shared bottom edge before the column is read - the failure `squat_ride_shaft`
    documents, where taking the band as a fraction of each frame's own shape flattened a 27 px
    travel to nothing.

    555 ms per stroke makes this the fastest scene in the set (median 405 u/s, over a Handy 1's
    364) - which is what the `handy1` variant is for, and why it is generated rather than judged."""
    top = [210, 211, 184, 151, 189]
    return cycle(norm([-y for y in top]), 9, "BlindedBeast_Start")


def beast_cum():
    """`Blinded Beast Grabscreen Cum` - 33 frames @9fps = 3666.67 ms.

    The same column proxy, and it goes to **zero for 23 consecutive frames**:

        frame       0    1    2    3    4   5-27    28    29    30    31    32
        area      183  101   34   29   15      0   298   452   452   440   323

    That is not the beast lifting off - it is the opposite. It pulls its haunches together and
    seats itself, which closes the gap the camera was seeing the column through; the left-flank
    top edge rises to the canvas top over the same frames because its back arches while its hips
    go down. The ejaculation confirms the reading: white fluid at the bottom of frame first
    appears at f11 and grows in steps through f12, f14, f16, f17 and f20 (6, 47, 121, 155, 233,
    453 px), which is a climax happening *while seated*, not after a withdrawal.

    So: a short settle over f0-f5, seated from f5 to f27, and the dismount in f28-f32 with the
    largest exposure of the clip. The 2.5 s seated stretch is scripted the way §48 scripted
    `Nun_Cum`'s - buzz bursts on the events that are actually there, at 0<->40 every 111 ms
    (360 u/s), placed on the two frames where the fluid steps hardest (f14 and f20). Two bursts,
    not a tremor across the whole hold: a scene with nothing moving gets nothing written on it."""
    acts = [(0, 41), (111, 22), (222, 8), (333, 6), (444, 3), (556, 0)]     # settle, f0-f5
    acts += [(1444, 0), (1556, 40), (1667, 0)]                              # spurt at f14
    acts += [(2111, 0), (2222, 40), (2333, 0)]                              # spurt at f20
    acts += [(3000, 0), (3111, 66), (3222, 100), (3333, 100),               # dismount, f28-f32
             (3444, 97), (3556, 72), (3667, 41)]
    return "BlindedBeast_Cum", acts, 3667


def beast_start_t():
    """`Blinded Beast_T Grabscreen Start` - 6 frames @8fps = 750 ms, one stroke.

    The transformed stage: same staging, redrawn at full 480x270, pink shaft on brown fur. The
    pink area is flat across the clip (381-459 px) and its *centroid* is the signal, so this one
    is a translation rather than a change in how much is exposed:

        frame        0      1      2      3      4      5
        pink cy  206.3  202.9  188.8  179.2  184.5  190.2      (27 px, y grows downward)

    Rider rule again: the column riding higher means the beast has lifted. f0 is seated, f3 is the
    top. Same phase as the untransformed stage, which is the cross-check that the two stages are
    the same animation redrawn - they peak at the same point of their own cycle."""
    cy = [206.3, 202.9, 188.8, 179.2, 184.5, 190.2]
    return cycle(norm(cy, deep_is_max=True), 8, "BlindedBeast_Start_T")


def beast_cum_t():
    """`Blinded Beast_T Grabscreen Cum` - 28 frames @8fps = 3500 ms.

    Opens on the same three frames as `beast_start_t` (pink area 404, 381, 429 in both), then:

        frame        0      1      2      3      4      5      6      7      8    9-22
        pink cy  206.3  202.9  188.8  154.5  183.1  159.4  134.4  145.6  187.7   ~210

    Two hard lifts (f3 and f6, the second the highest point of the clip) and then seated for
    fourteen frames at a centroid lower than anything in `beast_start_t`'s whole range - so the
    cum pose is deeper than the loop ever goes, and the curve is allowed to reach 0 there.

    From f23 the pink mask stops measuring the body: the count goes 592 -> 1356 -> 2776 and stays
    there, which is fluid, not motion. That is where the whole-frame difference also jumps
    (12.4, 15.8, 13.4 against 0.7-2.3 through the hold), so the clip's last five frames are the
    ejaculation and are scripted as bursts rather than as position.

    **The hold was re-measured in §97, and the whole-frame difference had put its one burst in the
    wrong place.** The play asked for the shaft's shake as the proxy; the shaft does not shake.
    Its mask spans x 224-255 in every one of the fourteen hold frames and its top edge moves
    183-186 px, which on a 270 px frame is under `motion_proxy`'s 3% jitter floor - scripting it
    would be scripting pixel noise. What actually moves is the **fluid over the player's head**,
    and it moves throughout:

        frame       9   10   11   12   13   14   15   16   17   18   19   20   21   22
        fluid px    9   20   37   77  120  240  246  255  268  291  267  281  308  315
        drip to y 227  227  229  231  233  251  254  254  254  254  254  254  254  256

    The surge is f12-f14 (+40, +43, +120 px, and the drip reaching the floor at f14), and the old
    script had *nothing* there: whole-frame difference reads 2.11 and 1.48 across those two frames,
    because a 120 px splash is nothing against a 480x270 frame. It is the clearest event in the
    hold and it was invisible to the proxy that was used. The two later ripples (f17-f18 +13/+23,
    f20-f21 +14/+27) are real but small, and keep the smaller burst the old curve gave the second
    of them.

    Amplitudes follow §48's rule that the lever is amplitude, not more pulses: 0<->50 at 111 ms
    (450 u/s, `shared_zombie`'s reference shape) for the surge, 0<->40 and 0<->30 for the two
    ripples. `variants.py` clamps the handy1 copy to that device's 364 u/s."""
    cy = [206.3, 202.9, 188.8, 154.5, 183.1, 159.4, 134.4, 145.6, 187.7, 210.8]
    pos = norm(cy, deep_is_max=True)                      # f9's 210.8 anchors the deep end
    acts = [(k * 125, int(round(p))) for k, p in enumerate(pos)]           # f0-f9, 0-1125 ms
    acts += [(1500, 0), (1611, 50), (1722, 0),            # f12-f14, the surge - fluid 37 -> 240 px
             (1833, 50), (1944, 0)]
    acts += [(2125, 0), (2236, 30), (2347, 0)]            # f17-f18, +13 then +23 px
    acts += [(2500, 0), (2611, 40), (2722, 0)]            # f20-f21, +14 then +27 px
    acts += [(2875, 0), (3000, 40), (3125, 0),            # f23-f27, the cum
             (3250, 40), (3375, 0), (3500, 6)]            # ends on f0's position
    return "BlindedBeast_Cum_T", acts, 3500


# ---------------------------------------------------------------------------------------------
# GoonShroom - the second grappler (§66), with a grab screen and three cling tiers.
#
# The grab screen is three mushrooms over the player, the middle one squatting; the exposed tip
# between its cheeks is a pale yellow-green (109,172,106) that the caps' blue-green (68,169,128)
# does not reach. R-B separates them cleanly - the tip sits at +3, the caps at -60 - so the mask
# is `(G > 140) & (R - B > -10) & (R > 80)` inside x 0.44-0.56.
#
# The three caps also bob, but by 3-7 px on a 209 px sprite (1.4-3.3%, at or under `motion_proxy`'s
# jitter floor) against a 14x range on the tip. They agree on which end is up and are ignored for
# everything else.


def gs_start():
    """`GoonShroom_GrabscreenStart` - 6 frames @8fps = 750 ms, one stroke.

        frame        0     1     2     3     4     5
        tip area   248    89    18    41    68   158      (14x range)

    Rider rule: the exposed tip is below the squatting shroom, so f0 (most showing) is the top of
    the lift and f2 (almost nothing) is fully seated. The caps confirm the direction - all three
    are highest at f0 - though they reach their lowest at f4 rather than f2, which is the body
    still compressing a frame after the seat. Their travel is at the jitter floor and the tip's is
    not, so the tip decides the phase."""
    area = [248, 89, 18, 41, 68, 158]
    return cycle(norm(area), 8, "GoonShroom_Start")


def gs_cum():
    """`GoonShroom_GrabscreenCum` - 25 frames @8fps = 3125 ms.

    The one cum scene in this file that needs no phase analysis: the same proxy works end to end,
    the whole-frame difference is a near-flat 3-8 for every frame pair, and nothing occludes the
    band at any point.

        f0-f5    248  95  24  50  68 166     the start clip's stroke, frame for frame
        f6-f9    290 245 124  56              a second, faster one
        f10-f15   84 122 179 231 305 311      a long lift, to the clip's maximum
        f16-f21  298 261 230 145  69  34      and a long plunge
        f22-f24   36  31  52                  held at the bottom

    Two strokes, a slow withdrawal and a slow deep thrust it stays down from. Measured throughout;
    the only written thing is the closing point, which returns to f0."""
    area = [248, 95, 24, 50, 68, 166, 290, 245, 124, 56, 84, 122, 179, 231,
            305, 311, 298, 261, 230, 145, 69, 34, 36, 31, 52]
    return cycle(norm(area), 8, "GoonShroom_Cum", cycles=1)


# The cling tiers. These are screen-edge overlays - one, two or three shrooms drawn hanging into
# frame - and the sprite's bottom edge *is* the screen edge, so a shroom sinking below it is drawn
# smaller rather than moved. That makes visible alpha area the natural proxy, and it is the same
# measurement `animcheck.motion_proxy` makes for `imp_1` (silhouette height, taller = higher =
# withdrawn); on tier 1, where both are available, they agree to within 2 points.
#
# All three dip hardest at f2 and recover by f5. The later tiers recover more slowly - 68, 56, 42
# at f3 - because more creatures are in frame and they are not in phase with each other. That is
# the whole of what the sprites escalate by, and on the device it is nothing: §81's play found
# the three as one intensity rather than a climb.
GS_TIERS = {
    "goonshroom_1": [10724, 9256, 2559, 8125, 10014, 10691],
    "goonshroom_2": [28467, 26256, 18948, 24292, 25927, 27435],
    "goonshroom_3": [66147, 63289, 55827, 60128, 62216, 64412],
}

# The climb, authored on top of the measurement (§83), the way the imps' is (§38). What escalates
# there is stroke RATE, not depth: every imp tier reaches a true 0 and a true 100, and the tiers
# run 2.0, 3.5 and 5.9 strokes/s - a whole extra stroke for each extra imp. The shrooms get the
# same treatment at their own 750 ms cycle: one dip per cycle, then two, then three, for 1.33,
# 2.67 and 4.00 strokes/s. That is 1 : 2 : 3 against the imps' 1 : 1.75 : 2.95.
#
# The first three points of tiers 2 and 3 are still their own measurement - the crest at f0 and
# the hard dip at f2 - so the primary stroke stays in phase with what is on screen and only the
# recovery half, which the sprites spend slowly climbing back, carries the added strokes. Every
# gap in the masters is >=100 ms and every transition in them stays under 960 u/s, a Handy 2 Pro at
# max overclock. The gallery twins replay the same curve on a 8/9 faster clock and so peak at
# 1056, which is the clip being faster and not a choice made here - the `handy1` variant is the
# answer for hardware that cannot follow, and `imp_3` (peak 1587) is far past both.
#
# The measured recovery values the climb replaces - f3-f5, 56/73/89 and 42/62/83 - stay in
# GS_TIERS above, so tier 1 still uses its own and reverting is a matter of deleting GS_CLIMB.
GS_CLIMB = {
    "goonshroom_2": [(375, 84), (500, 8), (625, 74)],
    "goonshroom_3": [(350, 90), (450, 5), (550, 92), (650, 6)],
}
GS_CYCLE_MS = 750.0


def gs_tier(name):
    """`GoonShroomGrapple_One/Two/Three` - 6 frames @8fps = 750 ms each."""
    def build():
        pos = [int(round(v)) for v in norm(GS_TIERS[name])]
        if name not in GS_CLIMB:
            return cycle(pos, 8, name)                    # tier 1: measured, frame for frame
        step = 1000.0 / 8
        beats = [(k * step, pos[k]) for k in range(3)] + GS_CLIMB[name]
        acts = [(int(round(c * GS_CYCLE_MS + t)), p)
                for c in range(LOOP_CYCLES) for t, p in beats]
        end = int(round(LOOP_CYCLES * GS_CYCLE_MS))
        acts.append((end, pos[0]))
        return name, acts, end
    return build


gs_1, gs_2, gs_3 = (gs_tier(n) for n in ("goonshroom_1", "goonshroom_2", "goonshroom_3"))


# ---------------------------------------------------------------------------------------------
# Gallery twins.
#
# §68 predicted these from the clip lengths and the sprite lists confirm every case. Eight of the
# ten scenes need one; two do not, and knowing *why* is the point:
#
#   Serpent_Cum          `Gallery_Serpent_Grab_screen_Cum` lists cum-Sheet_0..26 at 8 fps - the
#                        same 27 sprites, the same 3375 ms. One script is correct for both.
#   BlindedBeast_Start   `Gallery_BlindedBeast_Grab_Start` is sex-Sheet_0..4 at 9 fps, identical.
#
# Of the eight that do, seven share their master's sprite names, so `_remap_by_frame` can build
# the timeline map from the frames themselves rather than assuming the two clips differ
# uniformly - and for six of the seven it then *proves* uniformity by producing a straight 8/9
# rescale. The seventh does not: `Gallery_BlindedBeast_Grab_Cum` inserts one extra frame
# (`BlindedBeast-Cum2_15`, which the in-game clip skips) and holds the rest, so only that segment
# stretches. A uniform scale would have smeared 111 ms across the whole scene.
#
# `Serpent_Loop` is the exception in the other direction: the viewer plays a *redrawn* sheet
# (`sex-Sheet 1_0..6` against `sex-Sheet_0..6`), so there are no shared names to anchor on and it
# takes a plain rescale. Seven frames to seven frames at 875 -> 777.78 ms is 8/9 exactly.
REMAPPED = (
    # row,                            master,                gameplay clip,
    #                                 gallery clip,                              cycles
    ("BlindedBeast_Cum_Gallery", "BlindedBeast_Cum", "Blinded Beast Grabscreen Cum",
     "Gallery_BlindedBeast_Grab_Cum", 1),
    ("BlindedBeast_Start_T_Gallery", "BlindedBeast_Start_T", "Blinded Beast_T Grabscreen Start",
     "Gallery_BlindedBeast_Grab_Start_T", LOOP_CYCLES),
    ("BlindedBeast_Cum_T_Gallery", "BlindedBeast_Cum_T", "Blinded Beast_T Grabscreen Cum",
     "Gallery_BlindedBeast_Grab_Cum_T", 1),
    ("GoonShroom_Start_Gallery", "GoonShroom_Start", "GoonShroom_GrabscreenStart",
     "Gallery_Goonshroom_Gangbang_Loop", LOOP_CYCLES),
    ("GoonShroom_Cum_Gallery", "GoonShroom_Cum", "GoonShroom_GrabscreenCum",
     "Gallery_Goonshroom_Gangbang_Cum", 1),
    ("goonshroom_1_Gallery", "goonshroom_1", "GoonShroomGrapple_One",
     "Gallery_Goonshroom_Grabbed_1", LOOP_CYCLES),
    ("goonshroom_2_Gallery", "goonshroom_2", "GoonShroomGrapple_Two",
     "Gallery_Goonshroom_Grabbed_2", LOOP_CYCLES),
    ("goonshroom_3_Gallery", "goonshroom_3", "GoonShroomGrapple_Three",
     "Gallery_Goonshroom_Grabbed_3", LOOP_CYCLES),
)


def serpent_loop_gallery():
    """`Gallery_Serpent_Grab_screen_Loop` - 7 redrawn frames @9fps = 777.78 ms."""
    return _scaled_from("Serpent_Loop", "Serpent_Loop_Gallery", LOOP_CYCLES, 7000.0 / 9.0)


def remapped_scenes():
    """Build the frame-remapped gallery twins. Loads the assets once, hence a generator."""
    import animcheck as _A
    env = _A.load_env()
    for row, master, play_clip, gal_clip, cycles in REMAPPED:
        yield _remap_by_frame(env, master, row, play_clip, gal_clip, cycles)


MASTERS = (serpent_loop, serpent_cum,
           beast_start, beast_cum, beast_start_t, beast_cum_t,
           gs_start, gs_cum, gs_1, gs_2, gs_3)

# Everything here is a new row; `authored.write` only updates an existing Definitions.csv line.
NEW_ROWS = ("Serpent_Loop", "Serpent_Cum", "BlindedBeast_Start", "BlindedBeast_Cum",
            "BlindedBeast_Start_T", "BlindedBeast_Cum_T", "GoonShroom_Start", "GoonShroom_Cum",
            "goonshroom_1", "goonshroom_2", "goonshroom_3",
            "Serpent_Loop_Gallery") + tuple(r[0] for r in REMAPPED)

NOTE = "Derived from the 0.3.1 grab screen; see code/grabs031.py for the reasoning."


def main():
    built = [fn() for fn in MASTERS]
    if "--write" in sys.argv:
        for name, acts, total in built:                  # masters first: the twins read the files
            ensure_row(name, total)
            write(name, acts, total, NOTE)
    else:
        for name, acts, total in built:
            report(name, acts, total)

    # The twins replay their master's *file*, so a dry run before the first --write has nothing
    # to read. That is the point of reading the file rather than the function: re-running --write
    # after editing a master regenerates its twin, and the two cannot drift.
    missing = [n for n in (r[1] for r in REMAPPED) if not os.path.exists(
        os.path.join(ROOT, "Edi/Gallery/detailed", n.lower() + ".funscript"))]
    if missing:
        print(f"\n  {len(REMAPPED) + 1} gallery twins not built: their masters are not written "
              f"yet ({missing[0]} ...).\n  Run with --write.")
        return

    for name, acts, total in [serpent_loop_gallery()] + list(remapped_scenes()):
        if "--write" in sys.argv:
            ensure_row(name, total)
            write(name, acts, total, NOTE, min_gap=SCALED_FLOOR.get(name, 100))
        else:
            report(name, acts, total)


def report(name, acts, total):
    gaps = [b[0] - a[0] for a, b in zip(acts, acts[1:])]
    speeds = sorted(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000 for a, b in zip(acts, acts[1:]))
    print(f"{name:<30}{len(acts):>3} acts  end={total:<5} range "
          f"{min(p for _, p in acts):>3}-{max(p for _, p in acts):<4} min gap={min(gaps):>4}ms  "
          f"median={speeds[len(speeds) // 2]:>4.0f} peak={speeds[-1]:>4.0f} u/s")


if __name__ == "__main__":
    main()

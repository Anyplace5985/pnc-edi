#!/usr/bin/env python3
"""Ladders: sets of scripts a live signal switches between while the player is not in a scene.

    python3 code/ladders.py            # print what would be written
    python3 code/ladders.py --check    # do the shipped files still match?  (exit 1 if not)
    python3 code/ladders.py --write    # write the funscripts and add Definitions rows

No venv and no game install: nothing here is derived from a clip at run time. The one measurement
that shaped the serpent tiers - the hypnosis spiral's 500 ms period - is recorded in the comment
below rather than re-read, the way every other generator in this tree bakes its frame evidence.

Two of these exist.  The **filler ladder** is the seven rows the mod picks between on damage and
heat (`filler`, `filler_damage_25/50/75`, `filler_cum_25/50/75`), inherited from the upstream mod
and never measured against anything.  It is the only ladder left: the **serpent hypnosis** row
below used to be one too, and §125 replaced its tiers with a single row whose amplitude the mod
moves through Edi's `Intensity` endpoint.  It stays in this file because its shape is measured
against the game's own clip, which is what this module is for.

WHAT MAKES A LADDER DIFFERENT FROM A SCENE

A scene is dispatched once and plays out.  A ladder row is *replaced mid-playback* by its
neighbour, as often as the signal moves, and Edi has no crossfade: `SendPlay` POSTs a different
row name, Edi re-slices that file and plays it from the top.  So every switch is a discontinuity
unless the two files are built to make it one.  Three rules follow, and they are the whole reason
this module exists instead of seven hand-edited JSON files:

  1. **One time grid per ladder.**  Every row in a ladder puts its actions at the same
     milliseconds.  Then "the same phase" means the same point in the same gesture, and a switch
     that preserves phase is a change of amplitude rather than a jump to somewhere else.
  2. **A common anchor at both ends.**  Every row starts and ends at position 0, so a switch that
     lands on the loop seam steps the device by nothing at all.  `InproveLoopDetection` already
     forces `last.pos = first.pos` per file (learnings/edi-integration.md); matching *across*
     files is the part left to us.
  3. **Amplitude is the escalation lever, never density.**  The rows differ by how far they
     travel, not by how many points they have.  That is this project's own rule from §35 - a
     ±7 wiggle at 62 ms flattens to a straight line - and it is what makes rule 1 affordable.

The mod does the other half: it switches with `?seek=<phase>` so the incoming row starts where the
outgoing one had got to, and it puts hysteresis on the thresholds so a signal sitting on a
boundary does not flap.  See `Plugin.SendPlay` and `SerpentHypnosis.cs`.

Conventions are the ordinary ones - >=100 ms between points, speeds inside the reference band.
See ../learnings/funscript-authoring.md.
"""
import sys, os

from authored import ROOT, write                                        # noqa: E402
from rederive import ensure_row                                         # noqa: E402


# ---------------------------------------------------------------------------------------------
# The filler ladder
#
# GRID.  The six inherited rows already agree on a shape - a zigzag whose gaps widen monotonically
# through the cycle, so the pulse decelerates - and disagree only on the numbers:
#
#     filler_damage_25   200 220 230 230 250 260 300 310
#     filler_damage_50   150 180 190 200 220 240 330 490
#     filler_cum_50      190 200 210 220 260 280 300 340
#     filler_cum_75      130 150 170 180 210 240 320 600
#
# The grid below is those four averaged and rounded, which keeps the character they share and
# discards the disagreement that was costing us rule 1.  (`filler_damage_75` has ten points and
# `filler_cum_25` eight; they are the same shape at a different count, and they join the rest.)
#
# LENGTH is unchanged at 2000 ms.  Nothing needs it shorter now that the mod preserves phase
# across a switch instead of waiting for the seam.
FILLER_GRID = [0, 170, 360, 560, 770, 1010, 1270, 1580, 2000]

# Peaks rise through the cycle and ease off at the end; troughs are shallow, deepest in the
# middle.  Both envelopes are read off the inherited rows (`filler_damage_75` peaks 82/95/88/100,
# troughs 14/4/24) and are now stated once for the whole ladder instead of seven times.
PEAKS = [0.82, 0.95, 1.00, 0.88]
TROUGHS = [0.14, 0.04, 0.24]

# (row, peak amplitude, floor).  The floor is what separates the two families: damage jolts all
# the way to the bottom on every trough, arousal swells over a raised floor that drops as heat
# rises.  That distinction is in the inherited rows too (cum_25 troughs 18-34, damage_75 troughs
# 0-24); this keeps it while putting both families on one grid, so a priority flip between them
# is a change of depth rather than a change of gesture.
#
# `filler` is the row that plays for most of a session and it is the one row the grid was not
# derived from: the inherited version was a single 0-40-0 stroke per 1200 ms, 66 units/s of
# travel, while the six intensity rows were already eight points per 2000 ms.  §87 put all seven
# on the intensity grid and left `filler` at its inherited amplitude, which quietly doubled it to
# 128 units/s - four pulses in the time it used to take one - and a 2026-08-22 session felt it as
# the idle filler moving too much.  Density is not available as a fix here (rule 1), so the
# amplitude is set to whatever reproduces the travel rate that was accepted before: 20 gives
# 64 units/s, within a couple of units of the inherited 66.  The other six rows keep their old
# travel to within the rounding (damage_75 323 -> 323, cum_75 302 -> 296) and are left alone.
FILLER_ROWS = [
    ("filler",           20, 0),
    ("filler_damage_25", 55, 0),
    ("filler_damage_50", 75, 0),
    ("filler_damage_75", 100, 0),
    ("filler_cum_25",    55, 30),
    ("filler_cum_50",    75, 20),
    ("filler_cum_75",    100, 10),
]


def filler_row(name, amp, floor):
    """One row of the filler ladder on the shared grid.

    Index 0 and 8 are the anchor, odd indices are peaks, even ones in between are troughs."""
    acts, peak, trough = [], 0, 0
    for i, t in enumerate(FILLER_GRID):
        if i == 0 or i == len(FILLER_GRID) - 1:
            pos = 0
        elif i % 2 == 1:
            pos = amp * PEAKS[peak]; peak += 1
        else:
            pos = floor + (amp - floor) * TROUGHS[trough]; trough += 1
        acts.append((t, int(round(pos))))
    return name, acts, FILLER_GRID[-1]


# ---------------------------------------------------------------------------------------------
# The Black Serpent's hypnosis row
#
# `canHypnotise` on BrawlerEnemyAI, in the game's own words: "it drags the player's camera onto
# itself while it's on-screen and advances until it lands a grab".  There is no grab screen and no
# sexual clip - the three Hypnosis clips sit on the enemy's own controller beside Idle and Walk -
# which is why §71 left the states inert.  What is scripted here is the approach, not the scene:
# the closer it gets, the further the device travels, and when it reaches `grabRange` the grab
# lands and `Serpent_Loop` takes over from position 0, where these leave off.
#
# MEASURED, against `Black_Serpent_Hypnosis_Loop` in the 0.3.1 assets:
#
#   * 8 frames at 8 fps = **1000 ms**, which is the file length below.
#   * The silhouette is pinned - top edge 374-381 px on a 381 px sprite, 1.8%, under
#     `motion_proxy`'s 3% jitter floor - so the body is not what moves.
#   * `motion_map` puts every bit of real change in one blob: the spiral hovering over her head.
#     Its bright-pixel count, its radius and the phase of its first angular harmonic are identical
#     at frames k and k+4 and differ everywhere else, so the spiral's own period is **4 frames =
#     500 ms**, run twice per clip.
#
# To re-derive any of that:
#
#     PNC_GAME_DIR=game-linux .venv/bin/python -c "import sys; sys.path.insert(0,'code'); \
#       import animcheck as A; env=A.load_env(); \
#       sp,dur,fps=A.clip_frames(env,'Black_Serpent_Hypnosis_Loop'); \
#       print(len(sp),dur,fps,A.motion_proxy(sp)[1],A.top_edges(sp)); \
#       A.motion_map(sp,'/tmp/hyp.png')"
#
# So the device period is 500 ms and the file is two cycles - the same two-cycle convention every
# grab loop in this set uses, and here it is also the clip's own length, which means a phase
# preserved across a tier switch is a phase in the animation as well.
#
# POLARITY does not arise: a spiral turning at a constant rate has no deep end.  The guide's rule
# for motion that circles rather than strokes ("switch direction at each extreme so the device
# keeps moving even though nothing goes up and down") is what the triangle below is.
#
# The prefab's own numbers - hypnosisStartRange 8 m, grabRange 2 m, maxHypnosisDuration 6 s - set
# the band the tiers divide, and the mod reads them off the live component rather than repeating
# them here, so a retuned serpent retunes the ladder with it.
HYPNOSIS_PERIOD = 500
HYPNOSIS_CYCLES = 2

# Peak travel per tier.  Amplitude only: the spiral does not speed up as the serpent closes, so
# neither does the script.  90 over 250 ms is 360 units/s, just inside a Handy 1's 364, so the
# whole ladder is playable on the slowest device in the set without slew limiting.
# The far end of the band is deliberately not the smallest thing on the device.  The hypnosis
# does not replace a still device, it replaces the *filler*, and the same 2026-08-22 session that
# felt `filler` as too busy also felt the serpent as not clearly different from it.  Shape already
# differs - a constant-rate triangle at 500 ms against a decelerating zigzag at 2000 ms - but
# shape alone is not what a stroker communicates.  So the band starts at an effective 40 (160
# units/s of travel) against the idle filler's 64, which is a step up rather than a change of
# texture, and still leaves a clear increment above it.
# **One row, and it is no longer a ladder at all** (§125). Three tiers became two in §120 because
# the serpent crosses its 8 m-to-2 m band too fast for a middle rung to be felt; the 2026-08-25
# runs then showed that two is still one step in six metres, and that the problem was never how
# fast the ladder switched but how few places it could switch to. Edi's own `Intensity` endpoint
# scales the device's stroke range live, so the approach is now this single row played at an
# amplitude the mod moves with the distance - no tiers, no boundaries, nothing to keep on a shared
# grid with. `Serpent_Hypnosis_1` (peak 40) went with the tiers rather than being parked: a row
# nothing dispatches is a row that drifts.
#
# The peak stays 90. Intensity only ever scales *down* from what the script asks for, so the
# authored row has to be the loudest the approach will ever be, and the far end of the band is
# reached by playing this at 44% - which is the 40 units the deleted row used to play.
HYPNOSIS_ROWS = [("Serpent_Hypnosis", 90)]


def hypnosis_row(name, amp):
    """One spiral turn per 500 ms, anchored at 0 at every seam - including the mid-file one."""
    acts = []
    for c in range(HYPNOSIS_CYCLES):
        acts.append((c * HYPNOSIS_PERIOD, 0))
        acts.append((c * HYPNOSIS_PERIOD + HYPNOSIS_PERIOD // 2, amp))
    acts.append((HYPNOSIS_CYCLES * HYPNOSIS_PERIOD, 0))
    return name, acts, HYPNOSIS_CYCLES * HYPNOSIS_PERIOD


NEW_ROWS = {name for name, _ in HYPNOSIS_ROWS}


def build():
    for name, amp, floor in FILLER_ROWS:
        yield filler_row(name, amp, floor)
    for name, amp in HYPNOSIS_ROWS:
        yield hypnosis_row(name, amp)


def report(name, acts, total):
    gaps = [b[0] - a[0] for a, b in zip(acts, acts[1:])]
    fast = max(abs(b[1] - a[1]) / (b[0] - a[0]) * 1000 for a, b in zip(acts, acts[1:]))
    print(f"{name:<18}{len(acts):>3} acts  end={total:<5} range {min(p for _, p in acts)}-"
          f"{max(p for _, p in acts):<4} min gap={min(gaps)}ms  peak={fast:.0f} u/s")


def check():
    """Do the shipped `handy2pro` files still match what this module generates?

    A ladder's invariant is not visible in any one file - a hand-edited `filler_cum_50` looks
    perfectly reasonable on its own and only steps the device against its neighbours. `deploy.py
    --check` answers "is the game running the working tree" and nothing answered "is the working
    tree still a ladder", so this does. `--write` is the fix for anything it reports."""
    import json
    bad = 0
    for name, acts, total in build():
        path = os.path.join(ROOT, "Edi/Gallery/handy2pro", name.lower() + ".funscript")
        if not os.path.exists(path):
            print(f"  MISSING  {name}  ({os.path.relpath(path, ROOT)})"); bad += 1; continue
        on_disk = [(a["at"], a["pos"])
                   for a in json.load(open(path, encoding="utf-8-sig"))["actions"]]
        if on_disk != acts:
            print(f"  DRIFTED  {name}"); bad += 1
    # The grid and the anchor are the properties the mod relies on, so say them out loud rather
    # than leaving them implied by "no drift".
    grids = {tuple(t for t, _ in a) for _, a, _ in
             [filler_row(n, amp, f) for n, amp, f in FILLER_ROWS]}
    print(f"  filler ladder: {len(FILLER_ROWS)} rows on {len(grids)} grid(s), "
          f"{FILLER_GRID[-1]} ms; hypnosis: {len(HYPNOSIS_ROWS)} row, "
          f"{HYPNOSIS_CYCLES * HYPNOSIS_PERIOD} ms")
    if bad:
        print(f"ladders: {bad} file(s) do not match the generator - re-run with --write")
        return 1
    print("  ok - every ladder row is what code/ladders.py generates")
    return 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    for name, acts, total in build():
        if "--write" in sys.argv:
            if name in NEW_ROWS:
                ensure_row(name, total)
            write(name, acts, total,
                  ("One row of a switched ladder - shared grid, shared anchor, amplitude is the "
                   "only difference. See code/ladders.py.")
                  if name not in {n for n, _ in HYPNOSIS_ROWS} else
                  ("The serpent's approach, played at an amplitude the mod moves with the "
                   "distance. See code/ladders.py."))
        else:
            report(name, acts, total)
            print(f"{'':<18}{acts}")

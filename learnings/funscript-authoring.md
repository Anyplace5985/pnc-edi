# Writing a curve for the hardware

Device speed limits, point spacing, range decisions, per-device variants, and where the existing scripts came from.

**Read this when:** writing or editing a curve, or judging whether a script is playable on a given device

**Keywords:** units per second, Handy, stroke length, 100ms, buzz, vibration, slew limit, variant, handy1, provenance, ladder, shared grid, anchor

---

A funscript that matches the animation perfectly can still be unplayable. Position is 0–100 over
the device's stroke, so **speed = |Δpos|/Δt in units/s**, and every device has a ceiling:

| device | stroke | cap | units/s |
|---|---|---|---|
| Handy 1 | 110 mm | 400 mm/s | **364** |
| Handy 2 Pro, stock | 125 mm | 450 mm/s | 360 |
| Handy 2 Pro, max overclock | 125 mm | 1200 mm/s | **960** |
| Handy 2 Pro, motor absolute | 125 mm | 1600 mm/s | 1280 (not selectable) |

**The 125 mm rows are a Handy 2 Pro, and were all along.** They were labelled "Handy 2" until §103
because that is what the device was believed to be; the numbers came off the 2 Pro's own menu and
did not change when the label did. `speedcheck.py`'s keys are `handy2pro` / `handy2pro_oc`.

**Take these off the device, not off review articles** — those quote 800 mm/s for the
overclock, which is low by a third. The real figures are in the device's own slider-overclocking
menu, which also sets a *minimum*: 32 mm/s stock, 15 mm/s at max overclock. Below that the motor
does not track smoothly, so an extremely slow ramp is as unplayable as a fast one — it just fails
in the other direction. (Only 4 of 1271 transitions here fall under the stock floor, three of them
1–6 units wide; `Dragon_Grabbed`'s 3.9 s opening stroke at 31.7 mm/s is the only real one.)

Past the cap a stroker does not fail loudly — it **fails to arrive**, covering part of the
commanded travel before the next command lands. The stroke silently shortens and fast sections
turn to mush. That is invisible in every check that compares a script to its animation.

**Different kinds of scene are scripted differently** — the guide is explicit about it:

- **"Better to skip a stroke than add a non-existing stroke."** Do not invent motion.
- **"Often better to exaggerate the movement than to be completely true to the position."**
- **Blowjobs** are the stated exception to "avoid strokes under 20%": short strokes of 10–20% are
  right "when the girl only works the head", and oral "can often benefit from short, but slow,
  strokes". Where she moves laterally or circles with her tongue, *switch direction at each
  extreme* so the device keeps moving even though nothing goes up and down.
- **Riding/cowgirl** where she moves toward the camera on the way up "can easily feel out of sync
  due to difficult angles" — trust the depth cue, not apparent screen position.
- **Be true to the 0–100 range**: absolute position should mean actual depth.

The last two bullets fight: *exaggerate* pulls toward using the whole range, *be true to depth*
pulls toward a narrow band high up for head-only work. The line taken here is **exaggerate the
motion so a small bob is felt, but do not fake depth that is not on screen.**

- **≥100 ms between points.** The original Handy guarantees ~2 commands/s, ~6 at best. Denser
  points are averaged away. The best script in this set (`shared_plantasha`, verified 0.3%) keeps
  90% of gaps ≥100 ms, mode 125–150.
- **Bursts over the cap are normal, sustained excess is not.** That same script runs median 274,
  p95 483, peak 644 — well over 364 in places. Judge the median and p90, never the max.
- **A buzz is a half-range oscillation, not a tremor.** `shared_zombie` writes vibration as
  0↔50 every ~100 ms (410–540 u/s). A stroker has no vibrator motor; large fast strokes *are* the
  vibration. A ±7 wiggle at 62 ms is simultaneously too small to feel and too dense to reproduce —
  it flattens to a straight line, which is how §35's imp cum scene ended up feeling empty.
- **Avoid strokes under 20%** except during a blowjob, where 10–20% is accepted.

**Judge a script against a device by its median, never its maximum.** The maximum is an artistic
choice — a deliberate snap the motor renders as "as fast as you can" — and clipping it removes
intended punch. The median is what the motor has to sustain, and sustained excess is what makes
the stroke collapse. Getting this backwards produced a second stroker variant that limited 12 scripts
when only one (`imp_3`) was actually too fast for the device; the other eleven were being clipped
for accents. It was deleted. The Handy 1 variant survives because there the *median* transition
across the whole set (363 u/s) sits at the cap.

**Per-device versions are a variant, not a setting.** Edi picks the script by variant and the
variant is the *folder name*, so `Gallery/handy1/` needs no mod change — a device's `Variant` in
`EdiConfig.json` selects it. Generate by **slew limiting, never global scaling**: clip each
transition to `limit * dt`, so slow strokes keep their full range and only the impossible ones
shorten. And limit **cyclically** — every row is `Loop=true` and `InproveLoopDetection` snaps the
last action onto the first, so a start-to-end limiter leaves the wrap as an unclipped jump.
`code/speedcheck.py`, `code/variants.py`.

**Before building a ladder at all, ask whether the device can just be turned down (§125).** Edi's
`POST /Edi/Intensity/{max}` scales the stroke range live without re-dispatching anything, so a
graded set of rows that differ *only* in amplitude does not need to be a set: author the loudest
one and let the mod move the range. The serpent's hypnosis went three rows -> two -> one that way.
Two things decide whether it applies: the rows must differ in amplitude alone (Intensity moves
only the top of the range, so a set that widens from both ends - like the filler's cum rows -
cannot be reproduced), and the driving signal must move fast and continuously enough that steps
read as steps rather than as gestures. Everything below still governs the sets that stay ladders.

**A ladder escalates by amplitude on a shared grid, never by its own timing (§87).** Where several
scripts are alternatives for one situation - the seven filler rows, and until §125 the serpent's
hypnosis tiers - give them identical action times and one anchor position, and let only the travel differ.
Two reasons, and they point the same way: this project's own rule that the lever for a section
that reads as empty is amplitude rather than more pulses (§35), and the fact that anything else
makes the switch between two rows a jump to an unrelated place in an unrelated gesture. The
inherited filler set had six grids, six start positions and three different point counts for what
is visibly one shape.

**A ladder needs two guards, and they are not the same guard (§112).** Hysteresis is in the
*driving quantity* - metres, heat percent - and answers "is this crossing real". A minimum dwell is
in *seconds* and answers "is this crossing slow enough to be felt". The serpent's ladder had the
first and not the second, so honest crossings arrived 160 ms apart and read as noise; the filler
ladder has the same shape of exposure. Measure the dwell on `Time.unscaledTime`, or the pause menu
freezes it forever. And the count is a consequence: three steps over an approach crossed in three
seconds is not three steps, it is one blur, so **how many tiers a set should have is a question
about the crossing time, not about how much amplitude range there is to spend.** And when the
answer to that question comes out at "one", the set was never a ladder: the serpent's crossing was
short enough that two tiers still left three unresponsive metres either side of a single step, and
§125 replaced the whole apparatus - tiers, boundaries, hysteresis, dwell - with one row scaled by
Intensity.

**Judge "how fast should it feel" against the animation, not the tension.** The serpent's hypnosis
spiral turns at a constant rate the whole way in, so its ladder escalates at one fixed 500 ms
period rather than getting quicker as the grab approaches. Scripting a rising rate would have been
scripting the threat, which is not on screen.

**A ladder's grid belongs to its calmest row, and putting the loudest rows' density under the
calmest one doubles what the device does at rest (§91).** §87 averaged the filler grid from four
*intensity* rows and left `filler` - the row that plays for most of a session - at its inherited
amplitude on that grid: four pulses per 2 s where the inherited row had one per 1.2 s, and 128
units/s of travel where it had 66. It was felt immediately as the idle filler moving too much.
Because a shared grid is the point of a ladder, density is not available as a fix afterwards; the
amplitude has to absorb it (40 -> 20 restores 64 units/s). **Check every row's travel rate against
what it replaced before and after building a ladder** - one number per row, and it would have
caught this before the session did.

**The bottom rung of a ladder that interrupts the filler has to beat the filler (§91).** The
serpent's hypnosis tiers started at 30 against a filler at 40, so walking into a hypnosis made the
device do *less*, and the session felt the serpent as not clearly different rather than as an
escalation. Shape was distinct - a constant-rate triangle at 500 ms against a decelerating zigzag
at 2000 ms - and shape turned out not to be what a stroker communicates. 40/65/90 against an idle
filler of 20 is the fix. **Compare a new ladder to what it replaces, not to silence.** The rule
survives the ladder: the serpent's single row is authored at 90 and its far end is that row at 44%
intensity, which is the same 40 units against the same idle filler of 20.

## Provenance of the existing scripts

Three eras of script exist, and it matters which you're editing:

| file | origin | quality |
|---|---|---|
| `gallery.funscript` | **everydayhandyuser**, in the original `pnc edi integration` release | the original gallery scripts |
| `zombie/plantasha.funscript` (+ `.ofsp`) | shipped inside that same release, **scripted to video in OpenFunscripter**; scripter not named | best — verified within 0.3% |
| `new.funscript` | **Dupli9d**, 1 Jun | explicitly "very much work in progress"; a strip diced into consecutive slices |
| `ambient/peek.funscript` | **AniFS**, 6 Jun, scripted to mr_spunky's captures | good |
| `imp1/2/3.funscript` | **mr_spunky** | mixed |

`CREDITS.md` is the fuller version of this table, and the release thread is where all of it was
posted. **One entry here was wrong for months, in a way worth knowing about:** those two
OFS-authored files were credited to a name that is nobody on the thread — it is the *Windows
account name* embedded in the absolute paths inside the `.ofsp` projects, which
`strings` will show you. An identifier read out of a file is evidence about the machine it was
written on and only sometimes about who wrote it, and a stranger's local account name is not
something to publish either way (§142).

What that path does establish is that the scripts were authored inside the original release's own
directory, which is how they came to ship in it. Definitions had been pointing at `new.funscript`
slices while the properly authored files sat unreferenced.

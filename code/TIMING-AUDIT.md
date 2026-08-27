# Timing audit — animation periods straight from the game

2026-08-16. Companion to `NAMING-AUDIT.md`.

Every `Definitions.csv` slice compared against the **exact duration of the animation it plays**,
read out of the game's own `AnimationClip` assets. No video measurement, no autocorrelation.

## Method

Unity stores a clip's length in `m_MuscleClip.m_StopTime` (seconds), and the sprite-swap frame
count in `m_ClipBindingConstant.pptrCurveMapping`. Both read without script metadata:

```python
env = UnityPy.load("sharedassets0.assets", "sharedassets1.assets", "resources.assets")
for o in env.objects:
    if o.type.name != "AnimationClip": continue
    d = o.read_typetree()
    ms     = d["m_MuscleClip"]["m_StopTime"] * 1000
    frames = len(d["m_ClipBindingConstant"]["pptrCurveMapping"])
```

230 scene clips carry durations. Everything is a whole number of frames at 6, 8, 9 or 10 fps —
these are sprite animations, so the period is exact by construction.

## Why this supersedes measuring from video

PROJECT.md documents five distinct ways video measurement went wrong: harmonics, frame
quantisation, windows longer than one scene, magnitude signals giving the half-period, and
autocorrelation being meaningless below ~2 cycles. None of that applies here. The clip *is*
the ground truth.

The method validates against the scenes already confirmed by other means:

| scene | verdict from earlier work | this method |
|---|---|---|
| `Mimic_Start` | "verified correct — slice is exactly one animation cycle" | **1.000 cycles, 0 ms** |
| `peek_wendigo_ride` | retimed in §4 to fix a 2% slip | **4.000 cycles, 0 ms** |
| Gravy set | user: "really good" | all within 26 ms |
| Baphomet except `Loop2` | user: "very good" | Start exact, Cum/Cum2/Start2 within 23 ms |

And it confirms PROJECT.md's standing hypothesis: **the residual error is loop length, not
stroke period.** `Nun_Grab` measured 600 ms across four independent windows and the clip is
exactly 600 ms — the period was never wrong, the slice is 47 ms too long.

## The table

`cycles` = slice ÷ clip. A correct looping slice is a whole number.
`fix` = move `EndTime` when the cycle count is already right, or rescale when it is not.

| scene | file | slice ms | clip | clip ms | cycles | err ms | fix |
|---|---|---|---|---|---|---|---|
| `imp_grab_cum` | imp | 1506 | `Imp_Grab_Cum` | 3500.0 | 0.430 | -1994 | rescale x2.3240 to 1 cycles (3500ms) |
| `Mimic_Cum` | mimic_cum | 5580 | `MimicCum` | 3750.0 | 1.488 | +1830 | rescale x0.6720 to 1 cycles (3750ms) |
| `Nun_Cum` | nun_cum | 4201 | `GhoulGrabCum` | 3300.0 | 1.273 | +901 | rescale x0.7855 to 1 cycles (3300ms) |
| `Gooper_Cum` | gallery | 1739 | `GooperGrabScreenCum` | 1500.0 | 1.159 | +239 | rescale x0.8626 to 1 cycles (1500ms) |
| `Mimic_Loop` | mimic_loop | 1437 | `MimicGrabLoop` | 625.0 | 2.299 | +187 | rescale x0.8699 to 2 cycles (1250ms) |
| `Gooper_Start` | gooper_start | 2046 | `GooperGrabScreen` | 800.0 | 2.558 | -354 | rescale x1.1730 to 3 cycles (2400ms) |
| `ambient_gooper_bed_blowjob` | ambient_gooper_bed_blowjob | 3000 | `GooperPilloaryGallery_Loop` | 888.9 | 3.375 | +333 | rescale x0.8889 to 3 cycles (2667ms) |
| `Plantasha_Start` | new | 904 | `PlantashaGrab` | 1000.0 | 0.904 | -96 | rescale x1.1062 to 1 cycles (1000ms) |
| `imp_grab_loop` | imp | 1900 | `Imp_Grab_Loop` | 875.0 | 2.171 | +150 | rescale x0.9211 to 2 cycles (1750ms) |
| `Plantasha_Cum` | plantasha | 7133 | `PlantashaCum` | 3875.0 | 1.841 | -617 | rescale x1.0865 to 2 cycles (7750ms) |
| `Wendigo_Start` | gallery | 5489 | `WendigoKiss` | 5166.7 | 1.062 | +322 | rescale x0.9413 to 1 cycles (5167ms) |
| `Wendigo_Continued` | wendigo_continued | 3751 | `WendigoSex` | 1000.0 | 3.751 | -249 | rescale x1.0664 to 4 cycles (4000ms) |
| `Gravy_Cum2` | gallery | 11463 | `Gallery_Gravy_Grabbed_Cum2` | 1500.0 | 7.642 | -537 | rescale x1.0468 to 8 cycles (12000ms) |
| `Nun_Grab` | nun_grab | 1247 | `GhoulGrabStart` | 600.0 | 2.078 | +47 | rescale x0.9623 to 2 cycles (1200ms) |
| `ambient_imp_gangbang` | ambient_imp_gangbang | 3000 | `Gallery_Imp_Gangbang_Loop` | 777.8 | 3.857 | -111 | rescale x1.0371 to 4 cycles (3111ms) |
| `Dragon_Grabbed` | gallery | 4675 | `DragonFaceSit` | 4833.3 | 0.967 | -158 | EndTime 22284+4833 = 27117 |
| `imp3` | imp3 | 5160 | `Imp_Grab_Three` | 500.0 | 10.320 | +160 | rescale x0.9690 to 10 cycles (5000ms) |
| `imp1` | imp1 | 5330 | `Imp_Grab_One` | 500.0 | 10.660 | -170 | rescale x1.0319 to 11 cycles (5500ms) |
| `imp2` | imp2 | 4850 | `Imp_Grab_Two` | 500.0 | 9.700 | -150 | rescale x1.0309 to 10 cycles (5000ms) |
| `Dragon_Cum` | gallery | 1139 | `DragonSexScene` | 555.6 | 2.050 | +28 | rescale x0.9756 to 2 cycles (1111ms) |
| `Baphomet_Loop2` | gallery | 1230 | `Gallery_Baphomet_Grabbed_Riding_Loop` | 625.0 | 1.968 | -20 | EndTime 18497+1250 = 19747 |
| `Baphomet_Loop` | gallery | 1480 | `Gallery_Baphomet_Grabbed_BJ_Loop` | 750.0 | 1.973 | -20 | EndTime 11953+1500 = 13453 |
| `Gargoyle_Cum` | gallery | 3342 | `GargoyleCum` | 3375.0 | 0.990 | -33 | EndTime 30140+3375 = 33515 |
| `Baphomet_Cum2` | gallery | 2523 | `Gallery_Baphomet_Grabbed_Riding_Cum` | 2500.0 | 1.009 | +23 | EndTime 19744+2500 = 22244 |
| `Zombie_Cum` | zombie | 10133 | `ZombieGrabScreen_Cum` | 2555.6 | 3.965 | -89 | EndTime 13700+10222 = 23922 |
| `Gravy_Start2` | gallery | 2855 | `Gallery_Gravy_Grabbed_Start2` | 2875.0 | 0.993 | -20 | EndTime 46403+2875 = 49278 |
| `peek_nun_mimic` | peek | 3533 | `Peephole_Nun&Mimic_Loop` | 888.9 | 3.975 | -23 | EndTime 7770+3556 = 11326 |
| `Gravy_Loop2` | gallery | 1566 | `Gallery_Gravy_Grabbed_Loop2` | 777.8 | 2.013 | +10 | EndTime 49276+1556 = 50832 |
| `peek_gooper_pillory` | peek | 3534 | `Peephole_GooperBJ_Loop` | 888.9 | 3.976 | -22 | EndTime 28240+3556 = 31796 |
| `Gravy_Start` | gallery | 3852 | `Gallery_Gravy_Grabbed_Start` | 3875.0 | 0.994 | -23 | EndTime 33498+3875 = 37373 |
| `Baphomet_Start2` | gallery | 2486 | `Gallery_Baphomet_Grabbed_Riding_Start` | 2500.0 | 0.994 | -14 | EndTime 15994+2500 = 18494 |
| `Gargoyle_Grabbed` | gallery | 1991 | `GargoyleSex` | 1000.0 | 1.991 | -9 | EndTime 28132+2000 = 30132 |
| `Gravy_End2` | gallery | 3766 | `Gallery_Gravy_Grabbed_End2` | 3750.0 | 1.004 | +16 | EndTime 62339+3750 = 66089 |
| `Baphomet_Cum` | gallery | 2510 | `Gallery_Baphomet_Grabbed_BJ_Cum` | 2500.0 | 1.004 | +10 | EndTime 13450+2500 = 15950 |
| `Gravy_Cum` | gallery | 6974 | `Gallery_Gravy_Grabbed_Cum` | 7000.0 | 0.996 | -26 | EndTime 39412+7000 = 46412 |
| `Zombie_Loop` | zombie | 5315 | `ZombieGrabScreen_Loop` | 666.7 | 7.972 | -19 | EndTime 3300+5334 = 8634 |
| `peek_imp_three_way` | peek | 3100 | `Peephole_Imps_Loop` | 777.8 | 3.986 | -11 | EndTime 2006+3111 = 5117 |
| `Gravy_Loop` | gallery | 1995 | `Gallery_Gravy_Grabbed_Loop` | 1000.0 | 1.995 | -5 | EndTime 37367+2000 = 39367 |
| `Baphomet_Start` | gallery | 2502 | `Gallery_Baphomet_Grabbed_BJ_Start` | 2500.0 | 1.001 | +2 | none — exact |
| `peek_plant_bj` | peek | 3334 | `Peephole Plantasha Loop` | 1111.1 | 3.001 | +1 | none — exact |
| `peek_zombie_bj` | peek | 4000 | `Peephole Zombie Loop` | 1333.3 | 3.000 | +0 | none — exact |
| `peek_wendigo_ride` | peek | 2667 | `Peephole_Wendigo_Loop` | 666.7 | 4.000 | +0 | none — exact |
| `peek_nuns_threeway` | peek | 3334 | `Peephole_Nuns_Loop` | 555.6 | 6.001 | +0 | none — exact |
| `Mimic_Start` | gallery | 1750 | `MimicGrabInit` | 1750.0 | 1.000 | +0 | none — exact |

## Reading the fix column

- **none — exact** : leave alone.
- **EndTime N** : the script has the right number of strokes, the window is just cut a few ms
  short or long. Change `EndTime` in `Definitions.csv` and nothing else. Cheapest possible fix.
- **rescale xF** : the slice is not close to a whole number of cycles, so the script content
  itself has the wrong stroke count. Multiply every `at` by F and reset the window, or
  re-author. These are the ones that read as "doesn't match the action" rather than "drifts".

## Traps found while doing this

**Gameplay and gallery-viewer clips are not always the same length.** Gooper is the clear case:

| | in-game | gallery viewer |
|---|---|---|
| start | `GooperGrabScreen` 800 ms | `Gallery_Gooper_Grab_Start` 1000 ms |
| cum | `GooperGrabScreenCum` 1500 ms | `Gallery_Gooper_Grab_Cum` 1750 ms |

This explains the TODO's unresolved "`Gooper_Cum` — two windows disagree (995 and 1748)":
those were measurements of two different animations. **No single slice can be exact for both**,
so pick the in-game one and accept the viewer being ~14% slow, or split the row.

Dragon differs too (`DragonFaceSit` 4833 ms in-game vs `Dragon_Gallery_Grabbed` 4667 ms), and
the Gargoyle/Nun alt clips differ from their base clips in a few places
(`GooperGrabScreenCum` 1500 vs `GooperGrabScreenCumAlt` 1400, `GhoulGrabCum` 3300 vs
`AltGhoulGrabCum` 5500). The table above uses the **in-game** clip throughout.

**Zombie base and alt are timing-identical.** `ZombieGrabScreen_Loop` and `_LoopAlt` are both
666.7 ms / 6 frames / 9 fps, with identical muscle-clip byte size; `_Cum` and `_CumAlt` are both
2555.6 ms / 23 frames. The alt is a re-skin. One funscript correctly serves both, which is what
`Definitions.csv` already does — the `ZombieAlt1_*` rows point at the same file *and the same
slice*, so they are aliases expressed as rows.

**`Plantasha_Start` was retimed against a wrong number.** Earlier work recorded "slice 904 ms ≈
one 886 ms animation cycle, three strokes inside it" and concluded the timing was fine and the
problem was shape. The clip is **1000 ms** (`PlantashaGrab`, 8 frames at 8 fps), so the slice is
0.904 of a cycle. It is a timing problem after all.

**`Baphomet_Loop` has the same defect as `Baphomet_Loop2`** — both are 20 ms short of two
cycles. Only `Loop2` was ever reported.

**imp1/2/3 are ~10 cycles of a 500 ms clip.** The TODO guessed `imp3` "flutters at 172 ms, i.e.
~4 strokes per 666 ms animation cycle". The clip is `Imp_Grab_Three`, 500 ms, 4 frames at 8 fps
— so the cycle is 500 ms, not 666.

## Not covered

Diorama (`ambient_*`) scripts other than the two listed have no single obvious source clip —
the diorama animators are named for the room (`Gooper Bed Blowjob`, `Nun Chair Fuck`,
`Mimic wall fuck`) and were rebuilt by hand in §2 at 3000 ms. Worth a second pass: the two that
*can* be checked are both wrong (`ambient_gooper_bed_blowjob` 3.375 cycles of an 888.9 ms clip,
`ambient_imp_gangbang` 3.857 of 777.8), which suggests the whole set was authored to a round
3000 ms rather than to the animation.

The clip durations behind this table were cached to a scratch file while it was being written;
regenerate them with the snippet above if the game updates.


---

# Applied 2026-08-17

## Four scenes that §3 had made worse

`gallery.funscript` carries 27 chapters — the original author's own slice boundaries. Seven are
orphaned because §3 repointed those scenes onto dedicated files. Comparing the two showed the
repointing **broke cycle alignment in four cases**:

| scene | original chapter | cycles | §3 replacement | cycles | now |
|---|---|---|---|---|---|
| `Nun_Grab` | 1199 ms | 1.998 | 1247 ms | 2.078 | **1200 ms, 2.000** |
| `Mimic_Cum` | 3733 ms | 0.995 | 5580 ms | 1.488 | **3750 ms, 1.000** |
| `Mimic_Loop` | 1252 ms | 2.003 | 1437 ms | 2.299 | **1250 ms, 2.000** |
| `Wendigo_Continued` | 1986 ms | 1.986 | 3751 ms | 3.751 | **4000 ms, 4.000** |

`nun_grab.funscript` and `mimic_cum.funscript` turned out to be the chapter content **uniformly
time-scaled** — every keyframe ×1.049 and ×1.50 respectively. Someone stretched them to match a
video measurement, and that is exactly what broke the alignment. `mimic_loop` and
`wendigo_continued` are genuinely re-authored, so those keep their new shape and were only
rescaled.

All four were fixed by scaling every `at` by `target / slice`, anchored at **0** — not at the
first action. `mimic_loop`'s content starts 240 ms in (Edi inserts a point at `StartTime` when
the first action is more than 100 ms past it), and rebasing to the first action would silently
delete that lead-in.

## `Plantasha_Start` freed from `new.funscript`

The row was the last thing referencing `new.funscript` — Dupli9d's 728-action WIP strip — for a
single 904 ms slice. Extracted to `plantasha_start.funscript`, reproducing Edi's own slice rules
(endpoint insertion within a 100 ms tolerance, `last.pos = first.pos` for loops), so playback is
unchanged. `new.funscript` moved to `Edi/_reference/source-scripts/`, outside `GalleryPath`, and
dropped from the distributable.

**Still 0.904 cycles of its 1000 ms clip.** The extraction was deliberately faithful; retiming it
is a one-line scale whenever the rest of the drift list gets done.

## `GenerateDefinitionFromChapters` is harmless

Checked against the Edi source (`github.com/NoGRo/Edi`,
`Edi.Core/Gallery/Definition/DefinitionRepository.cs`). Two reasons it cannot touch our data:

```csharp
if (!csvFile.Exists) {            // only runs when Definitions.csv is absent
    GenerateDefinitions(GalleryPath);
    csvFile = new FileInfo($"{GalleryPath}Definitions_auto.csv");
```

and `GenerateDefinitions` writes to **`Definitions_auto.csv`**, never `Definitions.csv`. The 27
chapters are inert. Leave the flag alone.

Also worth knowing from that file: **duplicate row names throw** ("Can't have two galleries with
the same name"), and Edi slices with `at >= StartTime && at <= EndTime` then snaps the first and
last action onto the exact bounds. So the *played* duration is always the slice length — which is
why a retime has to rescale the content, not just move `EndTime`.


---

# 2026-08-17: strips split, two originals lost

The six multi-scene strips were split into one file per scene. Originals archived to
`Edi/_reference/source-scripts/` — **except `ambient.funscript` and `peek.funscript`, which were
deleted before being archived and are not recoverable.**

`gallery`, `imp`, `plantasha` and `zombie` were recovered from `mod/old/pnc0.2.1 patch fix.zip`
and verified by action count (447 / 28 / 84 / 77, all matching). `ambient` and `peek` came from
the eroscripts thread directly (AniFS, 6 Jun) and appear in no distribution zip.

What is gone is only the material **outside** the referenced slices: 3 of 59 actions in
`ambient`, 15 of 138 in `peek` — transitions between scenes in AniFS's capture strip. Every
referenced scene was extracted with playback verified identical, so nothing that plays was lost.
The practical cost is that the `peek` chapter boundaries can no longer be re-derived the way
`gallery`'s were, which is how four scenes got fixed earlier today.


---

# 2026-08-17: reading the animations directly

`code/animcheck.py`. An `AnimationClip` in this game is an ordered list of `Sprite` references at
a fixed sample rate, so the **frames themselves** are readable from the shipped assets — not just
the duration. That replaces video measurement outright for the scenes it can handle.

    .venv/bin/python code/animcheck.py "ZombieGrabScreen_Loop" zombie_loop --sheet

It prints the per-frame motion, the script sampled at the same phases, and their correlation;
`--sheet` writes a contact sheet of the frames so the scene can simply be looked at.

## Two proxies, both signed

1. **Silhouette top edge.** Sprites are alpha-trimmed from the top and share a bottom edge, so
   the trimmed height *is* the outline's top. Clean when the body's outline moves.
2. **Signed displacement.** Centre of where content appeared minus centre of where it vanished,
   against the median frame. Handles internal motion when the outline is pinned.

Both are signed on purpose. A frame-difference *magnitude* peaks twice per stroke — the trap
already documented above — and the first attempt at this produced exactly that noise.

## Validated on a known case

`Zombie_Loop` was reported inverted by feel. Measured against `ZombieGrabScreen_Loop`:
**correlation −0.63**, and **+0.63** after inverting. Two independent proxies agreed. That is the
control that makes the rest of the results trustworthy.

## Where it fails

- `nun wall chain head` — outline pinned, and the signed proxy gives `[0, 80, 100, 77, 99, 78]`:
  frame 0 is an outlier and the rest barely separate.
- `imp gangbang` — three imps moving independently; a single 1-D signal cannot represent it.

Semantics ("which end is deep") is still a judgement call, but it can be made from the contact
sheet rather than from a capture session.

## The diorama clip mappings were wrong

The earlier table mapped `ambient_*` scenes onto **gallery** clips. The dioramas have their own,
and they are much shorter. Corrected:

| scene | clip | period | slice | cycles |
|---|---|---|---|---|
| `ambient_gooper_bed_blowjob` | `gooper bed blowjob` | 500 | 3000 | **6.000** |
| `ambient_gargoyle_ledge_fuck` | `gargoyle ledge fuck` | 400 | 3200 | **8.000** |
| `ambient_mimic_wall_fuck` | `mimic wall fuck` | 500 | 3000 | **6.000** |
| `ambient_nun_wall_chain_head` | `nun wall chain head` | 750 | 3000 | **4.000** |
| `ambient_plantasha_blowjob` | `plant bj window` | 750 | 4500 | **6.000** |
| `ambient_nun_chair_fuck` | `Nun chair fuck` | 625 | 3145 → **3125** | 5.000 |
| `ambient_zombie_bench_fuck` | `zombie bench fuck` | 625 | 4867 → **5000** | 8.000 |
| `ambient_imp_gangbang` | `imp gangbang` | 1250 → **625** | 3000 → **3125** | 5 strokes |

Most were already exact — §2 authored them to a round 3000 ms and happened to land on it. The
earlier "the whole set is wrong" conclusion came from the wrong clips.

`ambient_wendigo_hole` has no obvious diorama clip; unresolved.

## A clip's length is not its stroke period

`imp gangbang` is a 1250 ms clip whose frames 0–4 and 5–9 are near-duplicates: they differ by
0.7–2.5 where neighbouring frames differ by 2.9–9.2. **It contains two strokes; the real period
is 625 ms.** Aligning to the clip would have given 2500 or 3750 ms; aligning to the stroke gives
3125 ms, a 4% change instead of 17–25%.

`animcheck.py` now detects this automatically by frame self-similarity and reports
`clip contains N identical strokes`. Check it before retiming anything.

## Rebuilt rather than inverted: `ambient_mimic_wall_fuck`

The outline is pinned (the figure is chained to the wall by the arms), so the silhouette proxy
is blind here. The moving element is the mimic's tongue — the red mass — and its top edge tracks
cleanly across the 5 frames: `67, 62, 78, 82, 75` px, with its area swelling as it rises
(2804, 2856, 1417, 1515, 1936).

Applying "tongue at the top = stroker at the top", one 500 ms cycle becomes
`75, 100, 20, 0, 35` at 100 ms steps, repeated for the 6 cycles of the 3000 ms slice. 43 hand
actions replaced by 31 derived ones — the animation is 10 fps, so five points per cycle is its
full resolution and anything finer is invented motion.

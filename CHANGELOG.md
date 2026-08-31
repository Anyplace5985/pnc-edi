# PNC + Edi — the decision record

Numbered `§1` upward, one entry per change: **what changed and why**, and at the end, what was
tried and rejected so it is not tried again. Only changes still in effect are listed.

**The numbers are the point.** `learnings/` states a rule and cites the `§n` that produced it, and
so do a dozen source comments — around 900 references in all. An entry here is the evidence behind
a rule somewhere else, which is why every number keeps its place even when its entry is two
sentences long.

**This is not release notes.** What a player needs — what changed, and what to do differently — is
[RELEASES.md](RELEASES.md), which is what ships in the archive. Nothing here is written for
somebody who only plays the game.

**The full narrative is not in this repo.** Each entry used to carry the session behind it: the
measurements, the theories that were wrong, what a log said on which evening, the reasoning that
led somewhere and the reasoning that did not. That is 11,700 lines of working notes and it is
`HISTORY.md`, untracked, in the working tree only — same treatment as `TODO.md` (§146), and for
the same reason: a clone should carry what another person can use, not a record of how the work
felt. If you need the full story behind an entry and you have no `HISTORY.md`, it is not
recoverable from this repo.

*(§1–§89 of the old narrative form did reach the public, inside the 2.5.2 archive and the portable
patch built on it, before this split. That is why the split is worth doing rather than academic:
everything from §90 on has never been published.)*

---
## 1. Gallery — wiring the two unused funscripts

The two scripts AniFS posted to the thread were sitting in `Edi/Gallery/` unreferenced.
Each is one long file containing several scenes; Edi plays a *slice* of a file, so they
needed `Definitions.csv` rows with per-scene time ranges.

## 2. Dioramas — all nine rewritten

The nine ambient diorama scripts were 0↔100 square waves, and four of the nine were one
file serving several scenes. All rebuilt with measured periods and a shaped stroke.

## 3. Enemy grab scenes — repointed to the properly authored scripts

`zombie.funscript` and `plantasha.funscript` were authored in OpenFunscripter against
per-scene video captures (their `.ofsp` project files name the source `.mp4`s) but were
unreferenced. The definitions pointed at slices of Dupli9d's work-in-progress strip
instead — including two rows with byte-identical ranges for different enemies.

## 4. Retimed from reference video

Eight gallery rows rescaled against reference video — shape preserved exactly, tempo only.
`peek_wendigo_ride` 653 -> 666.75 ms, `Nun_Grab` 572 -> 600, `Wendigo_Continued` 712 -> 1000,
`Mimic_Loop` 574 -> 625, `Gooper_Start` 963 -> 1000, `Nun_Cum` 788 -> 600 per stroke, `Mimic_Cum`
415 -> 623, `imp1` 432 -> 666. A further dozen were measured and confirmed already correct.

## 5. Definitions.csv hygiene

- `Type` column `reactive` → `reaction` on `filler_damage_25/50/75`. Edi only recognises
  `filler|gallery|reaction`; `reactive` silently fell through to plain gallery playback,
  ignoring the Reactive toggle and never auto-stopping.
- Removed dead rows `MimSic_Cum` (superseded by `Mimic_Cum` in the shipped DLL) and
  `Imp_Imp 1` (the DLL uses `Imp_Imp1`, no space).
- Deleted 13 unreferenced funscripts: 7 `peek_*` stubs, 2 superseded `ambient_*` stubs,
  `zombie (2).funscript` / `zombie - Copy.funscript` (byte-identical duplicates), and two
  generated files later superseded. `detailed/` went from 36 files with 13 orphans to 26,
  all referenced. Kept both `.ofsp` project files.

## 6. Config

**`BepInEx/config/com.edi.pnc.cfg`**
- `Patterns` restored to the plugin's full 9-entry default. It had been truncated to 6,
  silently dropping `plantasha blowjob`, `zombie bench fuck` and `wendigo hole` — those
  three dioramas could never fire from in-world proximity.
- Re-merged the split `imp gangbang 2` entry so its slug is `ambient_imp_gangbang`.
- Added `imp_loop=imp_grab_loop;imp_cum=imp_grab_cum;imp_grab=imp_grab_start` to
  `GalleryAliases` — these had been trimmed out, so the imp Loop/Cum scenes were rejected
  from the gallery with `EDI-SKIP`.

## 7. Plugin source recovered

The tree in `code/edimod/` was a v1.0.0 snapshot a week older than the shipped v2.0.8
DLL — 41 files vs 48, missing `HeatLockSystem`, `GrabEnemyProtection`, four
`EnemyReactivation*Hook` files, and crucially `GalleryRegistry.LoadDefinitions`.

## 8. Plugin fixes (behaviour changes beyond what was shipped)

1. **Blocked-grab dispatch leak.** `ImpGrappleGate` blocks a non-imp grab during an imp
   grapple via a prefix returning `false`, but Harmony still runs postfixes — so
   `GrabHooks.StartGrab_Postfix` dispatched the grab script anyway, yanking the device off
   the imp's loop every retry (~3 s). Added the same gate to the postfix.
2. **Reinforcement imps spawning through the floor.** `TryGetSpawnTransform` copied the
   *player's* Y to a point metres ahead, ignoring terrain. Added a downward raycast to
   snap to the actual floor. Also fixes the numpad debug spawner.
3. **Nothing stopped on quit.** There was no `OnApplicationQuit`/`OnDestroy` anywhere;
   closing the game left Edi looping the last gallery forever. Added one that blocks up to
   1.5 s so the POST actually lands (fire-and-forget is lost on process exit).
4. **Menus kept playing filler.** `OnSceneChanged` always called `GoFiller()`. Menu scenes
   (incl. game over → main menu) now `SendStop()` instead.
5. **Filler resumed at the previous run's intensity.** `RefreshPlayerHeatSnapshot` only
   *updated* when a `PlayerStats` existed, so in menus/gallery the old percentages
   persisted and filler came back as e.g. `filler_cum_75`. Now zeroed when there is no
   player.
6. **Enemies woke up after the death scene.** Once out of HP the player must finish the
   grab scene then press any key to quit — but `EnemyReactivationHelper` re-enabled AI
   regardless, letting an enemy grab them again and block the quit. Gated
   `ReactivateComponent` on `Plugin.PlayerDead` (explicitly disabling, not just
   returning). Renderers/colliders still restore, so nothing turns invisible.

## 9. Grappling imps no longer linger in the level

The imp that grapples you stayed standing in the world and slowly sank through the floor.
Vanilla never shows the world model during a grapple — the visual is a 2D UI overlay, and
`PerformGrabAttack` does `SetActive(false)` as soon as the grapple starts. `KeepImpsAfterGrappleShake`
needs the imp to survive the later `Destroy`, which `BlockDestroy` already handles on its own; but
`PerformGrabAttack_Postfix` *also* called `KeepAttachedImpVisible`, re-activating the object and
undoing vanilla's disappearance. `StabilizeAttachedImp` then disabled every collider without pinning
the Rigidbody, so an active body with nothing to stand on integrated downward.

## 10. Horny limit scales off the cum meter instead of max HP

The horny limit — the `Y` in the on-screen `Horny X/Y` — was `maxHealth / 10`, so a beefier
class got a longer horny bar. Wrong stat: vanilla keeps health and heat capacity apart, and the
coupling was entirely ours. `GetTotalLocks()` now divides the chosen stat by
`HeatLockUnitsPerLock`, with `HeatLockScaleSource` selecting `Heat` (default, the cum meter) or
`Health` (the old behaviour). Both stats default to 100, so the default class still gets 10 locks.
`_baseHeat` is re-recorded on every `SetMaxHeat` rather than snapshotted once, because class
multipliers and armour move capacity after startup.

## 11. Full lock means max heat, overheat clears at the lock floor, overflow restored

Three linked changes to the heat-lock endgame. **Full lock parks at `maxHeat - 1`** rather
than one point below the overheating threshold. That old dodge existed because vanilla's
`hasBeenOverheated` clears automatically only at exactly zero heat, which a lock floor makes
unreachable — one overflow would have disarmed the player for the rest of the run.
**`ClearOverheatAtFloor` fixes that at the source**, treating the lock floor as this system's
"fully cooled". And **heat overflow is restored**, since parking at the cap no longer costs the
player their attacks.

## 12. Cumming in a scene no longer costs HP

`GrabScreen.TriggerMaxHeatAnimation` deliberately drops invulnerability, lands damage and
puts it back — the only damage source that can kill the player *during* a scene, which is what
leaves a run softlocked. `CumDamageGate` flags the window and `GameplayHooks.TakeDamage_Prefix`
returns early inside it (`DisableCumDamage`, default true). Suppressed at `TakeDamage` rather than
by zeroing the serialized fields, so the animation and cooldown behave exactly as vanilla; the
reset is a `[HarmonyFinalizer]` so a throw cannot leave all player damage suppressed.

## 13. Dying *during* a scene now presents a game over

Dying while a scene was already running left the run unplayable: no game over, but enemies
inert, so the only way out was quit-to-menu.

## 14. Dying in an imp grapple plays out as the imp trio scene

§13 made the death *survivable-looking*: the player was revived to 1 HP for the duration,
which reads as invulnerability — enemies hit you, nothing happens, and the game over only
lands later. Replaced with a death sequence (`GrappleDeathSequence`, new file).

## 15. Damage filler now follows current health instead of sticking

`filler_damage_*` never went away once you were hit — healing back up, including this mod's own
auto-heal, left it playing. Two independent causes: `_lastDamagePercent` was a **high-water mark**
whose only reset is the no-`PlayerStats` branch, so in-game it could only ratchet up; and nothing
re-evaluated on a heal, because `RefreshFillerForCurrentHeat` early-outs unless heat moved and
healing changes HP. `GetFillerGallery` falls back to the damage map, so at low heat the stale damage
bucket won indefinitely.

## 16. Enemies revived after a scene keep the health they went in with

An enemy killed during an H-scene came back at **half max health**
(`EnemyKeepAliveHelper.RestoreHealthForAi`), which handed the player's kill back with
interest a few seconds later — the delay being `EnemyReactivationDelaySeconds` (5 s), since
the restore rides along with `EnemyReactivationHelper.Reactivate`.

## 17. Leaving a gallery scene stops the device instead of looping filler

Going from a gallery scene back to the character list left the device running. The TODO
blamed a missing hook, but `EnemyGalleryUI.ExitGrabView` was already patched — three
separate defects downstream of it were doing the damage.

## 17b. Enemies frozen after a scene ends

Enemies often never resumed after a scene — standing still, or doing nothing at all — well
past the intended `EnemyReactivationDelaySeconds` pause.

## 18. Extra spawns are scattered instead of stacked

Room spawns dropped several imps in the same spot: `ExpandSpawnPositions` padded the
spawner's position list by re-adding the **same `Transform`**, so two enemies got identical
coordinates. Each extra slot now gets a real Transform from `CreateScatteredPoint`, which tries up
to 8 candidates on a ring (`SpawnScatterRadius`, default 2 m) and requires floor under it, body
clearance — which also rejects a spot another enemy already holds — and a clear straight line from
the original, so a scatter cannot push a spawn through a wall. A slot with nowhere to go is
dropped rather than stacked, and says so in the log.

## 19. Mimics are usable again after their scene

A mimic that had grabbed you once stayed standing but could never be interacted with again.
Vanilla mimics are one-shot *by construction*: `TriggerMimicGrab` latches `hasTriggeredGrab` and ends
in `Destroy`, so the flag never needs resetting because the object ceases to exist a frame later.
`KeepEnemiesAfterGrab` blocks that `Destroy`, so the chest survives with the flag already latched and
`Update` gates interaction on `!hasTriggeredGrab` — kept alive without being made usable. `RearmMimic`
now clears the flag on reactivation, gated on the same setting that caused the survival.

## 20. Heat potions remove horny locks instead of flat heat

Flat cooling was close to worthless once locks existed: `CoolHeat_Prefix` trims any cooling
at the lock floor, so a potion drunk while locked was partly or entirely discarded. The three heat
potions now remove locks instead — Small 2, Medium 5, Large 10, configured by
`HeatPotionLockRemoval` and matched case-insensitively with the longest key winning.
`RemoveLocks` takes the locks and the heat they were holding, clamped at both ends. Vanilla's
cooling is suppressed by a flag rather than by zeroing `instantHeatReduction`, which lives on a
shared `ScriptableObject` and would leak across every copy of the item.

## 21. Diorama releases need line of sight and a look timer

A diorama's one-time horny release fired the moment it came into **earshot**:
`AmbientProximity.Tick` picked the nearest playing `AudioSource` within
`maxDistance x AmbientHearingMultiplier` and called `TryReleaseFromAmbient` on the spot. So
it could be spent by walking past a wall with a diorama behind it, without ever seeing it.

## 22. Peek holes are no longer treated as dioramas

The look meter appeared at the wendigo *peephole*, which is not a diorama. Peek holes carry
their own looping audio, and several diorama patterns match it —
`wendigo hole scene`, `zombie blowjob hole scene`, `zombiebjpeep` — so `AmbientProximity`
picked the peephole up as an ambient source and drove both playback and the release meter
from it.

## 23. Diorama visibility fixed, peepholes stop trapping, status text shortened

**Not one diorama ever charged.** The visibility test cast a single ray at the audio
source's own position — which sits at the object's origin, near the floor, and typically
exactly behind whatever is in front of it. Dioramas are routinely partly obstructed (prison
bars, furniture the player can see over), so that one ray failed essentially everywhere, and
a failing test is invisible: no bar, and no status either, because the source was neither
spent nor unusable.

## 24. One-time releases reset per run

**`UsedReleaseSources` was never cleared** — not on scene change, not on a new run. A
diorama or peephole consumed in one run stayed consumed until the game process exited.

## 25. Diorama line of sight: the ray was hitting the player

The ray started at the camera, which sits inside the player, so the first thing it hit was
the player's own collider — every sample point, every diorama, always. The occlusion test could
never pass anywhere in the game, and §23's widened sample spread could not have helped because the
failure was never about the diorama. `IsBlocked` now uses `RaycastAll` and discards hits belonging
to the player. Camera selection also skips cameras with a `targetTexture`, and
`AmbientPeekHoleRadius` drops to 1.5 m after the exclusion swallowed the zombie bench-fuck
diorama.

## 26. Dioramas: stop raycasting, use the game's own unlock box

The fourth failed test of the look meter produced two more blockers, neither of them the
player's body §25 had fixed — and not one `[EDI] Play ambient_*` in the whole run, since §21 gates
playback on the same test. **The game already answers this question without sight at all.** Every
diorama room carries a hand-placed `GalleryUnlockTrigger` with a `galleryID` of `D1`–`D9`, which is
the level designer's own definition of *the player has arrived at this diorama*.
`DioramaUnlockTriggers` finds them at runtime and answers from the trigger box instead of a
raycast.

## 27. Dying in a grab played damage filler over the whole death scene

`DeathHooks.Revive_Postfix` called `GoFiller()` unconditionally. A grab scene revives the
player *into* the scene, and vanilla's `Revive()` lands about two milliseconds after `GrabHooks`
has dispatched the scene's gallery — so the revive hook stomped it and the whole 16-second death
scene ran on `filler_damage_*`. Not enemy-specific: every grab scene entered at 0 HP went the same
way. `Revive_Postfix` now falls back to filler only when nothing else is playing
(`ReviveKeepsSceneGallery`, default true).

## 28. Releases: full payout, heat that actually moves, and a watch bar for peepholes

Three fixes to how a release pays out. **A diorama clears every lock** rather than one
(`AmbientReleaseClearsAllLocks`, default true), matching what a peephole gives. **The heat is
refreshed too**: `TryRelease` called only `EnsureHeatBounds`, so overheat stayed latched at the old
floor and the filler kept driving off a stale reading — even clearing every lock would have looked
like nothing happening. **Peepholes get a watch bar** instead of §23's instant release; the trap
was the countdown text, not the timer. `KeyholeReleaseWatchSeconds` is its own setting, because the
queued path gated on a `SceneEscapeGate` flag that is never armed for a keyhole and therefore read
a stale value left by the previous grab scene.

## 29. Name resolution rebuilt on ground truth

Name resolution had grown to **seven** overlapping resolvers ending in a substring matcher
that returned *something* for any string containing an enemy name — which is why gaps were
invisible, and why peek scenes resolved onto grab galleries. Ground truth came from the game: 168
`AnimatorController` assets read out of the shipped `.assets` files, and `code/slugharness`
compiles the real `NameRemap.cs` so coverage is countable. **131/131 pairs now map explicitly and
the greedy matcher is deleted**; an unmapped slug is returned unchanged and logged once as
`[ALIAS-GAP]`. The table moved into the DLL, having been the *default value* of a config setting
that froze on each user's first run. Full write-up in `code/NAMING-AUDIT.md`.

## 30. Gallery files: one scene per file

**Every animation's exact duration is readable** from `AnimationClip.m_MuscleClip.m_StopTime`,
so retiming no longer needs video measurement. Six multi-scene strips were split into 35 dedicated
files — 59 rows, 59 funscripts, every slice `0..len` — reproducing Edi's `inproveLoopAccion`
semantics and verified byte-identical through Edi's own pipeline. It also showed **§3's repointing
had made four scenes worse**, drifting `Nun_Grab`, `Mimic_Cum`, `Mimic_Loop` and
`Wendigo_Continued` off whole-cycle alignment; all four restored. `imp1/2/3` renamed `imp_1/2/3`.
Full write-up in `code/TIMING-AUDIT.md`.

## 31. Imp grapple, peek browsing, and the cum that never ended

**The cum animation repeated for the whole grab.** Vanilla ends a cum only when heat reaches
exactly 0, and a horny lock puts a floor under heat, so `heatFullyCooled` is never set and the
animation-complete event no-ops every time it fires — at any lock count. `CumCooldownEndsAtLockFloor`
completes the cooldown at the lock floor instead, the same trap §11 hit with overheat.
`FullLockHoldsCum` covers the remaining case, where the floor is `maxHeat - 1` and the cum would end
and retrigger within a frame. **Imp tiers no longer collapse onto one loop**: `GrappleLoopDelaySeconds`
defaults to 0, because vanilla has no generic grab loop to switch to.

## 32. Funscripts validated against the game's own animations

`code/animcheck.py` (one scene) and `code/animsweep.py` (all 51). An `AnimationClip` here is an
ordered list of `Sprite` references at a fixed rate, so the **frames themselves** are readable
from the shipped assets — exact period, exact motion, and the pixels can simply be looked at.
That replaces video capture for everything it can measure.

## 33. The second imp gangbang diorama, and a fallback that had quietly gone stale

Started as a documentation inconsistency: §6 recorded "adding an `ambient_imp_gangbang_2` row"
in the **do-not-redo** list, while TODO step 6 asked for exactly that. Both were written in good
faith — §6 rejected the row because no second funscript existed, §32 later found D5 and D6 are
different animations — but nobody reconciled them, so the do-not-redo entry was pointed at work
that had become correct.

## 34. Retiming pass: every script against its own animation's duration

`code/retime.py` — report by default, `--apply` to fix, `--max-pct` to change the cap. It reads
each clip's duration out of the shipped assets, divides the script length by it, and reports how
far that lands from a whole number.

## 35. The 3-imp grapple scenes, measured per imp instead of per frame

`imp_grab_loop` and `imp_grab_cum` felt arbitrary because every proxy so far averaged two imps
doing different things into one number. These are full-screen 480×270 frames with no alpha trim,
so the silhouette proxy is dead and `signed_shift` sees tails, arrows and background bodies as
readily as the act.

## 36. Scripting conventions, device limits, and per-device variants

Prompted by the imp cum scene reading as nothing. It was: the whole approach to expressing
vibration was wrong, and once measured against real scripting practice most of the set turned out
to be asking for motion no Handy can produce.

## 37. Step 1 polarity — neither scene needed inverting

Both were listed as polarity problems. Neither was. Both were the generic proxy watching the
wrong thing, and inverting would have made each *worse* while looking like a fix.

## 38. `Dragon_Cum`, and the scene-type conventions the guides give

**`Dragon_Cum`** — the frame is almost entirely dragon, so every whole-frame proxy tracks her mass
and reads INV −0.87. The cue from the feel pass was right: follow the penis of the character
lying on the ground. That is ~700–1400 px of cream at bottom centre, cleanly separable because the
dragon is deep red. Visible shaft runs `1354, 1159, 842, 732, 1179` px — most exposed at frame 0,
fully seated at frame 3.

## 39. The gooper scene was inverted — a shaft *through* a body reverses the rule

Caught on review, not by any tool. §37 derived `ambient_gooper_bed_blowjob` from the shaft visible
against the slime and mapped **more showing = withdrawn**, which is the rule for every other scene
in this set. It is the wrong rule here.

## 40. Step 4 — the three scenes authored from cues

No proxy finds these; each came from the feel pass as a statement about how it should feel.
`code/authored.py` holds the curves with the frame evidence and the cue that produced each, so
they are reproducible and arguable rather than an unexplained edit to a JSON file.

## 41. Step 5 — `Plantasha_Loop` dropped

A gallery entry for an animator state that does not exist — no Plantasha controller in the
game has a `Loop` state, verified from the assets before anything was touched. The only `loop`
states belong to the peephole, which used to reach this row through §29's greedy alias matcher and
now goes to `peek_plant_bj`. The row, both variants of `plantasha_loop.funscript` and the
`GalleryRegistry` seed came out; the gallery is 59 rows / 59 files. **The five aliases were
repointed to `Plantasha_Start` rather than deleted** — deleting them would turn a stray slug into
an `[ALIAS-GAP]` playing nothing.

## 42. Grab locks stopped depending on where you were standing

`AddLockForFirstScene` refused a lock whenever `SeenSceneSources` already held the key, and
`BuildSceneKey` includes the position **rounded to 0.1 m**. So the guard never meant "one lock per
enemy" — it meant **one lock per enemy per square decimetre**, which is why a mimic (which never
moves) granted exactly one lock per run while nuns and zombies seemed fine: they were being caught
somewhere new most of the time. **Grabs now lock on every entry**
(`HeatLockOncePerGrabSource`, default false). Peepholes and dioramas keep the guard, since they are
passive and would otherwise be farmable by walking back and forth.

## 43. `HeatLockUnitsPerLock` 10 → 20

A default change rather than a new mechanic — the setting already existed. What was missing
was any statement of what the number produces, because the divisor applies to the **final** heat
capacity, after the class's own multipliers and after this mod's `ClassHeatMultipliers` (shipped at
×2), so its input ranges over 100–250 rather than 100. At 10 that gave Mage and Ranger 25 locks to
work through; at 20 it is 13, and Knight drops from 10 to 5. Class stats read straight out of the
`PlayerClass` assets and confirmed against a run's own log.

## 44. Mimics: an interaction the game refuses no longer kills the chest

**The distance hypothesis was wrong** — all 18 gate lines read `inRange=True`, so the player
was never out of reach. What actually happens is that `MimicEnemy.TriggerMimicGrab` and the method
it calls **disagree about what refuses a grab**: the mimic checks only `grabScreen.IsGrabbed`, then
burns `hasTriggeredGrab` unconditionally and destroys itself, while `StartGrab` also checks
`CanBeGrabbed` and can bail after the chest has already committed. An interaction the game refuses
therefore killed the chest.

## 45. Mimics re-arm instantly instead of waiting on the enemy reactivation delay

`ScheduleReactivate` defers `Reactivate` by `EnemyReactivationDelaySeconds` (5), and
`RearmMimic` — the only thing that clears `hasTriggeredGrab` — runs **inside** `Reactivate`. So
a chest stayed inert for five seconds after its own scene.

## 46. A state the state machine cannot leave — Plantasha, and the same trap everywhere else (#14)

Diagnosed from one `SpinAiDiag` dump: three samples at +1.5 s, +6 s and +12 s after the grab
end, byte-identical — every gate open, nothing latched, no coroutine running, and she does nothing.
That ruled out the entire §17b family in one line. **The state itself is the trap**:
`UpdateStateMachine`'s switch has no handler for `Grabbing`, `Shooting` or `Dead`, so an enemy left
in `Grabbing` when its scene ends has nothing that can ever move it out. The same shape exists in
every enemy state machine in the game, which is what makes it worth a section.

## 47. The debug hotkeys, and two objects called the same thing

Started from "what do you mean a Wendigo was gated?" and ended up finding four defects, none of
which was the thing being asked about.

## 48. The last six scenes — and only two of them were the problem they were filed as

The six scenes `retime.py` reported and refused had been carried since §34 as "needs a feel
pass: is each one too fast or too slow?". Pulling the frames replaced that question for four of
them. **Timing is now 51/51 `ok` — the whole set is whole-cycle exact for the first time.**

## 49. A config setting in the wrong section is a setting the game never reads

Found by accident: `BepInEx/config/com.edi.pnc.cfg` kept turning up modified with no tool of ours
touching it. Bisecting every script left nothing — because the writer was **the game**. BepInEx
re-serialises the config on startup, and the only launch in days happened mid-session.

## 50. The gate that refused a scene and said nothing (#17)

The white screen came back — this time entering the **death grab** scene, not a full-lock cum. It
is not #15 returning: that was a latch, and this whole event ran at `locks=1/8 blocked=False
cumPlaying=False`. One gate, two symptoms, and it took a session to find because the gate was mute.

## 51. The gallery plays different animations, and a scene scripted against the wrong body

Feel-pass feedback, three findings, one of them structural. **`Wendigo_Continued` was
inverted and measured against the wrong subject** — `WendigoSex` has no alpha trim, so the
silhouette proxy had nothing to bite on and signed displacement tracked the cyan spill rather than
either body, scoring +0.45 against a curve running exactly backwards. A mid positive correlation
from a proxy watching the wrong object is worth nothing. **And the gallery viewer plays its own
`Gallery_*` clips**, which are a different length from the in-game clip for 12 of 29 rows — the
structural finding, and what §52 and §53 are about.

## 52. Six scenes the gallery now scripts for itself

§51 found that the gallery viewer plays its own `Gallery_*` clips and 12 of 29 rows differ in
length from the in-game clip they share a funscript with. This splits the six above the ~1.1×
threshold the feel pass established. **No DLL rebuild** — the mechanism was already there.

## 53. The rest of the gallery, held to the same standard as everything else

§52 split the six gallery mismatches above a **1.1× perceptibility** threshold and left six at
0.889×–1.065×. That was the wrong bar, and it was inconsistent with the whole rest of the project:
`animsweep` calls anything past **0.5%** not-ok, `retime` refuses to auto-apply past 5%, and the
set has been whole-cycle exact since §48. Leaving six rows 6–11% out because nobody happened to
notice them is the standard the tooling exists to prevent.

## 54. The suppression nobody undid (#18)

Reported from the 21:38 run: the wendigo grab scenes play correctly, but on exiting, the screen
freezes on the first frame of the wendigo start animation and stays there.

## 55. §54 reverted — the fix was wrong, and the probe said so

§54's `RestoreFullscreenGrabLayer` is removed. It did not fix the stuck screen and it made things
worse. Reverted rather than adjusted, because the reasoning behind it was wrong at the root.

## 56. The teardown undid itself — the animator was the thing turning the screen back on (#18)

The §55 probe localised it in one grab: of twenty EndGrabs sampled, **exactly one** — the
wendigo — turns the fullscreen grab layer back on between priority 500 and priority 10. Nothing in
either assembly does that. The mod's seven `SetActive(true)` calls are all enemy GameObjects, and
`GrabScreen::grabImage` is referenced in exactly three methods, only one of which sets it true and
only from `StartGrab`. **The animator did it**, out of a GameObject activation curve in the clip —
carried by six clips in the game, and they are the six chaser-boss ones.

## 57. The gallery feel pass — twelve for twelve, and the set is closed

The last twelve scripts, the `*_Gallery` rows from §52–§53, were played through the gallery viewer
on 2026-08-18. **All twelve match their scenes.** No changes needed, nothing to re-derive.

## 58. `mod/` deleted, and a release that builds itself — v2.1.0

`mod/` is gone: the hand-mirrored `single-mod` distributable, the 1.7 GB **PostNutCalamity 0.1.0**
build sitting inside it, `Edi.exe` and its `certificate.pfx`, the stale copy of the plugin source,
and `mod/old`'s original zips. In its place `code/release.py` assembles
**`dist/PncEdi-2.1.0.zip`** — 932 KiB, 172 files, no game binaries — from the working tree.

## 59. Edi bundled, the way the eroscripts mods do it

§58 shipped one archive and told players to fetch Edi themselves. That is not how mods in this
corner are distributed, and "download this, then download that, then put one inside the other" is
the step people get wrong. Edi is now bundled, fetched from its own GitHub release.

## 60. The release tested on fresh installs — and the one bug that found

`PncEdi-2.1.0.zip` extracted into untouched 0.2.1 installs of both builds and launched — the
Windows build under Wine and the native Linux build, identical from BepInEx onward, with the Linux
run also exiting cleanly. **The bug it found: the game does not ship executable.**
`Post Nut Calamity.x86_64` is mode 0666 in the shipped Linux build, and `start-pnc-linux.sh`
selected candidates with `[ -x ]`, so it found none and refused to start. It now tests `-f` and
chmods on the way through — before handing over to BepInEx's script, which has the identical trap.
**A permission bit is not a fact about a file, it is a fact about how the file got there**: any trip
through a zip loses it, and this only showed up because the test used a genuinely fresh unpack
rather than the working directory.

## 61. The archive is named for the game first

`PncEdi-2.1.0.zip` invited exactly one misreading, and it is the one that matters on a forum
post: that **2.1.0 was a version of the game**, which is on 0.2.1. Archives are now named for the
game first and the mod second — `PNC0.2.1-PncEdi-2.1.0.zip` — so the two numbers cannot be
confused. The game identity can only live in the name: `BepInPlugin` parses its version as semver
and the assembly attributes as `System.Version`, so neither can carry it.

## 62. The repo is the mod; the game is a symlink

This directory *was* a Post Nut Calamity 0.2.1 install with the mod living inside it, and
every path in the project assumed that — the csproj referenced `Post Nut Calamity_Data/Managed/`
two levels up, `animcheck.py` read `.assets` out of the repo root, and `.gitignore` defended a
2.3 GB tree with an allowlist. It is now the mod and nothing else: the game installs live outside
and are reached through the `game-windows` / `game-linux` symlinks, so a clone is small and two
game versions can be kept side by side.

## 63. Verifying the documentation against 0.3.1 before believing any of it

The game went 0.2.1 -> 0.3.1 and `Assembly-CSharp` grew 64% (613 KB -> 1002 KB, 321 -> 514 types).
Everything this project knows was measured against 0.2.1, so the first question is not "what is
new" but **"which of the things we wrote down are still true"**. `code/patchaudit.py` answers most
of it statically, and the answer is better than expected.

## 64. Porting to 0.3.1: the blocker, and wiring the new scenes that need no rebuild

Retargeted to game 0.3.1, mod version **2.2.0** — `PNC0.3.1-PncEdi-2.2.0.zip`. The 0.2.1 build is
not carried forward; the last archive for it is `PNC0.2.1-PncEdi-2.1.0.zip` and the naming from
§61 is what keeps the two legible side by side.

## 65. The guessable signal was outranking the game's own label

Asked why the port was looking at audio at all. The answer was that `Patterns` — a hand-maintained
list of AudioClip name fragments — is how a diorama is *identified*, on both routes. The better
answer is that it should not be, and the question exposed an inversion that had been there since
before §26.

## 66. Two grapplers, and one enemy with two grab screens

Both of these were found by static analysis during the wiring pass (§64) rather than in play, and
both are the shape where **the mod plays a real scene that is the wrong one** — which nothing
announces, and which no amount of reading `[ALIAS-GAP]` would ever surface.

## 67. Funscripts for the ten new dioramas and peek scenes

`code/scenes031.py` derives all ten - D10-D15 and the four peepholes - and the sweep is now
**73/73 ok** on timing, up from 63/63, with `Definitions.csv` at 81 rows. Each was looked at
before it was measured, which is the part that mattered: the generic proxy is wrong for almost
all of them, and in three cases the *first* scene-specific proxy was wrong too.

## 68. Checking the ten new scenes for the gallery split — and what it found instead

§52 exists because the gallery viewer plays its own `Gallery_*` clips and twelve differ in
length from the in-game clip, so one funscript cannot be whole-cycle correct for both. That question
had never been asked of §67's ten new scenes. **The ten are clean, for two different reasons**: the
six dioramas have no gallery twin at all, and all four peek scenes have one of the same length.
`gallerydiff.py` now carries the four pairs so a future game version re-asks by itself. What it
found instead is that the three enemies still to do are the opposite — seven of their nine pairs
differ, six by exactly 8/9.

## 69. The PPtr bug that used to help stopped helping

Asked whether the differing gallery versions needed extra funscripts. Checking that turned up
something else: `BlackSerpent GrabScreen` has 7 sprite frames and `animcheck.clip_frames` read it
as **zero**.

## 70. Documentation restructured: a learnings directory, and a TODO that is only TODO

Three files had grown into one another. `PROJECT.md` was 874 lines of which ~750 were accumulated
rules; `TODO.md` was 1017 lines of which most described work already finished; and both were loaded
in full whenever anything was consulted, because there was no way to load part.

## 71. The three new enemies scripted — the 0.3.1 port finished

The last substantial piece of the 0.3.1 port. Black Serpent, Blinded Beast and GoonShroom had
their grab screens wired since §66 and nothing to play: eleven slugs the slug harness printed as
`UNMAPPED`, which is inert and visible exactly as intended, and no use to anyone.

## 72. Escaping a grab was dead on 0.3.1 — the game turned legacy input into a throw

Reported as two broken things: the timed escape (wait out `EndGrabDelaySeconds`, press Q) and the
instant debug escape (numpad +). They are one fault, and it is not in the escape code at all.

## 73. The mod stands down from grab keep-alive — 0.3.1 ships the mechanic

Since §17 the mod kept grabbed enemies alive by force: block `Object.Destroy`, skip
`RemoveEnemyAfterGrab`, snapshot and restore health, then reactivate and rebuild the AI. 0.3.1 ships
the mechanic natively as `EnemyAI.hideInsteadOfDestroyOnGrab`, written by the code that owns the
state. **The mod now defers per enemy, on the game's own flag rather than on a version check** —
`VanillaGrabHiding.Handles(enemy)` reads the flag off whichever AI component the enemy has, so a
prefab that does not set it keeps the mod's mechanism and one that does gets out of the way.

## 74. The escape hint resolved its font once, too early — and the §73 stand-down is inert so far

Two findings from the 2026-08-18 Linux session. **The escape countdown was never on screen**,
though Q worked — which locates it between `ShowHint` being called and the screen. The font
hypothesis was right about the mechanism and wrong about the cause: the builtin font resolves fine
on this build, but `_hintFont` was resolved **once** and cached, so a null there is permanent for
the run. It now retries. **And §73's stand-down is inert so far**: no prefab in 0.3.1 sets
`hideInsteadOfDestroyOnGrab`, so the mod's own keep-alive is still doing all the work.

## 75. The game-over prompt was cancelled by our own teardown, inside a one-second window

TODO item 6: the player died in a nun grab, the log showed the deferred game over firing, and the
"press any key" prompt never appeared. Read as a suppression that outlived its case — the mod holds
three patches over `GameOverScreen` gated on `DragonGrabGameOverGuard.ShouldBlockGameOver` — but the
guard is not what does it, and the IL says so.

## 76. The seventh AI class, and a game over that any grab could undo

Three findings from the 2026-08-18 play-test. **The Black Serpent stopped acting after a
grab** because it runs `BrawlerEnemyAI`, a class 0.3.1 added that the §46 audit never saw, and
`SkipRemoveEnemyAfterGrab` names five classes without it. The generic `Object.Destroy` prefix still
kept the object alive, which is why the symptom was a standing serpent rather than a missing one:
state `Dead`, every coroutine stopped, and no `Dead` case in `UpdateStateMachine`. Six other
mechanisms named the same six classes, so none of them touched it either — **and the mod had been
logging the gap twice per run since the port**.

## 77. Correct §76: a grab taking the prompt down is the death rule, not a bug

§76 read two log lines as a defect and half-fixed a feature. A game-over prompt coming down
when a grab starts is **the mod's death rule doing exactly what it was built to do**: at 0 HP the
player stays grabbable, the grab that lands plays as the death scene, and the game over is presented
when that scene ends. §8 item 6 states it outright. Reverted from §76: the `OnPlayerDied` postfix,
`CanBeGrabbed = false` on commit (which would have refused the death grab outright),
`EnsureSceneEntrySurvival` declining during a presentation, and `Revive` is a release site again.

## 78. #14's strand: the mod restarted a grab and then killed it, one line apart

The 0.5 s hitch after a grab ends. The probe named the leaf in §73's run —
`StopGrab is nulling a live grabCoroutine while state=Grabbing`, from
`EnemyReactivationHelper.ApplyGrabEndCooldown` — and the missing half was *why the AI was in
Grabbing at all* on a path that had just reset it to Idle.

## 79. Escape delays retuned: 20 s, and 40 s for the chaser bosses

`EndGrabDelaySeconds` 30 → **20**, `EndGrabDelaySecondsChaserBoss` 90 → **40**, both as coded
defaults, and the live config moved onto both numbers — it had been sitting at 15 and 90.

## 80. Every peek scene went silent: 0.3.1 renamed the entries into jokes

**0.3.1 rewrote the peek entries' `enemyName` into flavour titles** — "It'll Fit... See!",
"Snussy Ray", "Making Puppies" — and `enemyName` was one of only two things `PeekGalleryMap.Resolve`
matched on. The other, `enemyID`, is `"P1"`..`"P11"`, which never matched anything either. So every
lookup missed and the fallthrough built a plausible-looking slug for a row that cannot exist, for
all eleven entries. The gap was **announced** rather than silent — `ALIAS-GAP`, `EDI-SKIP` and a
line per scene in `PncEdi-missing-definitions.log` — which is §2's rule working.

## 81. First play of the 0.3.1 set: two fixed, two queued

The gallery versions of §71's and §67's thirty unheard scripts, played for the first time. Four
findings; the two that are a number are done, the two that are a curve are not.

## 82. Release 2.5.0 — the 0.3.1 port, cut

The archive built for game 0.3.1 has existed since §71 and was never published; §75-§81 then
changed real behaviour on top of it. This section cuts the version that ships.

## 83. The GoonShroom cling tiers climb — 2.5.1

§81's play named the first of its two queued curve changes: `goonshroom_1` is right, and `_2`
and `_3` read as three takes on one intensity rather than the escalation the imp set has. This
does that, and takes the version with it.

## 84. `localhost` is not `127.0.0.1` on Windows — 2.5.2

The mod did nothing on a real Windows install. Under Proton the same build, the same config and
the same gallery worked. The two logs from the Windows session settle it between them.

## 85. A POST nobody watches — 2.5.3

§84's bug survived a whole Windows session behind a log that read as perfect, because
`[EDI] Play <name>` is written whether or not a byte left the process. This closes that.

## 86. The goonshrooms call each other in — 2.5.4

Reinforcement was the last imp-only piece of the grapple. §66 had already made the *cling
dispatch* follow whichever family is attached, so a goonshroom grapple plays `goonshroom_1/2/3`;
what still did not follow was the spawner, so a goonshroom grapple stayed at however many walked
into you while an imp grapple called in a third every 5 s.

## 87. The Black Serpent's camera grab, and what it taught the filler ladder — 2.5.5

Two asks from 2026-08-22, and they turned out to be one problem: a set of scripts that a live
signal switches between while the player is in no scene at all.

## 88. A reference video per scene, rendered rather than captured — tooling

Asked for on 2026-08-22: a frame-accurate reference video per scene, named for its funscript, so
another scripter can work against a video whose timing *is* the game's and hand back a curve that
needs no retiming. `code/refvideo.py` writes 93 of them into `Edi/_reference/videos/` — every row
in `animsweep.MAP`, which is every gallery row that answers to an animation.

## 89. Multi-axis, and the links to Edi itself

A scripter wants to work on multi-axis. Nothing here blocked that, but three things made it harder
than it needed to be, and all three are cheap.

## 90. The videos are for someone who has never seen this project — tooling

The reference folder from §88 read like an extract of this repo's notes: row names, ladder rows,
`textureRectOffset`, a sidecar of JSON per scene. Every word of it true, and all of it noise to the
person it is for — a scripter who wants to open a video and write a multi-axis script for it. Two
changes, both about removing steps rather than adding information.

## 91. What a session felt, and one enemy that was never there — 2.5.6

A Linux run on 2026-08-22 produced six notes and two asks. Four of them were answerable from the
tree; the rest need the log lines that only another session can produce, and are written up in
`TODO.md` with the exact line to look for rather than guessed at here.

## 92. The log was there the whole time — 2.5.7

§91 answered four of the 2026-08-22 notes from the source and said the other three needed another
session. **That was wrong, and wrong in an avoidable way: nobody opened the log.** All three were
already answered in `BepInEx/LogOutput.log` and `PncEdi-missing-definitions.log` from the run that
produced the notes. The rule this project keeps writing down — *a gap must be inert and visible* —
had done its job at every one of these; the visible part was simply never read.

## 93. The first item off the 2.5.7 list — the GoonShroom gallery plays

Confirmed in play on 2026-08-22 (Linux, 23:55-23:56 session), the first of the seven confirmations
the 2.5.7 handoff asked for. §92's one-line `Goon Shroom=goonshroom` remap entry does what it was
meant to: all five GoonShroom gallery rows resolve and dispatch.

## 94. Two guesses retired: the peek heuristic, and "assume there are more"

Desk work, no gameplay involved. Both items were the same shape — a place where the project was
carrying an assumption instead of an answer — and both are now settled in a way a future game
build re-checks by itself.

## 95. The setting a diagnosis depends on stops being a manual step — tooling

`WriteUnityLog = true` has now been the reason a session started blind twice (§56, §72), and both
times the fix was to set it by hand in the game's `BepInEx/config/BepInEx.cfg` and write a note
saying to check it next time. The note is what failed. `deploy.py` has forced `[EDI] Debug = true`
into every dev install since it existed, for exactly this reason; the BepInEx-side setting that
makes the game's own throws visible was left to a person.

## 96. Two seconds of loop after a cum, and a log line that stops blaming the wrong file — 2.5.9

**The post-cum grace (`Gameplay/PostCumGraceSeconds`, 2 s).** Under a horny lock the heat floor is
`maxHeat * locks / total`, so at 13 or 14 of 15 it sits one or two units below max. §11's
`CumCooldownEndsAtLockFloor` ends the cum at that floor; vanilla then refills those one or two units
in a fraction of a second and `TriggerMaxHeatAnimation` fires again before the grabbed loop has
played through once. On screen it is a flicker. On the device it is worse, because loop and cum are
different gallery rows: two scripts alternating several times a second. Full lock was already
handled — `FullLockHoldsCum` keeps the cum on screen where the floor is exactly one unit down — and
this is the tier below it, which had nothing.

## 97. The shaft does not shake; the fluid does — `BlindedBeast_Cum_T`'s hold re-measured

The last queued curve change from §83, and the last item on §81's play. The note read: *its one
late buzz burst was placed by whole-frame difference, not by anything visibly moving; the play
suggests the real proxy is the shaft's shake during the hold.*

## 98. The debug installs stop being quiet twice over — tooling

§95 forced `WriteUnityLog` and `[Logging.Disk] Enabled` and deliberately stopped, leaving two
questions as preferences rather than work: whether a run's log should survive the next launch, and
whether `Ambient/DiagnosticMode` belongs on in a dev install. Both are now decided the same way
§95 decided its pair — as a property of *being a debug install*, set on the deploy side, so
neither depends on what is committed.

## 99. The first real run of 2.5.9, and five defects its log named — diagnosis

2.5.8 and 2.5.9 had never been played. This is the session that played them: 40 minutes on Linux,
2026-08-23, the first log to survive its own successor thanks to §98's `AppendLog`. Clean of
`ALIAS-GAP` and `EDI-SKIP`, no new lines in `PncEdi-missing-definitions.log`, and the five
`failed: Connection refused` all predate Edi starting.

## 100. The rooms the game actually authored — spawn composition, `grappler-bias`

§91 added the goonshroom to `EnemySpawnShufflePool` because a session had found none anywhere.
That was the right fix for the symptom and it hid the cause: **the shuffle should not have been
choosing at all.**

## 101. Two numbers nobody had checked — the auto-heal unit, and the spawn ceiling

Both came out of one question — does the extra spawning trade against the HP regen — and
neither figure survived being looked at. **`HeatLockAutoHealRate` is in hundredths**:
`ApplyHeatScaledAutoHeal` multiplies by a hard-coded `0.01`, so the shipped `1` meant 0.01 HP/s, or
2.8 hours to refill the bar. §58 had read the description rather than the formula and marked it
`DEFAULT`, switching the mechanic off in every release from then to 2.5.2. **And the spawn ceiling
was an emergent product** rather than a number anyone chose, which is what §108 then had to finish
correcting.

## 102. Three of §99's four defects, and what the log said that §99 did not

§99 diagnosed five defects from the 2026-08-23 run and fixed none of them. This is the first
three, all in the plugin. The fourth (the hypnosis ladder's minimum dwell) is a judgement about
how the ladder should read and wants a play, not an edit, so it stays open.

## 103. The device was never a Handy 2 — a naming error, and the two totals it hid

The stutter reported on 2026-08-24 came with a correction: the device is a **Handy 2 Pro**, not a
Handy 2 with overclock, which is how every note in this project had recorded it. The obvious
reading of that — `speedcheck.py` has no profile for the user's hardware, so every "under the cap"
claim in the tree was made against a device nobody owns — turned out to be wrong, and the correction
is worth more than the fix.

## 104. The stutter is Edi's seeked loop — one defect, verified against the protocol

The 2026-08-24 report, given properly: *"when rapidly changing between the serpent hypnosis
scripts, the following serpent loop is laggy and stays laggy — skipped strokes — but shows
correctly on the Edi preview device, and after transitioning to cum and back to the loop it plays
normally again."* Every clause is load-bearing, and together they name the bug.

## 105. The device says it: a seeked loop is 1625 ms of buffer for a 1750 ms loop

§104 named a defect from code and protocol; the no-seek test build in `test/no-seek-into-looping-rows`
did not clear the stutter, and it was demoted to "real but not the cause". **That demotion was
wrong.** `code/handystate.py` asked the device what it was holding, and the answer is the
prediction, on the hardware, to the millisecond.

## 106. The stutter was Edi's, in four places, and is now filed upstream

§104 named a defect from code and protocol and was demoted when a test build did not clear
the fault; §105 proved a second from the device and it did not clear it either. The answer came from
**measuring the hardware rather than reading the source**: four defects in one method,
`HandyV3Device.SelectLoopPointsFromSeek`, all reachable only when a looping gallery is played with a
seek. The rotated buffer is never rebased to zero (the jerkiness); `SeekTime` stays in the gallery's
coordinates while the buffer is rebased (the desync, introduced by fixing the first); the buffer is
one inter-point gap short of a period; and the closing point collides with the shifted opening one.
Filed upstream as Edi PR #15.

## 107. Shipping a patched Edi, on purpose and with an expiry date

§106 left players on stock Edi v1.0.4, which stalls and desyncs the device on every pause and
resume. The fix exists, is filed as NoGRo/Edi PR #15, and is in no released build. So the archive
now ships **v1.0.4 plus that PR**, built from the branch, until upstream releases one.

## 108. Two defaults and a pin: the zero-lock spawn floor, and what the dev installs were running

Three small things, each wrong for a while with nothing saying so. **The spawn multiplier at
zero locks was 2, not 1** — §101 turned `SpawnCountMultiplier` into the zero-lock end of a ramp and
left the value it had carried when it meant something else, so an unlocked room spawned double
before the run had started. Now 1, which also restores vanilla spawn distance in an unlocked room.
**Nothing logged the ramp**, so "the floor is vanilla again" and "the patch never ran" looked
identical; `[SPAWN] wave x1.00 at lock progress 0.00: 5 -> 5` now names both ends once per wave.
**And the two dev installs were testing a stock Edi**, not the patched one.

## 109. The goonshroom's cum never played, and one space in a parameter name is why

Reported after the 2026-08-23 run and left deliberately uninvestigated (TODO, "Also open,
smaller"): reach max heat with goonshrooms attached, the scene plays, heat resets to the floor -
and never builds again. The first two suspects recorded there, a goonshroom path missing its
imp-only counterpart and `PostCumGraceSeconds` leaving `heatIncreaseBlocked` set, were both wrong.

## 110. What the Blinded Beast key found: two spawn-resolver defects, and a correction to §100

TODO item 6 asked for a Blinded Beast hint and key. The key itself was one config entry and one
binding. Getting it to spawn anything took two fixes, and finding out why corrected a claim this
project had already written down as airtight.

## 111. The debug keys, cut down to the number row

Eleven enemies, twelve keys, three of which did not spawn enemies and several of which answered
questions that are closed. Cut and re-laid-out, by decision, after a run showed which were
which.

## 112. The hypnosis ladder: two tiers, a minimum dwell, and only while the camera is pulled

The last of §99's four defects. **Three tiers were one too many** — the band is 8 m down to
2 m and a serpent closing it at walking pace gives three tiers about a second each, with the log
showing tier 3 landing 160 ms after tier 2. A step that short does not register as a step, so
`SerpentHypnosisGalleries` defaults to the two ends of the range and the contrast per step doubles;
nothing was regenerated or deleted, so going back to three is one config line. **A minimum dwell
was added, which is not the hysteresis already there**: hysteresis is in metres and asks whether a
crossing is real, and cannot help when a real crossing simply arrives too fast. And the ladder now
runs only while the camera is pulled.

## 113. Funscripts are not audio: the hearing metaphor out of the whole tree

A terminology correction, and worth a section because it had spread far enough through the tree
that the next pass would have copied it.

## 114. Five small open items closed at once — mod 2.5.11

None of these needed a run to decide, and all of them had been sitting in `TODO.md` as "known, not
fixed". They are unrelated to each other; what they have in common is that each was a place where
something claimed more coverage than it had — a keep-alive that covered one family and a game
version ago, a death sequence that covered one family, an audit that covered two of three
reflection routes, a spawn census that covered one of two spawn routes, and a display gate that
covered the config setting but not the scene.

## 115. The source cleanup, part one — the tooling and Plugin.cs

**No behaviour changed anywhere.** Every audit was captured before the pass and diffed after:
`patchaudit`, `cfgaudit`, `speedcheck`, `spawntables`, `animsweep`, `gallerydiff`,
`ladders --check`, `release --check`, `deploy --check` all produce byte-identical output, the
0.2.1 sweep still reads 63/63, `refvideo --verify` still decodes all 93, and the DLL rebuilds
clean with the same 9 pre-existing warnings. This is the "code cleanup and a better layout" item
from TODO §3, taken as far as it goes without a decision from the user, and it does not touch the
question that needs one (whether to un-ILSpy the rest of the tree — see below).

## 116. The decompiler idiom, removed — and the rule that protected it, retired

**Decided by the user, and it is what unblocked this:** there will be no future re-decompile of
this mod. The "match the decompiler idiom" rule in `code/README.md` and its re-apply list existed
only to keep a re-decompile a diff rather than a merge, so both are gone. §115 had left this open
as the one part of the cleanup needing a decision.

## 117. One parser for the `key=value` config format

Asked directly whether §115 and §116 had applied any design pattern. They had not — everything
structural in them was extract-method, extract-module and separate-concerns-by-file, which is the
honest answer and also the right work. So the tree was read again looking specifically for a
place where a *pattern* earns itself, and there was exactly one worth doing.

## 118. A test suite, and the boundary of what one can cover here

The project had no test infrastructure — only *audits*, which answer "does the mod still
bind to the game" rather than "does this function still do what it did", which is the question a
refactor asks. The boundary was decided first: most of the mod is Harmony patches over live game
objects, and mocking those would test the mocks. What is pure logic is steps 2-4 of the pipeline —
`ConfigMap`, `NameRemap`, `GalleryRegistry`, `GalleryAliases`/`GalleryTable`, `DioramaGalleryMap` —
the part between the game handing over a name and the HTTP call. 103 tests at the time, run with
`dotnet test code/tests/PncEdi.Tests.csproj`.

## 119. What the 2.5.11 run found, and the one bug that could end a run without ending it

The first play of 2.5.11 (2026-08-24, Linux, ~10 minutes on the sewers floor). Three of the seven
things it was sent to check came back clean; the other four are below, and two of them were not on
the list at all. **The mod is 2.5.12 for this**, because three of the fixes change what a player
sees.

## 120. What the 2.5.12 run found: the guard that was one stage too late

The first play of 2.5.12 (2026-08-24, Linux, sewers again — beast, serpent, chaser bosses, mimic,
goonshrooms and zombies). `ALIAS-GAP`, `EDI-SKIP` and `failed:` all zero. **The mod is 2.5.13 for
this.** The run also produced the first rotated log: §119's launcher change had landed, so the
2.5.11 session survived as `BepInEx/logs/LogOutput-20260824-132009Z.log` while this one was written
into a file of its own — which is the first time two runs could be read side by side without
counting lines.

## 121. One command for the thirteen checks — `code/check.py`

PROJECT.md's "Checking your work" table had grown to thirteen entries with four different
invocations (`python3`, `.venv/bin/python`, `dotnet test`, `dotnet run --project`). Running them
all by hand after a change is a minute of copy-paste; what actually happened is that a session ran
the two or three it remembered, and the rest were run when someone thought of them. `code/check.py`
runs the lot, in dependency order, and returns one exit code.

## 122. What the 2.5.13 run found, and one rule replacing another: protect, do not block

The first play of 2.5.13, and **the mod is 2.5.14 for what came out of it**. §120's move —
refuse the release while a game-over prompt is up — held, with both deaths answered at the panel and
none of 2.5.12's failure lines present. The rule it produced replaces §120's: **protect, do not
block**. Blocking an interaction the game offers turns one defect into a different one, so the mod
now guards its own state and lets the game's flow run.

## 123. The 1300 ILSpy locals, named

§116 left one thing behind on purpose: about 1300 locals still called `text`, `num`, `flag` and
`array`. Those were the ones a transform could not do. `string`, `int` and `bool` say nothing
about what a variable *is*, so every one of them is a judgement about what the expression means -
a hand pass, file by file, not a rewrite rule.

## 124. What the 2.5.14 run found: a constant mistaken for a measurement, and a gap that was never the mod's

The first play of 2.5.14 (2026-08-25, Linux, caverns — mimics, serpent, beast, goonshroom pile).
Clean of `ALIAS-GAP`, `EDI-SKIP` and `failed:`. **The mod is 2.5.15 for what came out of it.**

## 125. Distance drives the device, not the playlist

The hypnosis ladder had two answers available and both were bad. More tiers is the move the
2026-08-23 run already rejected - a step too short to register is not a step - and one flat script
throws the approach away entirely, which is the thing the feature exists to have.

## 126. Three open checks closed without a run, and one retired as unreachable

Nothing was built here. Four things were open on 2026-08-26 that each looked like they needed a
session at the keyboard, and three of them turned out to be already answered - two by earlier play,
one by the assets. The fourth is not a check anyone can run, in this build or any build shipped so
far.

## 127. The portable-patch fork, integrated: a mod manager, gameplay profiles, and custom enemies

`pncedi-portable-patch` is a fork of **2.5.2**, and three things in it were worth having. This
brings them across onto 2.5.15 rather than merging that tree: its baseline is thirteen versions and
a source refactor behind, so what came over is the *features*, adapted, and the diff against its
files was used as a reading aid rather than as a patch.

## 128. The port, reviewed — four things that do not survive this tree's layout

§127 brought roughly five thousand lines of custom-enemy code across on compile-correctness alone:
it built, `patchaudit` was clean, and the seams were hand-written and read. The bodies were not.
§127's own handoff said so, which is a note to a future session and not the same as having done it.
Reading them found four things that behave differently here, each of which could have shown up as
something other than what it was.

## 129. §127 and §128 played, and what a log said that reading had not

The branch had never been launched. §128's review had read the ported code and fixed what reading
could find; §127's three features had been reasoned about and not once seen. The 2026-08-26 run put
all of them on screen, and the log of that run — `game-linux/BepInEx/LogOutput.log`, ten minutes,
1880 lines — answered more than the run itself did.

## 130. The re-grab loop, measured rather than reasoned about — and three package decisions

§129's handoff named a suspect for the half-second re-grab cycle: `ClearStaleCoroutineHandles`
calling `StopGrab` with no `IsGrabbing` guard, on the ENEMY-AUTOFIX path that reaches enemies which
were never deactivated. It was a mechanism, not a diagnosis, and the handoff said so: instrument it
first, one guard if confirmed.

## 131. The custom-enemy framework becomes its own plugin

Four and a half thousand lines of package loading, sprite animation, gallery section and two shipped
behaviours moved out of `PncEdi` into `PncCustomEnemies`, a third BepInEx plugin. The mod that talks
to a device and the mod that loads other people's enemies are now separable: delete the DLL and what
remains behaves as though packages never existed.

## 132. The plugin boundary, and the check that keeps it honest

§131 split the mod into three plugins so they could move independently. That is only true if
changing one cannot silently break another, so this is where each one's responsibilities are
written down and where the gap in the enforcement got closed.

## 133. The learnings index gets a step that can be seen

`learnings/` is eleven files of rules this project paid for, and `CLAUDE.md` has asked every session
to "open the index before anything non-obvious" since it existed. Asked, and been ignored - this
session included. §130 worked out that committing a coroutine-driven state before its coroutine is
running is a latent hang by reading `AiStateGuard`'s header comment, when
`learnings/grab-and-ai-mechanics.md` had carried exactly that rule since §46. The same session
re-derived the CMF velocity-assignment trap from `WallPictureTrapPull`'s docstring, which
`unity-runtime.md` lists in its keywords.

## 134. A package's capture stops being processed as an enemy grab

Both behaviours that ship with the custom-enemy framework capture the player the same way: they call
vanilla's `GrabScreen.StartGrab(gameObject, null, ...)` and hand it their own GameObject as the
"enemy". From `PncEdi`'s side that is indistinguishable from a goonshroom grabbing you, so the whole
grab pipeline ran on it — and every step of that pipeline is wrong for a scene the package owns.

## 135. Custom enemies get a distribution: text in git, media as its own download

One `.gitignore` line, `BepInEx/custom-enemies/*`, was throwing away three things with
nothing in common: 53 MB of third-party art and audio (a real licence question, not ours to
redistribute), 1.0 MB of **our own funscripts** — the same product as `Edi/Gallery/`, authored and
measured by this project, with no third-party licence touching them — and 6.8 KB of hand-tuned
manifests and `SOURCE.txt`. The middle row was collateral of a rule aimed at the video beside it,
and the manifests were the tuning problem §134 walked into: the witch's `captureDistance` lived in
the changelog and two game installs and no tracked file. Text goes in git; media becomes its own
download.

## 136. The port to game 0.3.2, where vanilla had already fixed one of our open items

Game 0.3.2 landed on 2026-08-25 and this is the port, done on branch `port-0.3.2` against the
procedure in `learnings/porting-a-new-game-version.md`. Nothing in it has been played yet.

## 137. The documents put back inside their own boundaries

No code changed. `TODO.md` had grown from §70's 126 lines to **1207**, and almost none of it was
open work: closed items kept in place with a strikethrough and a "confirmed in play" note, a handoff
per session going back six of them, and a "standing guidance" section that had quietly become a
second copy of `learnings/`. It is now **195 lines** — open, pending-a-decision and
deferred-by-choice items, one handoff, nothing else.

## 138. The 0.3.2 port played, and what the log said about §136

The first run of 2.6.0 on game 0.3.2 (2026-08-27, Linux, ~21 minutes, 6,508 lines). **The port is
confirmed**: `[AI-AUDIT] ok`, one `[AI-GUARD]` line all session and **zero `unstuck`**, so the guard
is not fighting 0.3.2's new `Stunned` state; `[INPUT] backend repaired -> NewInputSystem` is the
known BepInEx-probes-before-the-keyboard line; no `[KEYBIND]` complaint and no throw. Serpent ramp,
witch aura, grapple tiers, escape, grab pipeline, game over, spawn and heat locks all behaved.

## 139. The custom gallery screen, read instead of inferred

The confirming run §138 asked for, which took three launches because the first two fixes were built
on the one part of that screen nobody had ever looked at.

## 140. Two reference targets deleted

A publishing item, decided rather than discovered.
`code/PncEdi-source-stale-2026-05-30/` and `code/PncEdi-v2.0.8-original.dll` are gone — the old
reference tree and the untouched shipped binary that was the revert target. Neither had been read in
months, and the DLL in particular is someone else's compiled mod shipped under no licence, which a
public clone is not the place to keep redistributing. Neither is recoverable: §143's squash means
what is not in the working tree is not anywhere. The three documents that named them now say so
rather than pointing at a path that is not there.

## 141. The publishing read-through, and the credit that was owed

A pass over every document with a publishing eye - `PROJECT.md`, `TODO.md`, `CLAUDE.md`,
`code/README.md`, the two audits, all of `learnings/`, and the `BepInEx/custom-enemies/` format
docs - looking for what would read wrongly to a stranger. What it did *not* find is worth stating
first: no author identity anywhere, no credentials (`code/dist/EdiConfig.json` ships `"Key": null`),
no first-person author voice, and nothing unfair about upstream or about the game's developer -
`working-practice.md` already carries "inherited code is not wrong, it is differently-assumed" as
its own correction.

## 142. The release thread read, and what it corrected

§141 wrote `CREDITS.md` around a gap — two of the authors it credited had no name in this tree.
Reading the mod's own Eroscripts thread closed the gap and corrected the shape of the credit
itself, which was wrong in a more interesting way than being incomplete.

## 143. The CHANGELOG read through with a publishing eye

The last of the publishing items, and the one with no check behind it: ~9,700 lines of narrative
that `release.py` ships in every archive as `PncEdi-CHANGELOG.txt`, never once read as a whole by
anyone deciding what a stranger should see. §141 did that pass over every other document and found
four wrong claims in shipped text; this is the same pass over the file that was left out of it
because of its length. Read end to end, 143 entries.

## 144. The dead zombie knob, deleted

The last item standing between the tree and a release build, and the smallest: what to do about
`ZombieGrappleChargeRate`. §138 established that it reaches nothing — `ApplyZombieGrappleTuning` is
a postfix on `ChargingEnemyAI.Start` that then requires `key == "zombie"`, and no zombie prefab is a
`ChargingEnemyAI` in 0.2.1, 0.3.1 or 0.3.2. The zombies are plain `EnemyAI`, so they neither charge
nor grapple, and the intersection the patch is gated on has been empty since before this mod was
recovered. §138 left three ways open: delete it, repoint it at the clinging family, or keep it and
say what it is.

## 145. The plugin DLLs untracked, and a README for strangers

The three plugin DLLs under `BepInEx/plugins/` had been tracked since the repo began, on a reason
written into `.gitignore`'s own header: they are what `release.py --no-build` ships, and the only
artefacts a clone cannot rebuild without a game to compile against. That reason is true and it was
still the wrong call for a repo about to go public.

## 146. `TODO.md` untracked, and the documents that assumed it

`TODO.md` was tracked, and it is the one file in this repo written with no reader in mind — one
person's handoff to their next session, carrying half-formed diagnoses, what is annoying, and what
is not worth doing. Publishing it makes it one of two things: curated, which costs exactly the
honesty that makes it useful, or a private to-do list handed to strangers. Untracked, it stays what
it is.

## 147. Two dead switches, found by checking a report against this tree instead of believing it

A player posted a bug list and a wishlist in the release thread. It was worth reading and it was
**not a report about this mod**: post 112 is a reply to post 80, by the author of the other build
in that thread, so every bug in it was observed on that fork. Only the follow-up replies here, and
on the same build. That was established after the first two items had already been worked, which
is why it is the first thing this entry says — the list is a set of leads, and a lead is checked
against this tree or it is nothing.

## 148. Heat scaling read out of the IL, and filler that outlives the run

Two jobs out of the release thread's list, one static and one built. **The heat-scaling
report was answered from the assembly rather than from a run**, since post 114 measured it on the
other build: `ikdasm` over `Assembly-CSharp.dll` shows `PlayerStats::maxHeat` has exactly three
writers, and the class multiplier, armour's additive bonus and the buff system all reach
`SetMaxHeat` — so scaling *is* dynamic here, and `_baseHeat` re-records on every change. No defect
that can be closed from a desk. **And filler outlived the run**: it kept playing past the point
where the percentages it reads belong to a run that has ended.

## 149. Device variants named after devices, and a second stroker script after all

Out of the release thread again, but a different thread: the multi-axis scripting guide,
<https://discuss.eroscripts.com/t/multi-axis-scripting-in-ofs-tutorial-tips-and-resources/328979>.
It was read for its speed limits, which were reported as being much lower than this project uses.

## 150. Softening a scene without editing its script

The other half of the thread's post 113 list: a player whose desk `imp_3` shakes was told to copy
the `handy1` variant over `detailed` as a stopgap. That is the wrong lever twice over - it swaps a
*speed* limit in to fix a *strength* complaint, and it does it by overwriting the masters.

## 151. The chaser bosses get an aura, and the ramp is rate-limited

The last of the release thread's feature requests (post 113's list, §147 for what that list is and
is not): the filler should build as the dragon's or the wendigo's approach closes in, instead of
playing the same way whether the boss is across the floor or behind you. `ChaserAura.cs`, and the
whole of it is `SerpentHypnosis`' §125 apparatus pointed at a second signal - one row, no tiers,
`POST /Edi/Intensity/{max}` moving the device's range in place while the filler keeps looping.

## 152. §147-§151 played, and five of the six things the run found

Three in-game runs on 2026-08-29, 16:40-17:06, all in one `game-linux/BepInEx/LogOutput.log`
(2890 lines — the launcher rotated nothing between them, so it is one file). Every one of
§147-§151's seven confirmations came back: the menu filler and the pause settings work, the
renamed `handy2pro` variant plays, §147's spawn fix holds with no level change, §147's service
exemption matched its fragment, §150's two knobs compose correctly, and §148's open question —
whether `activeSceneChanged` fires before or after the new scene's `Awake` — is settled *after*,
read straight off `playerStats=yes baseHeat=100` on every `[SCENE]` line rather than reasoned about
from the IL. Floors 2+ were observed for the first time in this project's history and hold no
defect: `Floor1` at `5/8` -> `Stage1Shop` -> `Floor2` at `1/9` in one run, `14/14` against 275 heat
in the other, the feared `M=5` never appearing. The release thread's imp-downing report (post 112,
§147) does not reproduce here either — the downed scene's own row plays, phase-matched.

## 153. §152's four fixes played, a new pause defect found, and the chaser aura rebuilt as a real row

A second run, 17:57–18:12 on 2026-08-29, one log (`game-linux/BepInEx/LogOutput.log`, no rotation
since launch). Three of §152's four fixes are confirmed; the fourth prompted a redesign rather
than a confirmation, once played against.

## 154. §153's focus/pause defect fixed (twice), ChaserStomp played and retuned, and a silent lock-loss found

**The focus/pause fix took two passes, because the first covered half the state space.**
§153's defect was `OnApplicationFocus`'s regain branch calling `SendResume()` off its own flag with
no read of `PauseHooks.GamePaused`, so an alt-tab undid the pause menu's own pause a minute early.
Guarding on `!GamePaused` then breaks `FillerWhilePaused`: opening the menu with filler active
leaves the device unpaused, but losing focus pauses it anyway, and the blanket guard would leave
that pause stuck forever. `PauseHooks` grew `DevicePausedByMenu` so the guard can ask the sharper
question — defer to the menu only when the menu is the one actually holding the device paused.
`ChaserStomp` was played and retuned, and a silent lock-loss found on entering the shop.

## 155. §154's shop fix played wrong and re-diagnosed from timestamps, and ChaserStomp's ramp deleted in favour of the row's own grace

**§154's shop fix was built on a theory nobody had checked against the log's own timestamps,
and it did not survive being played.** The theory was that the shop's transient `baseHeat=100`
arrives *after* `ResetForScene` zeroes `_baseHeat`. Lining the timestamps up rather than the printed
content found it backwards: the clamp fires 21 ms **before** the scene change, while `_baseHeat`
still holds the previous floor's real value, and the shop never sends a correcting `SetMaxHeat` at
all. The real fix defers the clamp instead of gating it on a reset. The generalised lesson is in
`learnings/debugging-and-diagnostics.md`: an ordering theory is a guess until the timestamps are
compared. `ChaserStomp`'s ramp was deleted in favour of the row's own grace.

## 156. The three femboy-witch masters' backwards timestamps, fixed by tracing Edi's own loader

§149 found three `femboy-witch` aura masters with a tail written past the row's own 60 s
duration, and left open whether it was a real closing stroke or noise. Reading Edi's own
`FunscriptRepository.ReadGallery` settles it: it filters to `at >= StartTime && at <= EndTime`
before anything else runs, so an action past the declared `endTime` is dropped before dispatch —
never played, wherever it sits in the file. `inproveLoopAccion` then forces `last.pos = first.pos`
on whatever survives. Every file's in-window last action already sat at exactly `at=60000` with the
first action's `pos`, so the honest wrap point was never missing, just followed by dead data.
Data-only fix, and the loader's own filter proves it was inert.

## 157. §155's shop-lock fix and ChaserStomp retune both played and confirmed; a real pause-menu gap found and fixed alongside them

**§155's deferred heat-lock clamp is confirmed — the shop no longer costs locks.** Entered
`Stage1Shop` at 8/8, no clamp line fired during the visit, and the full count survived to the exit.
The clamp's other half — that it still fires when it should — remains unexercised, because no
genuine mid-floor armour shrink happened this session; that is untested, not known broken. **The
reworked `ChaserStomp` band plays well**, and `ChaserStompIntensityNearDistance` moved 5 → 6 m on
that read. A real pause-menu gap was found and fixed alongside them.

## 158. The gameplay-profile audit: `Vanilla` really is vanilla, and one display-only gap found instead

The open item asking whether `Vanilla` actually leaves combat, health, heat and spawning to the
game — never audited before, and flagged as likely to have gaps because a patch only obeys
`GameplayProfileRules`'s truth table if it *asks*. Read `GameplayProfileRules.cs` and
`GameplayProfiles.cs` first, then all 30 `[HarmonyPatch]` classes in `code/edimod/PncEdi`, tracing
what each does under `Vanilla` specifically rather than trusting a grep for `ConfigEntry`.

## 159. The 2.6.0 release build, and WebM package video confirmed on Windows

`check.py --full` ran 13/14, `deploy` the one failure — `--check` reported `game-linux: would
change 1 file(s)` with no `--verbose` to say which. `python3 code/deploy.py` wrote it; `check.py
--full` then ran 14/14. `python3 code/release.py` built
`dist/PNC0.3.2-PncEdi-2.6.0.zip`, 89.8 MB, sha256
`2230f0601a9c004677d7027bcafc896b5c0af2fa50dee84efd57c3da5b2f583e`.

## 160. Self-contained custom-enemy packages, investigated; `speedcheck` now walks package scripts

`TODO.md` carried "each custom enemy should carry everything it needs inside its own directory and
ship as its own zip", raised with no investigation behind it and a note not to start without one.
This is the investigation. Read `release.py`'s `custom_enemy_files` / `custom_enemy_gallery` /
`build_package`, `deploy.py`'s `payload`, the plugin's `SyncFunscripts` / `UpsertDefinitions` and
its per-package config binds, and `variants.py`'s `emit_packages`.

## 161. The witch loops' seams, repaired: an artefact is dropped, a slow stroke is clipped

§160's finding, measured and fixed. Every witch aura script ends on a point whose position equals
the first point's — the loop seam Edi's `InproveLoopDetection` wants — and §156's truncation left
some of them with an unreachable segment into it. On a `Loop=true` row that segment runs on every
cycle, so it is not a one-off blemish at the end of a minute: it is a jerk once a minute, forever.
**This is not "trimming loop seams" in the rejected list below.** That was moving a row's ending to
close a seam and it cost real content; here the seam point itself is untouched and what goes is a
point the device cannot reach it from.

## 162. The class-selection screen made honest: profile-gated, and armour counted once

Two display defects on one screen, both closed in `ClassSelectionHooks.cs`, both landing before
2.6.0 is posted rather than after. Neither changes what a run plays at — the runtime was right
about the numbers all along and the screen was not.

## 163. 2.6.0 rebuilt, so the version that ships is the version that was fixed

§159 built the archive, then §161 repaired ten funscripts and §162 fixed the class screen. The
version number does not move for either — nothing is posted yet, so 2.6.0 is still an unreleased
number and rebuilding it is free, where bumping to 2.6.1 would publish a version history nobody
outside this tree ever saw. `check.py --full` 14/14 (`speedcheck`'s remaining over-cap rows are the
buzz sections §161 identified, not the seam defect), then `python3 code/release.py`:
`dist/PNC0.3.2-PncEdi-2.6.0.zip`, 89.8 MB, 355 files. Still Edi v1.0.4 + PR #15, for the reason
`PROJECT.md` gives: the PR is merged but v1.0.4 is still the newest tag. What is left is posting
it.

## 164. The two custom-enemy packaging decisions, taken

§160 left two questions that were decisions rather than work. **A package may ship its own
assembly.** The alternative was growing the manifest vocabulary until packages stop needing new
behaviours, which is a chase with no end. BepInEx runs on Mono with no sandbox, so a package's DLL
has the game's full privileges and no loader design changes that — what the design owes is
therefore **consent and disclosure**, not containment: default-off per package, a log line naming
the assembly, and the documents saying plainly that a package is no longer only data. **The gallery
stays duplicated**, with both writers kept in step, because a player has neither repo nor Python and
the repo has to be able to check what it deployed.

## 165. Packages may ship their own code, and the framework carries none of the enemies'

§164 took the decision; this built it. `PncCustomEnemies.dll` is now a loader with no enemy in it:
the charm-circle boss it used to contain lives in the Femboy Witch package as `CharmWitch.dll`,
compiled from `code/packages/charm-witch/` against nothing but a public API.

## 166. The settings window, made to read like something a player chose

§165's consent switch was correct and unusable. The custom-enemy panel lists every bool in the
`Custom Enemies` section as its own row, so two installed packages showed as three toggles -
**"femboy witch", "femboy witch code", "joker wall code"** - with no indication that two of them
belonged to the first two, and no way to tell a package's on/off switch from permission to run its
code.

## 167. One switch per package, and it is the consent

**The first play of §165 found the shape of the mistake immediately: both packages were enabled and
did nothing.** They only worked after finding the second switch, allowing the code and restarting —
which is exactly the failure §166 had already half-noticed and answered with a better-drawn version
of the same two questions.

## 168. Five things the player-facing README said that were not true

The fresh-install test began by reading `PncEdi-README.txt` as a stranger would, and it did
not survive that reading. Copying the gallery beside an existing Edi throws away the loop-detection
and bundler settings the scripts were written against — the supported route is pointing that Edi at
**our config file**. "Under Proton, just launch as usual" is wrong without
`WINEDLLOVERRIDES="winhttp=n,b"`, and the failure looks like the mod not working. The variant was
documented as a JSON edit when it is a drop-down. An unconfigured device is **not** muted, as the
README claimed. And four `ChaserAura*` settings deleted in §153 were still documented.

## 169. The first run of what a stranger actually installs

`../fresh-test/` is a 0.3.2 Linux game with `PNC0.3.2-PncEdi-2.6.0.zip` extracted over it and
nothing of this repo in it — no symlink, no `deploy.py`, no dev config. **Nothing had ever been
tested that way**: every check this project has runs against a tree `deploy.py` controls, and
`deploy.py` repairs exactly the things an archive could get wrong.

## 170. Off did not mean off, and the install test is what noticed

**Step 3 of the fresh-install test — both packages installed, neither switched on — found
the defect the whole §165-§167 arc exists to prevent.** `Definitions.csv` went from 104 rows to 120
and sixteen of the witch's funscripts were copied into every variant folder, from a package whose
code the install had refused. The player saw none of it, because `Enabled` *was* consulted at spawn
and at gallery listing — everything behind the UI happened anyway. `LoadManifest` did the whole load
without ever asking whether the package was on, which was correct while "disabled" meant "do not
spawn it". §167 changed the switch into consent and nobody went back to the loader.

## 171. The witch that could be played but not loaded

**Step 4 — both packages switched on — spawned a witch that fought like a zombie**: no charm
circle, no capture, vanilla attacks, with the behaviour throwing `FileNotFoundException` on the
dream video. **Two resolvers, disagreeing.** Playback goes through `PackageVideo.ResolvePath`, which
prefers a `.webm` sibling of whatever the manifest names — that is what makes one asset set work on
Linux, and what lets `release.py --package` drop 36 MB of H.264 masters nothing would open.
Validation went through the witch's own `ResolvePackageFile`, which resolves the literal name. So
the archive shipped only the sibling and validation demanded the original. Packages now name the
WebM and ship only that.

## 172. Three answers the wall trap stopped giving, and the one that showed

**Step 4, second run: the witch works, and the joker's capture does not animate.** It grabs you, the
overlay appears, and it sits on frame 0 — while the gallery plays the same frames perfectly and
Edi gets `joker_wall_massage` and `joker_wall_cum` on time. Device right, picture frozen.

## 173. A switched-off package still hands Edi its funscripts

**§170 was right about the code and one step too far about the gallery.** It made a code package
that is switched off load nothing at all, including its funscripts and its rows in
`Definitions.csv`. That is clean as a sentence and expensive in practice, because of when Edi reads
that file: **once, at its own startup.**

## 174. The video verify was never a check, and it cost more than the rest combined

`refvideo.py --verify` was a `check.py` step from §121, on the reasoning that it exits non-zero and
so wraps cleanly. That is true and it is not the question. The question is what a step in this
runner is *for*: `check.py` is the thing you run after any change, and every other step in it
answers "did this tree just stop being correct". `refvideo --verify` answers "are the reference
videos still the frames of their clips" — and those videos are a §88 one-off, rendered once for
other scripters to measure against, read by nothing in the mod and by no other tool. They cannot
drift unless someone deletes or re-renders them, which is not something a code change does.

## 175. One gallery importer, reading manifests instead of kinds

§173 left an asymmetry it named and did not close: a switched-off witch hands Edi her funscripts and
her sixteen rows, and a switched-off Joker hands it nothing, so turning the Joker on costs an Edi
restart that turning the witch on does not. The reason was structural rather than deliberate. The
enemy registry globs `enemy.json`, so it was the only importer the framework had; a wall trap's rows
were built inside `WallPictureTrap.dll`, which does not load while the package is off. Two kinds,
two importers, two answers to one question.

## 176. The changelog splits: the decision stays, the session goes private

The changelog had become two documents wearing one name. Half of it is what a change was and why,
which another person needs and which `learnings/` cites by number; the other half is how the
session went — measurements, theories that turned out wrong, what a log said on which evening —
which nobody but its author can use. It was also being shipped to players as
`PncEdi-CHANGELOG.txt`, so an archive whose README promised "what changed, in detail" delivered
11,700 lines of working notes. The decisions keep their numbers here; the sessions moved to
`HISTORY.md`, untracked like `TODO.md` (§146), and `RELEASES.md` took the archive's slot. The
entries were cut mechanically and then hand-corrected in the 49 places where the machine's choice
did not state the decision.

## 177. Two versions in one file, six releases apart, and the gate that could not see it

`PncEdi/Plugin.cs` declared its version twice: the `[BepInPlugin]` attribute carried `2.6.0` as a
string literal, and the `PluginVersion` constant three lines below said `2.0.8`. BepInEx reads the
attribute, so the log and the mod manager were right and the constant was a lie — harmless only
because nothing read it. `release.py` already cross-checked four declarations and was written to
prevent exactly this, but it parsed the attribute's literal, so the one declaration that drifted
was the one it never looked at. The attribute now takes the constants, as both other plugins
always did, and `code/versionaudit.py` checks every place that states a version. The release is
**3.0.0** rather than 2.6.0, because the portable patch already reports itself as 2.6.0 in the
release thread and this build is breaking anyway.

## 178. One name per package, and the capability names left alone

The two packages each answered to two names: the Femboy Witch was `charm-witch` in the source tree
and `femboy-witch` on disk, and the Joker Wall Trap displayed as plain "Joker" while its code, its
manifest and its documentation called it a wall picture trap. The **content** names are now one
each — `displayName` carries the full name, and `release.py` derives the archive name from it, so
`PncEdi-Joker-<date>.zip` became `PncEdi-JokerWallTrap-<date>.zip` with no separate table to keep
in step. The **capability** names are deliberately unchanged: `charm-witch` is a published
behaviour any manifest may select, and `wall-trap.json` is a kind the framework does not know at
all, so collapsing either onto the content name would claim a capability belongs to one package.
`Bog Witch` also stays — it is the invented example in `CUSTOM-ENEMIES.md`, not an alias.

## 179. No tracked file names a directory outside the repo

The repo is about to be public and a reader's layout will not match the author's, so a tracked
document that names a sibling directory is either wrong for them or plausible enough to follow.
Fourteen places across `PROJECT.md`, `README.md`, `code/README.md`, `PncEdi.csproj` and five tools
named a real path — mostly `../Archive/PNC 0.2.1 Win`, the install every verified number in this
project was measured against. They now describe the thing and let the reader supply the path, or
use a placeholder in the command. The `game-windows` / `game-linux` symlinks are the only way out
of the repo and stay exactly as they were: each person points them at their own copy.

Nothing about the 0.2.1 install's importance changed — `PNC_GAME_DIR` still reproduces a pre-0.3.1
figure, and the documents still say to keep that install. What is gone is the assertion about where
it lives. Machine-specific locations worth keeping live outside the repo entirely.

## 180. The templates caught up with the format, and a gate so they stay caught up

`BepInEx/custom-enemies/_example/` is the format's own worked shape and ships in every mod archive,
and it had drifted four framework versions behind the reference beside it. It taught the AssetBundle
route not at all, and `behaviour`, `assembly`, `stripBaseEnemy`, `galleryVideos`, `spriteVisual.continuous`
and a scene's `sound` / `aliases` / `startTime` not at all either. Three of its claims were wrong
rather than merely absent:

- both templates overrode fields on `ChargingEnemyAI` of a `zombie`. **The game's seven AI classes
  are siblings, not a hierarchy** — each extends `MonoBehaviour` and each declares its own
  `maxHealth` — and §138/§144 established that no zombie prefab is a `ChargingEnemyAI` on any build
  this project has run. So the template's headline demonstration of `fields` matched no component,
  logged one warning and changed nothing. Now `EnemyAI`, which is what a zombie carries.
- `funscripts/` held `handy2pro/` alone, while the document four inches above it says a player whose
  device names a missing variant gets **nothing** for that enemy. Now all three, with the climax
  chosen to sit over a Handy 1's 364 units/s and under a Handy 2's 600, so the `handy1/` copy
  demonstrates the rule: shorten the stroke, never stretch the time.
- `wall-trap.json.example` carried no `assembly` block. A wall trap is a manifest kind the framework
  does not implement, so without one a copy of that template loads nothing, publishes nothing, binds
  no config switch and logs nothing — **the one failure in this format with no symptom at all.**
  That copy also lived in `joker-wall/`, which the mod archive does not ship, so the only template
  for one of the two package kinds reached nobody who had not already bought into the kind. It is
  now `_example/wall-trap.json.example`, one copy, and `WALL-PICTURE-TRAPS.md` points at it.

There are six manifest templates now, one per route — clone, runtime PNG, AssetBundle, a behaviour
asked for by name with **no code**, a behaviour published from an assembly **with code**, and a
package kind of its own — plus a `SOURCE.txt.example`, since every shipped package carries one and
the template set did not say so. `_example/README.md` names which is which and states the three
mistakes that cost the most.

**`code/exampleaudit.py` is the new gate, and sixteen is the check count.** The reason `_example/`
could drift is that every gate skips it, each for a good reason: `packageaudit.py` because a
template names a DLL that is not there and a behaviour nothing publishes, `speedcheck.py` because
its scripts have no rows, `PackageGalleryImport` and `PackageAssemblies` because it must never load.
Nothing about a template is wrong at runtime — it never runs. So the audit asks a template's own
questions instead, and the load-bearing one is **coverage**: every field the framework reads has to
appear in some template, or the run fails naming the field. A new manifest field is now a new line
in a template or a new line in the audit's `NOT_TEMPLATED` with a reason, and a session has to
choose between them. Seven mutations were checked to fail before it was wired in.

**And `.gitignore` would have dropped every new template on the floor.** The package rules name back
`*.json`, `SOURCE.txt` and `funscripts/**/*.funscript`; a template matches none of the three,
because its manifests end `.example` precisely so nothing discovers them. The templates that existed
were tracked only because they predated the rule. `release.py` builds the archive from the working
tree, so the new ones would have shipped to players and reached no clone, and every check in this
repo would have passed. `_example/**` is named back in whole now, and the audit asks `git
check-ignore` about every file it ships.

Three things fixed along the way. `CustomEnemies.cs` was the one discovery path that did not skip
`_example` by name — harmless while every file there ends `.example`, but it was the path that would
half-load a template renamed in place, registered by one path and refused a gallery and a config
switch by the other two. And `release.py` still named `CustomEnemies.SyncFunscripts` and
`UpsertDefinitions` in three comments; §175 deleted both.

The archive's own `README.txt` now names `_example/` and says what to do with it — it had pointed
only at the reference document, and called the directory "a template" when it holds six.

`CUSTOM-ENEMIES.md` gains the sibling-class rule, the "only fields, never properties" rule that goes
with it — its own `fields` example had been overriding a `moveSpeed` that exists on no AI class, an
enemy's speed being a property on its A\* `FollowerEntity` — a `SOURCE.txt` section, and a pointer
from each route to the template that shows it.

## 181. The aura's hold on the device, reconnected, and one debug key for every package kind

Two things the §165 extraction left behind, found by asking what in `PncCustomEnemies` was still
required after §175 homogenised the two packages. The answer was "almost all of it" — the framework
is lean now — but one seam in it had never been connected at all.

**`EdiChannelHeld` had returned false since §165.** Before the extraction the framework contained
the witch and read her directly:

    CustomEnemyBridge.EdiChannelHeldTest = () => CharmWitchController.IsPlayerInsideAnyAura;

§165 replaced that with a registry, `PackageSceneOwners.AnyHoldsEdiChannel`, and never changed the
witch to join it. `PackageRuntime.RegisterEdiChannelOwner` has no call site in any commit in this
repo's history. So the list was always empty, the delegate always false, and the guard at
`Plugin.cs:1232` — whose own comment says a charm circle must not have the channel taken back by the
dozen callers of `GoFiller` that mean "nothing else is happening" — never fired. `CharmWitchController`
implemented `IPackageEdiChannelOwner` and computed `HoldsEdiChannel` the whole time; nothing asked.

**Why this one hid when §172's twin was caught.** The installer wires three seams that "used to test
for a type this plugin contained". Two of them, `OwnsGrabScene` and `OwnsSceneVisual`, are asked *of
a GameObject the caller already has* and reach it with `GetComponent`, so a package that implements
the interface is wired by existing. The third asks "is *anyone* holding the channel", which has no
object to ask and cannot afford a per-frame scan, so it is a registry — **the only one of the three
that needs the package to opt in, and therefore the only one that can be half-implemented.** That
asymmetry is the whole defect, and `packageaudit.py` now refuses an assembly that names
`IPackageEdiChannelOwner` and never names `RegisterEdiChannelOwner`, beside the check §172 added for
its neighbour. `CharmWitchController.IsPlayerInsideAnyAura`, orphaned since §165, is deleted.

This is very likely part of what TODO records as the witch's aura "flapping" between a witch row and
a filler row. It is not offered as the whole explanation — an aura *exit* returning to filler is
correct — and the missing hysteresis at the aura boundary stays open on its own merits.

**One debug key for every package kind.** An `enemy.json` package was spawned by the framework's
`Tools / SpawnCustomEnemyKey` with `Tools / SpawnCustomEnemyId` choosing between packages, while the
Joker Wall Trap bound `Wall Picture Traps / PlaceTrapKey` in its own section. Both were defensible
alone and wrong together: ten enemy packages share one key and a selector, and a second package of
any invented kind would have brought a third key in a fourth config section. The framework had the
key and the selector; what it lacked was a way to say "place *your* thing" to a kind it does not
implement.

`IPackageDebugSpawn` is that — one method, `bool DebugSpawn()`, returning false when there was
nowhere to put anything so the log can say so rather than leaving the key looking dead.
`PackageDebugSpawn` is the dispatcher, and it owns id resolution for the whole install, because
"which package did you mean" is one question and answering it in two places is how two answers
drift. The trap implements the interface and binds no key; F10 is gone and F9 does both.

**`PackageApi.Version` is 2**, per that file's own rule that it bumps whenever anything in it
changes shape. Both shipped manifests and both code-shipping templates say `"api": 2`;
`exampleaudit.py` reads the number out of the source, so it followed by itself.

Also removed: `CustomGallerySection.IsCustomGalleryActive`, declared and never called. That was the
only genuinely dead code the sweep found — after §175 deleted `SyncFunscripts` and
`UpsertDefinitions`, the redundancy the question was aimed at is already gone.

## Tried and reverted — do not redo


- **Trimming loop seams.** 14 galleries end on a different position than they start.
  Trimming to close them cost real content (`imp1` lost its final stroke) and left dead
  time against the animation. Edi's `InproveLoopDetection` already absorbs seams at load.
- **Retiming `Gravy_Loop` 994 → 631 ms.** The 631 came from a 35 s window spanning several
  Gravy scenes. The script's 994 ms super-cycle is real — verified by the position
  sequence repeating exactly — and later measured at 998 ms.
- **Retiming `imp_grab_start/loop` to 666 ms.** That figure came from the *Imp 2* scene's
  window, not the grab loop.
- **Retiming `Gooper_Cum` 839 → 875 ms.** One 3.1 s window at ac +0.50; below the bar.
- **Retiming `plant_bj` / `nuns_threeway`.** Their apparent 1% error was frame
  quantisation in the measurement; both are +0.1% once measured sub-frame.
- **`play.sh` / `ab.sh` helper scripts.** Edi's own UI covers it.
- **Restoring the fullscreen grab layer at EndGrab** (§54, reverted in §55). It looked like a
  suppression with no counterpart; the counterpart is `GrabEndHelper.CleanupGrabPresentation`,
  in a different class, and it deliberately sets the overlay alpha to **0**. "Restoring" the
  original alpha fights it and puts a tint back over the screen. The stuck-screen bug is not in
  those three objects at all — `grabUI` and `grabOverlay` are null on this build.

- **A `docaudit.py` gate over `TODO.md`** (§138), checking for strikethrough on closed items, more
  than one handoff section and a 300-line ceiling. It worked - all three findings fired on the real
  1207-line file and none on the cut-down one - and was removed the same session as disproportionate
  to a documentation habit. The rule lives in `CLAUDE.md`, which every session reads. Do not rebuild
  the check without asking; the objection was to the machinery, not to the rule.

### Superseded

- **Adding an `ambient_imp_gangbang_2` row**, rejected in §6 in favour of re-merging the
  `imp gangbang 2` alias. Done properly in §33. The §6 reasoning ("no second funscript exists")
  was sound at the time; it stopped being true and nobody revisited it.

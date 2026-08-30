# PNC + Edi — changes made

Work from 2026-08-15 (§1–§8: scripts, config, source recovery) and 2026-08-16 (§9–§25:
gameplay and device-dispatch fixes). Only changes that are **still in effect** are listed;
things tried and reverted are noted at the bottom so they aren't re-attempted.

If the working tree has a `TODO.md`, that is the handoff document — start there, not here. It is
untracked private working notes, so a clone does not carry one; without it, the newest `§n`
entry below is the most recent state of play.

This repo is the mod alone; the game installs it is deployed into are outside it, reached
through the `game-windows` / `game-linux` symlinks (§62). There is no mirrored copy of anything —
`mod/single-mod` was deleted in §58 and `code/release.py` / `code/deploy.py` build what they need.

---

## 1. Gallery — wiring the two unused funscripts

The two scripts AniFS posted to the thread were sitting in `Edi/Gallery/` unreferenced.
Each is one long file containing several scenes; Edi plays a *slice* of a file, so they
needed `Definitions.csv` rows with per-scene time ranges.

- Moved `ambient.funscript` and `peek.funscript` into `Edi/Gallery/detailed/`
  (variant is the folder name; the only configured device variant is `detailed`).
- Identified each scene by matching against mr_spunky's reference captures, reading the
  on-screen menu labels frame by frame.
- Sliced to whole stroke cycles, first position == last, so each loops seamlessly.

| gallery | file | range |
|---|---|---|
| `peek_imp_three_way` | `peek` | 2.006–5.106 |
| `peek_nun_mimic` | `peek` | 7.770–11.303 |
| `peek_plant_bj` | `peek` | 12.662–15.996 |
| `peek_wendigo_ride` | `peek` | 18.455–21.122 |
| `peek_nuns_threeway` | `peek` | 22.986–26.320 |
| `peek_gooper_pillory` | `peek` | 28.240–31.774 |
| `peek_zombie_bj` | `peek` | 34.106–38.106 |
| `ambient_zombie_bench_fuck` | `ambient` | 10.640–15.507 |
| `ambient_plantasha_blowjob` | `ambient` | 38.753–43.253 |

**Also fixed while in there:**
- `peek_nuns_threeway` pointed at `peek_nuns _threeway` (stray space) — never matched.
- `peek_zombie_bj` had EndTime *before* StartTime — always empty.
- `ambient_plantasha_blowjob` was borrowing 3.2 s of an unrelated scene.

## 2. Dioramas — all nine rewritten

The nine ambient diorama scripts were 0↔100 square waves, and four of the nine were one
file serving several scenes. All rebuilt with measured periods and a shaped stroke.

| scene | period | source of the number |
|---|---|---|
| `ambient_nun_chair_fuck` | 629 ms | audio impact train (6 onsets) + collar tracking |
| `ambient_nun_wall_chain_head` | 750 ms | head-size (occlusion) tracking, per user cue |
| `ambient_gooper_bed_blowjob` | 500 ms | measured |
| `ambient_gargoyle_ledge_fuck` | 400 ms | measured (confirmed the previous 417 ms) |
| `ambient_wendigo_hole` | 633 ms | measured |
| `ambient_imp_gangbang` | 600 ms | measured |
| `ambient_mimic_wall_fuck` | 500 ms | measured |
| `ambient_zombie_bench_fuck`, `ambient_plantasha_blowjob` | — | AniFS's scripts (above) |

Stroke shape is the impact profile measured from `nun_chair`: hard bottom, fast kick off
it (~700 u/s, tempered from a raw 1360 u/s the device could not track), peak at ~1/3 of
the cycle, long descent back into the next impact. Floors returned to 0 so impacts land.

## 3. Enemy grab scenes — repointed to the properly authored scripts

`zombie.funscript` and `plantasha.funscript` were authored in OpenFunscripter against
per-scene video captures (their `.ofsp` project files name the source `.mp4`s) but were
unreferenced. The definitions pointed at slices of Dupli9d's work-in-progress strip
instead — including two rows with byte-identical ranges for different enemies.

| gallery | now points at |
|---|---|
| `Plantasha_Loop` | `plantasha` 4.300–10.600 (7 clean 900 ms cycles) |
| `Plantasha_Cum` | `plantasha` 23.967–31.100 (up → down → vibrate → up) |
| `Zombie_Loop`, `ZombieAlt1_Loop` | `zombie` 3.300–8.615 (665 ms, video says 666) |
| `Zombie_Cum`, `ZombieAlt1_Cum` | `zombie` 13.700–23.833 (2533 ms super-cycle, video 2550) |
| `Zombie_Start`, `ZombieAlt1_Start` | `zombie` 3.526–4.182 (one clean cycle) |

## 4. Retimed from reference video

Rescaled (shape preserved exactly, tempo only).

| gallery | was | now | basis |
|---|---|---|---|
| `peek_wendigo_ride` | 653 ms mean | 666.75 ms | dropped AniFS's compressed 600 ms lead-in cycle from the loop |
| `Nun_Grab` | 572 ms | 600 ms | four windows: 598/600/600/600 |
| `Wendigo_Continued` | 712 ms | 1000 ms | ac +0.86, window matches one scene |
| `Mimic_Loop` | 574 ms | 625 ms | two windows (626, 1249 = 2×625) |
| `Gooper_Start` | 963 ms | 1000 ms | two windows (1002, 995) |
| `Nun_Cum` | 788 ms/stroke | 600 ms | stroke-rate comparison |
| `Mimic_Cum` | 415 ms/stroke | 623 ms | stroke-rate comparison |
| `imp1` | 432 ms/stroke | 666 ms | ac +0.93 |

**Confirmed already correct** (measured, no change): `Gravy_Loop` 994 vs 998,
`Gravy_Loop2` 779 vs 778, `Gargoyle_Grabbed` 1006 vs 1000 (four windows),
`Baphomet_Loop2` 621 vs 625, `Dragon_Cum` 540 vs 552, `Mimic_Start` (slice *is* one
animation cycle), `Plantasha_Start` (three strokes inside one cycle), plus all zombie rows.

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

**`Edi/EdiConfig.json`**
- Both devices on `Variant: "None"` → `detailed`. `None` mutes a device outright, which
  included the preview device (nothing was auditionable without hardware).

## 7. Plugin source recovered

The tree in `code/edimod/` was a v1.0.0 snapshot a week older than the shipped v2.0.8
DLL — 41 files vs 48, missing `HeatLockSystem`, `GrabEnemyProtection`, four
`EnemyReactivation*Hook` files, and crucially `GalleryRegistry.LoadDefinitions`.

Re-decompiled the shipped DLL with ILSpy 11 and repaired it to compile:
`((Type)(ref x)).M()` → `x.M()` (52), `Object`/`Random` aliases (23 files), interpolated
string handler `ref` → `out` (21), nested enums qualified (`EnemyAI.AIState`,
`SweeperEnemySpawner.EnemySpawnData`, 15), plus assorted operator/`Unsafe` artefacts.
csproj: fixed `GameDir` (resolved to `PNC 0.2.1 Win/PNC 0.2.1 Win/`) and added
`Assembly-CSharp-firstpass` + `UnityEngine.IMGUIModule` references.

Verified equivalent to the shipped binary (all methods, all 65 registry names,
`BepInPlugin`/`HarmonyPatch` attributes intact) and confirmed working across three
gameplay sessions. Original preserved at `code/PncEdi-v2.0.8-original.dll`.

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

Vanilla never shows the world model during a grapple: the grapple visual is a **2D UI
overlay** (`GrappleScreenobject.grappleUI` + an Animator playing `OneImp`/`TwoImps`/
`ThreeImps`), and `ChargingEnemyAI.PerformGrabAttack` does `gameObject.SetActive(false)`
as soon as `StartGrapple` succeeds, then `Destroy`s the imp on shake-off
(`RemoveOneGrappler`) or `EndGrapple`.

Our `KeepImpsAfterGrappleShake` feature needs the imp to survive that `Destroy` so it can
be re-released near the player — and `GrabSurvivalHooks.BlockDestroy` already handles
that on its own. But `GrappleHooks.PerformGrabAttack_Postfix` *also* called
`KeepAttachedImpVisible`, which re-activated the object and re-enabled every renderer,
undoing vanilla's disappearance. `StabilizeAttachedImp` then disabled every collider
without pinning the Rigidbody, so an active body with nothing to stand on integrated
gravity and sank.

`KeepAttachedImpVisible` → **`StowAttachedImp`**: keep it alive, but gone.
`SetActive(false)` covers renderers, colliders, physics and AI in one step;
`StabilizeAttachedImp` additionally mirrors vanilla's own `SilenceForGrab` (renderers off,
colliders off, `ChargingEnemyAI` disabled, `Rigidbody.isKinematic = true`) as
belt-and-braces for anything that reactivates the object mid-grapple. The saved kinematic
flag is restored next to the collider states in `RestoreImpPhysics`; release order
(`SetActive(true)` → renderers → physics → reposition → `ScheduleReactivate`) is unchanged,
and `EnemyReactivationHelper.Reactivate` re-enables the AI as before.

One guard: the trio-grab overflow (3 grapplers + max heat) hands one imp to `GrabScreen`
as the on-screen representative and re-activates it itself, so `StowAttachedImp` skips
deactivating whatever is currently `GrabScreen.Instance.GrabbingEnemy`.

Also dropped the now-pointless `KeepAttachedImpVisible` call in
`ImpGrappleReinforcement.SpawnAndAttachRoutine` before `StartGrapple` —
`DebugEnemySpawn.EnsureSpawnActive` already activates the fresh spawn.

## 10. Horny limit scales off the cum meter instead of max HP

The horny limit — how many locks it takes to go from empty to fully locked, the `Y` in the
on-screen `Horny X/Y` — was `maxHealth / 10`:

```cs
return Mathf.Max(1, Mathf.FloorToInt((float)Mathf.Max(1, _baseHealth) / 10f));
```

Wrong stat: a beefier class got a longer horny bar. Vanilla keeps the two apart —
`PlayerClassManager` applies `healthMultiplier`/`bonusHealth` and
`heatCapacityMultiplier`/`bonusHeatCapacity` from independent `PlayerClass` fields — so the
coupling was entirely ours. (There is no stamina stat in the game at all; `grep -i stamina`
over `Assembly-CSharp.dll` is empty. The heat bar *is* the cum meter.)

`GetTotalLocks()` now divides the chosen stat by `HeatLockUnitsPerLock`:

| config | meaning |
|---|---|
| `HeatLockScaleSource` | `Heat` (default) = heat capacity / cum meter; `Health` = old max-HP behaviour |
| `HeatLockUnitsPerLock` | points of that stat per lock, default 10 (was a hardcoded `/ 10f`) |

Both stats default to 100, so the default class still gets 10 locks and the feel is
unchanged; only classes whose two multipliers disagree move.

**`_baseHeat` is re-recorded, not snapshotted once.** Heat capacity is not final until the
class multipliers land (`PlayerClassManager`, then our own
`ClassHeatMultipliers.ApplyToPlayerHeat` multiplying again), and armour can move it
mid-run. So a `SetMaxHeat` postfix calls `RecordBaseHeat` on every change and clamps
`_locks` down if capacity shrinks under the locks already taken. This is the opposite of
the health side, where `RecordBaseHealth` deliberately *refuses* values inflated by god
mode (`CfgPlayerMaxHealth`, 999999) — nothing inflates heat that way.

`ApplyFullLockHealthReset` still uses `_baseHealth` — that one is about health and was left
alone. (The full-lock heat band was reworked in §11.)

## 11. Full lock means max heat, overheat clears at the lock floor, overflow restored

Three linked changes to the heat-lock endgame.

**Full lock parks at `maxHeat - 1`** (`HeatLockSystem.GetFullLockHeat`, was
`GetFullLockMovementSafeHeat`) — 99/100 by default, where it used to sit one point below
`overheatingThreshold`, i.e. 79/100.

That old dodge existed because of vanilla's overheat rule. `PlayerStats.CanAttackNow()` and
`CanDash` are both:

```cs
if (hasBeenOverheated) return currentHeat <= 0f;
return true;
```

`hasBeenOverheated` is set when heat overflows past max and clears in only three places:

| where | condition |
|---|---|
| `HandleOverheatingStates()`, per frame | `currentHeat <= 0f` |
| `ClearOverheatIfBelowMax()` | `currentHeat <= maxHeat` |
| `LoadFromData` (save restore) | unconditional |

The second is **not** an automatic check — it is a method with exactly three call sites in
the whole assembly (`ConsumableSystem.ApplyConsumableEffects`,
`BuffDebuffSystem.ApplyImmediateEffects` / `ApplyOverTimeEffects`), so it only fires when
the player consumes something. Nothing inside `PlayerStats` calls it. The only automatic
path is the `<= 0f` one — and a lock floor holds heat above 0 permanently, so one overflow
would disarm the player for the rest of the run. Parking below the overheating threshold
was the original author's way around that.

**`HeatLockSystem.ClearOverheatAtFloor` fixes it at the source instead.** The lock floor is
this system's equivalent of "fully cooled", so overheat clears there rather than at 0 — by
calling vanilla's own `ClearOverheatIfBelowMax()` once heat is back at the floor (any floor
satisfies its `<= MaxHeat` precondition). Runs from `Tick` and `AfterHeatChanged`, gated on
`ClearOverheatAtLockFloor` (default true). With no locks held the floor is 0, which is
exactly vanilla, so the patch is inert until the player is actually locked.

Overheating therefore still disarms — attacks and dashes remain vanilla-gated on
`hasBeenOverheated`, no patches on `CanAttackNow`/`CanDash` — it is just recoverable now:
cool back to your floor and you are re-armed.

**Overflow restored.** `TryGetLockedHeatRange`'s ceiling was `MaxHeat`, so `EnsureHeatBounds`
pulled any overshoot straight back down and vanilla's overflow never happened under locks.
The ceiling is now `MaxHeatWithOverflow`. A 30-heat cast at 99 heat lands at 129, sets
`hasBeenOverheated`, and ticks back down to the floor at ~`heatCooldownRate`/s — roughly
three seconds of being disarmed and grabbable as the price of a badly timed cast.
`GenerateHeat` already caps itself at `maxHeatOverflow` (`overheatingThreshold + 50`, so 130
by default), so this change is really just "stop pulling it back down"; `HandleHeatCooldown`
does the ticking, and `CoolHeat_Prefix` still stops the fall at the floor.

No display work was needed — vanilla already caps the bar (`fillAmount = Mathf.Min(1f, …)`
in both `UpdateHeatBarImmediate` and `HandleHeatBarAnimation`), turns the fill red on
`IsInHeatOverflow`, and prints the true number (`129/100`) via `UpdateHeatText`.

**Deliberately not patched: `PlayerStats.IsAttackLocked()`.** It reads like a twin of
`CanAttackNow`, but it is what `EnemyAI`/`ChargingEnemyAI`/`ProjectileEnemyAI` consult via
`IsPlayerVulnerable` to decide whether the player can be grabbed, and what
`OverheatedScreenEffect` renders. Widening it would rewrite the grab loop. It now clears
along with everything else at the floor, which is the intended coupling: overflow makes you
grabbable until you cool off.

*Superseded:* an earlier build of this section added an `OverheatRules.cs` that relaxed
`CanAttackNow`/`CanDash`/`GetTimeUntilCanAttack` to "locked only at max heat". That file is
deleted and its `OverheatLocksAtMaxHeatOnly` config replaced by `ClearOverheatAtLockFloor` —
clearing at the floor achieves the same recovery without weakening the overheat penalty.

## 12. Cumming in a scene no longer costs HP

`GrabScreen.TriggerMaxHeatAnimation` — the player's cum in an H-scene — deliberately drops
invulnerability to land damage, then puts it back:

```cs
playerStats.SetInvulnerable(false);
playerStats.TakeDamage(Mathf.RoundToInt(maxHeatDamage));
if (!isDragonGrab && grabDamagePercent > 0f)
    playerStats.TakeDamage(Mathf.RoundToInt(playerStats.MaxHealth * grabDamagePercent));
playerStats.SetInvulnerable(true);
```

That is the only damage source that can kill the player *during* a scene — and a death
mid-scene is what leaves the run softlocked, since the deferred game over only arms for
players who were already dead when the scene started (TODO bug 7).

`CumDamageGate` (new file) flags the window around `TriggerMaxHeatAnimation` and
`GameplayHooks.TakeDamage_Prefix` returns early inside it. Config `DisableCumDamage`,
default true. Applies to every grab scene, not just grapple-initiated ones — the code path
is shared and a grapple-only carve-out would be arbitrary.

Two deliberate details:

- **Suppressed at `TakeDamage`, not by zeroing the serialized fields.** The cum animation,
  `heatIncreaseBlocked` and the cooldown all behave exactly as vanilla; only the HP loss is
  gone. Zeroing the fields would instead push a `TakeDamage(0)` through
  `Plugin.NotePlayerDamage` and register with the damage-filler tracker.
- **The reset is a `[HarmonyFinalizer]`, not a postfix.** A postfix is skipped when the
  original throws, which would leave the flag stuck on and silently suppress *all* player
  damage for the rest of the run. A void finalizer that ignores `__exception` runs either
  way and still rethrows.

This removes the common cause of the softlock but **not** the softlock itself: TODO bug 7
stays open, because dying mid-scene is still reachable through
`HeatLockSystem.ApplySceneEntryPenalty` (−40 HP on scene entry at full lock) and through
enemy hits landing during a grapple.

## 13. Dying *during* a scene now presents a game over

Dying while a scene was already running left the run unplayable: no game over, but enemies
inert, so the only way out was quit-to-menu.

The deferred-game-over machinery existed but could never arm for this case.
`EnsureSceneEntrySurvival` is called from scene-*entry* hooks only
(`GrabStruggleHooks`, `GrappleHooks`, `CameraSwapHooks`), and it early-returns unless the
player is **already** at 0 HP. That covers "killing blow lands, then the death grab starts".
It cannot cover "player was in a scene and then died".

What actually happens on such a death:

- `TakeDamage` writes `currentHealth` directly (not via `SetHealth`), so HP does reach 0,
  and it calls `Die()`.
- `GameplayHooks.Die_Prefix` blocks the original `Die()` for the duration of any scene
  (`ShouldBlockLethalHealth` → `IsSexSceneActive`), so vanilla never fires `OnPlayerDeath`
  and `GameOverScreen` is never told.
- `DeathHooks.Die_Postfix` runs anyway — Harmony runs postfixes even when a prefix returns
  `false` — and sets `Plugin.PlayerDead = true`, which is what makes enemies stay inert.

So the run ended up flagged dead, with no death having been presented.

**Fix:** `Die_Postfix` now arms `EnsureSceneEntrySurvival` in its play-out branch. HP is
already 0 there, so the existing arming logic applies unchanged — the player is put back to
1 HP for the duration and the existing `CompleteSceneEntrySurvival` calls fire the game over
at scene end. Skipped while `ForcingPendingSceneEntryGameOver` is set, or the forced `Die()`
inside `CompleteSceneEntrySurvival` would instantly re-arm what it just consumed.

**Also fixed: the trio hand-off.** `GrappleScreenobject.TriggerTrioGrabOverflow` calls
`StartGrab(...)` and *then* `EndGrapple(...)`, so `EndGrapple_Postfix` →
`CompleteSceneEntrySurvival("grapple")` used to fire at the **start** of the imp loop —
dropping a game over onto a scene that had not played yet. `CompleteSceneEntrySurvival` now
stays armed and returns early if any other scene is still live, letting whichever scene is
actually running complete it. Safe because every caller runs after its own flag is cleared:
`FinishGrabEnd` is an `EndGrab` postfix (`isGrabbed = false` first), `ResetState` sets
`Active = false` before calling, and `EndGrapple_Postfix` follows `isGrappling = false`.

## 14. Dying in an imp grapple plays out as the imp trio scene

§13 made the death *survivable-looking*: the player was revived to 1 HP for the duration,
which reads as invulnerability — enemies hit you, nothing happens, and the game over only
lands later. Replaced with a death sequence (`GrappleDeathSequence`, new file).

When health reaches 0 during an imp grapple:

1. **Health stays at 0.** No revive. `EnsureSceneEntrySurvival` is skipped in favour of
   `HeatLockSystem.ArmPendingGameOver`, which arms the deferred game over without touching
   health or clearing `PlayerDead`.
2. **Struggling stops working.** Prefixes on `GrappleScreenobject.TrackMouseShake` and
   `RemoveOneGrappler`. The shake bar is zeroed on entry and the grapple text is replaced
   (`GrappleDeathText`, default "Overwhelmed!") — vanilla's "Shake mouse to escape!" would
   otherwise read as a broken control. `UpdateGrappleUI` rewrites that text on every attach,
   so it is reapplied each tick.
3. **Imps are called in.** `ImpGrappleReinforcement` normally obeys `GrappleReinforcement`,
   which is optional; while the sequence runs it is forced on and uses
   `GrappleDeathImpInterval` (1 s) instead of the usual 5 s. Without this a death with
   reinforcement disabled would sit at one or two imps with nothing to escalate it.
4. **Vanilla escalates it.** At three imps the sequence pushes heat to max, which is the
   other half of `CheckTrioGrabOverflow`'s condition, and the game moves itself into the
   trio `GrabScreen` scene.
5. **That scene counts as the game over.** The grab's end fires the armed pending game over
   through `CompleteSceneEntrySurvival`, using §13's deferral so the grapple's own end does
   not fire it early.

**Bail-outs, because this is a death the player cannot escape.** A stall here would strand
the run exactly like the softlock this replaced. If max heat does not escalate within 2 s
(`enableTrioGrabOverflow` off on the prefab, or the grab refused), the private
`TriggerTrioGrabOverflow` is invoked directly; if that also fails to produce a grab, the
grapple is force-ended so the game over can present on its own.

Two ordering traps worth recording:

- **Damage keeps arriving after death.** `Die` is blocked during scenes, so `isDead` never
  latches and every further damage tick re-enters `Die` — the log shows six
  `[PLAYER-DEATH]` lines for one death. So the death handler must answer "already handled"
  (`HandleDeath` returns true while active) rather than only "just started", or the second
  tick falls through to the old revive path and undoes the whole thing.
- **The trio scene is itself a scene entry**, so the grab's own
  `EnsureSceneEntrySurvival` would have revived the player to 1 HP for the death scene.
  It now defers to `ArmPendingGameOver` while the sequence is active.

Spawned imps get `PrepareSpawnedImp` first: the spawner runs while `PlayerDead` is set, so
`EnemyReactivationHelper` holds the new imp's AI disabled and it can arrive without health —
and `StartGrapple` rejects an enemy at 0 HP, or refuses outright if `CanBeGrabbed` is false.
Both are ensured before the imp is offered.

## 15. Damage filler now follows current health instead of sticking

`filler_damage_*` never went away once you were hit — healing back up, including our own
`HeatLockSystem.ApplyHeatScaledAutoHeal`, left it playing.

Two independent causes, both in `Plugin.cs`:

1. **`_lastDamagePercent` was a high-water mark** — `Mathf.Max(_lastDamagePercent, damage / maxHealth)`
   in `NotePlayerDamage`, whose only reset is `RefreshPlayerHeatSnapshot`'s *no-PlayerStats*
   branch, i.e. menus and the gallery. In-game it could only ratchet up.
2. **Nothing re-evaluated on a heal.** `RefreshFillerForCurrentHeat` early-outs unless
   `_lastCumPercent` moved, and healing changes HP, not heat.

`GetFillerGallery` tries the cum map first and falls back to the damage map, so at low heat
the stale damage bucket won indefinitely.

Now `UpdateDamagePercent` recomputes it as the **standing deficit**, `1 - CurrentHealth/MaxHealth`,
from `RefreshPlayerHeatSnapshot`, and `RefreshFillerForCurrentHeat` re-evaluates when either
the heat *or* the damage percentage moves. No new hooks were needed —
`RefreshFillerForCurrentHeat` already runs every frame from `Update`, so a heal is picked up
on the next one.

**Precedence reworked too** (`FillerIntensityPriority`, default `Higher`). Arousal used to
win outright, with damage as the fallback for "heat below the lowest bucket" — fine before
heat locks, broken after them, because the lock floor holds heat permanently above 0. With
15 locks on a 150 heat bar each lock is worth 10 heat, so from 4 locks on the cum map always
matched and `filler_damage_*` became unreachable regardless of health:

| locks held | heat floor | damage filler reachable? |
|---|---|---|
| 0–3 | 0–20% | yes |
| 4+ | ≥26.7% | never |

`ResolveFillerIntensity` now plays whichever percentage reads higher, falling back to the
other signal when the leader sits below its own lowest bucket. `Cum` restores the old
precedence, `Damage` inverts it.

The bucket meaning changes with it, for the better: `25=filler_damage_25;50=...;75=...` now
reads as "how hurt are you" rather than "how big was the worst hit". For a first hit from
full health the two coincide, so the feel is unchanged; it now also decays back to the plain
filler as health returns. `NotePlayerDamage` runs from the `TakeDamage` *prefix*, before
health drops, so it projects the incoming hit to keep the reaction on the same frame.

## 16. Enemies revived after a scene keep the health they went in with

An enemy killed during an H-scene came back at **half max health**
(`EnemyKeepAliveHelper.RestoreHealthForAi`), which handed the player's kill back with
interest a few seconds later — the delay being `EnemyReactivationDelaySeconds` (5 s), since
the restore rides along with `EnemyReactivationHelper.Reactivate`.

**What vanilla does:** nothing, because the enemy no longer exists.
`EnemyAI.RemoveEnemyAfterGrab` (same in `SpinningEnemyAI`/`ProjectileEnemyAI`) is
`TransitionToDead()` + `Destroy(gameObject)` — every grab *consumes* its enemy, so the base
game never has to answer "what health does it come back with". Imps do not even have the
method; the grapple destroys them via `RemoveOneGrappler`/`EndGrapple`. The revive is
entirely our `KeepEnemiesAfterGrab` feature, which blocks that destroy so scenes stop
depopulating the level and then has to invent a number.

Worth being precise about when it fires: `RemoveEnemyAfterGrab` never touches
`currentHealth`, and `RestoreHealthForAi` only acts at `currentHealth <= 0`. So this is not
topping up an enemy you merely wounded — it only ever revives one that was **killed during
the scene**, its `Die` having been skipped by `SkipEnemyDieDuringGrab`.

`GrabReviveHealth` (default `Snapshot`) now decides:

| value | behaviour |
|---|---|
| `Snapshot` | the health it had when its scene started, recorded by `SnapshotHealth` from `GrabEnemyProtection.OnGrabStarted` and `GrappleEnemyProtection.AttachImp` |
| a number | that percent of max — `50` is the old behaviour |
| `0` | never revive; the body stays down but present |

Snapshots are keyed by AI component instance id, consumed on use, and cleared on scene
change. If none exists (an enemy protected by some path that never snapshotted), it falls
back to the old half-max. Revives now log as `[ENEMY-REVIVE] <name> 30/100`.

For true vanilla behaviour — the enemy destroyed by the scene — the switch is
`KeepEnemiesAfterGrab=false`, not `GrabReviveHealth=0`.

**Follow-up: the enemy was also unkillable for 5 s after the scene.** `SkipEnemyDieDuringGrab`
blocked `Die` for the whole of `KeepEnemiesAfterGrabGraceSeconds`, not just while the scene
was on screen. Since `EnemyAI.TakeDamage` ends with `if (currentHealth <= 0) Die();`, every
killing blow in that window was rolled back and the health bar visibly jumped back up to the
restored value — which reads as "hits do nothing, then its health goes up".

The grace exists so the grab teardown's delayed `Destroy` cannot delete the enemy; it should
never have made the enemy immune to the *player*. `Die` is now blocked only by
`IsProtectedDuringScene` (the infinite window while the scene is live), and if a protected
enemy dies after its scene the protection is released outright — otherwise `BlockDestroy`
would swallow the `Destroy` at the end of vanilla's `Die` and leave a corpse standing in the
level forever. Logged as `[ENEMY-KILL] <name> killed after its scene - protection released`.

## 17. Leaving a gallery scene stops the device instead of looping filler

Going from a gallery scene back to the character list left the device running. The TODO
blamed a missing hook, but `EnemyGalleryUI.ExitGrabView` was already patched — three
separate defects downstream of it were doing the damage.

**1. The stop was a play.** `EndMenuGalleryView` ended in `Plugin.GoFiller()`, and
`GoFiller` is `SendPlay(filler, loop: true)` whenever filler is enabled. In a menu there is
no gameplay to fill between, so leaving a scene started an endless filler loop. Section 8.4
fixed exactly this for scene transitions; the gallery path was missed.
New `Plugin.EndGalleryPlayback` sends a real `SendStop` when no `PlayerStats` exists, and
falls through to filler when the view is in-game (peek scenes), where filler is right.

**2. The guard only allowed one exit per gallery visit.** `MenuGalleryOpen` is set by
`OpenGallery` and cleared by the first `EndMenuGalleryView`, but nothing re-set it — a
gallery step plays through `SendMenuGalleryStep`, which never touched the flag. So viewing a
second scene and leaving it found `if (MenuGalleryOpen || ViewingPeekScene)` false and did
nothing at all: playback simply continued. Now tracked by `GalleryPlaybackActive`, set
whenever a step actually plays (enemy and peek paths) and cleared on the stop, so the guard
means "we started something" rather than "the gallery was opened recently".

**3. Opening the gallery started the filler.** `EnemyGallery_OpenGallery_Postfix` logged
"silence until tab playback" and then called `GoFiller`, which is the opposite of silence.
Routed through `EndGalleryPlayback` so it now matches its own description.

## 17b. Enemies frozen after a scene ends

Enemies often never resumed after a scene — standing still, or doing nothing at all — well
past the intended `EnemyReactivationDelaySeconds` pause.

**The game pauses AI itself.** Every AI's `Update` starts with

```cs
bool flag = IsPlayerGrabbedByGrabScreen() || CinematicCameraSwapTrigger.IsAnyInCinematicView;
if (flag) { PauseAIBehavior(); wasPlayerGrabbedLastFrame = true; return; }
if (wasPlayerGrabbedLastFrame && !flag) { ResumeAIBehavior(); wasPlayerGrabbedLastFrame = false; }
```

`PauseAIBehavior` calls `StopPathfinding()` (`followerEntity.simulateMovement = false`), and
the matching resume runs **only from that same Update, and only while the flag is set**. We
disable the AI component for the duration of a scene, so that `Update` frequently never runs
and the resume never happens.

**And our reactivation did not stand in for it.** `ReactivateComponent` wrote
`currentState = Chasing` directly — but `TransitionToChasing()` is what calls
`StartPathfinding()`. The enemy came back certain it was chasing while `simulateMovement` was
still false: standing still forever, animator idle, AI component enabled so nothing looked
wrong. Only `EnemyAI` and `ChargingEnemyAI` happened to also get `StartPathfinding` here;
**`ProjectileEnemyAI` and both dragons never did**, and `SpinningEnemyAI` (no pathfinding at
all, e.g. Plantasha) was simply parked in `Idle` rather than re-evaluating what it should do.

Now `ResumeAiBehaviour` drives the game's own `ResumeAIBehavior()` for every type, which
re-picks the state properly — `SpinningEnemyAI`'s version re-measures distance and chooses
Idle/Grabbing/Spinning/Shooting — and routes through the transitions that restart movement.
It also clears `wasPlayerGrabbedLastFrame` and calls `StartPathfinding` as a fallback, which
re-teleports the follower to where the enemy actually is after a scene moved it.

**Second cause: stale coroutine handles.** Deactivating a GameObject kills its coroutines
but leaves the handles non-null, and `NearbyEnemyHider` deactivates enemies for the duration
of a scene. Guards like

```cs
private void StartSpin()
{
    if (spinCoroutine == null && !(player == null)) { ... spinCoroutine = StartCoroutine(SpinSequence()); }
}
```

then refuse to ever start a new one. `spinMovementActive` stays false, `FixedUpdate` zeroes
the velocity every frame, and the enemy never moves again — while still attacking, because
`HandleGrabHit` runs straight from `Update` rather than a coroutine. That is the "Plantasha
can't move but still attacks" case exactly.

`ClearStaleCoroutineHandles` now drives the game's own `StopSpin`/`StopCharge`/`StopAttack`/
`StopShooting`/`StopGrab` on reactivation, each of which stops the coroutine *and* nulls its
handle. Going through them rather than nulling the fields directly means a genuinely live
coroutine is torn down properly instead of leaked.

**Third cause: orphaned action flags.** Same root cause as the stale handles, different
victims. `StartSpinMovement`/`StopSpinMovement`/`PerformDash` are **public** — they are
animation events — so several state flags are set by one event and cleared by a *later* event
or by the second half of a coroutine. Neither arrives if the object is deactivated
mid-action.

`isDashing` is the damaging one. `SpinningEnemyAI.FixedUpdate` only applies spin velocity
while `spinMovementActive && !isDashing`, and `PerformDash` itself guards on `!isDashing`, so
a single orphaned dash leaves Plantasha **spinning on the spot forever** — animation and audio
playing, no movement — while normal attacks and grabs still work. There is no `dashCoroutine`
field and no `StopDash`, so `ClearStaleCoroutineHandles` could not reach it; the flag has to
be cleared directly.

An orphaned `spinMovementActive` is the audio half: `UpdateSpinLoopSound` starts the spin loop
whenever it is set, so the sound played through the whole wake delay with nothing spinning.

`ClearOrphanedActionState` now clears `isDashing`, `spinMovementActive`, `grabInDamagingState`,
`hasDealtDamageThisAttack` and `hasDealtChargeDamage`, and calls `StopSpinLoopSound` /
`StopIdleMovingSound` for loops that otherwise only stop from `Update`. It runs at **reveal**
as well as at wake, because the object is active from reveal onward while `Update` is not
running to stop anything.

**Safety net:** `EnemyInactiveAutofix` could not see either class of stuck enemy, since the
object is active and the component enabled. It now also reactivates anything whose state is
`Chasing` while its follower is not simulating movement (`IsStuckChasing`), or which has been
in `Spinning` for over 5 s without `spinMovementActive` (`IsStuckSpinning`, for the
follower-less spinners) — combinations that only occur when this goes wrong. The scan is
skipped entirely while a scene is on screen, since every AI is *supposed* to be paused then.

## 18. Extra spawns are scattered instead of stacked

Room spawns dropped several imps in the same spot. `GameplayHooks.ExpandSpawnPositions`
padded the spawner's position list by re-adding the **same `Transform`**:

```cs
for (int i = positions.Count; i < num; i++)
    positions.Add(positions[i % count]);   // same Transform, same world position
```

so two enemies were handed identical coordinates. Imps are the visible case because
`ImpSpawnWeightMultiplier = 2` makes them the likeliest pick per slot.

It also explains the "sometimes": the multiplier is
`max(1, SpawnCountMultiplier) * (1 + 1.2 * HeatLockSystem.CurrentLockProgress)`, so it climbs
with the horny meter. At `SpawnCountMultiplier = 1` and no locks nothing is duplicated at
all; at full lock every position is duplicated ~2.2x.

The spawner consumes `Transform`s, so a duplicate cannot simply be nudged — each extra slot
now gets a real Transform from `CreateScatteredPoint`, which tries up to 8 candidates on a
ring around the original (`SpawnScatterRadius`, default 2 m, inner bound 40% of it) and
requires each to:

1. **hit floor** on a downward raycast — the spawn point's own Y is not valid ground a couple
   of metres away, the same correction §8.2 applied to `TryGetSpawnTransform`;
2. **have body clearance** (`Physics.CheckCapsule` 0.3–1.6 m, r=0.35), which also rejects a
   spot already occupied by another enemy — the actual goal;
3. **be reachable in a straight line** from the original point (`Physics.Linecast`), so the
   scatter cannot push a spawn through a wall.

If all 8 fail the slot is **dropped** rather than spawned, logged as
`[SPAWN] dropped N/M extra spawn slot(s) with no room to scatter into`. These are bonus
enemies on top of what the level asked for, so one fewer beats two inside each other — and
beats one inside a wall. The Transforms come from a small pool of empties under a
`PncEdi_SpawnScatter` object, reused across waves.

Left alone: `EnsureFallbackSpawnPositions` needs no floor snap, since it adds the spawner's
own level-authored `spawnPositions`, which are already placed on the ground.

## 19. Mimics are usable again after their scene

A mimic that had grabbed you once stayed standing but could never be interacted with again.

Vanilla mimics are one-shot *by construction*: `TriggerMimicGrab` sets `hasTriggeredGrab`,
starts the grab, and ends in `Object.Destroy(base.gameObject)`. The flag never needs
resetting because the object ceases to exist a frame later.

`KeepEnemiesAfterGrab` blocks that `Destroy` (via `GrabSurvivalHooks.BlockDestroy`), so the
chest survives — with the flag already latched. `Update` gates interaction on
`!hasTriggeredGrab`, so the mimic came back visible, re-enabled, and permanently inert. The
mod kept it alive without making it usable.

`RearmMimic` now clears the flag on reactivation, gated on the same `KeepEnemiesAfterGrab`
that caused the survival in the first place, and logs `[ENEMY-WAKE] re-armed mimic <name>`.

Note that mimics genuinely need no other reactivation work: no coroutines, no pathfinding, no
movement, and their reveal is a one-off sound and effect rather than a persistent visual
state — which is why `Reactivate` only ever enabled the component and
`EnemyInactiveAutofix` skips them outright.

## 20. Heat potions remove horny locks instead of flat heat

The game ships three: **Small**, **Medium** and **Large Heat Potion** (found in
`sharedassets0.assets`; `ConsumableSystem.ApplyConsumableEffects` applies their
`instantHeatReduction` through `PlayerStats.CoolHeat`).

Flat cooling was close to worthless once locks existed — `HeatLockSystem.CoolHeat_Prefix`
trims any cooling at the lock floor, so a potion drunk while locked was partly or entirely
discarded. Removing locks is the only thing that lowers that floor.

| potion | locks removed |
|---|---|
| Small | 2 |
| Medium | 5 |
| Large | 10 |

Configured by `HeatPotionLockRemoval`
(`small heat potion=2;medium heat potion=5;large heat potion=10`), matched
case-insensitively against the item name with the longest key winning, so a generic key
cannot shadow a specific one. An item with `instantHeatReduction > 0` that matches nothing
keeps vanilla behaviour, and clearing the setting restores flat cooling for everything.

`HeatLockSystem.RemoveLocks` takes the locks **and the heat they were holding**:
`heatPerLock = MaxHeat / totalLocks`, so removing *n* also sheds `n × heatPerLock`. Both ends
are clamped — locks can never go below 0 (the count is clamped to what is actually held
first), and heat is clamped to `[0, MaxHeat]` — so an oversized potion empties the meter
rather than going negative. It then re-runs `EnsureHeatBounds` and `ClearOverheatAtFloor`,
since the floor has just dropped and the overheat lock may now be liftable, and calls
`Plugin.NotePlayerCum` so the filler re-evaluates against the new heat bucket.

Vanilla's own cooling is suppressed via a flag read by `CoolHeat_Prefix`, rather than by
zeroing `item.instantHeatReduction` — that field lives on a shared `ScriptableObject`, so
writing to it would leak across every copy of the item. The flag is cleared in a
`[HarmonyFinalizer]`, so an exception mid-effect cannot leave every later `CoolHeat` in the
run suppressed.

Drinking with no locks held removes nothing and logs
`[HEAT-POTION] '<name>' had no horny to remove` — the potions are now purely a lock cure.

## 21. Diorama releases need line of sight and a look timer

A diorama's one-time horny release fired the moment it came into **earshot**:
`AmbientProximity.Tick` picked the nearest playing `AudioSource` within
`maxDistance x AmbientHearingMultiplier` and called `TryReleaseFromAmbient` on the spot. So
it could be spent by walking past a wall with a diorama behind it, without ever seeing it.

`AmbientReleaseGaze` (new file) now gates the release on actually watching:

- **In view** — `WorldToViewportPoint` with a 5% margin, so it must be properly on screen
  rather than clipping the edge.
- **Line of sight** — a raycast from the camera, stopping 1.5 m short of the target so the
  diorama's own props and colliders do not read as blocking the diorama.
- **Held for `AmbientReleaseLookSeconds`** (default 3).

The meter **drains rather than resetting** when the diorama leaves view, at
`AmbientReleaseDecayMultiplier` x the fill rate (default 1, i.e. the same speed; 0 never
drains). A glance away costs progress instead of the whole attempt.

Progress shows as a bar under the existing "Horny X/Y" readout on the same top-right canvas
(`HeatLockSystem.SetAmbientGauge`), width-driven from a 1x1 white sprite so it needs no
sliced art.

**Playback follows the same rule.** The diorama funscript itself is gated on the same
visibility test, so a diorama heard through a wall no longer drives the device — the script
starts when you can see it and stops when you cannot. A grace window keeps a pillar or
doorframe passing across it from stuttering playback off and back on, which matters because
losing the gallery bounces the device to filler and back.

> **Superseded by §26.** The visibility test is now the diorama's gallery-unlock box, not a
> raycast, and the two config keys were renamed with it:
> `AmbientRequiresLineOfSight` → `AmbientPlaybackRequiresPresence`,
> `AmbientLineOfSightGraceSeconds` → `AmbientPlaybackLingerSeconds`.

One thing it deliberately does *not* do:

- **It will not run the meter down on a release the player cannot spend.** With no locks
  held, `TryRelease` would consume the one-time source and report "no horny lock to remove",
  so the meter does not charge at all until there is something to release.

`AmbientReleaseLookSeconds = 0` restores the old fire-on-earshot behaviour.

## 22. Peek holes are no longer treated as dioramas

The look meter appeared at the wendigo *peephole*, which is not a diorama. Peek holes carry
their own looping audio, and several diorama patterns match it —
`wendigo hole scene`, `zombie blowjob hole scene`, `zombiebjpeep` — so `AmbientProximity`
picked the peephole up as an ambient source and drove both playback and the release meter
from it.

The resolved name cannot distinguish them: a peek hole matched by a diorama pattern still
resolves to an `ambient_*` name, so `PeekGalleryMap.IsPeekScript` (a `peek_` prefix test)
never fires. The discriminator has to be the object.

`HeatLockSystem.IsNearPeekHole` now looks for a keyhole `CameraSwapTrigger` within
`AmbientPeekHoleRadius` (4 m) of the audio source, and `AmbientProximity` classifies each
source **once at scan time** (`Rescan`) — a `FindObjectsByType` per frame would be far too
costly. Sources flagged as peek holes are skipped entirely: no proximity playback, no look
meter.

Peeks keep their own path, which already existed: `TryReleaseFromKeyhole` →
`QueueKeyholeRelease` for the release on interacting with the hole, and the camera-swap scene
for playback. Dioramas keep the line-of-sight system.

**The on-screen "already used" line came back too.** `TryRelease` has always put a 6 s status
under the Horny readout (`SetReleaseStatus`), but the gaze gate returns *before* reaching it,
so a spent diorama silently showed no bar — indistinguishable from the feature being broken.
`SetAmbientReleaseStatus` now surfaces the same wording at the same moment the old code did,
on coming into earshot: `ambient wendigo hole already used`, or
`ambient wendigo hole unused, no horny lock to remove`.

**Diagnostics added** for the other half of the report — no meter appeared at two real
dioramas. Alongside the on-screen line, the log now says which case it is:

```
[HEAT-LOCK] no look meter for ambient_nun_chair_fuck: release already used
[HEAT-LOCK] no look meter for ambient_nun_chair_fuck: no horny locks held, nothing to release
[HEAT-LOCK] diorama ambient_nun_chair_fuck in sight - filling
[HEAT-LOCK] diorama ambient_nun_chair_fuck out of sight - draining
```

## 23. Diorama visibility fixed, peepholes stop trapping, status text shortened

**Not one diorama ever charged.** The visibility test cast a single ray at the audio
source's own position — which sits at the object's origin, near the floor, and typically
exactly behind whatever is in front of it. Dioramas are routinely partly obstructed (prison
bars, furniture the player can see over), so that one ray failed essentially everywhere, and
a failing test is invisible: no bar, and no status either, because the source was neither
spent nor unusable.

`HasLineOfSight` now samples a small spread — the origin plus eye-level, shoulder and
knee-height offsets and four lateral ones — and counts the diorama visible if **any** point
is clear. Raised points see over furniture; lateral ones find the gaps between bars. The
viewport margin also relaxed from 5% to 2%.

Added `"Look at it to release"` on screen when an available diorama is in earshot but not in
view, so "available but you are not looking at it" no longer looks identical to a broken
feature.

**Peepholes no longer trap the player.** `CameraSwapHooks` called `SceneEscapeGate.BeginScene()`
for every interact scene, so a peek held the player until the watch time elapsed
(`GrabEndHelper` blocks escape while `!SceneEscapeGate.CanEscape`). Keyhole triggers now skip
that gate entirely — a peep is a look, not a commitment.

**Peephole releases are instant.** `TryReleaseFromKeyhole` queued the release and paid out at
scene end, and only if the watch time was satisfied. It now clears on peeping via
`ReleaseAllFromKeyhole`, keeping the same reward the queued version gave — a peephole clears
**every** lock — without the wait. It also runs `ClearOverheatAtFloor` and `NotePlayerCum`,
which the queued path did not, so overheat and the filler follow the change immediately.

**Status text is short and nameless.** It read like a debug build and the long lines clipped:
`ambient wendigo hole unused, no horny lock to remove` → `Nothing to release`. Likewise
`Already used`, `Horny -1`, `Horny cleared (-4)`. The HUD box also went from 520x90 to
560x130 so two lines cannot clip.

`AmbientPeekHoleRadius` default lowered 4 m → 2.5 m, so the peek-hole exclusion cannot
swallow a diorama that merely happens to be near a peephole.

## 24. One-time releases reset per run

**`UsedReleaseSources` was never cleared** — not on scene change, not on a new run. A
diorama or peephole consumed in one run stayed consumed until the game process exited.

Under the original fire-on-earshot behaviour, merely walking past a diorama spent its
release, so after a few runs in one session every diorama in the save read as already used.
That is indistinguishable from the release system being broken, and it is the most likely
reason no diorama ever produced a bar during testing: the meter deliberately does not charge
a release that is already spent.

`ResetForScene` now clears `UsedReleaseSources` and `SeenSceneSources`, logging
`cleared N used release source(s) for the new scene`. One-time means once per run, not once
per launch.

Also split the ambient stop log so the two causes are distinguishable:
`out of sight -> filler` versus `left earshot -> filler`.

## 25. Diorama line of sight: the ray was hitting the player

The log settled it in one line:

```
[HEAT-LOCK] look check: imp gangbang d=7.7m cam='Effects Camera' centre=on screen, blocked by 'collider' at 0.5m
```

**Blocked at 0.5 m by the player's own body.** The ray starts at the camera, which sits
inside the player, so the first thing it hits is the player's collider — every sample point,
every diorama, always. The diorama was on screen the whole time; the occlusion test could
never pass anywhere in the game. Widening the sample spread and relaxing the viewport margin
in §23 could not have helped, because the failure was never about the diorama.

`IsBlocked` now uses `RaycastAll` and discards hits belonging to the player (matched by
`transform.root` against the player object, plus a `Player` tag check) before deciding, and
the diagnostic reports through the same path so it stays honest.

Camera selection also improved: when falling back past `Camera.main`, cameras with a
`targetTexture` are skipped (they do not render the player's view) and the lowest-depth
remaining camera wins. The log showed `cam='Effects Camera'`, which projected correctly but
is not obviously the view camera.

**Peek-hole exclusion was also swallowing a diorama.** The log showed
`'zombie dick sucking noises' is a peek hole` — the zombie bench-fuck diorama, sitting within
2.5 m of a peephole trigger. `AmbientPeekHoleRadius` default drops to 1.5 m so only a source
essentially *on* the peephole is excluded. The unambiguous case
(`ambientaudiosourcewendigopeek`) is still caught by name and position.

That classification also logged on every `Rescan` — 138 lines for one source in a single run.
Now logged once per source.

---

## 26. Dioramas: stop raycasting, use the game's own unlock box

The fourth failed test of the look meter produced two different blockers, neither of them the
player's body that §25 had fixed:

```
[HEAT-LOCK] look check: mimic wall fuck d=3.5m ... blocked by 'Floor_5x5' at 0.5m
[HEAT-LOCK] look check: imp gangbang  d=7.9m ... blocked by 'collider'   at 0.5m
```

Not one `[EDI] Play ambient_*` in the whole run either — §21 gates playback on the same test,
so the sight test failing killed the diorama scripts as well. That is issue #12 (D6 played
nothing), and it was never a D6 problem.

**The game already answers this question, and it does not use sight at all.** Every diorama
room carries a hand-placed `GalleryUnlockTrigger`: a trigger box with a `galleryID` of `D1`–`D9`
whose `OnTriggerEnter` calls `GalleryProgressManager.UnlockEnemy`. Walking into that box is
how the diorama's gallery entry unlocks — the level designer's own definition of *the player
has arrived at this diorama*. Extracted from `sharedassets1.assets`:

| ID | trigger object | room | box |
|---|---|---|---|
| D1 | `NunChairUnlockerD1` | Dungeon Jail Hallway Room | 5×5×5 |
| D2 | `GooperBedD2UnlockTrigger` | Mansion hallway w rooms | 1×1×1 |
| D3 | `ZombieBenchUnlockerD3` | Mansion Courtyard room 2 | 1×1×1 |
| D4 | `GargoyleD4Unlocker` | Mansion staircase room | 3×1×1 |
| D5 | `ImpD5GalleryUnlockTrigger` | Dungeon Cross Room | 5×5×5 |
| D6 | `ImpGangbangUnlockerD6` | Mansion 2 square room | 1×1×1 |
| D7 | `NunWallBJUnlockerD7` | Cavern bench room | 5×5×15 |
| D8 | `MImicWallFuckD8` | Dungeon 4 way | 5×5×5 |
| D9 | `PlantBJUnlockerD9` | Mansion Courtyard room | 1×1×2 |

`DioramaUnlockTriggers` finds these at runtime, resolves each `galleryID` through the existing
`DioramaGalleryMap` to its `ambient_*` script, and answers "is the player in this diorama's
box". No camera, no ray, no guess about where the art sits — the three things that each broke
the test in turn.

- **Look meter** = inside the box (plus `AmbientReleaseTriggerPadding`, default 1.5 m) **and**
  facing the source within `AmbientReleaseLookAngle` (default 75°). Facing is an angle, not a
  ray: being a metre out on where the art is does not matter to a direction.
- **Playback** = inside the box plus `AmbientPlaybackTriggerPadding` (default 4 m, deliberately
  looser, so the script does not cut out as you shift your feet in a 1 m box). The
  `AmbientPlaybackLingerSeconds` window absorbs the rest.
- Overlap is tested **collider bounds against box bounds**, which is what `OnTriggerEnter`
  actually does. Four of the nine boxes are 1 m tall and sit at floor level, so a point test on
  the player transform would miss them.

### The raycast is gone entirely

Not fixed — **deleted**. Once the box answers "at the diorama" and an angle answers "looking at
it", nothing was left for a ray to do:

- **Peek holes never reached it.** `AmbientProximity.Tick` skips `IsPeekHole` sources before
  anything else, and a peek is driven by interacting with the hole (§22, §23).
- **Every diorama has a box.** The nine `Patterns` entries map one-to-one onto D1–D9.

So `HasLineOfSight`, `IsPointVisible`, `IsBlocked`, `IsPlayerOwned`, the sample-offset spread
and the layer-mask plumbing all went, along with `AmbientSightIgnoreLayers` and
`AmbientLookRequiresClearRay` — 175 lines. A gallery with no box now falls back to earshot for
playback and facing for the release, rather than to geometry.

Two things worth recording about *why* the ray could never have worked, since the temptation
will be to bring it back:

- **The mask was `-5`** — everything except Ignore Raycast — **with triggers counted as solid**.
  The game has a `Player` layer (16), a `Floor` layer (14), plus `Blocker`, `Interactable`,
  `Effects`, `Pickups`. The player's own body, the floor slab under an audio source sitting at
  floor level, and every interaction volume in between all reported as walls.
- **The camera was wrong.** `cam='Effects Camera'` in every log line: `ResolveViewCamera`
  cached whatever the depth-ordered fallback found and never re-derived it. That fallback is
  deleted too; `FirstPersonController.cameraComponent` (private, read with `Traverse`) is the
  real view camera and the facing test uses it.

**Log spam fixed.** `out of sight - draining` appeared every frame — 12,483 `[HEAT-LOCK]` lines
in a five-minute run. The drain path nulled `_gallery` the moment the meter hit zero, so
`NoteCandidate` re-armed on the next frame, reset `_lastVisible` and logged the transition
again. The candidate is now dropped only once it is *both* out of earshot and spent.

New config, all in `[Gameplay]`: `AmbientReleaseUseUnlockTriggers` (false → boxes ignored,
facing and earshot only), `AmbientReleaseTriggerPadding`, `AmbientPlaybackTriggerPadding`,
`AmbientReleaseLookAngle`.

**Renamed**, because both names described the raycast rather than what they do:

| was | is | now means |
|---|---|---|
| `AmbientRequiresLineOfSight` | `AmbientPlaybackRequiresPresence` | playback requires being at the box, not merely in earshot |
| `AmbientLineOfSightGraceSeconds` | `AmbientPlaybackLingerSeconds` | seconds playback continues after stepping out of the box |

Both were at their defaults everywhere, so nothing needed migrating; BepInEx will drop the old
keys on its next clean write. `AmbientPlaybackLingerSeconds` has a much smaller job than the
grace window did — it debounces the box boundary, where the bounds-overlap test can flip frame
to frame, rather than a pillar crossing a ray. **Default dropped 0.75 → 0.25** to match: 0.75
was sized for a ray flickering behind level geometry, and at that length playback noticeably
trails you out of the room. Raise it if stepping around inside a box makes the script stutter.

Internally `HasPlaybackLineOfSight` → `IsPlayerAtDiorama` and `_lastLineOfSightAt` →
`_lastAtDioramaAt`, for the same reason.

**Known wrinkle:** `_lastAtDioramaAt` is a single static, not per-gallery. Walking straight from
one diorama into another's earshot within the linger window lets the second play for the
remainder of it without the player being at its box. Narrow, self-correcting, and only visible
as a diorama briefly playing from the wrong place.

**Loose end:** the trigger objects name D5 as an imp scene (`ImpD5GalleryUnlockTrigger`, Dungeon
Cross Room) while `DioramaAmbientMap` maps `D5=ambient_wendigo_hole` and `D6=ambient_imp_gangbang`.
D6 is `ImpGangbangUnlockerD6`, so D6 is right; D5 is suspect. The new
`[HEAT-LOCK] unlock triggers:` roster line names every ID and what it resolved to, so one run
in the Dungeon Cross Room settles it.

---

## 27. Dying in a grab played damage filler over the whole death scene

Reported as "during game over it kept playing the damage filler instead of the zombie scene".
The log gave it in three lines:

```
18:22:59.009  [GRAB-START] prefab='Zombie_Enemy_ALT1'
18:22:59.010  [EDI] Play Zombie_Loop          <- scene dispatched, correctly
18:22:59.010  [PLAYER-REVIVE] ok
18:22:59.012  [EDI] Play filler_damage_50     <- stomped, 2ms later
```

`DeathHooks.Revive_Postfix` called `Plugin.GoFiller()` unconditionally. A grab scene revives
the player *into* the scene — that is how §13/§14's "dying in a grab plays out as that scene"
works — and vanilla's `PlayerStats.Revive()` lands about two milliseconds *after* `GrabHooks`
has dispatched the scene's gallery. So the revive hook forced filler over the top and the
whole 16-second death scene ran on `filler_damage_*`.

Not enemy-specific: every grab scene entered at 0 HP went the same way.

`Revive_Postfix` now falls back to filler only when nothing else is playing, using the state
`SendPlay` already records:

```csharp
internal static bool IsGalleryPlaybackActive =>
    !_fillerPlaybackActive && !ShouldBeStopped && !string.IsNullOrEmpty(LastSent) && LastSent[0] != '_';
```

(The `_` test skips the `__paused__` / `__stopped__` / `__resumed__` sentinels `LastSent`
also carries.) Config `ReviveKeepsSceneGallery`, default true.

**Note this is not what TODO #2 predicted.** That guessed at `filler_damage_75` being
`Type=reaction`, auto-stopping after 2 s and leaving silence. The real mechanism is a live
override, and the symptom is filler playing rather than nothing.

---

## 28. Releases: full payout, heat that actually moves, and a watch bar for peepholes

### A diorama clears every lock

It paid out one. `AmbientReleaseClearsAllLocks` (default true) makes it clear the lot, the same
payout a peephole gives.

### The heat was never refreshed

The bigger half of "it didn't remove the heat". `TryRelease` called only `EnsureHeatBounds`,
where the peephole path has always also called `ClearOverheatAtFloor` and `Plugin.NotePlayerCum`.
Without those the lock count drops but overheat stays latched at the old floor and the filler
keeps driving off a stale heat reading — so even clearing every lock would have looked like
nothing happening. The ambient path now does all three.

### Peepholes: watch timer instead of instant

§23 made peephole releases instant to stop them feeling like a trap. The trap was the countdown
*text*, not the timer, so the timer is back as a fill bar — the same gauge the diorama look
meter uses, under the Horny readout.

`KeyholeReleaseWatchSeconds` (default 10) is **its own setting**. The queued path used to gate on
`SceneEscapeGate.WatchTimeSatisfied`, which could never have worked for a peephole:
`CameraSwapHooks` deliberately skips `SceneEscapeGate.BeginScene()` for keyhole triggers (§23,
"a look, not a commitment"), so the gate is never active and `WatchTimeSatisfied` falls through
to `_lastWatchTimeSatisfied` — **a stale flag left by the previous grab scene**. The independent
timer is not just tidier; it is the only way this could work.

- Pays out the moment the bar fills, mid-scene, like a diorama. Banking it until scene end would
  have made `0` mean "sit through the scene anyway".
- Leaving early costs the progress, not the release: the key never reaches `UsedReleaseSources`,
  so peeking again re-arms from zero. No status text — the bar vanishing says it.
- `0` pays out on peek with no bar (`HasKeyholeWatchBar` is pending **and** seconds > 0, so it
  cannot flash for a frame).
- `ReleaseAllFromKeyhole` and `BuildPendingKeyholeStatus` deleted; the queue is the only path.

The keyhole bar is checked *before* `AmbientReleaseGaze.Enabled`, which covers the **diorama**
look timer — setting `AmbientReleaseLookSeconds = 0` would otherwise have silently taken the
peephole bar with it.

### Status text

The diorama messages were the only ones putting internal jargon on screen — `ambient imp
gangbang already used` leaked both the source-kind prefix and the raw pattern name.

| was | is |
|---|---|
| `Look at it to release` | `♦` (`AmbientNearbyIcon`) |
| `ambient <name> already used` | `Already used` |
| `ambient <name> unused, no horny lock to remove` | *(nothing)* |
| `Nothing to release` | *(nothing)* |
| `<label> already used` | `Already used` |
| `<label> unused, watch Ns longer` | the fill bar |
| `<label> not used, watch Ns longer` | *(nothing)* |
| `<label> cleared all horny locks` | `Horny cleared (-N)` |
| `<label> used, no horny locks to clear` | *(nothing)* |

The icon must be a glyph Unity's builtin Arial actually has — the readout is a legacy `UI.Text`
with `Resources.GetBuiltinResource<Font>("Arial.ttf")`, a dynamic font, so emoji will not render.
`♦` is in WGL4, which Arial covers completely. `AmbientNearbyIcon` exists so the glyph can be
swapped without a rebuild.

### An empty payout no longer burns the source

Both payout paths marked the source spent *before* checking there was anything to spend:

```csharp
UsedReleaseSources.Add(key);
if (_locks <= 0) { ...; return; }   // permanently used, player got nothing
```

The gaze gate refuses to start the meter at zero locks, but it re-checks per frame while the
payout is three seconds later — and the peephole window is ten. Anything emptying the locks
inside that window (a heat potion, another release landing) meant the bar filled, the source was
consumed for the rest of the run, and nothing happened. Indistinguishable from the feature being
broken, which is the failure mode this system has already burned four test rounds on.

The check now precedes the `Add` in both `TryRelease` and `PayPendingKeyholeRelease`, so an empty
payout leaves the release available. Logged as `release not spent, no locks held at payout`.

`PayPendingKeyholeRelease` also picked up `ClearOverheatAtFloor` + `NotePlayerCum`: the deleted
instant path had them, this one never did, and it is now the only way a peephole pays out — so
it had silently inherited the same "locks drop but the heat does not move" bug fixed above.

**Also fixed:** a spent diorama said "already used" once, for six seconds, then stayed silent
however many times the player came back. `SetReleaseStatus` only bumps a 6 s timer, and the call
was tied to the once-per-reason log guard. The log stays throttled; the status now refreshes
every 2 s while the player is at a spent diorama.

---

## 29. Name resolution rebuilt on ground truth

Full write-up in `code/NAMING-AUDIT.md`; this is the summary.

Name resolution had grown to **seven** overlapping resolvers, ending in a per-enemy substring
matcher that returned *something* for any string containing an enemy name. That last one is why
gaps were invisible, and it produced real bugs: peek scenes resolved onto grab galleries (TODO #11), and alt handling
contradicted itself.

Ground truth came from the game: 168 `AnimatorController` assets read out of the shipped
`.assets` files with UnityPy, giving every animator state the game can produce. A harness
(`code/slugharness`) compiles the mod's **real** `NameRemap.cs` and reports what every
`(enemy family, state)` pair resolves to, so coverage is countable rather than argued.

- **131/131 pairs now map explicitly. The greedy matcher is deleted** — `TryResolveByEnemy`,
  `ResolveStage`, `TryResolveImplicitAlias`, `NormalizeGameplayName`, ~3.7 KB. An unmapped slug
  is returned unchanged and logged once as `[ALIAS-GAP]`; `SendPlay`'s `IsKnown` gate then drops
  it without disturbing the running script.
- **The table moved into the DLL** (`GalleryTable.cs`, 326 + 40 entries). It used to be the
  *default value* of a config setting, which froze on each user's first run: the shipped config
  was four versions behind the code and ~90% of gameplay was running on the fallback.
  `GalleryAliases` / `InGameAliases` are now empty override lists layered on top, so an update
  reaches the user and a user tweak survives the update.
- **`EnemyRemap` was missing four entries** (`Zombie_Enemy`, `Zombie`, `Plantasha_Enemy`,
  `Plantasha`). Harmless while the fallback existed, fatal without it. Confirmed fixed in game:
  `[GRAB-START] prefab='Zombie_Enemy_ALT1' key=zombie`.
- **Peek scenes resolve by animation clip.** Every peek trigger in the game is named `P1`..`P7`,
  carrying no identity, so the clip name is the only signal — `PeekClipMap`, checked before the
  alias table. All 21 peephole clips resolve, including the game's own misspellings
  (`Planatasha`, `GooperPilloary`) and `PeepHole` vs `Peephole`.
- Dead rows removed: `Zombie_Start`, `ZombieAlt1_Start`, `imp_grab_start` (no such animator state
  exists), `gargoyle_grab` (shadowed by an alias).

## 30. Gallery files: one scene per file

Full write-up in `code/TIMING-AUDIT.md`.

**Every animation's exact duration is readable** from `AnimationClip.m_MuscleClip.m_StopTime`.
Retiming no longer needs video measurement, and it validated itself against the scenes already
confirmed by other means (`Mimic_Start` 1.000 cycles, `peek_wendigo_ride` 4.000).

- **Six multi-scene strips split into 35 dedicated files.** 59 rows, 59 funscripts, every
  `FileName` equal to its `Name` lowercased, every slice `0..len`. The split reproduces Edi's
  `inproveLoopAccion` semantics — including borrowing a neighbouring action's position for an
  interpolated endpoint — and every extraction was verified byte-identical through Edi's own
  pipeline. Originals archived to `Edi/_reference/source-scripts/`.
- **§3's repointing had made four scenes worse.** `gallery.funscript` carries 27 chapters, the
  original author's boundaries; comparing them showed `Nun_Grab`, `Mimic_Cum`, `Mimic_Loop` and
  `Wendigo_Continued` had drifted off whole-cycle alignment. `nun_grab` and `mimic_cum` turned
  out to be the chapter content uniformly time-scaled (×1.049 and ×1.50) to match a video
  measurement. All four restored to exact cycles.
- `imp1/2/3` renamed `imp_1/2/3` — snake_case, and a direct hit for the grapple's `imp_` + tier
  dispatch instead of an alias hop.
- **`GenerateDefinitionFromChapters` is harmless**, checked against the Edi source: it only runs
  when `Definitions.csv` is *absent*, and writes to `Definitions_auto.csv`.

## 31. Imp grapple, peek browsing, and the cum that never ended

### The cum animation repeated for the whole grab

Vanilla ends a cum only when heat reaches **exactly 0**, in two gates:

```csharp
HandleHeatBuildup():           if (CurrentHeat > 0f) return;  heatFullyCooled = true;
OnMaxHeatAnimationComplete():  if (!heatFullyCooled) return;  animator.SetBool("MaxHeat", false);
```

A horny lock puts a floor under heat, so 0 is unreachable, `heatFullyCooled` is never set, the
animation-complete event no-ops every time it fires, and the cum repeats until the grab ends —
**at any lock count**. `CumCooldownEndsAtLockFloor` (default true) completes the cooldown at the
lock floor instead. Exactly the trap §11 hit with overheat, which also tested for exactly-0.

`FullLockHoldsCum` (default true) covers the remaining case: at full lock the floor is
`maxHeat - 1`, so the cum would end and retrigger within a frame. A postfix on
`OnMaxHeatAnimationComplete` re-asserts `MaxHeat` and replays the current state, so it holds
cleanly instead of flickering to the grabbed loop.

### Imp tiers no longer collapse onto one loop

`GrappleLoopDelaySeconds` default 1.2 → **0**. Vanilla's `GrappleScreenobject` holds
`oneEnemyAnimation` / `twoEnemyAnimation` / `threeEnemyAnimation` and a matching audio loop for
as long as that many imps are attached — there is no generic grab loop to switch to. The mod was
replacing the tier script with `imp_grab_loop` 1.2 s after every escalation, so `imp_1/2/3`
(2.6 / 4.1 / 6.8 strokes per second) were barely perceptible before being overwritten.

Also retimed: `imp_grab_cum` 1506 → 3500 ms (one cycle of `Imp_Grab_Cum`, was restarting 2.3×
per animation) and `imp_grab_loop` 1900 → 1750.

### Peek scenes no longer play while browsing

`PeekScenesUI.DisplayCurrent` fires on every scroll, so a peek script started before *View
Scene* was pressed. Gated on `isViewingPeekScene`.

That also removed the `[ALIAS-GAP]` lines seen in the log: they came from a speculative probe
inside `PeekGalleryMap` that recovers via its own heuristic, so the miss was never a real gap.
That probe is now quiet.

### Heat bar

`ShowHeatBarDuringGrab` (default false, as before) re-enables the vanilla heat bar during grabs,
and a `[HEAT-TRACE]` line logs heat, the lock floor and vanilla's three cooldown flags twice a
second while grabbed. Without either there is no way to tell whether the cooldown is moving heat
or the floor is pinning it — which is what made the bug above hard to see.

---

## 32. Funscripts validated against the game's own animations

`code/animcheck.py` (one scene) and `code/animsweep.py` (all 51). An `AnimationClip` here is an
ordered list of `Sprite` references at a fixed rate, so the **frames themselves** are readable
from the shipped assets — exact period, exact motion, and the pixels can simply be looked at.
That replaces video capture for everything it can measure.

Two signed proxies: **silhouette top edge** (sprites are alpha-trimmed from the top and share a
bottom edge, so the trimmed height *is* the outline) and **signed displacement** (centre of where
content appeared minus where it vanished) for scenes whose outline is pinned. Both signed on
purpose — a frame-difference magnitude peaks twice per stroke.

**Timing is objective. Polarity is not.** The proxy assumes "higher on screen = withdrawn", which
is right for some scenes and backwards for others. A feel pass confirmed it: the sweep
flagged `Gooper_Start`, `peek_zombie_bj`, `peek_imp_three_way`, `ambient_plantasha_blowjob` and
`Gravy_Loop` as inverted and **all five are fine**. Treat a negative correlation as a shortlist
entry, never a verdict.

Applied:

- **Three inversions** — `Zombie_Loop`, `ambient_imp_gangbang`, `ambient_nun_wall_chain_head`.
  `Zombie_Loop` went −0.63 → +0.63 against its animation, which is the control that validates
  the method.
- **`ambient_mimic_wall_fuck` rebuilt, not inverted.** Its outline is pinned (arms chained), so
  the mimic's tongue was tracked instead: top edge `67, 62, 78, 82, 75` px across the 5 frames.
  43 hand actions → 31 derived. Confirmed good by feel.
- **Diorama clip mappings corrected.** The earlier table used *gallery* clips; dioramas have
  their own, much shorter. Five of eight were already exact. Retimed
  `ambient_nun_chair_fuck` 3145→3125, `ambient_zombie_bench_fuck` 4867→5000,
  `ambient_imp_gangbang` 3000→3125.
- **A clip's length is not its stroke period.** `imp gangbang` is 1250 ms holding *two* identical
  strokes — frames 0–4 and 5–9 differ by 0.7–2.5 where neighbours differ by 2.9–9.2. True period
  625 ms. Aligning to the clip would have meant a 17–25% change; aligning to the stroke, 4%.
  `animcheck.py` now detects this automatically.
- **`D5=ambient_wendigo_hole` was wrong.** D5's room (`Dungeon Cross Room`) contains an
  `Imp Gangbang` object; the only "wendigo hole" in the game is `AmbientAudioSourceWendigoPeek`,
  the wendigo *peephole's* ambient audio. Now `D5=ambient_imp_gangbang`. See the peek-vs-diorama
  note in PROJECT.md.

---

## 33. The second imp gangbang diorama, and a fallback that had quietly gone stale

Started as a documentation inconsistency: §6 recorded "adding an `ambient_imp_gangbang_2` row"
in the **do-not-redo** list, while TODO step 6 asked for exactly that. Both were written in good
faith — §6 rejected the row because no second funscript existed, §32 later found D5 and D6 are
different animations — but nobody reconciled them, so the do-not-redo entry was pointed at work
that had become correct.

**D6 holds two strokes, not one — the gap is 4%, not 2×.** §32 measured `imp gangbang 2` as
1200 ms / one stroke and concluded the two dioramas were 1.92× apart, needing a new curve built
from scratch. Wrong: D6's 12 frames are **two identical six-frame strokes of 600 ms**, drawn 1 px
apart horizontally. Aligned per-frame, the two halves differ by 0.40 against a neighbour baseline
of 3.30 — a ratio of 0.12, *tighter* than D5's 0.30. Unaligned it scores 0.70 and misses the 0.5
threshold, which is why `stroke_period` reported one long stroke.

- `animcheck.stroke_period` now differences frames at their best integer x-offset (±3 px).
  Both clips resolve correctly (625 ms × 2, 600 ms × 2) and the full 51-scene sweep is
  unchanged otherwise — `imp_1` 10.660, `Gravy_Cum2` 7.642, `peek_gooper_pillory` 3.976 all as
  recorded in §32.
- **`ambient_imp_gangbang_2` added**: 31 actions, 3000 ms = 5 × 600 ms, correlation **+1.000**
  against its animation. Derived, not rescaled — the shared curve is D5's "hard bottom, fast
  kick" impact profile, which bottoms a frame early here. D6's motion is the rear imp's rise and
  fall (head down at frame 3 = deep = pos 0), read off the contact sheet and tracked with the
  signed-displacement proxy.
- `Patterns` split: entry 1 keeps `imp gangbang|imp_gangbang|imp gangbang sound|imp gangbang 1`,
  a new entry supplies `imp gangbang 2|imp_gangbang_2`. Separation is exact rather than lucky —
  `MatchPattern` scores an equality hit at +1000, so D6's object scores 1014 against entry 1's
  12, and D5's `imp gangbang` cannot contain `imp gangbang 2` at all.
- `D6` / `ImpGangbangD6` → `ambient_imp_gangbang_2`; `Definitions.csv` row and funscript in both
  trees; added to the `GalleryRegistry` seed.

**`DioramaGalleryMap.DefaultDSlotAmbients` deleted.** §32's D5 correction reached the
`DioramaAmbientMap` config-default string but not this parallel 9-element array, which still
carried `ambient_wendigo_hole` at index 4 — in the shipped DLL, not just the source. `Resolve`
falls to it whenever the config map lacks the key, so D5 was wrong for anyone who blanked or
trimmed the setting, and invisible here because our config is patched. The array is now gone;
`Reload` parses the setting's own `ConfigEntryBase.DefaultValue` into a `Fallback` dictionary, so
the built-in and the shipped default are the same string by construction. Verified by field name:
`DefaultDSlotAmbients` present in `PncEdi-v2.0.8-original.dll`, absent now.

This also removes the last documented code ceiling. A D10 no longer needs a rebuild — it needs a
`DioramaAmbientMap` entry, like every other slot. (The array never enabled D10 anyway; it failed
its own bounds check and fell through to the keyword heuristics.)

**Also found:** `mod/single-mod`'s config had drifted from the game's on `ShowHeatBarDuringGrab`
(`false` shipped, `true` locally for debugging). The distributable is correct and the local tweak
is deliberate — but the documented regeneration recipe copies local → distributable, so running
it would have shipped the tweak. `code/README.md`'s recipe now resets it and says to diff first.

---

## 34. Retiming pass: every script against its own animation's duration

`code/retime.py` — report by default, `--apply` to fix, `--max-pct` to change the cap. It reads
each clip's duration out of the shipped assets, divides the script length by it, and reports how
far that lands from a whole number.

**The criterion validated itself before anything was changed: 20 of 51 scenes were already at
exactly N.000 cycles**, authored by five different people across three eras of the thread. That
clustering only happens if clip duration is the period the authors were targeting, which is what
justifies treating the outliers as defects rather than as a bad model. (`m_AnimationClipSettings.
m_LoopTime` is False on all 51, including dioramas that visibly loop forever — looping is driven
by the animator state, not the clip import flag, so that field settles nothing. Ignore it.)

**Fixing means scaling, never trimming.** Trimming costs real content and desyncs the shape — see
the reverted list below. A scale under ~5% is beneath the just-noticeable difference for stroke
timing, so it removes the drift without changing the feel; `--apply` refuses anything larger.
That cap also makes the pass safe under both readings of these scenes: if a state loops, the
script is now exact; if it plays once, a sub-5% length change is irrelevant either way.

**24 scenes scaled**, biggest first: `Gravy_Cum2` 11463→12000 (−4.47%, the drift TODO step 2
already suspected), `Dragon_Grabbed` 4675→4833, `imp_3` 5160→5000, `imp_1` 5330→5500,
`imp_2` 4850→5000, `Dragon_Cum` 1139→1111, `Baphomet_Loop2` 1230→1250, `Baphomet_Loop`
1480→1500, `Gargoyle_Cum` 3342→3375, `Baphomet_Cum2` 2523→2500, `Zombie_Cum` 10133→10222,
`Gravy_Start2` 2855→2875, `peek_nun_mimic` 3533→3556, `Gravy_Loop2` 1566→1556,
`peek_gooper_pillory` 3534→3556, `Gravy_Start` 3852→3875, `Baphomet_Start2` 2486→2500,
`Gargoyle_Grabbed` 1991→2000, `Gravy_End2` 3766→3750, `Baphomet_Cum` 2510→2500, `Gravy_Cum`
6974→7000, `peek_imp_three_way` 3100→3111, `Zombie_Loop` 5315→5333, `Gravy_Loop` 1995→2000.

Sweep went from **28 ok / 11 near / 12 OFF to 45 ok / 0 near / 6 OFF**. All nine dioramas were
already exact and were not touched — including `ambient_imp_gangbang`, which is 3125 = 5.000 ×
625 ms and needed no retime.

Both trees updated together: funscript actions scaled, `Definitions.csv` `EndTime` rewritten,
loop seams kept closed (`last.pos = first.pos`), all 60 rows verified monotonic with no rounding
collisions (smallest surviving gap 16 ms).

The floor is 0.1%, not zero: several periods are not a whole number of ms (555.6, 666.7, 888.9),
so the target is itself rounded and a 1 ms "error" is that rounding. `peek_nuns_threeway` at
3334 vs a 3333.3 target is correct as it stands.

**Six left alone**, all needing 6–27% — a real change to how they feel, not a drift fix:

| scene | script | nearest target | off by |
|---|---|---|---|
| `Nun_Cum` | 4201 | 3300 (1×) | +27.30% |
| `Gooper_Cum` | 1739 | 1500 (1×) | +15.93% |
| `Gooper_Start` | 2046 | 2400 (3×) | −14.75% |
| `Plantasha_Start` | 904 | 1000 (1×) | −9.60% |
| `Plantasha_Cum` | 7133 | 7750 (2×) | −7.96% |
| `Wendigo_Start` | 5489 | 5167 (1×) | +6.23% |

The first three are not near *any* integer multiple, so they are authoring problems rather than
mistimed ones. The last three are one or two cycles stretched. All six want a feel pass
before anyone scales them — see TODO.

Also: `animsweep.py`'s body now sits behind `if __name__ == "__main__"`, because `retime.py`
imports its `MAP` and was triggering a full 51-scene sweep on import.

### 34b. `imp_1` rebuilt — length was never its problem

Retiming it to 5500 (11 × 500 ms) fixed the drift and left the real fault untouched: its **stroke
rate** was wrong. `Imp_Grab_One` is 4 frames @ 8 fps = 500 ms, one stroke. The script's prominent
peaks sat 767/798/795/778/796 ms apart — ~778 ms, **1.56× slower than the animation**, so the
device lagged visibly. It also never left the 0–80 band and parked at 0 between strokes.

Rebuilt from the frames: silhouette top edge `70, 42, 61, 91` px → pos `57, 0, 39, 100`, 4 points
per 500 ms cycle, 11 cycles, 45 actions. **Correlation +1.000**, full 0–100 range, and phase
aligned so script t=0 is animation frame 0.

Polarity needed no inversion. These are the grapple **UI** sprites (`imp grapple-Sheet`, 373×70,
drawn along the bottom of the screen) — an imp's horned head bobbing, lowest at frame 1 and
highest at frame 3. Head down = deep = pos 0, which is the default convention.

**The sweep had flagged `imp_1` as INV (−0.63). That was an artifact, not a polarity problem** —
sampling a 778 ms script at the animation's 500 ms period drifts the phase across 11 cycles and
the correlation is noise. Same illusion as the spurious +0.900 on `ambient_imp_gangbang_2` in
§33. **A correlation is only meaningful once the periods match; check the rate before reading the
sign.** After the rebuild it reads +1.000.

Left alone, needing a decision: the three tiers use different sheets (`imp grapple-Sheet`,
`imp grapple2-Sheet`, `imp grapple-3Sheet`) but all run 4 frames / 500 ms, while `imp_2` strokes
at 263 ms (0.53×) and `imp_3` at 130 ms (0.26×). Running *faster* than the animation is plausibly
deliberate tier intensity, unlike `imp_1` running slower, so they are reported rather than
rebuilt.

**`retime.py` gained `a.strk` / `s.strk` / `rate`** so this class of fault is visible without
hand-measuring. It is a ranking aid, not a verdict — the same standing as polarity. `s.strk` is
solid; `a.strk` divides the cycle by the maxima a silhouette proxy can see, and that proxy cannot
resolve individual strokes inside a long varied clip (`Gravy_Cum` reports one 7000 ms "stroke"
for 56 frames). A first attempt flagged 33 of 51 scenes and was thrown away — comparing the
script's stroke against `stroke_period`'s output is meaningless whenever the clip is not itself
one stroke.

**Proxy selection fixed while doing it.** `animcheck` switched to signed displacement only when
the top edge's range was *exactly* zero. Four scenes move 1.4–2.4% — 3–5 px on a 127–280 px
sprite, i.e. alpha-trim jitter — and reading that as signal invents strokes: `ambient_imp_gangbang_2`'s
3 px wobble made its 600 ms cycle look like two 300 ms strokes. The test is now range as a
fraction of height, at 3%, in a shared `motion_proxy()` used by all three tools. It denoises
rather than reclassifies — every affected scene's correlation improved and none changed sign:

| scene | before | after |
|---|---|---|
| `ambient_nun_chair_fuck` | +0.60 sil | +0.88 sig |
| `ambient_zombie_bench_fuck` | +0.52 sil | +0.89 sig |
| `ambient_gargoyle_ledge_fuck` | +0.31 sil | +0.82 sig |
| `ambient_imp_gangbang_2` | +0.61 sil | +1.00 sig |
| `Gargoyle_Grabbed` | +0.40 sil | +0.40 sil (5.9%, correctly kept) |

---

## 35. The 3-imp grapple scenes, measured per imp instead of per frame

`imp_grab_loop` and `imp_grab_cum` felt arbitrary because every proxy so far averaged two imps
doing different things into one number. These are full-screen 480×270 frames with no alpha trim,
so the silhouette proxy is dead and `signed_shift` sees tails, arrows and background bodies as
readily as the act.

**A colour mask separates them.** The shaft and balls are tan (R>150, G>100, B>80); the imps are
deep red (G≈54). Counting tan pixels in a row band says how much of the shaft is uncovered there:

| band | rows | what it is |
|---|---|---|
| tip | 100–120, x 180–300 | the imp on the tip — more tan = exposed = withdrawn = 100 |
| balls | 180–200, x 180–300 | the imp on the balls |

Both come out clean and in anti-phase, which is the giveaway that a whole-frame proxy could never
have worked:

```
tip    1281 1247 1083  973 1028 1223 1310    min at frame 3
balls   120  163  204  283  375  215  174    max at frame 4
```

**`Imp_Grab_Cum` is not four strokes.** `stroke_period` reports reps=4 and it is right about the
pixels — the *balls* imp repeats its 875 ms bob all four times. The tip imp does something else
entirely: descends through cycle 0, stays down through cycles 1–2, releases in cycle 3.

```
cycle 0: 1281 1247 1122 1007  872  678  635   descend
cycle 1:  633  637  639  642  740  739  854   hold deep
cycle 2:  641  660  659  657  645  747  730   hold deep
cycle 3:  608  613  639  642 1032 1223 1310   release
```

That is a single 3500 ms arc, and any retiming or shape work driven by the reps=4 figure would
have been wrong. **When a scene has two actors, measure the region, not the frame.**

Rebuilt by `code/impgrab.py` (re-runnable, `--no-tremor` for the bare stroke):

- `imp_grab_loop` — 29 actions, 1750 ms = 2 × 875 ms, stroke bottoming at 375 ms
- `imp_grab_cum` — 57 actions, 3500 ms, the descend/hold/release arc above

Both track the tip signal at **+0.998** (the residual is the tremor). `imp_grab_loop`'s rate is
now 1.00× against its animation.

**Tremor is an authoring choice, not a measurement.** Nothing in either clip moves at vibration
speed — the balls imp cycles at 875 ms like everything else. It is synthesised at ~8 Hz, ±7, with
amplitude scaled by the balls signal so it swells when that imp is most engaged. Regenerate with
`--no-tremor` if it reads as jitter rather than buzz.

Note the sweep's polarity column stays meaningless for these two: it uses the whole-frame proxy
that this section exists to work around. Judge them with `impgrab.py`'s own numbers, and
`retime.py`'s `a.strk` for `imp_grab_cum` (4.07×) is the same artefact — a one-shot arc has no
stroke rate to compare.

---

## 36. Scripting conventions, device limits, and per-device variants

Prompted by the imp cum scene reading as nothing. It was: the whole approach to expressing
vibration was wrong, and once measured against real scripting practice most of the set turned out
to be asking for motion no Handy can produce.

### What the guides and the reference scripts actually say

From [eroscripts' getting-started guide](https://discuss.eroscripts.com/t/how-to-get-started-with-scripting/2234)
and the OFS-authored scripts already sitting in `Edi/_reference/source-scripts/`:

- **≥100 ms between points.** The original Handy guarantees ~2 commands/s and tops out near 6.
  Denser points are averaged away, not reproduced. `shared_plantasha` — the best script in the
  set, verified to 0.3% — puts 90% of its gaps at ≥100 ms, mode 125–150.
- **Speed** = |Δpos|/Δt → units/s; × stroke_mm/100 → mm/s. Handy 1 is 110 mm capped at 400 mm/s
  = **364 units/s**; Handy 2 is 125 mm at 450 stock, **1200 mm/s = 960 units/s at max overclock**
  (motor absolute 1600 mm/s). Those come off the device's own slider-overclock menu — review
  articles quote 800 mm/s for the overclock and are low by a third. The same menu sets a *minimum*
  speed (32 mm/s stock, 15 at max OC) below which the motor will not track smoothly.
- **Bursts over the cap are normal.** `shared_plantasha` runs median 274, p95 483, peak 644.
  It is *sustained* excess that hurts.
- **Avoid strokes under 20%**, except during a blowjob where 10–20% is accepted.

### How a real scripter writes a vibration

This was the missing piece. `shared_zombie`'s cum section:

```
14167 100 -> 14288   0   dt=121 dp=100   826 u/s
14288   0 -> 14410  50   dt=122 dp= 50   410 u/s
15040  50 -> 15143   0   dt=103 dp= 50   485 u/s
15143   0 -> 15236  50   dt= 93 dp= 50   538 u/s
15526   0 -> 15591 100   dt= 65 dp=100  1538 u/s   <- accent
```

A buzz is a **0↔50 half-range oscillation at ~100 ms**, not a small tremor. §35's ±7 at 62.5 ms
was both too small to feel and too dense to reproduce — the device averaged it into a straight
line, which is exactly why the scene felt empty. A stroker has no vibrator motor; large fast
strokes *are* the vibration.

`imp_grab_cum` rebuilt on that basis: descend (5 points), **24 buzz points alternating 0↔38–47
across the 2.1 s hold**, then release. 33 actions, min gap 104 ms, median 385 u/s, p95 452 —
inside the band the reference scripts occupy. `imp_grab_loop` regenerated at one point per
animation frame (125 ms), 15 actions, median 208 / p95 464, no buzz: there the balls imp bobs at
the same 875 ms as the stroke, so a second rhythm would only fight it.

### `code/speedcheck.py` — what the hardware can actually play

Reports point spacing and the speed each transition demands, per variant. On `detailed`:
**44 of 60 scripts exceed the Handy 1 ceiling and 37 have points under 100 ms.** Not a defect in
isolation — the reference scripts do too — but sustained excess is why fast scenes feel mushy.

### `code/variants.py` — one extra variant, not two

Edi selects a script by variant and **the variant is the folder name**, so this needs no mod
change and no config setting, exactly as suspected. `Edi/Gallery/` now holds:

| variant | limit | differs from `detailed` |
|---|---|---|
| `detailed` | none — the master, and the Handy 2 script | — |
| `handy1` | 364 u/s (110 mm @ 400 mm/s) | 44 of 60 |

Point a device at it in `Edi/EdiConfig.json`: `"Variant": "handy1"`.

**A `handy2pro` variant was generated and then deleted — limiting for it was wrong**, on two
counts. First the ceiling was too low: 640 u/s came from review articles quoting 800 mm/s, while
the device's own overclock menu goes to 1200 mm/s = **960 u/s**. Second, and worse, the check was
against *peak* rather than *sustained* speed. At the correct ceiling `detailed` sits at p50 363 /
p75 455 / **p95 872 u/s — under the 960 cap** — with only 4.7% of its 1271 transitions above it,
and exactly **one** script (`imp_3`, median 1041) sustained beyond it. The other eleven the
limiter touched exceeded only on isolated accents, which are written on purpose: `shared_zombie`,
the best script in `_reference/`, contains a 1538 u/s (1923 mm/s) transition no device can
literally reach, which renders as a snap. Clipping those strips intended punch from the one device
fast enough to enjoy it. `detailed` is not a fast script; it is a normal script with a fast tail.

The Handy 1 case is genuinely different: the median transition across the whole set is 363 u/s,
so *half of everything* is at or over that device's cap. That is sustained excess and it mushes,
which is what the variant exists for.

**Judge a script against a device by its median, never its maximum.** The maximum is an artistic
choice; the median is what the motor has to sustain.

**Slew limiting, not global scaling.** Scaling a whole script by one factor also shrinks the slow
sections that had headroom; global scaling would have crushed `ambient_gargoyle_ledge_fuck` from
90 range to 33. Clipping each transition to what the device can cover in the time available keeps
it at 61, and leaves 16 scripts untouched entirely:

```
reachable = limit * dt / 1000
pos = previous + clamp(target - previous, -reachable, +reachable)
```

Timing never moves — it is the sync to the animation. Worst range loss is 90→61; the minimum
resulting range is 24, still above the guide's 20% floor.

**The limiter has to be cyclic.** Every row is `Loop=true` and `InproveLoopDetection` rewrites the
last action to match the first at load, so a start-to-end limiter leaves the wrap unclipped: the
tail lags, gets snapped back to the head, and that jump is over the limit again. The first attempt
produced exactly that — 10 transitions up to 1633 u/s, every one of them the final segment.
Running the limiter repeatedly, each pass starting where the last ended, converges to a position
where the loop closes on its own. After the fix the worst overshoot anywhere is 4.3% and the
median 0.7%, which is integer-rounding on short gaps rather than lag.

---

## 37. Step 1 polarity — neither scene needed inverting

Both were listed as polarity problems. Neither was. Both were the generic proxy watching the
wrong thing, and inverting would have made each *worse* while looking like a fix.

**`ambient_nun_wall_chain_head`** — she kneels and the chained figure hangs, so the outline never
moves and `signed_shift` reads whatever else shifts. The cue given on the feel pass was
exact: *narrowest hood = all the way down*. Measured as the mean width of the black hood over
rows 90–135, that is frames `51.2, 47.4, 45.9, 46.1, 48.3, 50.5` px → `100, 29, 0, 3, 46, 86`,
narrowest at frame 2.

The old script bottomed at **525 ms against an animation whose narrowest point is 250 ms** — a
275 ms phase error, over a third of the cycle. That is why the earlier inversion did not help:
**inverting cannot fix phase.** A script that is out of phase reads "wrong" exactly like one that
is inverted, and the correlation sign cannot tell them apart. Rebuilt: +0.443 → **+1.000**.

**`ambient_gooper_bed_blowjob`** — the silhouette top edge (146, 156, 140, 135, 133) tracks the
slime's own body, which peaks at frame 1. The act peaks at frame 3: the shaft shows *through* the
translucent slime, and its visible area runs 117, 195, 305, 383, 304 px — least at frame 0
(swallowed), most at frame 3. Slime and shaft are both green but the slime's G−R is ~46 against
the shaft's ~12, which separates them. Rebuilt from that: +0.27 → **+1.000**.

### `code/proxies.py` — a registry, so the sweep stops crying wolf

Four scenes now have scene-specific proxies, and the generic columns will never fit them. Left
alone, `animsweep` reports them INV forever and `retime` invents stroke rates, which is an
invitation for a later pass to "fix" scenes that were derived from the animation and are correct.
`proxies.py` registers each scene's own proxy; `animsweep` and `retime` consult it and print
`own` in the proxy column.

It also carries `ONESHOT` for scenes whose motion is a single arc rather than a cycle.
`Imp_Grab_Cum` is one: `stroke_period` sees the *balls* imp repeating and reports reps=4, so
folding the script into 4 cycles compared an arc against its own average and produced +0.05
noise. Compared over the whole clip it reads **+0.90** (the remainder is the synthesised buzz,
which is not in the animation).

Sweep polarity went from INV=9 / ok=29 / ? =13 to **INV=8 / ok=33 / ? =10**, with timing
unchanged at 45 ok / 6 OFF.

**The lesson worth keeping: a bad polarity reading is more often a bad proxy than a bad script.**
Three of the four scenes reworked in §35–§37 were flagged INV or ambiguous and none of them was
actually inverted.

---

## 38. `Dragon_Cum`, and the scene-type conventions the guides give

**`Dragon_Cum`** — the frame is almost entirely dragon, so every whole-frame proxy tracks her mass
and reads INV −0.87. The cue from the feel pass was right: follow the penis of the character
lying on the ground. That is ~700–1400 px of cream at bottom centre, cleanly separable because the
dragon is deep red. Visible shaft runs `1354, 1159, 842, 732, 1179` px — most exposed at frame 0,
fully seated at frame 3.

Duration was already correct (1111 ms = 2.000 cycles; §34's retime had fixed it from 1139).

Honest note: **this script was less broken than its flag suggested.** Sampled at frame times the
old curve read `100, 60, 19, 20, 60` against the animation's `100, 69, 18, 0, 72` — a symmetric
triangle approximating an asymmetric stroke. The rebuild reaches a true 0 at frame 3 and gets the
faster rise, +1.000, but the −0.87 was the proxy, not the script. Fourth scene in a row where that
was true.

Step 3 of the funscript plan is now complete.

### Scene-type conventions, from the eroscripts guide

Recorded because they should govern everything derived from here on, and because two of them pull
against each other:

- **"It is mostly better to skip a stroke than adding a non-existing stroke."**
- **"Often better to exaggerate the movement than to be completely true to the position"** — do
  not be literal about small on-screen motion.
- **Blowjobs:** "Short strokes (10-20%) are appropriate when the girl only works the head";
  "blowjobs can often benefit from short, but slow, strokes". This is the stated exception to
  "avoid strokes less than 20% in general".
- **Blowjobs, lateral motion:** "switch up/down direction when she reaches the left or right and
  circles back with her tongue. That creates constant movement even if she isn't really moving up
  and down."
- **Riding/cowgirl:** scenes where she moves toward the camera going up "can easily feel out of
  sync due to difficult angles" — trust the depth cue over apparent screen position.
- **Be true to the 0-100 range**, i.e. absolute position should mean actual depth.

The tension is between *exaggerate* and *be true to depth*. Resolution used here: **exaggerate the
motion so a small bob is felt, but do not fake depth that is not on screen.** Everything derived
so far normalises its proxy to the full 0–100, which is the exaggeration side of that trade and
correct for scenes with real depth variation (`ambient_gooper_bed_blowjob`'s shaft area varies 3×,
`Dragon_Cum` goes fully seated). It is *arguable* for head-only work — see TODO.

---

## 39. The gooper scene was inverted — a shaft *through* a body reverses the rule

Caught on review, not by any tool. §37 derived `ambient_gooper_bed_blowjob` from the shaft visible
against the slime and mapped **more showing = withdrawn**, which is the rule for every other scene
in this set. It is the wrong rule here.

**The shaft passes through the slime body.** The gooper is therefore a *sleeve travelling along
the shaft*, not a mouth working its tip, and its main body slides up and down around the base.
That reverses the reading: shaft protruding above the slime means the slime has slid **down to the
base**, which is deep. Bottom-aligned, the frames say it plainly — at frame 0 the shaft is a small
blob seen *through* the translucent slime (riding high, near the tip); by frame 3 it is a column
standing clear above it (slime at the base).

```
exposed shaft px   117  195  305  383  304
was (§37)            0   29   71  100   70     more showing = withdrawn   <- wrong
now                100   71   29    0   30     more showing = at the base = deep
```

**The sweep reported +1.000 before and after.** It measures agreement between script and proxy and
cannot see the proxy's sign, so a consistently inverted pair scores perfectly. Every correlation
in §35–§38 carries that caveat: *r validates consistency, never orientation.* Orientation is a
statement about what is happening in the scene, and only looking settles it.

**The general rule, for the next tentacle or slime:** where something *engulfs* the tip, exposed
shaft means withdrawn. Where something is *penetrated through* and rides the shaft, exposed shaft
above it means it has travelled to the base, which means deep. Ask which of the two a scene is
before assigning a sign.

`proxies.gooper_shaft` now negates its output and says why, so the registry carries the reasoning
rather than a bare number. Regenerated; `handy1` re-emitted.

Also worth recording as a process note: the first attempt at this fix silently did nothing. A
text replacement anchored on `out.append(float(m.sum()))` plus the following `OVERRIDE = {` matched
neither function, because `dragon_shaft` sits between them — and a no-op replacement reports
success. The mistake surfaced only because the printed positions were unchanged. **Assert on the
value you expect after a scripted edit**; the rewrite added `assert Pos[0] == 100 and Pos[3] == 0`.

---

## 40. Step 4 — the three scenes authored from cues

No proxy finds these; each came from the feel pass as a statement about how it should feel.
`code/authored.py` holds the curves with the frame evidence and the cue that produced each, so
they are reproducible and arguable rather than an unexplained edit to a JSON file.

**`Baphomet_Start`** — *vibrate near the top while she wraps her tongue round it, rather than
following her head; then refocus on her head as she goes down and takes it in one go.*

The frames back the cue exactly: 0–1 approaching in darkness, **2–10 (250–1250 ms) the tongue is
visibly coiled around the shaft while her head stays put**, 11 the mouth opens, 11–14 (to 1750 ms)
she descends in one motion, 15–19 held at the base. There is no head motion to follow during the
tongue phase, which is why the old curve's 100/50/100 wander had nothing behind it.

The guide prescribes this case directly — *"switch up/down direction when she reaches the left or
right and circles back with her tongue; that creates constant movement even if she isn't really
moving up and down"* — so the tongue phase is a shallow 70↔100 oscillation and the descent is one
clean 100→0 over 375 ms (267 u/s, inside even a Handy 1). Ends at 0, held. `Baphomet_Loop` starts
at 0, so that is also the right handoff, and Edi's loop fixup turns the open seam into a 750 ms
pull-off at 133 u/s rather than a jump.

**`Baphomet_Cum`** — *the stroker travels far up for no apparent reason; reduce that excursion.*

Confirmed from the frames: **her face never leaves the base for the whole clip.** Signed
displacement stays within ±33 through frames 0–13, is exactly 0.00 for 14–16, then goes large
negative for 17–19 — which is the scene *fading out*, not anyone moving. The old climb to 100 at
366 ms was invented. Rewritten as what it is: locked deep and pulsing, 0↔35 every 125 ms while
there is motion, still from 1750 ms. Peak 35 instead of 100 is the excursion reduction.

**`Gravy_Loop2`** — *would benefit from some bounce at the bottom.*

Measured first, and the shape was wrong too. The pale shaft below her is visible in only frames
1–3 (904, 725, 259 px) and hidden in 0 and 4–6, so **she is seated for over half the cycle**: up
fast on frame 1, down through 2–3, then a 444 ms bottom dwell. The old curve peaked at 248 ms
against an animation peaking at 111 ms. The bounce goes in the dwell — 0→25→0 at 111 ms, small and
quick so it reads as impact rather than a second stroke. It is an authored addition (nothing in
the sprites rebounds), but bottoming out is a real event and the dwell was otherwise empty.

### Two tooling additions

`proxies.py` gained `gravy_shaft` (the scene now reads **+0.98**, the 0.02 being exactly the
authored bounce) and an **`AUTHORED`** set. `Baphomet_Start` and `Baphomet_Cum` depart from any
proxy *by construction* — the first is scripted as a vibration instead of head position — so a
correlation is meaningless for them. The sweep prints `auth` and no `r`, rather than a low number
someone later reads as a defect.

Step 4 is complete. Six of the eight funscript-plan steps are done; what remains is cleanup
(step 5) and the six scenes needing a 6–27% retime decision.

---

## 41. Step 5 — `Plantasha_Loop` dropped

A gallery entry for an animator state that does not exist. Verified from the assets before
touching anything, since two premises in this session turned out to be wrong on inspection —
every Plantasha controller in the game:

```
Plantasha_GrabScreen:       PlanticaCum, PlanticaGrab
PlantashaAlt_GrabScreen:    PlanticaCum, PlanticaGrab
Gallery_Plantasha_Grabbed:  Cum, CumAlt1, Start, StartAlt1
```

No Loop state anywhere. The only `loop` states belong to `PlantBJGallery` and
`Plantasha Peephole Animator` — the peephole, which used to resolve onto this row through the
greedy alias matcher (§29's defect 1) and now goes to `peek_plant_bj` via `PeekClipMap`. The slug
harness agrees: no reachable state resolved to it.

Removed: the `Definitions.csv` row and `plantasha_loop.funscript` from both variants in both
trees, and the `GalleryRegistry` seed entry. The gallery is now **59 rows / 59 files**.

**The five aliases were repointed to `Plantasha_Start`, not deleted** — `plantasha_loop`,
`plantasha_loop_alt`, `plantasha_plantasha_grab_loop`, `plantasha_plantasha_grab_loop_alt`,
`plantasha_plantasha_loop`. Deleting them would turn a stray slug into an `[ALIAS-GAP]` playing
nothing; pointing them at the start scene means an unforeseen path still plays something sensible.

Rebuilt and deployed to both trees (three matching md5s). `Plantasha_Loop` no longer appears in
the binary at all. Harness 131/131 with 0 UNMAPPED; the script itself remains archived in
`Edi/_reference/source-scripts/shared_plantasha.funscript`.

Step 5 done. The funscript plan is complete apart from the six scenes awaiting a feel call.

---

## 42. Grab locks stopped depending on where you were standing

Bug #13's horny half, and the last of the three bugs the 2026-08-17 logs exposed.

`AddLockForFirstScene` refused a lock whenever `SeenSceneSources` already held the key, and
`BuildSceneKey` is `scene|kind|name|x,y,z` with the position **rounded to 0.1 m**. So the guard
never meant "one lock per enemy" — it meant **one lock per enemy per square decimetre**:

| | behaviour |
|---|---|
| walking enemy, new spot | lock granted |
| walking enemy, spot it used before | **refused** — observed as `scene REPEAT grab Gargoyle Alt` |
| mimic chest (never moves) | exactly one lock per run, ever |

No reading of the design produces that. It is an accident of geometry, and it is why a mimic
"stopped raising horny" while nuns and zombies appeared fine — they were simply being caught
somewhere new most of the time.

**Grabs now lock on every entry.** `AddLockForFirstScene` takes `oncePerSource`, and
`NoteGrabSceneTriggered` passes `HeatLockOncePerGrabSource` (default **false**). The old
behaviour is still reachable by setting it true, per the working practice, though it is a bug
rather than a preference.

**Peepholes and dioramas keep the guard.** Those are passive and would otherwise be farmable by
walking back and forth past one, which is the thing it exists to prevent.

Only the success path used to log, so a refusal was silent — which is why this survived so long.
`scene REPEAT ... (key already seen: ...)` now names the colliding key.

---

## 43. `HeatLockUnitsPerLock` 10 → 20

Reported 2026-08-17: the high-capacity classes end up with far too many locks to work through.

The setting already existed — `GetTotalLocks()` is `floor(scalingStat / HeatLockUnitsPerLock)`
— so this is a default change, not a new mechanic. What was missing was any statement of what
the number actually produces, because the divisor is applied to the **final** heat capacity.
`RecordBaseHeat` runs after the class's own `heatCapacityMultiplier`/`bonusHeatCapacity` *and*
after our `ClassHeatMultipliers` (shipped as `Knight=2;Rogue=2;Mage=2;Ranger=2;Dent Head=2`),
so the input to the division ranges over 100–250, not 100.

Class stats read straight out of the `PlayerClass` assets (`heatCapacityMultiplier`,
`bonusHeatCapacity`; MonoBehaviour raw-byte parse, per `code/README.md`):

| class | vanilla heat | with the shipped ×2 | locks @10 | locks @20 |
|---|---|---|---|---|
| Knight (asset `Warrior`) | 50 | 100 | 10 | **5** |
| Rogue | 75 | 150 | 15 | **8** |
| Dent Head | 100 | 200 | 20 | **10** |
| Mage | 125 | 250 | 25 | **13** |
| Ranger | 125 | 250 | 25 | **13** |

Rogue's 150 is confirmed against the 2026-08-17 log (`heat=82.4/150.0 locks=8/15`), which is
what validates the asset parse rather than just the arithmetic.

**Verified in game 2026-08-17**: the 14:46 run on a Rogue read `locks=1/8` … `-> 8/8`, i.e.
ceil(150/20) = 8, exactly as the table predicts.

The old comment claimed "both stats sit at 100 by default, so either source gives 10 locks".
That was true of the *bare* stats and false of every class actually in the game — the shipped
multipliers alone make it wrong for all five. Replaced with what the division really sees.

20 roughly halves every class from the old behaviour. `HeatLockUnitsPerLock = 10` restores the
previous feel; the setting is an int, so anything in between is available.

### The division now rounds up

`Mathf.FloorToInt` → `Mathf.CeilToInt`, so a capacity that is not a whole multiple of the
divisor keeps its partial lock (Rogue 150/20 = 7.5 → **8**, not 7; Mage/Ranger 12.5 → **13**).

The reason to prefer it is structural rather than cosmetic. `GetTotalLocks` ends in
`Mathf.Max(1, ...)`, and under flooring that clamp was **load-bearing** — it was the only thing
standing between a divisor larger than the smallest class capacity and a horny limit of zero.
A clamp doing real work is a clamp hiding the case it covers. Under ceiling the expression can
only reach 0 for a non-positive capacity, which neither scaling source can produce, so the `Max`
becomes a genuine backstop and the setting has no upper bound that breaks it.

**It does not move where the locks sit**, only how many there are.
`TryGetLockedHeatRange` computes the floor as `MaxHeat * _locks / totalLocks` — a proportion of
capacity, not `_locks * HeatLockUnitsPerLock` — so the final lock lands exactly at full whatever
the count. An earlier note in this session claiming the floor climbs in fixed steps of the
divisor, and therefore tops out below the bar on classes that do not divide evenly, was wrong.

---

## 44. Mimics: an interaction the game refuses no longer kills the chest

Bug #13's remaining half, and **the distance hypothesis was wrong**. TODO predicted
`dist=2.05 range=2.00 inRange=False`. The 13:59 log says otherwise on all 18 gate lines:

```
[MIMIC-GATE] 'Weapons Mimic(Clone)' dist=1.94 range=3.00 inRange=True ...
```

`range=3.00` (this is the Weapons Mimic), distances 1.77–2.67, `inRange=True` throughout. The
player was never out of reach and `GRAB-RESTORE` positioning is fine. Delete that theory.

### What actually happens

`MimicEnemy.TriggerMimicGrab`, from the assembly:

```cs
if (hasTriggeredGrab || grabScreen == null) return;
if (grabScreen.IsGrabbed) return;      // its ONLY refusal check
hasTriggeredGrab = true;               // burnt unconditionally
PlaySound(revealSound); Instantiate(revealEffect);
grabScreen.StartGrab(...);             // ALSO checks CanBeGrabbed, and bails
Destroy(gameObject);
```

The mimic and the method it calls **disagree about what refuses a grab**. `StartGrab` opens
`if (isGrabbed) return; if (playerStats == null || !playerStats.CanBeGrabbed) return;`, so
during post-grab immunity the mimic burns its one-shot flag, plays its reveal, and `StartGrab`
silently does nothing. Caught in one press 0.9 s after escaping the previous mimic scene:

```
13:58:14.212 [ENEMY-WAKE] re-armed mimic Weapons Mimic
13:58:14.532 [MIMIC-GATE] hasTriggeredGrab=False enabled=True   <- armed, E pressed
13:58:14.533 [GRAB-START] ignored: game declined the grab
13:58:14.784 [MIMIC-GATE] hasTriggeredGrab=True  enabled=True   <- burnt, no scene ran
             ... True for the rest of the run
```

Vanilla survives this because `Destroy(gameObject)` still runs — the chest vanishes, which is
its own bug but not an inert one. `KeepEnemiesAfterGrab` blocks that destroy, so the chest
stands there with the flag latched and `MimicEnemy.Update` gates on `!hasTriggeredGrab`
forever. `EnemyReactivationHelper.RearmMimic` is the only thing that clears it and it runs off
a **scene end**, which never came.

Third instance of PROJECT.md's §19 pattern — blocking a vanilla `Destroy` leaves one-shot state
latched — and the first to reach it without producing a scene at all, which is exactly why
nothing in the re-arm path could see it.

### The window is structural

`StabilizeAfterGrabEnd` applies the immunity *and* schedules the reactivation that re-arms the
mimic. The re-arm lands ~0.6 s in; the immunity runs ~1 s. So there is always a stretch where
the chest is armed and the game will still refuse. That matches the report exactly — with other
enemies around you never press E that fast, alone with the chest you do.

**Note the ~1 s.** Vanilla's `GrabScreen.GrabImmunity` is
`CanBeGrabbed = false; yield WaitForSeconds(1f); CanBeGrabbed = true`. Our
`EndGrabImmunitySeconds = 4` starts a *second*, longer coroutine, but vanilla's fires at T+1
and sets the flag back to true, cutting ours short. The log shows all three cases: refused at
0.76 s and 0.90 s, allowed at 1.25 s. **`EndGrabImmunitySeconds` above 1 does nothing** unless
vanilla's coroutine is also handled — not addressed here, but worth knowing before tuning it.

### Fix

`MimicGrabGate.TriggerMimicGrab_Prefix` refuses the interaction on exactly the condition
`StartGrab` would have refused it on, *before* the flag is burnt. To the player it is a no-op:
no reveal sound, no effect, no destroy — the chest is simply not interactable for the last
fraction of a second of immunity, and the next press works. `MimicGrabRespectsGrabImmunity`
(default true) restores the old behaviour.

Same family as §16 and §31, and the same lesson each time: **when the mod keeps something alive
that vanilla deletes, every early-out in the caller becomes a state leak.**

### Backstop

`Update_Postfix` re-arms any mimic that has sat with the flag set for
`MimicStrandedRearmSeconds` (default 3) while no scene is running — cover for any other route
that burns it without a scene, such as a throwing `StartGrab`, which skips the `Destroy` the
same way. It cannot fire mid-scene, because `NearbyEnemyHider` has the object hidden and the
component disabled then, so `Update` does not run at all.

The delay is the point rather than an implementation detail: `RearmMimic` runs off the
reactivation, which applies the grab-end cooldown deliberately, so clearing the flag the instant
a scene ends would let a mimic be re-used sooner than intended. Three seconds means the ordinary
re-arm always wins and this only ever rescues a chest nothing else was going to. Set 0 to
disable.

---

## 45. Mimics re-arm instantly instead of waiting on the enemy reactivation delay

`ScheduleReactivate` defers `Reactivate` by `EnemyReactivationDelaySeconds` (5), and
`RearmMimic` — the only thing that clears `hasTriggeredGrab` — runs **inside** `Reactivate`. So
a chest stayed inert for five seconds after its own scene.

The delay exists so an enemy cannot resume its AI the instant a scene ends and re-grab the
player before they can move. **A mimic has no AI to resume.** It is a chest that reads the
interact key in its own `Update`, and interacting with it is entirely voluntary, so there is
nothing for the delay to protect against. `MimicReactivateInstantly` (default true) short-
circuits both `ScheduleReactivate` and `ScheduleRespawn` for anything carrying a `MimicEnemy`.

**The delay was never what decided when a mimic came back, either.** In the 13:59 log the
re-arm lands 0.6 s after a scene end, not 5 s — because the player swung a weapon and hit the
attack-triggered reactivation path (`reactivated 1 enemy object(s) (player attack)`). The real
rule was "whenever you next attack something, or five seconds, whichever comes first", which
nobody designed and which is impossible to reason about from the outside. Instant is a rule.

### This makes §44 load-bearing rather than redundant

The tempting read is that removing the cooldown removes the bug, since the chest can no longer
be interacted with "during cooldown". It is the other way round. The re-arm and the player's
grab immunity are **independent clocks**:

| | before | after |
|---|---|---|
| chest armed at | scene end + 0.6–5 s | scene end + 0 |
| `CanBeGrabbed` true at | scene end + ~1 s | scene end + ~1 s |
| window where a press burns the flag | ~0.4 s (or none) | **the full ~1 s** |

Arming the chest sooner widens the overlap it can be destroyed in. §44's prefix is the only
thing coupling the two clocks, and without it this change would make bug #13 *easier* to hit,
not harder. Shipped together deliberately.

The 14:46 log settles it: **5 refusals** in one session of hammering E at a chest right after
escaping, each followed by a working grab a beat later, `hasTriggeredGrab=False` on every gate
line, and eight consecutive re-interacts without losing the mimic. Under §45 alone every one of
those five would have killed it.

### Addendum: the log line was lying

`ScheduleReactivate` is called three times for the same mimic in the same frame — the grab-end
restore, `NearbyEnemyHider`'s reveal, and the attack-triggered wake all converge there. The
`Pending` dictionary used to absorb that (later calls updated the entry instead of logging), and
short-circuiting above it lost the dedup: **41 `instant re-arm` lines for 12 actual re-arms.**

`Reactivate` is idempotent so the repeats did nothing, but this is the line the change gets
verified *by*, and one claiming a re-arm that did not happen is worse than no line at all.
`ReactivateMimicNow` now checks whether the object was inactive, the component disabled, or the
flag set, and reports only then. **A dedup you bypass is a dedup you have to reimplement** —
short-circuiting a path skips everything downstream of it, not just the part you were avoiding.

---

## 46. A state the state machine cannot leave — Plantasha, and the same trap everywhere else (#14)

Diagnosed from one `SpinAiDiag` dump. Three samples at +1.5 s, +6 s and +12 s after the grab
end, byte-identical:

```
[SPIN-AI] auto 'Plantasha_Enemy ALT1' state=Grabbing active=True enabled=True dist=2.5 (grab=2.5)
[SPIN-AI]     coroutines spin=null grab=null shoot=null flash=null
[SPIN-AI]     flags isDead=f isAttemptingGrab=f ... spinMovementActive=f
[SPIN-AI]     gates CanSpin=True CanGrab=True CanShoot=True HasLineOfSight=True
```

**Every gate open, nothing latched, no coroutine running — and she does nothing.** That rules
out the entire §17b family in one line, which is exactly what the instrumentation was for: the
static pass had already eliminated all seven candidates and this confirms none of them was it.

### The state itself is the trap

```cs
UpdateStateMachine() {
    switch (currentState) {
        case Idle:     HandleIdleState(d);     break;
        case Spinning: HandleSpinningState(d); break;
        case Grabbing: case Shooting: case Dead: break;   // <- NO HANDLER
    }
}
```

Grabbing, Shooting and Dead jump straight to `ret`. Escaping Grabbing depends **entirely** on
`GrabSequence`'s tail calling `TransitionToSpinning`/`TransitionToIdle`. There is no other exit.

And the state is committed before anything guarantees that coroutine exists:

```cs
TransitionToGrabbing() {
    currentState = Grabbing;    // committed FIRST
    StopSpin(); StopShooting();
    StartGrab();                // may do nothing at all
}
StartGrab() {
    if (grabCoroutine != null) return;   // three early-outs, each leaving
    if (!canGrab) return;                // currentState == Grabbing with no
    if (grabScreen == null) return;      // coroutine to ever transition out
    ...
}
```

So **any `TransitionToGrabbing` whose `StartGrab` early-outs strands the enemy permanently.**
Vanilla reaches it from `HandleIdleState` the moment the player stands at exactly `grabRange`
(2.5 here — and the dump reads `dist=2.5`) while a previous `GrabSequence` is still winding
down. `TransitionToShooting` is byte-for-byte the same shape, so Shooting strands identically.

**The mod widens the window rather than causing it.** `ResumeAiBehaviour` calls vanilla's
`ResumeAIBehavior` on every reactivation, which re-runs that same distance test immediately
after a scene, with the player standing right where the enemy just released them. That is why it
presents as "she goes inert after a grab" instead of as a rare vanilla hang — and it fits the
report exactly: *out of a grab, then dodging a grab, or getting hit during the immunity window*.

### Made universal: audited all six AI classes

The obvious follow-up — *does this hit every enemy that grabs during the immunity window?* — has
two separate answers, and both needed the whole assembly checked rather than assumed.

**Stranding: two classes of six.** Only these have non-`Dead` states with no case in their
`UpdateStateMachine` switch:

| class | states | unhandled |
|---|---|---|
| `EnemyAI` | Idle Chasing Attacking Grabbing Dead | Dead only |
| **`ChargingEnemyAI`** | Idle Chasing PreparingCharge Charging Dead | **PreparingCharge, Charging** |
| `ProjectileEnemyAI` | Idle Chasing Retreating Shooting Dead | Dead only |
| **`SpinningEnemyAI`** | Idle Spinning Grabbing Shooting Dead | **Grabbing, Shooting** |
| `DragonEnemyAI` | Idle Chasing Attacking Grabbing Dead | Dead only |
| `ProximityDragonEnemyAI` | Idle Chasing Attacking Grabbing Dead | Dead only |

`ChargingEnemyAI` has the identical commit-before-start shape —
`TransitionToCharging() { currentState = Charging; StopPathfinding(); StartCharge(); }` over a
`StartCharge` with two early-outs — and `PreparingCharge` is assigned from inside
`ChargeSequence`, so one handle (`chargeCoroutine`) drives both. The other four handle every
state they can enter and recover on their own, so they are deliberately **not** patched.

**Refused grabs: a second, worse defect, in the dragons.** Auditing every
`GrabScreen.StartGrab` call site in the assembly:

| caller | behaviour on refusal |
|---|---|
| `EnemyAI.HandleGrabHit` / `.OnPlayerGrabDetected` | `if (!grabScreen.IsGrabbed) return;` — correct |
| `SpinningEnemyAI.HandleGrabHit` | same — correct |
| `ProjectileEnemyAI.OnGrabProjectileHitPlayer` | same — correct |
| **`DragonEnemyAI` / `ProximityDragonEnemyAI`** `.HandleGrabHit`, `.OnPlayerGrabDetected` | **no check at all** |
| `MimicEnemy.TriggerMimicGrab` | no check — §44 |
| `GrappleScreenobject.TriggerTrioGrabOverflow` | not an enemy path, left alone |

The dragons burn `hasTriggeredDragonGrab`, call `ModifyGrabForDragon()`, stop `grabCoroutine`
unconditionally and then call `RemoveEnemyAfterGrab()` — **a grab refused during immunity
removes the dragon from the level with no scene ever playing.** Same family as the mimic, never
reported only because nobody had hit that window against a dragon.

### Fix: gate the cause, watch the invariant

**`EnemyGrabGate`** stops an enemy committing to a grab the game is about to refuse, testing
exactly what `StartGrab` tests on the same objects. **It patches the two dragon classes only**,
and that restriction is the important part — see below. `MimicGrabGate` calls into the same
predicate rather than keeping a second copy, per the standing rule that a shared decision needs
one writer. `EnemyGrabRespectsGrabImmunity`, default true.

**`AiStateGuard`** watches the invariant — *in a coroutine-driven state with no coroutine* — for
the two vulnerable classes, and returns the enemy to Idle, which is self-recovering.
`AiUnstickSeconds`, default 0.5, 0 disables.

### Side-effect review — one of these fixes was wrong first

The first version gated all eight enemy grab entry points. That was a bug, caught by reading
what vanilla's refused-grab path actually does in the four classes that handle it:

```cs
hasGrabbedThisAttempt = true;    // this swing is spent
grabInDamagingState = false;     // stop testing for the rest of the window
StartGrab(...);
if (!grabScreen.IsGrabbed) return;
```

**Those two assignments are what make a refused grab whiff.** Gating the method skips them, so
the enemy would have kept testing every frame and connected the instant immunity lapsed — escape
a grab, get re-grabbed by the same enemy a second later, mid-swing. A fix for a hang that
silently made the game harder. `EnemyAI`, `SpinningEnemyAI` and `ProjectileEnemyAI` have no bug
here, so they are now left alone; the dragons pay that same cost but their alternative is being
deleted from the level.

Everything else checked, and why each is safe:

| risk | finding |
|---|---|
| `HandleGrabHit` does more than grab | No. All four open `if (!grabInDamagingState) return; if (hasGrabbedThisAttempt) return; if (!canGrab) return; if (player == null) return;` — pure grab detection, no damage, no cleanup |
| `OnPlayerGrabDetected` is a grab-screen callback | No. It comes from `EnemyGrabDetector`/`DragonGrabDetector` `OnTriggerEnter`/**`OnTriggerStay`** — declining just retries next frame once immunity lifts |
| blocking leaks the grab projectile | No. `DestroyProjectile` is called by `GrabProjectile` itself, not by the enemy's callback |
| guard fires mid-charge | No. `chargeCoroutine` stays non-null through `ExecuteCharge` (started untracked, `pop`); its tail nulls the handle **and** moves the state in the same frame. `ShootSequence` and `GrabSequence` likewise. The 0.5 s grace covers that seam |
| guard fires while the AI is legitimately paused | Was possible. `Update` pauses on `IsPlayerGrabbedByGrabScreen() \|\| CinematicCameraSwapTrigger.IsAnyInCinematicView`, and `PauseAIBehavior` nulls the handles — so a paused enemy looks stranded. The guard now mirrors **both** halves; the cinematic half was missing and would have let a peek scene reset an enemy mid-charge |
| guard can't see a strand behind a stale handle | Covered by the existing reset: `ClearStaleCoroutineHandles` calls `StopCharge`/`StopGrab` on wake, which null the handle (and `isCharging`), after which the guard sees the stranded state |
| per-frame reflection cost | Reordered so a plain `currentState` field read rejects almost every frame before any `Invoke`. `WouldGameRefuseGrab`'s `FindGameObjectWithTag` fallback is now cached — it sat on a path that runs every frame per enemy |
| `TransitionToIdle` has side effects | `StopSpin`/`StopGrab`/`StopShooting` (all null-guarded) and `StopPathfinding`. Idle re-picks a transition next frame |
| dictionaries grow unbounded | Both keyed by instance id, entries removed as soon as the condition clears, and cleared on scene change |

**Both fixes are still needed.** The gate stops the common cause; the guard catches the state
regardless of route, and the routes are many (`HandleIdleState`, `ResumeAIBehavior`, the sequence
tails, our own reactivation) while `TransitionToShooting` and `TransitionToPreparingCharge`
repeat the shape. Fixing only the transition would leave a state the switch still cannot handle.

### These tables will go stale — so they check themselves

Both guards encode facts that exist only in the game's bytecode: which states have no `case`,
which coroutine drives each, which `StartGrab` callers re-test `IsGrabbed`. None is discoverable
at runtime, so both are hardcoded, and a game update invalidates them **silently** — a renamed
private field makes `AccessTools.Field` return null, the spec ends up with no stuck states, and
the watchdog runs happily while watching nothing. A silently disabled guard is worse than no
guard, because the bug it covers looks fixed.

`EnemyAiAudit` runs once at startup and prints one line:

- `ok - guard tables match the game assembly`
- `BROKEN: SpinningEnemyAI.grabCoroutine no longer exists` — reflection drift, guard is dead
- `BROKEN: … AIState value 2 is now 'X', expected 'Grabbing'` — the enum was reordered. The table
  is keyed on the raw int, so this repoints it while every name still resolves; the sneakiest of
  the three and invisible to a name-based check
- `GAP: <Type> can start a grab and was not in the §46 audit` — new class with a `GrabScreen`
  field; read its call site
- `GAP: <Type> runs its own state machine …` — new class with a `currentState` enum; read its
  `UpdateStateMachine`

The type heuristics are deliberately broad and over-report: a false positive costs one log line,
a false negative costs another three sessions of hunting. What the audit **cannot** see is a
`case` appearing or disappearing in a `switch` — that is IL, not reflection — so `code/README.md`
carries the two commands that redo the audit by hand, and a release that changes enemy behaviour
warrants running them whatever the audit says.

### Verified in game, 15:29–15:36

| what | evidence |
|---|---|
| `AiStateGuard` recovers Plantasha | **5× `unstuck 'Plantasha_Enemy' (SpinningEnemyAI): state=Grabbing`**, and she stayed playable throughout |
| `ChargingEnemyAI` (imps) fine | no strands logged, imps behaved |
| `EnemyGrabGate` scope correct | **11 refusals, every one `'Dragon'`** — the tag never named anything else |
| dragons survive a refused grab | the same dragon grabbed again at 15:34:07 and 15:34:27; never removed |
| full-lock cum (§15) | **12× `full lock -> holding the cum animation`**, each followed by `OnMaxHeatAnimationComplete fired (fullLock=True)`; `no cum state captured` never appeared |
| lock counts (§43) | correct |

**The guard turned out to be the primary fix for this path, not a backstop** — five recoveries in
one session, and without it she would have gone inert five times.

**The mechanism is not yet fully known, and one wrong explanation is recorded here so it is not
repeated.** The first reading of the log blamed *another* enemy's scene interrupting hers: her
`Update` pauses at `IsPlayerGrabbedByGrabScreen()`, `PauseAIBehavior` nulls the handles, and
`ResumeAIBehavior`'s if/else chain has no final `else`, so a distance matching none of its four
branches leaves the state untouched. That chain really does have no `else` — but it is not what
happened. The log says otherwise on two counts:

- **It is the same Plantasha, her own scene, every time.** `SCENE-HIDE hid 1` / `SCENE-SHOW
  revealed 1` with no `[SPAWN]` or `[ENEMY-REVIVE]` in the stretch, and `[GRAB-ANIM] … t=3.29`,
  `t=1.25`, `t=2.88` — a nonzero normalized animator time means the animator was never rebound,
  so it is the same component on the same object. A fresh spawn reads `t=0.00`.
- **The strand lands 0.504 s after `[ENEMY-WAKE] reactivated`, on all five.** That is exactly the
  grace period, so the enemy is stranded the instant the reactivation runs. The dragon's
  `[GRAB-GATE]` lines interleave only because it was swinging throughout.

So the trigger is our own wake path: `ReactivateComponent` sets `currentState = Idle`, then
`ResumeAiBehaviour` runs vanilla's `ResumeAIBehavior`, which finds the player inside `grabRange`
(they are restored about a metre away) and calls `TransitionToGrabbing` — which commits the state
and then calls `StartGrab`, whose three early-outs decide whether anything actually starts.
**Which early-out fires is still unknown**; deriving it from the disassembly failed twice, so
`SpinAiDiag` now carries a postfix on `TransitionToGrabbing` that reports the three conditions
whenever it leaves no coroutine behind (`SPIN-AI STRAND …`).

This does not change the fix. The guard covers the invariant regardless of cause, which is the
whole reason it was written that way — but the underlying strand is worth removing at source,
because 0.5 s of standing still is a visible hitch even when it recovers.

### The audit found two false positives, as designed

First run reported `DualWieldingSystem` and `AutoDoor`. Both are third-party library classes —
`PixelCrushers.GridController.DualWieldingSystem` holds a `GrabScreen` reference but never calls
`StartGrab`, and `DunGen.Demo.AutoDoor` is a door with a state enum. They looked like game code
because the message printed `Type.Name`, which drops the namespace.

Filtered on `t.Namespace != null`: every class the game defines is in the global namespace, and
everything namespaced is a vendored asset. Messages now print `FullName` so a future hit is
unambiguous. The over-reporting was the intended trade — it cost two log lines and one check.

### `SpinAiDiag` earns its keep

Seven candidates eliminated by reading, all correctly — and the actual cause was in none of them,
because it was not a latched value at all. Dumping *every* gate at once rather than testing
hypotheses one at a time is what turned this from a fourth session of guessing into one run. It
stays in, behind `Debug`, on `SpinAiDumpKey` (F9).

---

## 47. The debug hotkeys, and two objects called the same thing

Started from "what do you mean a Wendigo was gated?" and ended up finding four defects, none of
which was the thing being asked about.

### `[GRAB-GATE]` was reporting saves it never made

Nine lines named `'Wendigo'` in a run where **no Wendigo ever spawned** — the only `[SPAWN]`
lines were plantasha and zombie, and "wendigo hole" in the ambient scans is the peephole's audio
source. There is a Wendigo parked in the level with its AI ticking, waiting for its trigger time.

The gate's prefix sits in front of `HandleGrabHit`, whose own first line is
`if (!grabInDamagingState) return;`. So it fired on every frame that method was *called*, whether
or not the enemy was attempting anything. Every one of the nine was a false alarm. The gate now
requires `grabInDamagingState`, which is also the only window where blocking does anything:
outside it the original returns immediately anyway. `OnPlayerGrabDetected` keeps the unconditional
check — it is trigger-driven and already opens with `if (grabCoroutine == null) return;`.

**A log line that claims a save it did not make is worse than no line**, because it is the line
the change gets judged by.

### Two rooms, one object name — and the mod was already right

The Baphomet/Gravy attribution took two wrong turns before landing:

| room | object | component | animator | who | effect |
|---|---|---|---|---|---|
| **Shop** | `GloryHoleCamera` | `HealingCameraSwapTrigger` | `Minotaur` | **Gravy** | heals to full |
| **Jail** | `GloryHoleCamera` | `TrapCameraSwapTrigger` | `BJ Animator` / `Baph Sex Animator` | **Baphomet** | a trap |

Same object name, different characters. A `Baphomet Statue` stands in the Shop too, which is what
made "the healing hole is Baphomet's" look obvious — it is scenery. The statue's real job is in
the **Choice room**, where it is a `ChoiceItemPedestal`: `SpawnItems()` → you take one →
`PlayLaughAnimation()` → `ResetPedestal()`. Her animator has exactly two states, `Idle` and
`Laugh`, so the "she turns red like an enemy grabbing" reaction is complete as designed. The red
is the pedestal writing `outlineAlpha` — the same `_OutlineAlpha` property enemies use for their
highlight. Nothing broken, just a shared shader.

**`CameraSwapHooks` had this right all along**, and the reason is worth keeping: it explicitly
refuses to resolve by object name when the name contains `camera`/`gloryhole`/`trigger`, and reads
the live animator's **clip names** instead, testing `minotaur|gravy` before `baph`. Shop clips are
`Minotaur_*` → `gravy`; Jail clips are `Start/Middle/Cum/Fade` and `StartSex/SexMiddle/SexCum`,
carrying no character name at all → falls through to the explicit `gloryholecamera_*` aliases.
Both play the right scripts. **An object's name is not its identity; what it drives is.**

### `SpawnChestTrapKey` aimed at something that does not exist

There is **no mimic chest in the game**. `MimicEnemy` has exactly two instances (`Mimic`,
`Weapons Mimic`, both on the `M` key), and the only `TrapCameraSwapTrigger` in the entire game is
the Jail glory hole. The key's hint (`chest|trap|truhe|…`) matched loot containers and six
`Gas Trap`s instead.

It was broken three ways at once, each hiding the next:

1. **Keycode 223.** Unity's `KeyCode` enum has no members between 128 and 255 — ASCII to `Delete`
   (127), then `Keypad0` (256). Read out of `UnityEngine.CoreModule.dll` to be sure. The binding
   could never fire, so nobody ever saw defects 2 and 3.
2. **A hint that could not match.** `ScoreInteractiveTemplate` opens `if (!flag) return 0;`, and
   `flag` needs the hint to match the object name or its clip names. `GloryHoleCamera` contains
   neither `chest` nor `trap`; its clips are `Start/Middle/Cum/Fade`. Score 0, finds nothing.
3. **A fallback that would spawn junk.** `InteractiveFirst = true` meant a miss fell through to
   the name hint and would have cloned a `Common Chest` or a `Gas Trap`. It also swallowed the
   failure log: every `!interactiveFirst` guard skipped and it returned null silently.

Renamed to `SpawnGloryHoleTrapKey` (`Minus`), hint `gloryhole|glory hole|glory`, and switched to
`InteractiveOnly` so a miss reports instead of returning quietly. The selector now **requires**
`TrapCameraSwapTrigger`, which is what separates the Jail trap from the Shop's identically-named
healing trigger.

### Debug hotkeys did nothing while you were moving

Not intermittent, as reported — deterministic. BepInEx's `KeyboardShortcut.IsDown()` is
`GetKeyDown(MainKey) && ModifierKeyTest()`, and `ModifierKeyTest` builds
`modifierBlockKeyCodes` = every supported KeyCode **except the shortcut's own**, then requires
that none is held. Correct for a UI shortcut, wrong for a debug tool: walking means `W` is down,
so the key is dead exactly when you want it.

`Hotkeys.IsDown` keeps explicit modifiers and drops that rule — but **only for non-modifier
keys**. The first version dropped it entirely, which would have made `Ctrl+1` fire both
`FillerOnKey` (`Alpha1 + LeftControl`) and `SpawnZombieKey` (`Alpha1`). Held modifiers the
shortcut did not ask for still block. `DebugHotkeysIgnoreHeldKeys`, default true.

### `[KEYBIND]` audit

The 128–255 hole is invisible: a dead binding behaves exactly like a feature nobody implemented.
`Hotkeys.AuditBindings` reflects over every `ConfigEntry<KeyboardShortcut>` on `Plugin` at startup
and reports any main key in that range. Same principle as `[ALIAS-GAP]` and `[AI-AUDIT]` — the
gap has to announce itself.

---

## 48. The last six scenes — and only two of them were the problem they were filed as

The six scenes `retime.py` reported and refused had been carried since §34 as "needs a feel
pass: is each one too fast or too slow?". Pulling the frames replaced that question for four of
them. **Timing is now 51/51 `ok` — the whole set is whole-cycle exact for the first time.**

| scene | filed as | what the frames say | now |
|---|---|---|---|
| `Nun_Cum` | +27.30% | 300 ms descent, **2.7 s motionless**, 300 ms lift | 3300, r +0.90 |
| `Gooper_Cum` | +15.93% | two **unequal** strokes, 800 then 600 ms, + a 100 ms tail | 1500, r +1.00 |
| `Gooper_Start` | −14.75% | 800 ms cycle; the script holds **2** strokes at 1023 ms | 1600, r +1.00 |
| `Plantasha_Start` | −9.60% | a clean symmetric 1000 ms stroke | 1000, r +1.00 |
| `Plantasha_Cum` | −7.96% | 3.0 s hold + one 875 ms lift peaking at 3250 | 7750, r +0.77 |
| `Wendigo_Start` | +6.23% | 1.3 s dark approach, tongue, then a **1.8 s wipe to black** | 5167, authored |

Curves and evidence in `code/rederive.py`; new proxies in `code/proxies.py`.

### A cycle count is not a stroke count

`Gooper_Start` is the one that should have been caught earlier. `retime` computes
`n = round(end / period)`, so 2046 ms against an 800 ms cycle became `round(2.557) = 3` and it
proposed stretching to 2400 — a script that was **already 28% too slow**. The script plainly
contains two strokes (`0→0` at 610, `0→100` at 1007, repeat), so the target is 1600.

This is `imp_1` again (§34b) in a form the rate column could not catch: `imp_1` sat at exactly
11.000 cycles while stroking 1.56× slow, and here the cycle count was fractional *and* misleading.
**Count the script's own strokes before believing a target derived from its length.** The
`s.strk` column even said 678 ms, but that was the median of peak spacings contaminated by a
0→30→0 bounce at the bottom of each stroke — a median over four gaps, two of which were the
bounce.

### Two strokes in one clip need not be the same length

`GooperGrabScreenCum`'s frames 8–13 reproduce frames 0,1,4,5,6,7 exactly — the second stroke
**skips the two mid-descent frames**. So it is 800 ms then 600 ms, and the script's two equal
870 ms strokes cannot be fitted to it by any scale factor. That is why it reported 15.93% off
with no sensible target: there wasn't one. §33 found the mirror image of this in
`imp gangbang 2`, where two strokes hid inside one clip; here two *visible* strokes were assumed
equal because clips usually repeat themselves exactly.

The two Gooper scenes are in fact **one animation used three times**. `GooperGrabScreenCum`'s
first 8 frames carry the identical silhouette sequence to the whole of `GooperGrabScreen` —
212, 210, 206, 198, 193, 189, 203, 211 px in both — redrawn on its own sheet with the cum added.
So the stroke shape lives in one list, `rederive.GOOPER`, and the cum's fast half is that list
indexed `(0,1,4,5,6,7)`. Two scenes that share an animation should share a curve.

### Head-only work gets a band, not the full range

Both Gooper scenes are scripted into **100–50–100** rather than 0–100. The head — the upper blob,
the one with the eyestalks — is the only thing that moves: row by row the silhouette below row ~80
is identical in every frame, and all the variation sits in rows 10–70. It works the tip and
travels no real depth, which is the guide's stated exception to "avoid strokes under 20%"
(*short strokes are right when the girl only works the head*). The first version normalised to the
full range on the "exaggerate rather than be literal" side; 50 is the middle ground, chosen by feel.
`rederive.DEEP` is the single knob.

Halving the range halved the speeds as a side effect — peak 740 → 370 u/s — which takes
`Gooper_Start` out of the `handy1` limiter entirely and leaves `Gooper_Cum` with one clipped
transition instead of three.

**A polarity note worth keeping, because it looks like it should flip and does not.** §39
established that the gooper diorama is a *sleeve*: the shaft passes through the slime, so shaft
showing above it means the slime slid to the base, which is deep — the opposite of a mouth on the
tip. That rule inverts a **shaft-exposure** proxy. It does not touch a **body-position** proxy,
which is what the silhouette top edge is here: the shaft rises from the player at the bottom of
frame either way, so head-low is deep whether she is on the tip or sleeved on it. Same scene
family, same creature, and the §39 inversion still does not apply. Check which quantity a rule is
about before carrying it across.

### A clip can outlast its own frames — and animcheck was right by luck

These two Gooper clips are the only ones of the 51 with **more than one PPtr curve**: a
`Goop_overlay` drip layer animating alongside the body. `clip_frames` takes every `Sprite` in
`pptrCurveMapping` as one sequence, so it should have concatenated body and overlay into a
nonsense 16- or 29-frame animation. It did not, because the overlay's PPtrs carry a `m_FileID`
pointing at another assets file and the lookup dict was keyed on `path_id` alone — so they
resolved to unrelated `Texture2D`s and were filtered out. **The reader was correct because two
bugs cancelled.**

That also explains a number that never added up: `GooperGrabScreenCum` is 14 frames at 10 fps but
reports 1500 ms. `m_StopTime` is set by the *longest* curve, and the overlay runs 15 samples where
the body runs 14 — so the body ends at 1400 and holds its last frame for the final 100 ms. The
clip's loop length really is 1500; its frames just do not fill it.

Both are fixed rather than left to luck:

- `clip_frames` reads `genericBindings` for the PPtr curve count and, when there is more than one,
  cuts at the first frame number that fails to increase within a sheet (`_first_pptr_curve`).
  Names alone cannot do this — `GhoulGrabCum` is a *single* curve whose sprites run
  `Nun Sex CUM-Sheet_1_0..21` then `Nun Sex CUM-Sheet_3_0..10`, and that restart at `_0` is
  indistinguishable from a new curve until you notice a real sequence never counts backwards.
- frame *k* is sampled at `k/fps`, never at `k*dur/n` — `animcheck.frame_times`. Those are the
  same number for 49 of the 51 clips, which is why this was invisible; `Gooper_Cum` went from
  r **+0.82 to +1.00** on that one change alone, and no other scene moved by a digit.

### The static scenes are not static — the buzzes go where she twitches

`Nun_Cum` looked like 2.7 s of nothing: 17 of its 33 frames are byte-for-byte identical. Reading
it as dead would have been wrong. Measuring each frame's distance from the medoid (seated) pose
finds exactly two events inside the hold — a four-frame twitch at 900 ms and a one-frame twitch at
2100 ms — and the old script's three buzz bursts sat at 660, 1574 and 3021 ms, i.e. one roughly
right, one with nothing behind it, and one on top of the lift.

`Plantasha_Cum` has the same shape and settles *why* it matters: its twitches at 750 ms and
2125 ms land on **exactly the frames where new cum appears** (0→12→37→66 px, then
66→92→181→219→243). The twitch is the spurt. The old curve ran 14 evenly spaced pulses through
the whole hold, which is motion the animation never asked for.

**"Bit-identical frames" answers whether the picture changed, not whether the scene did.** A
whole-frame difference is dominated by the descent and the lift; the events inside the hold are
two orders of magnitude smaller and only visible once you difference against a *fixed* reference
pose instead of against the neighbouring frame.

`proxies.nun_cum_motion` picks that reference as the medoid, so it cannot drift to a hardcoded
index — and it carries the warning that a distance is a magnitude, safe here only because she is
seated or above it and never crosses the reference. On a scene that strokes through its own rest
pose it would fold the two halves together.

### A third of `WendigoKiss` is a transition

Measuring the tongue's pixel area against the amount of pure black in frame: the tongue arrives at
1500 ms, peaks at 2333, and from 2500 a wipe eats the picture — by 5000 ms the frame is 129k black
pixels, i.e. all of it. The old script oscillated 100↔40 to 5373 ms, straight through a black
screen. It is now scripted to wind down across the wipe so the handoff to `Wendigo_Continued`
starts from rest, and registered in `proxies.AUTHORED` — a decision about a picture that is no
longer there cannot be validated by correlation against anything.

---

## 49. A config setting in the wrong section is a setting the game never reads

Found by accident: `BepInEx/config/com.edi.pnc.cfg` kept turning up modified with no tool of ours
touching it. Bisecting every script left nothing — because the writer was **the game**. BepInEx
re-serialises the config on startup, and the only launch in days happened mid-session.

What it wrote is the interesting part. `DebugHotkeysIgnoreHeldKeys` came out **twice**: once bare
under `[Gameplay]`, once with its full comment block under `[Tools]`.

```cs
Config.Bind<bool>("Tools", "DebugHotkeysIgnoreHeldKeys", true, "...")   // Plugin.cs
```

```ini
[Gameplay]
DebugHotkeysIgnoreHeldKeys = true      # <- what §47 wrote by hand
```

**BepInEx resolves a setting by (section, key), not by key.** `Bind()` looked under `[Tools]`,
found nothing, took the coded default, and wrote a fresh entry there. The `[Gameplay]` line was
preserved as an orphan — BepInEx keeps unbound entries so a downgrade cannot destroy anyone's
config — and is read by nobody. So since §47 the setting has been **inert**: the file said `true`
and the default is `true`, which is exactly why nothing looked wrong. It would have surfaced the
first time somebody set it to `false` and their debug keys kept dying while they walked.

The cause is structural, not carelessness. `code/README.md` instructs adding new settings to the
config **by hand**, because BepInEx only rewrites the file on a clean run — so there is no
mechanism keeping the hand-written section in step with the `Bind()` call. Both trees had it.

`code/cfgaudit.py` now checks it, and exits non-zero so it can gate a release:

```
136 (section, key) pairs bound in code/edimod/PncEdi
BepInEx/config/com.edi.pnc.cfg: 136 entries
  ok - every entry sits in the section the code binds it to
```

One trap in writing it: **key on the (section, key) pair, not the key.** `Enabled` is legitimately
bound four times — `Ambient`, `Gameplay`, `Imp`, `Interactive` — and `GalleryPrefix` twice, so a
name-keyed audit reports three perfectly good entries as misplaced and buries the one real defect.
The first version did exactly that.

With that fixed, both trees are 136/136 correct and their only remaining difference is the two
documented intentional ones (`EndGrabDelaySeconds` 15→30, `ShowHeatBarDuringGrab` true→false).

**A config file is not self-validating, and a wrong entry fails silently in the safest-looking
direction** — it reads as the default, which is usually what the file already said. Same family as
§33's stale `DefaultDSlotAmbients`: a hand-maintained duplicate of something the code owns.

---

## 50. The gate that refused a scene and said nothing (#17)

The white screen came back — this time entering the **death grab** scene, not a full-lock cum. It
is not #15 returning: that was a latch, and this whole event ran at `locks=1/8 blocked=False
cumPlaying=False`. One gate, two symptoms, and it took a session to find because the gate was mute.

### Finding it: 25 `[GRAB-INIT]` for 26 `[GRAB-START]`

Every healthy grab in the run dispatches inside a millisecond —

```
[GRAB-START] prefab='Mimic' key=mimic anims=3
[GRAB-ANIM] controller='MimicGrab' clip='MimicGrabInit' hash=-1400517032 t=0.00
[EDI] Play Mimic_Start
```

— and exactly one did not:

```
20:16:00.546 [PLAYER-DEATH] force filler
20:16:02.006 [GRAB-START] prefab='Zombie_Enemy' key=zombie anims=2
20:16:02.007 [GRAB-ANIM] controller='ZombieGrabScreen' clip='ZombieGrabScreen_Loop' t=0.00
20:16:02.007 [PLAYER-REVIVE] ok                      <- not "keeping the scene gallery"
20:16:02.008 [EDI] Play filler_damage_50             <- and filler for the next 13 seconds
20:16:02.009 [HEAT-LOCK] scene entry survival set HP to 1 from grab
```

The marker census did the work: 26 `[GRAB-START]` against 25 `[GRAB-INIT]`. `[GRAB-INIT]` is the
last line before `Plugin.SendPlay`, so exactly one grab reached `FireCurrentGrabStep` and left
without dispatching — and the only way out of that function before `[GRAB-INIT]` is
`IsGrabAnimatorReadyForEdi()`, which had three failure modes and **logged none of them**.

Two are ruled out by the lines above: `anims=2` is not empty, and a controller name was read off
the animator so it is not null. That leaves `isActiveAndEnabled == false`.

### One fact, both symptoms

The player died at 20:16:00. `PlayerStats.Die` ends by invoking the `OnPlayerDeath` UnityEvent,
whose subscribers tear the UI hierarchy down. A zombie then grabbed the corpse, and
`HeatLockSystem.EnsureSceneEntrySurvival` revived the player to 1 HP precisely so the scene could
play — **into a hierarchy the death had already deactivated**. So:

- nothing renders → the white screen
- `IsGrabAnimatorReadyForEdi()` refuses → no `[EDI] Play`
- `Revive_Postfix` finds `IsGalleryPlaybackActive == false` and falls back to filler

That last step is §27's fix working correctly on bad input, which is why it looked innocent.

`OnPlayerDeath` is wired in **scene data, not IL**, so what it deactivates cannot be read out of
`Assembly-CSharp.dll` the way §46's AI tables were. Hence a probe rather than a blind fix.

### Both halves of the fix

`IsGrabAnimatorReadyForEdi()` is now a thin wrapper over `DescribeGrabAnimatorReadiness()`, which
returns null or the reason, and `FireCurrentGrabStep` logs it:

```
[GRAB-INIT] skipped: grab-screen animator inactive (activeInHierarchy=False activeSelf=True
                     enabled=True playerDead=False)
```

`activeSelf` against `activeInHierarchy` is the load-bearing pair: it says whether the animator's
own object was switched off or an ancestor was, which decides whether a `SetActive(true)` fix is
even addressable. Deduped on the reason string, because the chaser-boss refresh path retries until
playback starts.

Then the recovery: `HeatLockSystem.PendingSceneEntryGameOver` joins
`DragonGrabHooks.IsChaserBossPresentationActive` as an escape hatch in the gate. When the mod has
*itself* revived the player so a scene can finish, that scene is real by construction and an
inactive animator is the game's teardown rather than a refused grab. The device now plays the
enemy's script through the death scene.

Whether that also clears the white screen is unknown — it is the game's own rendering, and the new
skip line is what will tell us.

**A gate that refuses without logging is worse than no gate**, because everything upstream of it
looks healthy: `[GRAB-START]` fired, `[GRAB-ANIM]` named a real controller and a real clip, no
warning anywhere. §47 made the same point from the other side, about a line that *claimed* a save
it never made. Same rule either way — the gap has to announce itself, like `[ALIAS-GAP]`,
`[AI-AUDIT]` and `[KEYBIND]`.

### Also confirmed by the same run

| what | evidence |
|---|---|
| all-locks diorama release (§28) | `release 8 lock(s) from ambient imp gangbang -> 0/8 (was 8)` |
| peephole clear-all release (§28) | `clear all locks from peephole ImpKeyholePeepCamera -> 0/8 (was 8)` |
| `instant re-arm` once per scene end (§45) | 19 lines across 17 mimic scenes; the three-per-end behaviour is gone |
| `[GRAB-GATE]` no longer cries wolf (§47) | **0** lines in a run containing a real dragon grab, against 9 bogus `'Wendigo'` before |
| debug hotkeys fire while moving (§47) | plantasha, zombie, mimic and gargoyle all spawned mid-run |
| mimic intro on re-interact (#13) | 17 mimic grabs, `MimicGrabInit t=0.00` every time — closed as not-reproducible over three runs |
| startup audits | `[AI-AUDIT] ok`, `[KEYBIND]` silent, **0** `[ALIAS-GAP]` |

And the Plantasha strand (#14's remaining thread) **did not reproduce**: 317 `[SPIN-AI]` samples
across two instances, zero `STRAND`, zero `[AI-GUARD] unstuck`. It is intermittent, not
every-scene.

### §49 verified, by the same mechanism that exposed it

This run was the first launch after the section fix, so BepInEx's startup rewrite is the test.
`DebugHotkeysIgnoreHeldKeys` came back **once** where the pre-fix launch produced two copies — the
`[Gameplay]` orphan is gone and the `[Tools]` entry is the one being read. The rest of the rewrite
is BepInEx reordering two keys into `Bind()` order within their own section, with no key added,
removed or changed. That ordering is now the committed one, so future launches should be a no-op,
and the distributable was regenerated from it through the `code/README.md` recipe.

---

## 51. The gallery plays different animations, and a scene scripted against the wrong body

Feel-pass feedback, three findings, one of them structural.

### `Wendigo_Continued` was inverted, and measured against the wrong subject

CUE: *"seems off — the focus should be on the guy who is on top in this scene, unlike most other
scenes."* Both halves of that are right.

`WendigoSex` is 8 frames of full-bleed 480×270 with no alpha trim, so the silhouette proxy has
nothing to bite on and the sweep fell back to signed displacement — which tracked the cyan spill
rather than either body and scored **+0.45**. Comfortably inside "polarity agrees", against a curve
running exactly backwards. **A mid positive correlation from a proxy watching the wrong object is
worth nothing**; this is the sharpest example yet of PROJECT.md's "a low correlation only means
look at this one", because here a *decent* correlation meant the same thing.

Tracking the pale figure's y centroid (`proxies.wendigo_top`, a warm mid-tone at R−B≈52 against
the wendigo's near-black R−B≈4):

```
frame    0     1     2     3     4     5     6     7
y-cent  75.7  76.1  81.6  86.6  87.2  88.2  86.5  81.1     larger = lower on screen
pos      100    96    52    12     8     0    14    57
```

He descends over frames 0–5 and returns over 5–7 — 625 ms down against 375 ms up. The old curve sat
at 0 where he is fully withdrawn and peaked at 90 where he is deepest. Rebuilt: **+0.45 → +1.000**.

### The handoff, and a constraint that removes a choice

CUE: *"the most important thing is that it should transition cleanly into the continued section."*
In game the chain is `WendigoKiss` → `WendigoSexSceneIntro` → `WendigoSexScene`, with both later
states dispatching `Wendigo_Continued`, so the seam is Start's last position against Continued's
first.

`Wendigo_Continued` must open at 100, because its animation opens fully withdrawn. And
`Wendigo_Start` cannot simply be made to *end* at 100: every row is `Loop=true`, and Edi's
`inproveLoopAccion` forces `last.pos = first.pos`. **The ending is not independently choosable —
to end at 100 it has to start at 100.**

So the §48 wind-down now settles *upward* onto 100, and the opening 0→100 rise across the dark
approach is gone. No loss: there is nothing on screen for the first 1333 ms, so that rise was
invented motion, and parking at the top is where a stroke should begin from anyway.

### The gallery is not playing the same animation as gameplay

CUE: *"the two gooper scenes work well during gameplay, but seem off in the gallery"*, and
*"nun_cum seems not to loop great in the gallery, but works great during gameplay."*

Every row is reached from two places — an in-game animator state and a gallery-viewer one — and
`animsweep.MAP` only ever names the in-game clip. Everyone assumed the viewer replays the same
animation. **It does not.** The gallery has its own `Gallery_*` clips, and 12 of 29 rows differ in
length:

| row | gameplay | gallery | ratio |
|---|---|---|---|
| `Nun_Cum` | 3300 | 5500 | **1.667×** |
| `imp_1` / `imp_2` / `imp_3` | 500 | 667 | **1.333×** |
| `Gooper_Start` | 800 | 1000 | **1.250×** |
| `Gooper_Cum` | 1500 | 1750 | **1.167×** |
| `Plantasha_Cum` | 3875 | 3556 | 0.918× |
| `Plantasha_Start`, `imp_grab_loop`, `imp_grab_cum` | — | — | 0.889× |
| `Wendigo_Start` | 5167 | 5500 | 1.065× |
| `Dragon_Grabbed` | 4833 | 4667 | 0.966× |

The three reported from play are the three worst ratios among the scenes actually played, in
order, and everything reported as fine sits at ≤1.07 — so **the perceptibility threshold is
somewhere near 1.1**, which is a useful number to have. `code/gallerydiff.py` produces the table.

A script can only be whole-cycle correct for one of the two, so this is not a curve defect and no
amount of playing fixes it. It *is* separable, though, and without a rebuild: in-game lookups
check `InGameAliases` first and fall back to `GalleryAliases`, while gallery lookups read
`GalleryAliases` only (`GalleryAliases.cs`). Pinning the in-game slug in `InGameAliases` and
repointing the shared entry at a new row gives the two routes different scripts. Not yet done —
it is ~6 new scenes and a content decision.

One trap found while building the tool: **clip names are not unique.** `Gallery_Nun_Grab` exists
twice, at 600 ms @10fps (the grab screen) and 1625 ms @8fps (the enemy model's own grab), and
`clip_frames` returns whichever the asset walk reaches first — reporting `Nun_Grab` as 2.708× off
when the two grab screens are in fact identical. `gallerydiff` now collects every clip carrying the
name and says which one it took.

---

## 52. Six scenes the gallery now scripts for itself

§51 found that the gallery viewer plays its own `Gallery_*` clips and 12 of 29 rows differ in
length from the in-game clip they share a funscript with. This splits the six above the ~1.1×
threshold the feel pass established. **No DLL rebuild** — the mechanism was already there.

| new row | gallery clip | ms | was playing |
|---|---|---|---|
| `Nun_Cum_Gallery` | `Gallery_Nun_Cum` | 5500 | a 3300 ms script, 1.667× short |
| `imp_1_Gallery` | `Gallery_Imp_Grabbed_1` | 7333 | 500 ms cycles against 667 |
| `imp_2_Gallery` | `Gallery_Imp_Grabbed_2` | 6667 | same |
| `imp_3_Gallery` | `Gallery_Imp_Grabbed_3` | 6667 | same |
| `Gooper_Start_Gallery` | `Gallery_Gooper_Grab_Start` | 2000 | 800 ms cycles against 1000 |
| `Gooper_Cum_Gallery` | `Gallery_Gooper_Grab_Cum` | 1750 | a 1500 ms script |

Gallery is now 65 rows and 65 files per variant, sweep **57/57 `ok`**, harness 131 pairs 0 UNMAPPED.

### Four of the six needed no derivation at all

`Gallery_Gooper_Grab_*` and `Gallery_Imp_Grabbed_*` list **byte-identical sprites** to their
in-game clips — same frames, same order — and differ only in `m_SampleRate`: 8 fps against 10, 6
against 8. Nothing new to measure; they are the same shape on a slower clock. The Goopers reuse the
same `GOOPER` frame table and `DEEP` band, and the imps replay their master through
`_scaled_from`, which reads the master's *file* rather than hardcoding it, so the two cannot drift.

Only `Gallery_Nun_Cum` is different content: 55 frames against 33, and the medoid-distance proxy
shows why — the same scene with **three** twitches (900, 2100, 4000 ms) instead of two, over a
longer hold. Same descent, same lift, one more burst.

That the imp gallery variants land on their masters' exact correlations (+1.00 / +0.54 / −0.31) is
the check that scaling preserved shape and not merely length.

### The split, and the one thing that makes it work

The two routes resolve independently because in-game lookups check `InGameAliases` **first** and
fall back to `GalleryAliases`, while gallery lookups read `GalleryAliases` only. Repointing the
shared entry moves the gallery; a pin in `InGameAliases` holds gameplay where it was:

```ini
GalleryAliases = nun_cum=Nun_Cum_Gallery;gooper_start=Gooper_Start_Gallery;…
InGameAliases  = nun_cum=Nun_Cum;gooper_cum=Gooper_Cum;imp_1=imp_1;…
```

**The pin is only needed where the slug collides.** `nun_cum`, `gooper_cum` and `imp_1/2/3` are
produced by both routes and must be pinned, or the gallery override drags gameplay along with it.
`gooper_grab` is in-game only — the gallery says `gooper_start` — so it needs nothing. Getting this
backwards fails *silently*: gameplay would quietly start playing gallery-length scripts, which is
the exact defect being fixed. The harness prints the `via` column for every pair, so confirming it
is one command:

```
ingame   nun   GhoulGrabCum  nun_cum  -> Nun_Cum          InGameAliases
gallery  nun   Cum           nun_cum  -> Nun_Cum_Gallery  GalleryAliases
```

### A convention that was stricter than the corpus

`authored.write` asserted ≥100 ms between points, which `imp_3_Gallery` fails at 71 ms. But **24 of
the 59 existing scripts already have closer points** — `imp_3` itself down to 53 ms — because the
fastest scenes genuinely are that fast. 100 ms is the rule for a curve written from scratch, not a
property of the set, and a scene replayed from one of those inherits its spacing; it cannot be held
to a standard its own master fails. `write` now takes `min_gap`, and `_scaled_from` passes the
master's floor — which the scaling can only improve on (71 against 53, 116 against 87).

**An assertion that would reject the file it was derived from is measuring the wrong thing.**

---

## 53. The rest of the gallery, held to the same standard as everything else

§52 split the six gallery mismatches above a **1.1× perceptibility** threshold and left six at
0.889×–1.065×. That was the wrong bar, and it was inconsistent with the whole rest of the project:
`animsweep` calls anything past **0.5%** not-ok, `retime` refuses to auto-apply past 5%, and the
set has been whole-cycle exact since §48. Leaving six rows 6–11% out because nobody happened to
notice them is the standard the tooling exists to prevent.

All twelve are now split. **63/63 `ok`**, 71 rows, and `gallerydiff` reports *0 still sharing*.

### First, checking the whole surface rather than the enemies

Dioramas and peepholes were assumed rather than verified in §51. Checked properly:

- **Dioramas** — every diorama clip (`Nun chair fuck`, `imp gangbang`, `mimic wall fuck`, …)
  exists exactly **once** in the assets. There is no gallery variant, so the viewer plays the same
  animation and there is nothing to split.
- **Peepholes** — each has a gallery twin (`ZombieBJGallery`, `WendigoRidingGallery`,
  `GooperPilloaryGallery_Loop`, …), and all seven match their in-game duration exactly.

So the mismatch is confined to enemy grab screens, which is now closed.

### Second, replacing name-matching with the controller tables

§51's row→gallery-clip map was written by reading clip names, which is the guessing this project
keeps getting caught by. Redone from each `AnimatorController`'s `m_TOS` state list against its
`m_AnimationClips`, which is ground truth. Two things that only showed up that way:

- `Gallery_Imp_Grabbed` holds states `Cum, Imp 1, Imp 2, Imp 3, Loop` against clips
  `Gallery_Imp_Gangbang_Cum/Loop` **and** `Gallery_Imp_Grabbed_1/2/3` — two unrelated name
  families in one controller. Name-matching alone would not have paired those.
- `Gallery_Gargoyle_Grabbed` pairs states `Cum/CumContinue/Grabbed` against clips
  `Grabbed1/Grabbed2/Grabbed3`, which do not correspond by name at all. It happens not to matter
  (all its durations match gameplay), but it is a standing warning against the shortcut.

The state machine itself is a collapsed blob in the typetree — same as `m_MuscleClip.m_Clip` — so
state→clip cannot be walked directly; pairing within one controller is as far as the assets go.

### Third: scaling was the wrong transformation

Three of the six do **not** differ uniformly from their in-game clip, so a duration-ratio scale
would smear a local difference across the whole scene:

| row | how the gallery clip actually differs |
|---|---|
| `Wendigo_Start` | the same 31 frames at 125 ms instead of 166.7, then the final black frame **held for 13 more keyframes** (1750 ms) |
| `Dragon_Grabbed` | gameplay opens on `face_sit-Sheet_0` **twice**; the gallery does not |
| `Plantasha_Cum` | the gallery includes `Plantasha_blowjob_cum_1_15`, a frame gameplay **skips** |

So `_remap_by_frame` builds a piecewise-linear map between the two timelines from the frames they
share — anchored on where each distinct frame *first* appears, since keyframe index and frame index
are not the same thing once a clip repeats a frame — and sends every action through it. Exact at
every frame boundary, and a hold in one clip stretches exactly one segment. The other three
(`Plantasha_Start`, `imp_grab_loop`, `imp_grab_cum`) have byte-identical sprite lists and fall out
of the same code as a pure clock change.

Every variant lands on its master's correlation: +1.00/+1.00, +0.90/+0.90, +0.71/+0.72.

### And a floor that was backwards

§52 held a derived scene to its master's *millisecond* spacing. That is right when the gallery clip
is slower and wrong when it is faster — `Gallery_PlantashaGrab_Start` is 9 fps against 8, so its
remapped points are legitimately 111 ms apart where the master's are 125, and the assertion fired
on a correct file. `_derived_floor` now scales the master's spacing by the same clock change, so
the bar is "no worse than its source, measured in frames", capped at 100 so it can only ever relax
the convention. **A derived artefact has to be judged in the units it was derived in.**

### The pins

Only `plantasha_cum` collides among the new six — the gallery says `plantasha_start`,
`dragon_grabbed`, `wendigo_start`, `imp_loop`, `imp_cum` where gameplay says `plantasha_grab`,
`dragon_facesit`, `wendigo_kiss`, `imp_grab_loop`, `imp_grab_cum`. Harness confirms all 131 pairs
route correctly with 0 UNMAPPED, in-game rows reading `InGameAliases` and gallery rows
`GalleryAliases`.

---

## 54. The suppression nobody undid (#18)

Reported from the 21:38 run: the wendigo grab scenes play correctly, but on exiting, the screen
freezes on the first frame of the wendigo start animation and stays there.

**Edi's side was blameless**, which is what made it interesting — all three grabs in that log
dispatch perfectly:

```
[CHASER-GRAB] wendigo — overlay hidden, animator on for EDI
[GRAB-ANIM] controller='WendigoGrabScreen' clip='WendigoKiss' t=0.00
[EDI] Play Wendigo_Start  ->  Wendigo_Continued (intro)  ->  Wendigo_Continued (scene)
[GRAB-END] ...
```

Nothing in the log is wrong. The whole defect is in the presentation layer, which no marker
covered.

### An asymmetry with no counterpart

The wendigo is a **chaser boss**, so `SuppressFullscreenGrabLayer` runs on StartGrab and hides
three things to keep the first-person view during the grab:

| hidden | put back by |
|---|---|
| `grabImage` (SetActive false) | nobody |
| `grabOverlay` (SetActive false) | nobody |
| `overlayImage`'s alpha, forced to 0 | **nobody, ever** |

`ForceRestorePlayerView` — the thing that runs on EndGrab and *looks* like the counterpart — only
re-enables the camera, controllers and rigidbody. It never touches the layer.

Two of the three are usually masked, because the game's own `HideGrabUI()` deactivates
`grabImage` and `grabOverlay` too. The alpha is not masked by anything: the game re-reads
`grabOverlayColor` when it *shows* the layer, but the `Image` keeps whatever colour it was last
given. So **one chaser-boss grab left every later grab of any enemy with a fully transparent
overlay for the rest of the run** — a real bug that nobody had reported and that nothing would
have surfaced.

### Why the screen freezes

Reading `GrabScreen.EndGrab` in IL:

```
if (!isGrabbed) return;        // <- early return
isGrabbed = false;
... HideGrabUI();              // grabUI, grabOverlay, grabImage -> SetActive(false)
... PlayEndAnimation();        // -> RestoreAnimationController()
```

**A Harmony postfix still fires on that early return.** So `[GRAB-END]` in the log means "the mod's
postfix ran", not "the game tore its UI down" — the same trap as §50, where a silent gate made a
healthy-looking log while the device played filler. On the early-return path neither `HideGrabUI`
nor `RestoreAnimationController` runs, which leaves the grab layer up with the `WendigoGrabScreen`
controller still bound. A grab layer showing a still-bound wendigo controller renders as exactly
the reported still frame.

### The fix, and where it keys off

`RestoreFullscreenGrabLayer` now undoes the suppression on EndGrab: it restores `overlayImage`'s
colour from `grabOverlayColor` and calls the game's own `HideGrabUI()`. Calling that is deliberate
rather than belt-and-braces — it is idempotent, and it is the only thing that guarantees the layer
is down on the path where EndGrab never reached its own call.

It keys on a dedicated `_fullscreenLayerSuppressed` flag rather than on
`_chaserBossPresentationActive`. That distinction matters: the presentation flag is cleared from
**two** places, one of them `GrabEndHelper.FinishGrabEnd`, so whether it is still set when this
class's EndGrab postfix runs depends on Harmony ordering between two unrelated patches. **A restore
has to key on the thing it actually undoes**, not on a nearby flag that happens to correlate.

And the diagnostic logs *before* the restore, so the fix cannot hide its own evidence:

```
[CHASER-GRAB] EndGrab left: grabUI=… grabOverlay=… grabImage=… isGrabbed=… controller='…'
```

`grabUI=True` or `grabImage=True` confirms the early-return diagnosis; already-`False` means the
frozen picture came from somewhere else and the `controller=` name says where to look next.

### Confirmed good in the same run

`Wendigo_Start` and `Wendigo_Continued` in gameplay, including the §51 handoff — the rebuilt,
de-inverted `Wendigo_Continued` and the both-ends-pinned-to-100 transition both play correctly.

---

## 55. §54 reverted — the fix was wrong, and the probe said so

§54's `RestoreFullscreenGrabLayer` is removed. It did not fix the stuck screen and it made things
worse. Reverted rather than adjusted, because the reasoning behind it was wrong at the root.

### What the probe actually reported

```
[CHASER-GRAB] EndGrab left: grabUI=<null> grabOverlay=<null> grabImage=False
                            isGrabbed=False controller='WendigoGrabScreen'
```

Three of the four claims in §54 die on that one line:

| §54 assumed | reality |
|---|---|
| `grabUI`/`grabOverlay` were left active | both are **null** on this build — `HideGrabUI` was never going to touch them |
| the layer stayed visible | `grabImage=False`, already hidden |
| `EndGrab` returned early | `isGrabbed=False`, i.e. it ran past its own guard |

So none of the three objects §54 targeted was the thing still being drawn, and the early-return
theory — the whole mechanism of the entry — is simply not what happened.

### And the "missing counterpart" was not missing

`SuppressFullscreenGrabLayer` looked like it had no undo. It has one:
`GrabEndHelper.CleanupGrabPresentation` runs the entire teardown at EndGrab postfix priority 500 —
`HideGrabUI`, `RestoreAnimationController`, `SetActive(false)` on all three objects, the animator's
controller restored, `Rebind()`, `Update(0f)`, component disabled.

Including this:

```cs
Color value5 = val.Field("grabOverlayColor").GetValue<Color>();
value5.a = 0f;                       // deliberately ZERO
((Graphic)value4).color = value5;
```

**The teardown sets the overlay's alpha to 0 on purpose**, which is the state the suppression
wanted. §54 "restored" it to `grabOverlayColor`'s original alpha — putting a tint back over the
screen and fighting the real cleanup. That is the most likely thing the report of "made it worse"
was pointing at.

The lesson is not "check for a counterpart" — §54 did that — it is **that the counterpart may live
in a different class than the thing that needs undoing**. `SuppressFullscreenGrabLayer` is in
`DragonGrabHooks`; its undo is in `GrabEndHelper`. Grepping the file the suppression lives in finds
nothing and reads as proof.

### The dragon was not caused by any of this

Reported alongside: a dragon grab fired afterwards "even though there was no dragon present". The
log agrees it happened and shows it was not ours:

- there is **no `[SPAWN] dragon`** anywhere in the run — the only spawns are two wendigos;
- the dragon was already in the level, parked at **`(0.00, 1224.92, 30.82)`**, i.e. a chaser boss
  in its out-of-play holding position 1225 units above the floor;
- it announces itself as `[HEAT-LOCK] max from chaser Dragon -> 8/8` — the game's chaser mechanic,
  and the wendigo grab immediately before it had already pushed heat to 8/8 and 99%.

§54 only ran inside an EndGrab postfix and touched a UI colour and a hide call; neither can make an
AI commit a grab. Worth stating plainly that this is *not* proof it is old behaviour — the previous
log was overwritten, so there is nothing to diff against.

### A diagnostic gap worth more than the fix was

Line 1 of every log in this project:

```
[Error  :   BepInEx] Unable to start Unity log writer
```

`BepInEx.cfg` had `[Logging.Disk] WriteUnityLog = false`, so **Unity's own messages — including
every game-side exception — have never been in `LogOutput.log`.** An exception thrown partway
through `CleanupGrabPresentation` would abandon the rest of the teardown and leave exactly this
bug, and nothing would have recorded it. Set to `true` locally; the distributable's copy is left
alone, since users do not want the noise.

### The probe that replaces the fix

Still read-only, now watching the object that actually draws — the animator's own GameObject, not
the three `GrabScreen` fields — and sampled **twice**: at priority 650 (before
`CleanupGrabPresentation`) and at priority 10 (after every other EndGrab postfix). Comparing the
two says whether the teardown worked and something undid it, or never took effect at all.

```
[CHASER-GRAB] EndGrab left:   ... animator='<name>' active=… enabled=… controller='…' clip='…'
[CHASER-GRAB] after cleanup:  ... animator='<name>' active=… enabled=… controller='…' clip='…'
```

**Ship the probe, not the guess.** §54 shipped a fix built on an untested mechanism and had to be
taken back out; the one thing in it that earned its place was the log line that disproved it.

---

## 56. The teardown undid itself — the animator was the thing turning the screen back on (#18)

The §55 probe ran in the 00:00 run and localised #18 in one grab. Of the twenty EndGrabs it
sampled, **exactly one** — the wendigo — moves:

```
[CHASER-GRAB] EndGrab left:   … grabImage=False … animator='GrabScreen' active=True enabled=False controller='WendigoGrabScreen'
[CHASER-GRAB] after cleanup:  … grabImage=True  … animator='GrabScreen' active=True enabled=False controller='WendigoGrabScreen'
```

Every ghoul EndGrab in the same run reads `grabImage=False` on both lines. So the teardown *ran*
and something between priority 500 and priority 10 turned the fullscreen grab layer back on.

### Nothing in either assembly does that

Grepping settles it, and the answer is what makes the bug interesting:

- the mod has seven `SetActive(true)` calls and every one is an enemy GameObject;
- in `Assembly-CSharp`, `GrabScreen::grabImage` is referenced in exactly three methods —
  `InitializeUI` and `HideGrabUI` (both set it *false*) and `ShowGrabUI` (sets it true), and
  `ShowGrabUI` is called from **one** place, `StartGrab`, past a guard that no teardown reaches.

No C# in the process re-activates it. **The animator did**, out of a curve in the clip.

### Six clips in the game carry a GameObject activation curve, and they are the six chaser-boss ones

`m_ClipBindingConstant.genericBindings` names what a clip is allowed to write. A binding with
`typeID: 1` is a **GameObject**, and `attribute: 2086281974` is `CRC32("m_IsActive")` — an
activation curve. Sweeping all 208 clips that have any non-PPtr binding:

| clip | |
|---|---|
| `WendigoKiss`, `WendigoSex`, `WendigoSexIntro` | the wendigo grab scene |
| `DragonFaceSit`, `DragonSexScene`, `DragonSexSceneIntro` | the dragon grab scene |

and **nothing else in the game**. All six bind it on `path 413981131`, which is the same transform
hash their sprite PPtr curve draws to: the clip turns on the very object it then paints frames
onto. Every other grab screen — ghoul, zombie, mimic, gooper, gargoyle, plantasha — binds only
`m_Enabled` (`CRC32 3305885265`) and colour, never activation.

### Why that made the screen stick

`GrabEndHelper.CleanupGrabPresentation` hid the layer and *then* did the animator work:

```cs
grabImage.SetActive(false);          // ... and grabUI, grabOverlay, and the overlay alpha
…
animator.runtimeAnimatorController = originalController ?? defaultController;
animator.Rebind();
animator.Update(0f);                 // <- writes every property the bound clips declare
animator.enabled = false;
```

`Rebind()` + `Update(0f)` evaluates the bound controller at t = 0 and writes its bindings. For a
chaser boss the bound controller is still `WendigoGrabScreen` (the probe prints it), so that call
sets `m_IsActive = true` on `grabImage` — **after** the line that hid it. The animator is disabled
on the next statement, so nothing ever advances or clears it, and the fullscreen layer stays up
holding frame 0 of `WendigoKiss`. Which is, word for word, the report: *the screen freezes on the
first frame of the wendigo start animation*.

An animator only writes properties its clips bind, which is exactly why 25 non-chaser grabs in the
same log were unaffected by the identical code path.

**The fix is the order.** The animator block now runs first and the hides last, so the explicit
teardown has the final word. The overlay alpha moved with it for the same reason —
`WendigoSex`, `WendigoSexIntro` and `GhoulGrabStart` bind `m_Color.a` (`CRC32 304273561`), so
`Update(0f)` was rewriting that too, and zeroing it beforehand could never stick.

No config toggle: this is a reordering inside our own teardown, not a behaviour anyone would want
the old version of.

### The probe stays, and stops shouting

`_fullscreenLayerSuppressed` was set but never cleared, so after one wendigo grab the probe logged
on every later EndGrab of any enemy — 19 `GhoulGrabScreen` lines for one chaser-boss scene. It is
cleared at EndGrab now and re-arms on the next chaser-boss StartGrab. The two lines remain the
verification: **`grabImage=False` on `after cleanup:` is the fix working.**

### Verified in the 00:17 run

Both chaser bosses, one grab each, and both pairs are clean:

```
00:17:35  wendigo  EndGrab left: grabImage=False   after cleanup: grabImage=False
00:17:59  dragon   EndGrab left: grabImage=False   after cleanup: grabImage=False
```

The dragon is the stronger of the two, and by accident. Its grab enters on
`controller='DragonGrab' clip='DragonFaceSit'` but **ends bound to `WendigoGrabScreen`** — the
restore target `originalController` was whatever the previous grab left behind. So the animator was
holding a chaser-boss controller, carrying the `m_IsActive` curve, at exactly the moment
`Rebind()`/`Update(0f)` ran — the worst arrangement for this bug — and the layer still came down.
That is the point of fixing it by *order*: the outcome no longer depends on which controller
happens to be bound.

(2 grabs, 2 probe pairs. The `_fullscreenLayerSuppressed` latch fix is therefore not independently
exercised by this run — it needs a non-chaser grab following a chaser one to show, which the 00:00
run had 19 of.)

### Two things the run settled for free

- **#17 is fixed** (§50). The death grab at 00:01:46 now reads
  `[GRAB-INIT] nun/GhoulGrabscreen -> nun_grab` → `[EDI] Play Nun_Grab` →
  `[PLAYER-REVIVE] ok - keeping the scene gallery, no filler`, where the 20:16 run had no
  `[GRAB-INIT]` at all and fell through to `filler_damage_50` for thirteen seconds. Twice in the
  run, both clean.
- **`WriteUnityLog = true` works**, despite line 1 still reading
  `[Error :BepInEx] Unable to start Unity log writer` — that error is about redirecting BepInEx's
  output *into* Unity's log, a different setting. `[Info : Unity Log]` lines are now present, and
  there is **not one exception in the whole run**, which retires §55's standing suspicion that a
  throw partway through the teardown was abandoning it.

**A property is only rewritable if some clip declares it.** That is the whole asymmetry here, and
it is readable statically: `genericBindings` is the list of everything an animator is permitted to
touch. When state gets undone with no code that undoes it, ask what the animation is bound to
before looking for another caller.

---

## 57. The gallery feel pass — twelve for twelve, and the set is closed

The last twelve scripts, the `*_Gallery` rows from §52–§53, were played through the gallery viewer
on 2026-08-18. **All twelve match their scenes.** No changes needed, nothing to re-derive.

That closes the funscript work outright: 71 rows, 63/63 `ok` on timing, 0 gallery mismatches, and
now every one of them played — gameplay and gallery both.

Worth recording what the pass actually confirmed, since the twelve were not one kind of thing:

| how it was built | scenes | what a pass proves |
|---|---|---|
| derived from its own frames | `Nun_Cum_Gallery` | the only one with different *content* — 55 frames against 33, three twitches instead of two. Nothing was inherited, so this is the one the pass genuinely tested. |
| piecewise frame remap | `Wendigo_Start_Gallery`, `Dragon_Grabbed_Gallery`, `Plantasha_Cum_Gallery` | these differ from gameplay *locally*, so one segment stretched and the rest did not. A clean pass says the seams hold. |
| pure clock change | the other eight | shape is provably the master's (byte-identical sprite lists, correlations equal to their masters' to two decimals). A pass here confirms the master, not the derivation. |

So the informative results are the first four rows; the eight scaled ones were near-guaranteed by
construction and the pass is a spot-check. `Plantasha_Cum_Gallery` was the one flagged as most at
risk beforehand — its correlation fell furthest from its master (+0.61 against +0.77) — and it was
fine, which is a small point in favour of `_remap_by_frame` over a duration scale.

### What is deliberately not settled

**Vibration.** The pass judged stroke against picture. How the buzz sections *feel* on the device
was explicitly deferred and is the one thing that could reopen this. If they read as empty, the
lever is **amplitude, not more pulses** — the bursts already sit exactly on the frames where the
animation twitches (§48's medoid-distance finding), so adding pulses moves them off the evidence.
§35 is the cautionary case: a ±7 wiggle at 62 ms is simultaneously too small to feel and too dense
to reproduce, and flattens to a straight line. `shared_zombie`'s 0↔50 at ~100 ms is the shape that
works.

`Nun_Cum` / `Nun_Cum_Gallery` and `Plantasha_Cum` / `Plantasha_Cum_Gallery` are where to look
first — two bursts each where earlier versions had three or a continuous buzz. Note the gallery nun
is *not* simply its master stretched: its clip really does have three twitches.

The Gooper 100–50–100 band is the other deferred knob (`rederive.DEEP`).

---

## 58. `mod/` deleted, and a release that builds itself — v2.1.0

`mod/` is gone: the hand-mirrored `single-mod` distributable, the 1.7 GB **PostNutCalamity 0.1.0**
build sitting inside it, `Edi.exe` and its `certificate.pfx`, the stale copy of the plugin source,
and `mod/old`'s original zips. In its place `code/release.py` assembles
**`dist/PncEdi-2.1.0.zip`** — 932 KiB, 172 files, no game binaries — from the working tree.

Version bumped 2.0.8 → **2.1.0**. 2.0.8 is already public with different contents, and two
binaries wearing one version number is worse than no version at all.

### One archive for Windows and Linux

Asked for, and it turns out to be free. BepInEx's `BepInEx/core/` is managed code and is
**byte-identical** between the win-x64 and linux-x64 packs of the same build — verified, not
assumed. Only the loader differs, and the two can share a directory ignoring each other:

| platform | loads via | how it starts |
|---|---|---|
| Windows, and the Windows build under Proton | `winhttp.dll` + `doorstop_config.ini` | launch the game normally |
| native Linux | `libdoorstop.so` + `run_bepinex.sh` | `./start-pnc-linux.sh` |

`release.py` re-checks that byte-identity on every build, so if a future BepInEx breaks it the
build stops rather than shipping something that quietly works on one platform only.

`start-pnc-linux.sh` is ours and exists for one reason: BepInEx's `run_bepinex.sh` refuses to run
until it is told the executable name, either by editing the script or as `$1`. Ours finds the
`.x86_64` itself, preferring one whose name looks like the game and refusing rather than guessing
if several are candidates. **Deliberately a separate file** from `run_bepinex.sh`, which ships
verbatim — so upgrading BepInEx stays a straight copy with nothing of ours to re-apply.

Verified end to end short of Unity itself, by extracting the zip over a stub executable:

```
LD_PRELOAD = libdoorstop.so
DOORSTOP_ENABLED = 1
DOORSTOP_TARGET_ASSEMBLY = …/BepInEx/core/BepInEx.Unity.Mono.Preloader.dll
```

### Nothing binary is tracked, so the runtime is fetched and checked

The repo tracks no BepInEx and no loader — the `.gitignore` has always been a deny-everything
allowlist. Rather than copying them out of the working game directory (which a fresh clone does
not have, and which has never held the *Linux* loader at all), `release.py` downloads both packs
from a pinned build and verifies each against its SHA256 before use, caching under
`code/dist/cache/`. Offline, drop the two zips in by hand.

The archive is byte-reproducible from a commit: every entry is stamped with HEAD's commit time and
the README's build date comes from the same place, not from today's.

### The config guard, which immediately earned itself

PROJECT.md has warned since §36 that "the distributable config is generated from the local one, so
local tweaks ship", with the remedy being *remember to diff*. That is now an assertion. Every
setting whose live value differs from **its own documented default** must be declared in `SHIPPED`
with the value to ship and why; anything undeclared aborts the build:

```
release: these settings differ from their default and are not declared in SHIPPED …
  [Gameplay] AmbientReleaseLookSeconds = 0  (default '3')
```

It reads BepInEx's own `# Default value:` comments, which BepInEx writes from the `Bind()` call —
so the guard compares against the plugin's real defaults and cannot go stale.

Two accidents surfaced on its first run, both of which **had been shipping in `mod/single-mod` for
as long as it existed**, because the old process only ever diffed local against the mirror and the
mirror was made from local:

| setting | was shipping | now ships | |
|---|---|---|---|
| `HeatLockAutoHealRate` | **120** | 1 | 120 HP/s auto-heal — a testing tweak, near-invincibility |
| `PeekGalleryMap` | a 13-entry copy | the 16-entry default | the live copy is a stale *subset*; this setting replaces the default rather than layering on it, so three imp three-way spellings were being dropped |

Declared and shipped as they are: `GodMode = false` (the coded default is `true`, but
`EnableHeatLocks` replaces god mode and is on by default), `ShowHeatBarDuringGrab = false`,
`EndGrabDelaySeconds = 30`, and `GalleryAliases`/`InGameAliases` — the §52–§53 gallery split,
which is the entire mechanism for twelve scenes and has no code path that reproduces it.

`BepInEx.cfg` is deliberately **not** shipped, so a local diagnostic like `WriteUnityLog` cannot
leak into a release; BepInEx writes a stock one on first run.

### What it refuses to do

Ship a game binary, `Edi.exe`, `certificate.pfx`, or `EdiConfig.json` — that last one embeds Handy
connection keys, which are effectively credentials for someone's hardware. It also cross-checks
the **four** places the version is declared (three assembly attributes and `BepInPlugin`) and
warns when the local `BepInEx/core` is not the build being shipped, since in-game results proven
against a different runtime are not results about the release.

### Six tools lost their second write

`variants`, `retime`, `rederive`, `authored`, `impgrab` and `cfgaudit` each wrote to both the live
tree and `mod/single-mod`. They now write one. That is the actual reason to delete a mirror rather
than tidy it: every accident it caused was the same shape, one side updated and the other not, and
`release.py` reads the live tree at the moment the zip is built.

**A mirrored copy is a bug waiting for a deadline. Generate it instead.**

---

## 59. Edi bundled, the way the eroscripts mods do it

§58 shipped one archive and told players to fetch Edi themselves. That is not how mods in this
corner are distributed, and "download this, then download that, then put one inside the other" is
the step people get wrong. Edi is now bundled, fetched from its own GitHub release.

**One archive**, `PncEdi-2.1.0.zip`, 89.4 MB, extracted into the game directory. An Edi-less
variant for people updating the mod was built briefly and dropped: two downloads on a thread post
is a question every reader has to answer about themselves before they can start, and "which one do
I want" is a worse tax than 89 MB. The 220 MB `Edi.exe` compresses to that because it is a .NET
single-file host, so nearly all of it is stored assemblies.

Everything Edi needs sits together in `Edi/`:

```
Edi/Edi.exe            v1.0.4, unmodified from its GitHub release
Edi/EdiConfig.json     GalleryPath = .\Gallery, i.e. the folder beside it
Edi/Gallery/           the funscripts, 71 per variant
```

so the config points at the scripts by construction and a fresh install configures nothing.

### The shipped EdiConfig, and two locks on it

`EdiConfig.json` is where the secrets live, and not in a field called `key`: Edi names a connected
Handy **`The Handy [<connection key>]`**, so the *device names* are the credential. Anyone with one
can drive that hardware.

So the shipped file is hand-authored in `code/dist/EdiConfig.json` and tracked, rather than
scrubbed out of the live one at build time — a redaction that misses a field fails silently and
permanently, and it only has to be wrong once. It carries the built-in `Preview Device` and
nothing else; a real device appears the first time Edi sees it, on the player's machine.

The second lock is `release.py` reading **the live config**, extracting the actual secrets from it
— device names, the bracketed keys inside them, `Handy.Key` — and refusing to build if any of them
appears anywhere in the file about to ship. It also refuses any device but the preview one, any
`Handy.Key`, and anything merely *shaped* like a key (`[A-Za-z0-9]{6,}` in brackets), which covers
a stale copy or someone else's install.

That last check is the one that matters, and it is worth being concrete about why: the failure a
redaction cannot catch is a secret in a field nobody thought to redact. Tested with a fixture —
a key smuggled into an unrelated string is caught by the live comparison and by nothing else:

```
  clean:                        passes
  real device listed:           refused
  handy key set:                refused
  key hidden in a comment field: refused
```

### Pinned, not "latest"

The request was "the newest exe automatically". Half of that is right and half of it is a trap:

- an unpinned dependency makes the archive unreproducible — the same commit would build different
  zips on different days;
- and it means shipping, under our name, an Edi that nobody here has run against the game.

So `--update-edi` does the automatic part — queries the GitHub API, downloads the newest release,
hashes it, and prints the three constants to paste in — and stops there. Bumping the bundled Edi
stays a decision with a build and a run behind it. The pinned copy is verified against its SHA256
on every release build, exactly like the BepInEx packs.

```
$ python3 code/release.py --update-edi
latest is v1.0.4 (2026-08-16T00:19:00Z), Edi.exe 221 MB
  already pinned, nothing to do
```

### Two notes worth keeping

**Edi has no license file.** The repository publishes no licence, so redistribution is not
formally granted; it is bundled unmodified and credited, as the other mods on the thread do.
Recorded here because "the exe is a public download" and "we may republish it" are different
claims, and only the first is certain.

**Edi is Windows-only.** It is a WPF application, so the native-Linux instructions now say to run
it under Wine/Proton, or on another machine with `[EDI] Url` pointed at it — the mod only needs to
reach it over HTTP. The mod half is genuinely cross-platform; Edi is not, and the README should
not imply otherwise.

### A note on the README

It briefly carried both install paths behind `@IF BUNDLED@ … @ELSE@ … @END@`, which went away with
the second archive. Worth recording only because the reflex when two variants appear is to fork
the file, and the shared 80% — variants, configuration, troubleshooting, removal — is exactly the
part that then drifts. Branch inside one file, or have one variant.

---

## 60. The release tested on fresh installs — and the one bug that found

`PncEdi-2.1.0.zip` extracted into untouched 0.2.1 installs of both builds and launched. Both load.

| | |
|---|---|
| Windows build, Wine 11.15 | `System platform: Windows 10 (Wine 11.15) 64-bit` |
| native Linux build, `./start-pnc-linux.sh` | `System platform: Linux … 64-bit` |

Identical from there on both: BepInEx 6.0.0-be.785, `Loading [Post Nut Calamity EDI Integration
2.1.0]`, `[GalleryAliases] loaded 326 shared + 46 in-game-only mappings`, `[AI-AUDIT] ok`,
`Harmony patches applied`, `[EDI] Play filler`, scene change to `MainMenu`. The Linux run also
exits cleanly (`[EDI] application quitting -> Stop`).

### The bug: the game does not ship executable

`Post Nut Calamity.x86_64` is **mode 0666** in the shipped Linux build. `start-pnc-linux.sh` was
selecting candidates with `[ -x "$candidate" ]`, so it found none and refused to start:

```
start-pnc-linux.sh: no *.x86_64 game executable in …
```

It now tests `-f` and chmods on the way through, which it was already doing for `run_bepinex.sh`.
BepInEx's own script has the identical trap (`[ ! -x "${executable_name}" ]` → *"Please set
executable_name to a valid name"*), which is why our chmod has to happen **before** handing over
to it.

**A permission bit is not a fact about a file, it is a fact about how the file got there.** Any
trip through a zip, a Windows filesystem or a naive copy loses it, and a launcher that treats it
as identifying evidence refuses to start on a completely ordinary install. This only showed up
because the test used a genuinely fresh unpack rather than the working directory, where the bit
had been set by hand months ago.

### Edi, end to end, from the extracted archive

Worth doing because the archive now ships Edi and a config, and neither had been exercised.
`Edi/Edi.exe` runs under Wine, serves on `127.0.0.1:5000`, and reports the extracted folder as its
content root — so it read the shipped `EdiConfig.json`. Its own log then resolves rows out of the
`Edi/Gallery/` beside it:

```
[INF] Player event: Play [filler] at 0, Type:[filler], Loop:[True]
[INF] Player event: Play [Nun_Grab] at 0, Type:[gallery], Loop:[True]
[INF] Player event: Play [Nun_Cum_Gallery] at 0, Type:[gallery], Loop:[True]
[INF] Player event: Ignored not found [does_not_exist]
```

`Type:` and `Loop:` come from `Definitions.csv`, so that is the whole chain — shipped config →
`.\Gallery` → `Definitions.csv` → funscript — confirmed from the archive alone, including a
`*_Gallery` row from §52.

Note the HTTP status proves nothing: `/Edi/Play/does_not_exist` also returns **200**. Only the
`Ignored not found` line distinguishes a resolved name from an ignored one, which is worth knowing
before anyone tries to health-check Edi by curling it.

Edi rewrote `EdiConfig.json` on startup and changed **no value** — it round-trips the shipped file
exactly, and the only device in it afterwards is still `Preview Device`. Nothing of the author's
hardware appeared: Bluetooth is unavailable under Wine, and a Handy is reachable only with the key
that is deliberately not in the archive.

---

## 61. The archive is named for the game first

`PncEdi-2.1.0.zip` invited exactly one misreading, and it is the one that matters on a forum post:
that **2.1.0 was a version of the game**, which is on 0.2.1. Renamed so the two numbers cannot be
confused:

```
PNC0.2.1-PncEdi-2.1.0.zip
^^^^^^^^ the game it is for   ^^^^^ the mod, plain semver
```

### The game name cannot go in the version number, and that is a hard constraint

Worth stating because it is the obvious first attempt. `BepInPlugin` runs its version string
through **`SemanticVersioning.Version`** (`BepInPlugin::TryParseLongVersion`, read out of
`BepInEx.Core.dll`), and the three assembly attributes go through **`System.Version`**, which is
numeric-only. A version like `PNC0.2.1-2.1.0` therefore either fails to parse or lands in
pre-release metadata that nothing displays.

So the disambiguation lives in the two places that are free text:

| where | reads |
|---|---|
| archive name | `PNC0.2.1-PncEdi-2.1.0.zip` |
| plugin display name, and every log line | `Loading [Post Nut Calamity EDI Integration 2.1.0]` |
| shipped README header | `mod version PncEdi 2.1.0` / `built for Post Nut Calamity 0.2.1` |

and `release.py` now **enforces plain `MAJOR.MINOR.PATCH`** on the mod version rather than letting
a decorated one through to fail at load time:

```
release: mod version '2.1.0.4' is not MAJOR.MINOR.PATCH; BepInEx parses it as semver
```

(A four-part version is the realistic slip, since the assembly attributes want one. The existing
drift check catches the case where only *some* of the four declarations change; this one catches
the case where they all change together to something BepInEx cannot read.)

`release_stem()` composes the archive name from `GAME_SLUG`, `GAME_VERSION` and the version read
out of the source, so bumping either changes the filename and nothing else.

**Where a name is parsed by a machine, disambiguate in the part that isn't.** The version field
had no room for it; the filename, the display name and the README all did.

---

## 62. The repo is the mod; the game is a symlink

This directory *was* a Post Nut Calamity 0.2.1 install with the mod living inside it. Every path
in the project assumed that: the csproj referenced `Post Nut Calamity_Data/Managed/` two levels up,
`animcheck.py` read `.assets` out of the repo root, `.gitignore` opened with "this directory is a
game install" and defended a 2.3 GB tree with an allowlist, and `release.py` validated the local
BepInEx by looking at `ROOT`. It is now the mod and nothing else:

```
pnc-edi/
├── BepInEx/config/com.edi.pnc.cfg      the mod's whole presence in a BepInEx tree
├── BepInEx/plugins/PncEdi.dll
├── Edi/{Gallery,_reference,EdiConfig.json}
├── code/
├── game-windows -> ../PNC 0.3.1 Win     patched by code/deploy.py
└── game-linux   -> ../PNC 0.3.1 Linux
```

The 0.2.1 install moved to `../Archive/PNC 0.2.1 Win` **whole** rather than being deleted. Every
verified number in this project was measured from its assets — the 63/63 timing sweep, the clip
tables in `TIMING-AUDIT.md`, the two hand-built AI tables read out of its `Assembly-CSharp.dll` —
and none of that is re-derivable from a build the measurements were never made against. It is one
`PNC_GAME_DIR=` away at any time, and the sweep still reports 63/63 `ok` through it.

### Deploy is release, minus the three things a dev install is not

`code/deploy.py` imports `release.py` and calls its `bepinex_payload()`, `gallery_files()` and
`fetch_edi()` rather than reimplementing them, so the overlay you test is assembled by the code
that assembles the overlay you ship. That is §58's rule applied one level further out: the old
`mod/single-mod` was deleted because two trees that must agree should be *built* from one source,
and two game installs are the same problem with the same answer.

Three things deliberately differ, each because a dev install is not a player install:

| | release | deploy |
|---|---|---|
| `com.edi.pnc.cfg` | rewritten through `SHIPPED` | your live testing config, byte for byte |
| `Edi/EdiConfig.json` | the scrubbed template | your live one, and **only if the target has none** |
| `PncEdi-README.txt` | rendered for a named game version | not deployed at all |

The config row is the one that would have bitten: deploying the *shipped* config would silently
put `GodMode = false`, `HeatLockAutoHealRate = 1` and `EndGrabDelaySeconds = 30` into the install
on every build, i.e. quietly undo the testing setup each time you rebuilt to test something.
EdiConfig is user state — it carries device keys and the `Variant` choice — so a deploy writes it
once and never again.

### Patched on every build, not on every intention

`PncEdi.csproj` gained a `PatchGameInstalls` target that runs `deploy.py --dll-only` after the
build. PROJECT.md already records one full round of "the fix doesn't work" testing lost to a stale
deploy, back when deploy was a habit rather than a step; with the mod out of the game directory
that failure mode gets *easier* to hit, so the copy hangs off the build itself. It is
`ContinueOnError` and exits cleanly when no game is present — a missing game directory must never
be why a build fails — and `release.py` passes `-p:DeployToGames=false`, because building an
archive must not swap the binary you are currently testing.

Every write is skip-unchanged (byte compare; size-then-hash for the 220 MB `Edi.exe`), so a
re-deploy after a one-line change copies one file and a full re-run is a no-op in under a second.
`--check` exits non-zero when a target is out of date, which makes "is what I am about to launch
actually the working tree" a question with an answer.

### BepInEx to compile against no longer comes from a game

The csproj referenced `$(GameDir)BepInEx/core/`, which was fine while the runtime sat in the repo
and is a bootstrap loop now that it does not: you would need a deploy before you could build, and
a build before you had anything to deploy. `deploy.py --refs-only` extracts the pinned pack to
`code/dist/bepinex/core/` and the csproj references that, so a build depends on the *pin* and not
on any install. If it is missing the build stops with the command to run rather than fifteen
unresolved-reference errors.

### What this does not do

It does not port the mod to 0.3.1. `GAME_VERSION` in `release.py` still reads `0.2.1`, the archive
is still named for 0.2.1, and the deployed `PncEdi.dll` is HEAD's — the binary all the in-game
verification was done against. The one thing learned in passing: **the mod compiles clean against
0.3.1's `Assembly-CSharp.dll`**, same nine warnings, no errors, so nothing the mod references was
renamed or removed outright. A build against 0.3.1 differs from HEAD's DLL in 417 bytes, all of
them in the PE timestamp, the MVID and the debug-directory checksums — build metadata, no code.
That says the *compile surface* is unchanged; it says nothing about the two hand-built AI tables
or the animator state names, which is what `[AI-AUDIT]` and the slug harness are for.

---

## 63. Verifying the documentation against 0.3.1 before believing any of it

The game went 0.2.1 -> 0.3.1 and `Assembly-CSharp` grew 64% (613 KB -> 1002 KB, 321 -> 514 types).
Everything this project knows was measured against 0.2.1, so the first question is not "what is
new" but **"which of the things we wrote down are still true"**. `code/patchaudit.py` answers most
of it statically, and the answer is better than expected.

### The method: validate the analyser against the build it is known to describe

Every check below was run against **0.2.1 first**, where the mod is verified working and the docs
record the expected answer. That caught three separate bugs in the analyser before it was pointed
at 0.3.1, and each would have produced a confident, wrong finding:

| symptom on 0.2.1 | cause |
|---|---|
| every field on every type "missing" | the class stack only popped when another `.class` opened, so the first nested coroutine type swallowed the rest of its parent |
| still missing after that fix | ikdasm never emits a bare `}` - it writes `} // end of class 'X'` |
| `CameraSwapTrigger.ReturnToFirstPersonCoroutine` missing | a long return type wraps the signature onto a *third* line |
| `simulateMovement` missing | it is genuinely absent, and the mod already guards it with `FieldExists()` |

Only when 0.2.1 came back clean - all 147 Harmony patches, 23 typed reflections and 78 untyped
`Traverse` members resolving - was the 0.3.1 run worth reading. **An unvalidated static analyser
is a confident-sounding rumour**; the same rule as §48's "if the rule doesn't already explain most
of the data, it isn't a rule".

### What still holds

- **246 of 248 patch targets resolve.** Two do not, both on one class (below).
- **The AI guard tables are still exactly right.** `--ai` redoes §46 statically. On 0.3.1 the
  unhandled-state set is unchanged - `SpinningEnemyAI` (Grabbing, Shooting) and `ChargingEnemyAI`
  (PreparingCharge, Charging) - and the `StartGrab` callers that skip the `IsGrabbed` re-test are
  still `MimicEnemy` and the two dragons. **No new entry is needed**, including for the new AI
  class: `BrawlerEnemyAI` handles every non-`Dead` state and its `LandGrab` does re-test.
- **Every `AIState` enum is byte-identical.** This was the nastiest documented drift - the table
  keys on the raw int, so an inserted value repoints it while every name still resolves.
  `SpinningEnemyAI.Grabbing` is still 2, `ChargingEnemyAI.PreparingCharge` still 2.
- **The funscripts carry over untouched.** All **80** clips the set is scripted against exist with
  identical durations; `animsweep` reports **63/63 ok** and `gallerydiff` **0 mismatches** against
  0.3.1, the same figures as 0.2.1. One clip was removed in the whole game (`ImpMelee`) and it is
  not one of ours.
- **Every diorama, peek camera and enemy prefab survives.** All nine diorama objects, all five
  `AmbientAudioSource*`, all seven peek cameras, every `EnemyRemap` prefab key.
- **Legacy input still works**, which is the one that looked most dangerous: the game moved its own
  code to the new Input System (`InputManager`, `RebindMenu`, `InputSystemCharacterInput`, and
  `PauseMenuManager.pauseKey` is gone), and **every remaining `UnityEngine.Input` call in the
  assembly is vendor demo code**. But `PlayerSettings` is byte-identical between the builds across
  a 155-byte tail and differs only in one build-number int, and both ship the same input modules -
  so `activeInputHandler` is unchanged and every debug hotkey still binds. **A migration in the
  game's own code is not the same as the setting that would break ours.**

### What does not hold

**`GalleryTabController` was refactored, and one of the two breaks is fatal.** A `[HarmonyPatch]`
on a method that does not exist throws at patch time and takes the whole plugin down:

| 0.2.1 | 0.3.1 |
|---|---|
| `SetActiveTab(GameObject tab)` | `SwitchTab(int index)` |
| `dioramasTab` / `enemiesTab` / `peekScenesTab` fields | `tabs`, a `Tab[]` |

The new `Tab` carries `content`, `tabButton`, `firstInContent`, `dioramaGalleryBool` and
`enemyGalleryBool` - so the tab now *declares* what it is instead of being identified by comparing
GameObject references, which is what the mod was doing.

### The finding that is not a break

**Vanilla now does what `GrabEnemyProtection` does.** `EnemyAI` gained
`hideInsteadOfDestroyOnGrab` and `preserveHealthDuringGrab`, `GrabScreen` gained
`RegisterHiddenEnemy` + `hiddenEnemyToRestore`, and there is a new `IGrabHideable` interface with
`EndGrabHidden(float remainingHealth)`. The IL reads: if the flag is set, register with
`GrabScreen` and `SetActive(false)`; otherwise `TransitionToDead()` and spawn the death effect.
`EnemyAI.ResetGrabTransientState` is new too - §17b's "anything hidden mid-action needs its
transient state reset on the way back", now vanilla's own.

Nothing binds any worse for it, so this is not urgent. But the mod blocks `Object.Destroy` to keep
grabbed enemies alive, and vanilla no longer necessarily destroys them - which makes every §19/§44
lesson ("blocking a vanilla `Destroy` leaves one-shot state latched") live again from the other
direction. **Before keeping something alive that vanilla deletes, check that vanilla still deletes
it.**

---

## 64. Porting to 0.3.1: the blocker, and wiring the new scenes that need no rebuild

Retargeted to game 0.3.1, mod version **2.2.0** — `PNC0.3.1-PncEdi-2.2.0.zip`. The 0.2.1 build is
not carried forward; the last archive for it is `PNC0.2.1-PncEdi-2.1.0.zip` and the naming from
§61 is what keeps the two legible side by side.

### The blocker

`GalleryTabController.SetActiveTab(GameObject)` became `SwitchTab(int index)`, and the three
GameObject fields became a private `Tab[] tabs`. A `[HarmonyPatch]` naming a method that does not
exist throws at patch time and takes the whole plugin down, so nothing else in the port was
testable until this was rewritten. `patchaudit.py` now reports **248/248**.

The new shape is better and the rewrite leans on it. Before, the mod asked "is the tab I was handed
the same GameObject as `dioramasTab`?"; now each `Tab` carries `dioramaGalleryBool`, so it asks
"does this tab say it is the dioramas tab?". Nothing assumes a slot index — `defaultTabIndex`
exists and the order is authored in the inspector. `Tab` is a *private* nested type, so it cannot
be named in C#; the two `FieldInfo`s are resolved off the first instance seen.

### Wiring the new content that needs no rebuild

Six dioramas and four peek scenes, all config. The D-slots did not have to be guessed — **the
unlock trigger objects name their own slot**, which is the kind of self-identifying evidence §26
found for the unlock boxes in the first place:

| slot | unlocker object | scene | ms |
|---|---|---|---|
| D10 | `DragonD10Unlocker` | dragon squat ride | 750 |
| D11 | `WendigoD11Unlocker` | wendigo squat ride | 750 |
| D12 | `GoonShroomD12Unlocker` | goonshroom gangbang | 1500 |
| D13 | `NunWatersportsD13Unlocker` | nun watersports | 1333.33 |
| D14 | `PlantBJD14Unlocker` | plant gangbang | 1000 |
| D15 | `SerpentD15Unlocker` | serpent wall blowjob | 750 |

`DioramaAmbientMap` gains D10–D15, `Patterns` gains their ambient audio aliases, and `PeekClipMap`
/ `PeekGalleryMap` gain the four peepholes (`GargoylePeep`, `GravyPeep`, `Peephole_Serpent`,
`Peephole_Werewolf`). **The `Bind()` defaults are what changed**, not the config's additive
override lists — the §33/ownership rule: the table ships in the DLL so a new version reaches
everyone, whatever config they already have. The live `com.edi.pnc.cfg` was hand-edited to match,
because BepInEx only rewrites the file on a clean run and `release.py` aborts on an undeclared
difference from the documented default.

**`Patterns` matches the AudioClip name, not the object name**, and the clip PPtrs on the diorama
AudioSources are `{m_FileID: 0, m_PathID: 0}` — assigned at runtime by script, so which clip an
object plays is *not* statically readable. Five of the six audio names are exact (`wendigo squat
ride`, `goonshroom gangbang`, `nun watersports`, `plant gangbang`, `Serpent wall blowjob`); D10 is
carried as `dragon squat ride|Dragon sex 2` because the animation and the only new dragon audio
clip do not share a name. `DiagnosticMode` exists for exactly this and settles it in one walk-past.

### Two things found that are code, not config

**A GoonShroom grapple currently dispatches `imp_1/2/3`.** The patch notes say grapplers are now
imps *and* goonshrooms; the tier dispatch is gated only on `GrappleScreenobject.IsGrappling` and
builds its name as `CfgImpPrefix + count`. So a goonshroom grapple plays a real imp script — which
is worse than a gap, because nothing announces it. (The *gameplay* tweaks are safe:
`ImpGrappleGate.IsImpGrappleSession` tests every grappling enemy with `IsImpEnemy` and fails
closed.) The fix is for the prefix to follow the grappler family.

**The transformed Blinded Beast is not distinguishable from its first stage by slug.**
`BlindedBeastGrabScreen` and `BlindedBeastTransformedGrabScreen` both declare exactly `Loop` and
`Cum`, and the mod's slug is enemy key + state name — so both stages produce `blinded_beast_loop`
/ `blinded_beast_cum` while their clips differ (556/3667 against 750/3500 ms). The **controller
name** is the only discriminator, and `[GRAB-ANIM]` already logs it. Note the *gallery* side has no
such problem: `Gallery_BlindedBeast_Grabbed` names its states `Start`/`Start_T`/`Cum`/`Cum_T`, so
the viewer route splits cleanly. **The same scene can be ambiguous from one route and unambiguous
from the other** — §52's gallery split was the mirror of this, and the fix will be too.

Both are proven by `code/slugharness`, which gained the three new enemies' states: it prints the
exact slug each animator state produces, so neither of these had to be inferred from play.

---

## 65. The guessable signal was outranking the game's own label

Asked why the port was looking at audio at all. The answer was that `Patterns` — a hand-maintained
list of AudioClip name fragments — is how a diorama is *identified*, on both routes. The better
answer is that it should not be, and the question exposed an inversion that had been there since
before §26.

Every diorama carries a `GalleryUnlockTrigger` with a `galleryID`, and `DioramaAmbientMap` turns
that into the script. The mod already reads both. But:

| route | was | now |
|---|---|---|
| in-world | audio pattern identifies; box only gates *whether* it plays | **box identifies**; audio is the fallback |
| gallery menu | audio scan of the entry's hierarchy, `galleryID` only if that found nothing | **`galleryID` first**, audio only where there is no id |

So the signal that has to be extended by hand for every new scene, and can be wrong, was
outranking the label the game assigns itself. §26 found the boxes and used them for the release
mechanic and later for the playback gate — it just never moved *identification* onto them.
**Where the game already labels a thing, read the label** — the same lesson, one step further in.

### What the boxes actually say

Parsed out of the assets by hand (MonoBehaviour typetrees are not shipped, so `m_Script` is
matched against the `GalleryUnlockTrigger` MonoScript and `galleryID` read as the first
length-prefixed string after `m_Name`):

- **0.2.1: 9 boxes, D1–D9.** Every diorama has one.
- **0.3.1: 16 boxes, D1–D15** — including all six new dioramas, **and two `D2`s**.

The duplicate D2 is the patch notes' *"fixed diorama 2 not unlocking when it was on the secret room
version of the room"*: they added a second box for the other version of that room. It needed no
handling, because `DioramaUnlockTriggers.Entries` is a flat `List` and every query iterates it —
a galleryID was never assumed unique. **A dictionary keyed on the id would have silently kept one
box and dropped the other** (§42's "a dedup key made of position is a key made of luck", avoided
here by not keying at all).

Also worth keeping: an earlier pass concluded "D8 has no unlock box" by searching *GameObject
names* for `*Unlock*`. It has one; the mod finds boxes by component type, and the name search was
simply the wrong instrument. **Do not answer a question about components by searching names.**

### What it buys

D10–D15 are now identified exactly rather than by a pattern nobody has confirmed. The speculative
`dragon squat ride|Dragon sex 2` alias is deleted — it was a guess, and a dangerous one, since
`Dragon sex 2` could as easily be a dragon *grab* scene's audio and would have fired a diorama
during a grab. `Patterns` stays, because peek holes have no box and the gallery menu can be handed
a hierarchy with no id, but it no longer decides anything a box can answer.

**The residual, and it is visible rather than silent:** a diorama identified by its box whose audio
matched no pattern has no `AudioSource` for `AmbientReleaseGaze.NoteCandidate` to anchor on — it
declines a null source — so the scene plays but its look-to-release does not arm. The log says
`box D13 -> ambient_nun_watersports (no ambient pattern matched here)`, which is the cue to add the
pattern. Playback working while the release does not is a strictly better failure than §28's dead
gate, where a boolean that was always consulted and only sometimes initialised made the outcome
depend on unrelated history.

---

## 66. Two grapplers, and one enemy with two grab screens

Both of these were found by static analysis during the wiring pass (§64) rather than in play, and
both are the shape where **the mod plays a real scene that is the wrong one** — which nothing
announces, and which no amount of reading `[ALIAS-GAP]` would ever surface.

### A goonshroom grapple was playing the imps' scripts

Game 0.3.1's patch notes: *"Grappler enemies (Imps, Goonshrooms) are now persistent."* The cling
dispatch names its scene as `CfgImpPrefix + count` and is gated only on
`GrappleScreenobject.IsGrappling`, so a goonshroom clinging to the player played `imp_1/2/3`.

The *gameplay* half was already safe and is worth noting as the contrast:
`ImpGrappleGate.IsImpGrappleSession` tests **every** grappling enemy with `IsImpEnemy` and returns
false unless all of them are imps, so the imp-specific tweaks never fired for goonshrooms. Same
file, same feature, one half fails closed and the other borrows another creature's scripts.
**Enemy-specific behaviour and enemy-specific *content* are two separate assumptions, and gating
one does not gate the other.**

`GrappleEnemyProtection.ResolveGrappleFamily` reads the family off `grapplingEnemies`, and
`GrapplePrefixMap` (`imp=imp_;goonshroom=goonshroom_`) turns it into the prefix. A family not in
the map dispatches **nothing** and logs why, rather than falling back to imps — a gap is inert and
says so, a wrong scene is silent and plausible. An unreadable enemy list still falls back to
`CfgImpPrefix`, because imps were the only grappler that existed and that is what every verified
log was produced against.

The delayed-loop branch moved onto the same prefix (`imp_` → `imp_grab_loop`, `goonshroom_` →
`goonshroom_grab_loop`) instead of hardcoding the imp row.

Convenient result: the grapple dispatch produces `goonshroom_1/2/3` from the count, and the gallery
viewer's own states are `GoonShroom 1/2/3` → the same slugs. The two routes agree without a split.

### The Blinded Beast collides with itself

The two-stage miniboss has two grab screens, `BlindedBeastGrabScreen` and
`BlindedBeastTransformedGrabScreen`, and **both declare a state called exactly `Loop` and one
called exactly `Cum`**. The slug is enemy key + state, so both stages resolve to
`blinded_beast_loop` — while their clips are 556/3667 ms against 750/3500 ms, so one funscript
cannot be right for both.

The only thing that differs is the **controller**, which `[GRAB-ANIM]` has logged all along.
`GrabHooks.ApplyControllerVariant` appends a suffix when the live grab-screen controller matches
`GrabVariantSuffixes` (`BlindedBeastTransformedGrabScreen=_t`), giving `blinded_beast_loop_t`.
Longest key wins, so a shorter `BlindedBeast` added later cannot shadow it.

Two things about where that gate sits:

- It applies **only while `GrabScreen.IsGrabbed`**. `BuildGalleryName` also serves the camera-swap
  interact scenes, which have their own animator; without the gate those would be resolved against
  whatever controller the previous grab left in `CurrentAnimator`. That is §28's dead gate in
  miniature — a value that is always read and only sometimes current — and it is cheaper to
  prevent than to diagnose.
- The **gallery route needs none of it**: `Gallery_BlindedBeast_Grabbed` names its states
  `Start`/`Start_T`/`Cum`/`Cum_T`, so the viewer splits cleanly on its own, and it does not even
  reach this code (it goes through `PeekGalleryMap.BuildCombinedSlug`). **The same scene can be
  ambiguous from one route and unambiguous from the other** — §52's gallery split was this in
  reverse, where gameplay was fine and the viewer was not.

### The harness now under-reports, deliberately

`code/slugharness` compiles the real `NameRemap` and `GalleryTable` so it cannot drift from the
mod — but the variant layer is above them, in `GrabHooks`, and needs a live controller. So the
harness prints one `blinded_beast_loop` row where the game produces two. There is a comment
saying so at the table. **A tool that cannot see a layer should say which layer**, rather than
being quietly incomplete.

---

## 67. Funscripts for the ten new dioramas and peek scenes

`code/scenes031.py` derives all ten - D10-D15 and the four peepholes - and the sweep is now
**73/73 ok** on timing, up from 63/63, with `Definitions.csv` at 81 rows. Each was looked at
before it was measured, which is the part that mattered: the generic proxy is wrong for almost
all of them, and in three cases the *first* scene-specific proxy was wrong too.

### What the looking was worth

**D10 nearly shipped measuring a knee.** The first band for `dragon squat ride` was chosen by eye
and its right edge clipped the partner's raised leg, so the topmost pale pixel in it was sometimes
the knee. Rendering the mask and the picked pixel over the frames showed it immediately; picking
the band by *which columns actually travel* instead put it on the shaft, and a tight 10x crop
confirmed the shaft is what is there. **Choose a region by what varies in it, not by where the
interesting thing looks like it is** - and then look at the mask, not just its output.

**Three of the six dioramas have no measurable stroke.** `goonshroom gangbang` moves 5 px on a
181 px sprite, `nun watersports` is two poses one pixel apart, `serpent blowjob wall` holds for
four frames and then shifts 17 px. All at or under the 3%-of-height floor `motion_proxy` already
treats as jitter. Those are **authored on a measured period**: the period is a fact, the shape is a
decision, and the docstrings say which is which. Reproducing a 5 px wobble would be scripting
pixel noise and calling it measurement.

### Two new proxies, and the trap in each

**`moving_mass`** - the centroid of whatever differs from the median frame - is for the peek
scenes, which are full-bleed room art behind a keyhole vignette. There is no alpha trim, so the
silhouette proxy is dead; that is `Wendigo_Continued`'s problem. But the *room is static*, which
makes the median frame a background plate worth subtracting.

Its failure mode is specific and worth naming. `GargoylePeep_Loop`'s halves are the same motion -
frames k and k+5 differ in 1.1-2.5% of pixels - yet the proxy returned `65, 96, 96, 86, 100` for
the first half and `58, 48, 89, 0, 15` for the second. **Both cannot be true of two identical
halves, and that contradiction is what condemns the proxy**: where the halves are near-identical
the plate sits close to both, so the residual is the 1-2% that differs rather than the bodies, and
its centroid wanders. `peek_gravy_bath` ran the same proxy and repeated *exactly*, which is the
evidence its residual is tracking real periodic motion. **A repeat is how you tell a residual
proxy from noise; its absence, where the pixels prove a repeat exists, is how you tell noise.**

**`squat_ride_shaft`** measures the shaft tip where the rider's underside crosses it. It shipped
broken for one run: it took its band as a fraction of each frame's *own* `.shape`, and sprites are
alpha-trimmed per frame to different sizes (`dragon squat ride` runs 363x281 down to 355x284). So
the band landed on a different absolute column every frame and the y was read against a different
origin - it returned a near-flat `33, 26, 26, 26, 26, 28` for a shaft that travels 27 px, and the
sweep called a correct curve **inverted at -0.84**. §33 already said alpha-trimmed sheets are not
registered to each other; the corollary is that **a proxy taking `sprites` has to align them
itself, because nothing upstream does**. Aligned, the same scene reads +0.99.

That is also the argument for registering proxies rather than marking scenes `AUTHORED`: the
alignment bug was only visible because the sweep re-measured the curve against a named proxy. Four
of the ten now read +0.99 to +1.00; the six that cannot be measured say `auth` and say why.

### `SPLIT`, the mirror of `ONESHOT`

`stroke_period` misses a repeat on full-bleed peek clips: `GravyPeep_Loop`'s halves differ in 1.2-
2.2% of pixels at a mean |diff| under 0.8/255 and it still reports reps=1, because ~95% of every
frame is identical static background and that swamps the lag score. Without an override the sweep
measures a whole-cycle script against the clip's 1333 ms instead of the stroke's 667 and reports
2.5 cycles OFF. `proxies.SPLIT` states the true rep count where the pixels prove one; §33 is the
same failure from the other side, where a 1 px offset pushed a lag score *past* its threshold.

### `animcheck --motion`

The variance map that found the region in every one of these scenes is now a flag rather than a
scratch script. It answers "what moves at all" before anything is chosen to measure, which is the
question `--sheet` cannot answer on a full-bleed frame. Read it for *where* the change is
concentrated: a thin outline all round a body is that body translating a pixel or two, a bright
blob in one place is a part moving against the rest, and only the second is worth a proxy.

---

## 68. Checking the ten new scenes for the gallery split — and what it found instead

§52 exists because the gallery viewer plays its own `Gallery_*` clips and twelve of them are a
different length from the in-game clip, so one funscript cannot be whole-cycle correct for both.
That question was never asked of the ten scenes added in §67. Asking it:

**The ten are clean, for two different reasons.**

- **The six dioramas have no gallery twin at all.** Each clip exists exactly once in the assets and
  no `Gallery_*` clip corresponds to it, which is what PROJECT.md already recorded for the original
  nine. Worth stating *why* the keyword search looked alarming: `Gallery_Goonshroom_Gangbang_Loop`
  and `_Cum` exist, and they are not the D12 diorama's. They belong to
  `Gallery_Goonshroom_Grabbed`, the goonshroom **grab screen**'s gallery controller (states Loop,
  Cum, GoonShroom 1-3). Exactly the `imp gangbang` (diorama) versus `Imp_Grab_Loop` (trio grab)
  relationship, with the same word doing both jobs.
- **All four peek scenes do have their own gallery clip, and all four are the same length.** So no
  split - the same finding as the original seven, and now checked rather than assumed:
  `gallerydiff.py` carries the four pairs, so a future game version re-asks the question by itself.
  It reports 33 rows, 12 mismatched, 0 still sharing a script.

### The three enemies still to do are the opposite, and systematically so

Seven of their nine in-game/gallery pairs differ, and **six of the seven differ by exactly the same
ratio, 0.889 = 8/9**:

| | in-game | gallery | ratio |
|---|---|---|---|
| serpent loop | 875 | 777.78 | 0.889 |
| beast start `_T` | 750 | 666.67 | 0.889 |
| beast cum `_T` | 3500 | 3111.11 | 0.889 |
| goonshroom start | 750 | 666.67 | 0.889 |
| goonshroom cum | 3125 | 2777.78 | 0.889 |
| goonshroom grapple tier | 750 | 666.67 | 0.889 |
| beast cum | 3666.67 | 3777.78 | 1.030 |

8/9 is a frame *rate* difference, not a frame *count* one: the same frames played at 9 fps in the
viewer and 8 fps in play. That makes the split predictable rather than a per-scene surprise -
**expect nearly every new enemy row to need a `_Gallery` twin**, and expect the twin to be the
master replayed at 8/9 the length rather than a differently-shaped curve. `rederive.py`'s existing
gallery variants already work that way: they read the master's *file* rather than hardcoding it.

### One scene, two names

`peek_werewolf_ride`'s gallery clip is **`Blinded Beast Ride Gallery Loop`**. The peephole's own
clips (`Peephole werewolf Start/Loop/End`), its camera (`WerewolfPeepCamera`) and its ambient audio
(`Werewolf bouncing on it`) all say werewolf; the gallery says the miniboss. `PeekGalleryMap` and
`PeekClipMap` now carry both spellings, because the gallery entry is matched on the name the
*viewer* uses.

The key is `Blinded Beast Ride`, **with the "Ride"**, and that is not incidental. A bare
`BlindedBeast` key is a substring of `Gallery_BlindedBeast_Grab_Start` and would hand the
miniboss's own grab screens to a peephole script - which is precisely the collision `PeekClipMap`'s
own config comment was written about ("every peek trigger in the game is named P1, P2, P3..., the
clip is the only thing that says which peephole it is, and the alias table's per-enemy substring
matcher would otherwise claim it for that enemy's grab scene"). **When adding a substring key,
check it against the names you do *not* want it to match, not just the one you do.**

---

## 69. The PPtr bug that used to help stopped helping

Asked whether the differing gallery versions needed extra funscripts. Checking that turned up
something else: `BlackSerpent GrabScreen` has 7 sprite frames and `animcheck.clip_frames` read it
as **zero**.

PROJECT.md has warned about this since §48: *"A PPtr's `m_FileID` is part of its identity. Keying a
lookup on `path_id` alone across several loaded assets files silently resolves pointers to objects
in the wrong file. In `animcheck` this happened to **help** ... which is worse than failing, because
it produced right answers for a year with no reason to look."* `clip_frames` built
`objs.setdefault(o.path_id, o)` across all three `.assets` files, so the first file loaded won every
collision. The serpent's grab screen lives in `resources.assets`, its pointers are `m_FileID = 0`
meaning *that* file, and every one of them resolved into `sharedassets0` as an unrelated
`Texture2D` - then got filtered out by the `type.name == "Sprite"` test. Silently, to zero.

**Nothing measured was wrong.** Of 94 clips this project scripts against, exactly two were
affected - `GooperGrabScreen` and `GooperGrabScreenCum` - and those are the two §48 already
identified as the accidental-help case: the discarded pointers were the `Goop_overlay` drip layer,
so the body frames survived. The ten scenes added in §67 all resolved fully. That is the whole
impact, and it was worth measuring before touching anything: **a bug that has been producing right
answers is still a bug, but it is not an emergency.**

### Fixing it broke the thing it had been propping up

With `m_FileID` honoured, the Gooper overlay sprites resolve properly - and `_first_pptr_curve`,
which exists to cut a multi-curve clip down to its first curve, let one curve-start through: 8
frames became 9 and 14 became 18. It was trying to distinguish "a second object" from "page 2 of
the same atlas" by sheet name, because `GhoulGrabCum` is one curve that restarts its numbering at
`_0` partway through and would otherwise be cut in half.

`GhoulGrabCum` declares **one** PPtr curve, and `clip_frames` only calls `_first_pptr_curve` when
`genericBindings` reports more than one. **The counter-example it was guarding against cannot
reach it.** So the rule collapses to the plain one - cut at the first frame number that does not
increase - which gives 8 and 14 exactly. A guard written for a case that cannot occur cost the
case that does.

### And the docstring's other claim was an artefact of the bug

It said multi-curve clips were "the two Gooper clips and nothing else". With the pointers resolved
correctly there are **13**, including `DragonGrab`, `GhoulGrabCumContinue` and four `Gallery_*`
clips. The other eleven's second curves had been resolving to the wrong file and vanishing, which
is exactly why nobody had seen them. **When a lookup is known to silently drop things, every count
taken through it is a lower bound.**

Verified unchanged after the fix: `animsweep` 73/73 ok on 0.3.1 and 63/63 on the 0.2.1 control,
`gallerydiff` 33 rows with 0 still sharing, no new polarity flags (`Gooper_Start` in fact stopped
being one).

### What the original question was actually about

Nothing needs an extra funscript among the ten. `Definitions.csv` has no playback-rate column -
Edi slices a file to `[StartTime, EndTime]`, rebases and loops, and cannot time-scale - so a
length mismatch can only ever be fixed with a second, rescaled file. The six dioramas have no
gallery clip at all and the four peeks' gallery clips are the same length, so one file serves both
routes in every case (§68).

---

## 70. Documentation restructured: a learnings directory, and a TODO that is only TODO

Three files had grown into one another. `PROJECT.md` was 874 lines of which ~750 were accumulated
rules; `TODO.md` was 1017 lines of which most described work already finished; and both were loaded
in full whenever anything was consulted, because there was no way to load part.

```
PROJECT.md    874 -> 179    what the project is, layout, build/deploy/release, and a map to the rest
TODO.md      1017 -> 126    open work only
learnings/      0 -> 13 files + an index
CHANGELOG.md   unchanged    still the narrative record
```

### Why a directory rather than a bigger file

The point is **not having to load it all**. A single file has to be read whole to be searched; a
directory can be picked from. So the index carries, for each file, a *when to read it* line and a
keyword list, and every file opens with the same three-line header. Two ways in, both cheap:

- know the topic → the index table
- know a symptom or an identifier → `grep -ril "SetActive" learnings/`, `grep -rn "m_FileID" learnings/`

The split is by **task**, not by chronology: `funscript-timing.md` is what you want while retiming,
`grab-and-ai-mechanics.md` while touching grab dispatch, `porting-a-new-game-version.md` when the
game updates. Thirteen files, 90-200 lines each - small enough that loading the right one costs
almost nothing and the wrong one costs little.

Each claim keeps its shape from the old document: **bolded rule, then the concrete case that
produced it**, with `§n` back into the CHANGELOG. That was already the house style and it is a good
one for this - a rule with its evidence attached can be judged rather than obeyed.

### Moving it without losing it

The extraction was scripted rather than retyped: sections were sliced out of `PROJECT.md` verbatim
and the 36 paragraphs of the Unity section assigned to files by index, with an assertion that every
paragraph landed **exactly once**. Two categorisation errors surfaced while doing it - Edi's own
slice semantics had been filed under "Harness gotchas" alongside Harmony, and became
`edi-integration.md`; the newest learnings from §63-§69 were only in the CHANGELOG and were folded
in.

Closed content was checked before deletion, not after: every distinctive marker from `TODO.md`'s
bug diagnoses (`PendingSceneEntryGameOver`, `m_IsActive`, `CanBeGrabbed`, `no cum state captured`)
was confirmed present in `CHANGELOG.md` first. **Deleting a record is safe only once you have
looked for the copy you believe exists.**

### Two things the restructure itself turned up

**`learnings/` was invisible to git.** `.gitignore` is an allowlist - `/*` then `!` for each opted-in
path - so a new top-level directory is untracked until it is named. It was, for as long as it took
to run `git check-ignore`. The rule is now written into the file itself, because the failure is
silent: the work appears to exist and simply is not committed.

**Retargeting the citations broke the line budget.** Thirty-five comments and docstrings cited
"PROJECT.md's <rule>" for rules that had moved, which would have left dead pointers; rewriting them
to the owning learnings file lengthened the lines past 100 columns. Fixed by rewrapping only the
lines that mention `learnings/`. **A reference that no longer resolves is worse than no reference**,
so they were worth updating - but a bulk textual substitution changes more than the text.

## 71. The three new enemies scripted — the 0.3.1 port finished

The last substantial piece of the 0.3.1 port. Black Serpent, Blinded Beast and GoonShroom had
their grab screens wired since §66 and nothing to play: eleven slugs the slug harness printed as
`UNMAPPED`, which is inert and visible exactly as intended, and no use to anyone.

Now: **twenty rows**, eleven derived from the frames and nine gallery twins built from those.
`animsweep` goes 73/73 → 93/93 with no timing error and no new polarity flag; `gallerydiff` goes
33 rows/0 sharing → 44 rows/0 sharing. Mod **2.3.0**, because the animator-state table ships in
the DLL.

```
Serpent_Loop           875   x2     BlindedBeast_Start     556  x2     GoonShroom_Start   750  x2
Serpent_Cum           3375   x1     BlindedBeast_Cum      3667  x1     GoonShroom_Cum    3125  x1
                                    BlindedBeast_Start_T   750  x2     goonshroom_1/2/3   750  x2
                                    BlindedBeast_Cum_T    3500  x1
```

`code/grabs031.py` holds the derivations, the way `code/scenes031.py` holds the dioramas' — each
scene a function whose docstring carries the measured series and the polarity argument, so the
curve can be disagreed with rather than only re-run.

### One geometry, read two ways, and the two are opposites

Three of the four stagings are the same picture to a pixel counter — a creature filling the frame,
a few hundred pixels of shaft doing the work — and the sign is *not* recoverable from the pixels.

- **Sleeve** (§39's gooper, and now the Black Serpent's paizuri). The shaft passes **through** the
  body and the tip emerges on the far side. Total length is fixed, so the frame showing the most
  tip is the frame with the most of it *inside*: maximum protrusion is position **0**.
- **Rider** (§67's squat-ride dioramas, and now the Blinded Beast and the GoonShroom). The body
  sits **on** the shaft and the exposed part is below it. More showing means the rider has lifted:
  maximum exposure is position **100**.

Both proxies are "count the pale pixels near the middle". Both produce a clean, high-range,
well-correlated series. They disagree about which end of it is deep, and nothing in the
measurement can tell you which you are looking at. **Ask what the shaft passes through before
normalising anything** — it is the only step in this work with no numerical check behind it.

The serpent is where it nearly went wrong, and the thing that caught it was the *cum* clip. Its
middle fourteen frames are her mouth on it, and there the cleavage count collapses — not because
the scene got shallower but because her head is in front of the band. Chasing that produced the
right reading of the loop as well: the count is an exposure measurement in one clip and an
occlusion measurement in the other.

### Cum scenes are phase changes, not stroke rates

Four of the five cum clips change *what the camera is looking at* partway through, so no single
proxy measures the same thing at both ends — the §48 `Nun_Cum` situation, and handled the same
way: read the events off the frames and write those.

| clip | what it actually does |
|---|---|
| `BlackSerpent GrabScreen_Cum` | paizuri (f0-f4), her mouth on it in a **six-frame sub-loop that repeats exactly** (f5-f20), a pull-off (f21-f23), then f24-f26 return the loop clip's own f4, f5, f6 — so the curve ends on the loop's positions and hands back without a seam |
| `Blinded Beast Grabscreen Cum` | seats at f5 and stays seated for 23 frames; the white fluid at the bottom of frame first appears at f11 and steps at f12, f14, f16, f17, f20 (6, 47, 121, 155, 233, 453 px), which is a climax happening *while seated* |
| `Blinded Beast_T Grabscreen Cum` | two hard lifts (f3, f6) then fourteen frames deeper than the loop clip ever reaches; from f23 the pink mask stops measuring the body and starts measuring fluid |
| `GoonShroom_GrabscreenCum` | the exception — the same proxy works end to end, whole-frame difference a flat 3-8 for every pair, so it is measured throughout and nothing is written |

The five that change geometry are registered in `proxies.AUTHORED` with a note saying why: not
because their positions were invented — every one came off the frames — but because a correlation
taken over the whole clip compares two different scenes. Without that they would read `INV`
forever and every future sweep would re-flag work that is correct.

### §68's predictions, checked against the sprite lists

§68 read the gallery split off the clip *lengths* and predicted eight twins, six of them a flat
8/9 rescale. Reading the **sprite lists** rather than the durations confirms it and corrects one:

| | evidence | treatment |
|---|---|---|
| `Serpent_Cum`, `BlindedBeast_Start` | same sprite names, same rate, same ms | **no twin.** One script is correct for both |
| beast start `_T`, beast cum `_T`, goonshroom start/cum/1/2/3 | identical sprite lists at 8 vs 9 fps | frame remap, which then *proves* the 8/9 uniformity rather than assuming it |
| `BlindedBeast_Cum` | same sprites plus one inserted frame, `BlindedBeast-Cum2_15`, which the in-game clip skips | frame remap; only that segment stretches |
| `Serpent_Loop` | a **redrawn** sheet — `sex-Sheet 1_0..6` against `sex-Sheet_0..6` | no shared names to anchor on, so a plain 8/9 rescale |

§68 called the beast cum "different frame count — own derivation". It is not: it is the same
animation with a frame the gameplay clip drops. That is a remap, and the difference matters —
a fresh derivation would have thrown away a curve that was already right.

The redrawn serpent sheet is worth one more line. Its twin is a blind rescale, with no frame
correspondence behind it, so the sweep is the only thing standing between it and being wrong —
and it comes back **+0.98** against the redrawn sprites. Same picture, drawn twice.

### The bug the extra frame found

`_remap_by_frame` exists to handle exactly the `BlindedBeast_Cum` case, and could not. Its
docstring even names the case — "the gallery Plantasha cum includes a frame gameplay skips" — and
the remap still produced a twin **identical to its master except for the closing point**, which is
not what a clip 111 ms longer looks like.

`_frame_anchors` numbered each clip's distinct frames 0, 1, 2 … and joined the two timelines on
that number. That is the same thing as joining on frame identity only while both clips hold the
same frames in the same order. One insertion and every later frame maps to its neighbour's slot.

Fixed by anchoring on the sprite **name**. It corrects `Plantasha_Cum_Gallery` too, which had been
carrying a 111 ms misalignment from f15 on since §53 — the one existing scene with the same
insertion, and the one the docstring was written for.

**A tool that documents a case it does not handle is worse than one that says nothing**, because
the documentation is what stops anyone checking. The check that would have caught it is cheap and
is now what the twins are built on: if the two clips are the same length, a remap must be the
identity, and if they are not, it must move something other than the last point.

### The serpent's hypnosis is not a scene

`Black_Serpent_Hypnosis_Start/Loop/End` are 1000 ms each and the §66 harness printed all three as
`UNMAPPED`, which looks like three missing scripts. They are mapped to `-`.

The evidence is in `BrawlerEnemyAI` — `hypnosisStartRange`, `hypnosisLookSpeed`, `hypnosisLookHeight`,
`maxHypnosisDuration`, `StopHypnosis`, `EndHypnosis` — and in where the clips live: on the
**enemy's own controller**, beside `Black_Serpent_Idle` and `_Walk`, not on `BlackSerpent GrabScreen`.
There is no cum clip and no grab. It is crowd control that turns the player's head, and a sexual
script over a combat mechanic is a wrong scene, which is the one failure mode this project treats
as worse than a missing one.

Every non-H state of all three enemies is mapped to `-` for the same reason — idle, walk, attack,
charge, explode, and the beast's four transformed states. The harness now resolves **every** state
of every enemy, gameplay and gallery: zero `UNMAPPED`.

### Where it all went

| | |
|---|---|
| `code/grabs031.py` | new; the eleven derivations and the nine twins |
| `code/proxies.py` | five new scene proxies, and `_canvas` factored out of the bottom-align boilerplate every one of them needs |
| `code/rederive.py` | `_frame_anchors` joins on sprite name |
| `code/animsweep.py`, `code/gallerydiff.py` | the twenty rows, so both tools re-ask their question next version |
| `GalleryTable.cs` | the three enemies' states, in the DLL where every other enemy's live |
| `com.edi.pnc.cfg` | nine gallery redirects and seven in-game pins, beside the twelve from §53 |

---

## 72. Escaping a grab was dead on 0.3.1 — the game turned legacy input into a throw

Reported as two broken things: the timed escape (wait out `EndGrabDelaySeconds`, press Q) and the
instant debug escape (numpad +). They are one fault, and it is not in the escape code at all.

**Game 0.3.1 switched Player Settings' active input handling to the Input System package alone.**
Under that setting, every read of the legacy `UnityEngine.Input` class throws:

```
InvalidOperationException: You are trying to read Input using the UnityEngine.Input class,
but you have switched active Input handling to Input System package in Player Settings.
```

The deployed logs carried the sentence **10 994 times (Windows) and 75 306 times (Linux)** — and
the 0.2.1 log, in the same install layout, carries it **zero** times. That is the whole diagnosis;
everything below is the consequence.

`Plugin.Update` ran the gameplay block unguarded, and its **first** call is
`HeatLockSystem.HandleHotkeys()`, whose `IsRemoveHeatPressed` ends
`|| Input.GetKeyDown(KeypadMinus) || Input.GetKeyDown(Minus)`. So the throw happened three calls
*upstream* of the escape gate, every frame, and took the rest of the block with it:
`SceneEscapeGate.Tick` (the on-screen hint), `HandleEscapeKeys` (both keys),
`GrappleDeathSequence.Tick`, `ImpGrappleReinforcement.Tick`, `EnemyInactiveAutofix.Tick`.

### Why nothing said so

A MonoBehaviour exception goes to the **Unity** log, and `BepInEx.cfg` shipped
`WriteUnityLog = false` — §56's lesson, now paid for a second time. `LogOutput.log` read clean
while five subsystems had not run since startup. `WriteUnityLog = true` is now set in both installs.

### Why the configured keys were innocent

`KeyboardShortcut.IsDown()` goes through `BepInEx.UnityInput.Current`, which probes for the legacy
system at startup and falls back to `NewInputSystem` when the probe throws. Every *configured*
binding was therefore fine. What was not fine was the raw `Input.*` **fallbacks** sitting beside
them — `Shift+=` next to the debug shortcut, the keypad pair next to the heat-lock shortcuts, and
`Hotkeys.IsDown`'s own held-key logic, which is what put the sentence in the log 75 000 times
through `SpinAiDiag` and `InteractDiag`.

### The fix

- **`SafeInput.cs`** — the one route to `UnityInput.Current`. Nothing in the plugin calls
  `UnityEngine.Input` any more; all 17 call sites across `SceneEscapeGate`, `HeatLockSystem`,
  `Hotkeys`, `FreeCam` and `InteractDiag` now go through it.
- **`Plugin.Update`'s gameplay block is per-tick guarded.** The seven ticks are independent, so a
  throw in one is now one dead tick, logged once as `[TICK] <site> threw and is dead for this run`,
  instead of five silently dead subsystems.
- **`[INPUT] backend <name>` at startup**, so which input system BepInEx resolved is never a guess.

`patchaudit` is clean (147 patches, 23 typed reflections, 78 Traverse members) — nothing about the
binding surface changed, which is why the audit had nothing to say about a total functional
failure.

### The second half: BepInEx's own abstraction was already poisoned

The first fixed build changed nothing on screen. The log said why, and it was not the escape code
either:

```
[Warning:   BepInEx] [UnityInput] Failed to detect available input systems -
  System.NullReferenceException: Object reference not set to an instance of an object
  at BepInEx.NewInputSystem.GetControl (UnityEngine.KeyCode key, System.Boolean silent) [0x00803]
  at BepInEx.NewInputSystem..ctor ()
  at BepInEx.UnityInput.get_Current ()
[INPUT] backend NullInputSystem
```

Zero occurrences of the legacy-input sentence — that half was fixed — and still not one key
working. `UnityInput.Current` resolves its backend **once**, on first access, and caches it:
legacy first, `NewInputSystem` on the legacy throw, `NullInputSystem` if that throws too. And
`NewInputSystem`'s constructor resolves a control for *every* `KeyCode` immediately, reading
`UnityEngine.InputSystem.Keyboard.current`, which is still null that early in the run. Offset
`0x00803` is the switch arm for `KeyCode.Backspace`, the first key it tries. So BepInEx settled on
`NullInputSystem` — every key reads false, permanently, including every **configured**
`KeyboardShortcut`, since `IsDown()` reads the same cached field.

`SafeInput.EnsureBackend()`, called at the top of `Plugin.Update`, re-runs that probe once the
keyboard device exists and writes the working backend into `UnityInput.current` by reflection. It
repairs the shared field rather than keeping a private backend, because every `KeyboardShortcut` in
the plugin reads that field and nothing else would reach them. It is a no-op after the first
success, and logs `[INPUT] backend repaired -> NewInputSystem` when it lands or names the reason
once if it cannot.

### Verified

The 2026-08-18 22:39 Linux run, in the log:

```
22:39:30.705 [INPUT] backend at startup NullInputSystem
22:39:41.863 [INPUT] backend repaired -> NewInputSystem (was NullInputSystem; ...)
22:41:33.991 [GRAB-END] EndGrab key   [ESCAPE] debug instant (+)
22:41:54.490 [GRAB-END] EndGrab key                              <- Q, past the gate
```

Zero occurrences of the legacy-input sentence, no `[TICK] ... threw` line, both escape paths
exercised, and 54 `[Unity Log]` lines proving `WriteUnityLog` now carries game-side throws.

**The eleven seconds before the repair are the window being unfocused**, not a delay in the fix:
`[FOCUS] lost` at startup, `[EDI] Resume` at 22:39:41.388, repair 0.5 s later. The Input System has
no keyboard device while the window is not focused, so hotkeys are dead exactly while nobody can
press one.

### What the same run caught by itself

`[SPIN-AI] KILL 'Plantasha_Enemy': StopGrab is nulling a live grabCoroutine while state=Grabbing`,
naming `EnemyReactivationHelper.ApplyGrabEndCooldown` as the caller — **§14's strand is the mod's
own doing**, and `[AI-GUARD] unstuck ... for 0.5s -> Idle` 0.5 s later is the hitch it costs. Left
open in `TODO.md` by choice: the guard recovers it and she stays playable. The probe was written
for exactly this and fired without anyone going looking, which is the argument for shipping probes
rather than hypotheses.

---

## 73. The mod stands down from grab keep-alive — 0.3.1 ships the mechanic

Since §17 the mod has kept grabbed enemies alive by force: block `Object.Destroy`, skip
`RemoveEnemyAfterGrab`, snapshot and restore health, block `Die` while the scene is up, then
reactivate the enemy and put its AI back together afterwards. 0.3.1 has it natively, with the
game's own tooltip on the flag:

> `EnemyAI.hideInsteadOfDestroyOnGrab` — *"If true, this enemy is hidden (SetActive false) instead
> of destroyed when it grabs the player. It reappears in Idle if the player escapes the grab; if
> killed during the grab, it dies normally at EndGrab. Arena clearance still treats a hidden enemy
> as alive."*

The two halves are `RemoveEnemyAfterGrab` — `ResetGrabTransientState`, `currentState = Idle`,
`GrabScreen.RegisterHiddenEnemy(gameObject)`, `SetActive(false)` — and
`IGrabHideable.EndGrabHidden(float remainingHealth)`, which does `SetActive(true)`, restores the
transformed animator state, sets `lastGrabTime`, writes the health the grab screen snapshotted at
`StartGrab`, resets the transient state, goes back to `Idle` and turns pathfinding on.
`preserveHealthDuringGrab` decides whether grab-screen damage carries over at all. That is the mod's
whole mechanism, written by the code that owns the state.

**The mod now defers per enemy, on the game's own flag rather than on a version check.**
`VanillaGrabHiding.Handles(enemy)` reads `hideInsteadOfDestroyOnGrab` off whichever AI component the
enemy has, and where it is set:

| | before | now |
|---|---|---|
| `GrabSurvivalHooks.StartGrab_Postfix` | arms `GrabEnemyProtection` | does not arm it — so no `Destroy` blocking and no `Die` blocking for that enemy |
| `SkipRemoveEnemyAfterGrab` | always skipped vanilla | lets vanilla run, so the enemy is hidden **and registered** with the grab screen |
| `GrabEndHelper.StabilizeAfterGrabEnd` | full reactivation + respawn scheduling | the configured re-grab cooldown only |
| `NearbyEnemyHider.HideForScene` | hid the grabbed enemy with the rest | skips it; vanilla's `EndGrabHidden` is what brings it back |

Everything else is untouched: a prefab that does *not* set the flag stays on the mod's path, which
is also what keeps 0.2.1 working, and the chaser bosses (dragon, wendigo) keep their own handling
because the game-over guard is built around it.

**Skipping `RemoveEnemyAfterGrab` is now the dangerous option, not the safe one.** It used to mean
"do not delete the enemy"; on a 0.3.1 prefab it means the enemy is never hidden and never registered
as `hiddenEnemyToRestore`, so nothing calls `EndGrabHidden` at the end — the mod would have to
finish a teardown it no longer starts.

The one thing vanilla does not have is the mod's configured re-grab delay
(`EndGrabEnemyCooldownSeconds`); vanilla sets `lastGrabTime = now` and stops there. So the deferred
path still applies that, through a new `ApplyGrabEndCooldownToEnemy`, **without** the `StopGrab`
call the full reactivation makes — that call is §14's strand (`StopGrab` nulling a live
`grabCoroutine` while the state is still `Grabbing`, which `UpdateStateMachine` has no handler to
leave), so the deferred path is free of it by construction. `ApplyGrabEndCooldown` keeps the call
for the mod's own reactivation path, where the state is different.

`KeepEnemiesAfterGrab`'s description now says what it still governs: enemies the game destroys.

**`Debug` is now set from both ends rather than inherited from the working tree.** `deploy.py`
forces `[EDI] Debug = true` into both game installs, whatever is committed: they are debug installs,
every `Plugin.DBG` line is behind that one setting, and a `false` committed by accident does not
break anything visibly — it just makes the next investigation start from an empty log.
`release.py` ships `Debug = false`, so a player gets a quiet log. It is the one `SHIPPED` entry
that is not there because the live value deviates — live and coded default agree at `true` — and
the point of writing it down is that a reader should not have to infer that from silence.

**Which path an enemy takes is logged once per prefab**, because two implementations of one
mechanic is exactly the case where the wrong one running looks like a bug in the other:

```
[GRAB-HIDE] Hood_Enemy: vanilla hides it (hideInsteadOfDestroyOnGrab) - mod keep-alive stands down
[GRAB-HIDE] Hood_Enemy: vanilla still destroys it - mod keep-alive active
```

Mod **2.4.0**. `patchaudit` and `cfgaudit` clean. **Not play-tested, and the flag's value on the
shipped prefabs has not been read out of the assets** — a serialized bool needs the whole field
layout of an 88-field component to locate, and the log line answers it on the first grab instead.

---

## 74. The escape hint resolved its font once, too early — and the §73 stand-down is inert so far

Two findings from the 2026-08-18 23:02 Linux session.

### The countdown was never on screen — fixed, by the retry rather than the source

Reported as "no prompt to escape appeared, but Q worked after the 15 seconds". Those two facts
together locate it: `HandleEscapeKeys` and `Tick` are consecutive calls in the same `Plugin.Update`
block, so a working Q proves the gate was active and `ShowHint` *was* called every frame. Whatever
failed sat between that call and the screen.

The hypothesis was the font: `EnsureHintOverlay` built its `Text` from
`Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf")`, which returns only what a player build
contains, and a uGUI `Text` with a null font draws nothing at all — no exception, no warning. The
hint draws again after the change, but the log says the hypothesis as stated was wrong:

```
[HINT] font from Resources.GetBuiltinResource: LegacyRuntime
[HINT] escape hint drawn: "Press Q to escape in 15s" font=LegacyRuntime
```

**The builtin font resolves fine on this build** — the same call the old code made — so the source
was never the problem. What the old code did wrong was resolve it **once**: `_hintFont` was cached
by the first `EnsureHintOverlay`, and a null there is permanent for the run. The new
`ShowHint` re-asks whenever `_hintText.font` is still null, so a font that was not available at the
moment of the first grab is picked up at the next one. That is the only behavioural difference on
the path the log shows it taking, and it is consistent with a hint that was invisible for a whole
session and fine in the next.

Unproven, because the transient null did not recur to be caught: what is established is that the
hint draws, that the font source in play is the builtin one, and that a single-shot resolution of
anything Unity may not have loaded yet is a bug waiting for the wrong first frame.

The rest of the change stands on its own: the font is taken from `GrabScreen.GrabText.font` when
that exists (the game's own legacy `Text`, so it is known to render), with the builtin names and
any loaded `Font` behind it, and `[HINT]` names the source once and logs the first draw. Those two
lines are what turned a guess into a disproof inside one run.

### No enemy in the session takes the game's own hide path

§73's stand-down is written and correct and **has not run once**:

```
[GRAB-HIDE] Imp_Enemy ALT 4:      vanilla still destroys it - mod keep-alive active
[GRAB-HIDE] Hood_Enemy NoTape:    vanilla still destroys it - mod keep-alive active
[GRAB-HIDE] Gargoyle Alt:         vanilla still destroys it - mod keep-alive active
[GRAB-HIDE] Plantasha_Enemy ALT1: vanilla still destroys it - mod keep-alive active
[GRAB-HIDE] Weapons Mimic:        vanilla still destroys it - mod keep-alive active
```

Five prefabs, five times the fallback. `hideInsteadOfDestroyOnGrab` exists in 0.3.1's `EnemyAI`
with a tooltip describing the whole mechanic, and no enemy played so far has it set — the patch
note that prompted §73 ("Grappler enemies are now persistent") is about grapplers, which is a
different code path. So the mod's own keep-alive is still what runs, and the stand-down sits there
for whichever prefab converts first. **This is the answer to a question, not a failure**, and it
was one log line each to get rather than a field-layout parse of an 88-field component.

---

## 75. The game-over prompt was cancelled by our own teardown, inside a one-second window

TODO item 6: the player died in a nun grab, the log showed the deferred game over firing, and the
"press any key" prompt never appeared. Read as a suppression that outlived its case — the mod holds
three patches over `GameOverScreen` gated on `DragonGrabGameOverGuard.ShouldBlockGameOver` — but the
guard is not what does it, and the IL says so.

### What the game's own screen actually does

`GameOverScreen.TriggerGameOver` calls `OnPlayerDied`, which returns early if `hasShownGameOver` and
otherwise does one thing: `StartCoroutine(ShowGameOverSequence())`. That coroutine is where the
prompt lives, and it does not raise it immediately:

```
yield WaitForSeconds(delayBeforePrompt)   // 1 s
promptPanel.SetActive(true)
isWaitingForInput = true
... fade promptCanvasGroup over promptFadeInDuration (2 s)
```

`Update` only watches for the continue key while `isWaitingForInput && !hasShownGameOver`. So for
the first second after a game over there is a live coroutine and nothing on screen, and the only
thing that can ever set `isWaitingForInput` is that coroutine.

`GrabEndHelper.CancelGameOverPresentation` calls `StopAllCoroutines()` on the screen and clears
`isWaitingForInput` / `hasShownGameOver`. **A cancel landing in that window is unrecoverable**: the
coroutine is gone, `OnPlayerDied` is never called again, and the run sits on a dead screen. That is
the bug, and it needs no suppression to be armed — only a second teardown pass.

### Why one was guaranteed to arrive

`HeatLockSystem.CompleteSceneEntrySurvival` runs from `FinishGrabEnd`, an `EndGrab` postfix, and
triggers the game over there. Every other grab-end path calls the cancel:

- `PrepareGrabEnd` — the `EndGrab` **prefix** — cancels on entry;
- `CleanupGrabPresentation`, via `FinalizeGrabEndVisuals`, cancels again.

So any second `EndGrab` within the delay wipes the prompt. The escape key is exactly that:
`SceneEscapeGate.HandleEscapeKeys` → `GrabEndHelper.TryEndActiveHScene(forceImmediate: true)` →
`instance.EndGrab()`, and it stays reachable because `IsGrabSessionLive` tracks the mod's own
session flag rather than `isGrabbed`. The logged session has the debug escape immediately after the
game-over line — the player pressing escape at a screen that looked stuck is the same keystroke that
guaranteed it would stay stuck.

### The fix: a commit latch, not a new gate

`DragonGrabGameOverGuard` gained `CommitGameOverPresentation` / `ReleaseGameOverPresentation`.
`CompleteSceneEntrySurvival` commits **before** `TriggerGameOver`, because `StartCoroutine` runs the
sequence up to its first yield synchronously and everything else in that frame is a cancel risk.
While committed:

- `CancelGameOverPresentation` returns without touching the screen, and says so in the log;
- `ShouldBlockGameOver` and `ShouldBlockLethalHealth` both return `false`, so the three
  `GameOverScreen` patches stop short-circuiting the presentation the mod itself asked for.

Released where the presentation is finished or the run has moved on: `ShowGameOverPanel` (the player
answered the prompt), `RunRestartController.RestartRun`, and `PlayerStats.Revive`. Nothing time-based
— a player can stare at the prompt for a minute, and an expiry would put the original bug back.

`CancelGameOverPresentation` also took a `source` string and now logs every call with the screen's
`isWaitingForInput` / `hasShownGameOver`, so the next run says which path cancelled rather than
leaving it to be re-derived.

### `patchaudit` said the new patch target did not exist, and was wrong

Adding the `RunRestartController.RestartRun` patch produced
`HARMONY RunRestartController.RestartRun does not exist`. It does — `ikdasm` shows
`.method public hidebysig static void  RestartRun() cil managed` in both installs. The parser
deferred the method **name** to the following lines unconditionally, which is right for a
declaration whose return type wraps but wrong for a short one that carries its own signature: every
such method in the assembly was invisible to it. Fixed by searching the `.method` line itself first.
Clean afterwards on 0.3.1 and on 0.2.1 — **the analyser was validated against the build it is known
to describe before being believed about a new target**, which is the same rule that caught the
nested-type bug in the first place.

Mod **2.4.0**, both installs deployed. **Not yet play-tested**: the confirmation is one death in a
grab, watching for `[GAMEOVER] presentation committed`, then `[GAMEOVER] cancel from ... ignored`,
then the prompt.

---

## 76. The seventh AI class, and a game over that any grab could undo

Three findings from the 2026-08-18 Windows and Linux play-test of §75.

### The Black Serpent stopped acting after a grab — a hand-maintained list, missing an entry

Reported on Windows: escape a serpent grab with the debug key and the serpent stands there for the
rest of the run. The serpent runs **`BrawlerEnemyAI`**, a class 0.3.1 added and the §46 audit never
saw. Its `RemoveEnemyAfterGrab` is the ordinary vanilla shape:

```
StopAllCoroutines();  TransitionToDead();  Instantiate(deathEffect);  PlaySound(deathSound);
Destroy(gameObject);
```

`SkipRemoveEnemyAfterGrab` names five classes and `BrawlerEnemyAI` was not among them, so vanilla
ran. The generic `Object.Destroy` prefix still kept the object alive, which is exactly why the
symptom was a standing serpent rather than a missing one: state `Dead`, every coroutine stopped,
and `UpdateStateMachine` has no case for `Dead`. `EnemyReactivationHelper.Reactivate`, the health
snapshot and restore, `NearbyEnemyHider` and `EnemyInactiveAutofix` all name the same six classes,
so not one of them touched it either.

**The mod had been saying so since the port.** Both logs carry, twice per run:

```
[AI-AUDIT] GAP: BrawlerEnemyAI can start a grab and was not in the §46 audit...
[AI-AUDIT] GAP: BrawlerEnemyAI runs its own state machine and was not in the §46 audit...
```

That is the audit doing its job (§46 built it for exactly this) and nobody reading it. The GAP
lines are now part of what a port checks, not background noise.

The §46 audit, redone for this class:

| question | answer |
|---|---|
| states with no case in `UpdateStateMachine` | none but `Dead` — Idle, Chasing, Attacking, Shooting and Hypnotising all have handlers, so **no `AiStateGuard` entry** |
| re-tests `IsGrabbed` after `StartGrab`? | yes — `LandGrab` returns if the grab was refused, so **no `EnemyGrabGate` entry** |
| what it did need | the keep-alive, reactivation, hider and autofix coverage every other class has |

One extra wrinkle: `RemoveEnemyAfterGrab` reaches `Dead` through `TransitionToDead`, which writes
`currentState` only — `isDead` is set by `Die()` alone. `ClearDeadState` keyed its whole reset on
`isDead`, so even inside the reactivation path it would have skipped this enemy. It now handles the
Brawler's shape explicitly.

**The fix is one list, not seven edits.** `EnemyAiTypes` holds the roster; keep-alive, reactivation,
the hider, the autofix, `ResolveGrabAnims` and `VanillaGrabHiding.Handles` all read it instead of
spelling the set out. Six copies of a six-item list that agreed only by hand is what let a whole
enemy fall through, and `if two copies must agree, build one from the other` is the rule already in
`learnings/working-practice.md`. `MimicEnemy` stays out of the roster: no state machine, no
pathfinding, and every caller that wants it already handles it separately.

Verified in the 23:58 Linux run: the serpent is grabbed, `[ENEMY-WAKE] Black Serpent Enemy visible
now, AI in 5s`, and it grabs the player again 33 s later. `[AI-AUDIT] ok`.

### §75's latch worked, and showed what it did not cover

The good case is in both logs — `presentation committed ... -> released by ShowGameOverPanel`, with
the prompt on screen and answered. Two runs also caught the *inverse* of §75's bug, on a path the
commit latch did not reach:

```
23:55:41  [GAMEOVER] prompt up: ...                       <- vanilla's own game over, no mod commit
23:55:42  [GRAB-START] prefab='Hood_Enemy NoTape' ...     <- a nun grabs the corpse
23:55:42  [PLAYER-REVIVE] ok - keeping the scene gallery
23:55:42  [GAMEOVER] cancel from guard (waitingForInput=True hasShownGameOver=False)
```

A dead player is still grabbable, the grab's scene-entry survival revives them to 1 HP, and the
game over already on screen is torn down — the run continues as if the death had not happened. §75
committed the latch only where the *mod* triggers the game over, so a death in the open, where
vanilla presents it, was unprotected.

Two changes:

- `GameOverScreen.OnPlayerDied` gained a **postfix** that commits the latch whenever the
  presentation actually starts. Harmony runs postfixes even when a prefix returned false, so it
  tests `ShouldBlockGameOver` first — that is what keeps a deliberately suppressed chaser-boss game
  over from latching — and `hasShownGameOver`, so a second call latches nothing.
- Committing now clears `PlayerStats.CanBeGrabbed`, and `EnsureSceneEntrySurvival` declines while a
  game over is presenting. Clearing the flag uses **the game's own refusal path**: `StartGrab`
  declines, which every AI class already handles, rather than blocking `StartGrab` and stranding an
  enemy mid-commit. `Revive` is no longer a release site — the only revive that can happen while a
  game over presents is a scene dragging the dead player back in, which is the thing being stopped.

### "The UI is cut off on Linux" was the window manager

Reported as both the escape hint and the game's "press any key" prompt sitting too low and half off
the bottom edge on the native Linux build, while the same build under Proton was fine. Moving the
window to another screen and back fixed it: the compositor had placed the window partly off the
display. Neither the game nor the mod was involved, and there is no open item.

What survives is the diagnostic written to tell the two apart, because they look identical on
screen and both live UI elements sit in the bottom ~70 px:

```
[GAMEOVER] prompt up: screen=2560x1440 desktop=2560x1440 mode=FullScreenWindow dpi=0 safeArea=(0,0,2560,1440)
[GAMEOVER] prompt rect x=1936..2560 y=0..71 canvasScale=1.412 render=ScreenSpaceOverlay
```

`screen` matching `desktop`, a full-height `safeArea` and a rect inside `0..1440` say the game
placed it correctly — so anything the eye sees off-screen is outside the process. The same pair is
printed once for the escape hint.

Mod **2.4.0**, both installs deployed, `patchaudit` and `cfgaudit` clean. The serpent and the §75
prompt are confirmed in play; the vanilla-path latch above is built but not yet play-tested — the
check is to die in the open and let an enemy walk into the corpse: the grab should be refused and
the prompt should stay up.

---

## 77. Correct §76: a grab taking the prompt down is the death rule, not a bug

§76 read two log lines as a defect and half-fixed a feature. The lines:

```
23:55:41  [GAMEOVER] prompt up: ...                    <- vanilla presents at 0 HP in the open
23:55:42  [GRAB-START] prefab='Hood_Enemy NoTape' ...  <- a nun grabs the dead player
23:55:42  [PLAYER-REVIVE] ok - keeping the scene gallery
23:55:42  [GAMEOVER] cancel from guard (waitingForInput=True hasShownGameOver=False)
```

That is **the mod's death rule doing exactly what it was built to do**. At 0 HP the player stays
grabbable; the grab that lands plays as the death scene; the game over is presented when that scene
ends. §8 item 6 states it outright — "once out of HP the player must finish the grab scene then
press any key to quit" — `EnsureSceneEntrySurvival` exists to revive into that scene, and
`GrappleDeathSequence` goes as far as forcing `CanBeGrabbed = true` so the death grab can be
offered at all. The prompt coming down when a grab starts is the handoff, not a lost game over.

Reverted from §76:

- the `GameOverScreen.OnPlayerDied` postfix that latched vanilla's own game overs;
- `CanBeGrabbed = false` on commit, which would have refused the death grab outright;
- `EnsureSceneEntrySurvival` declining while a game over presents;
- and `Revive` is a release site again — it is *the* signal that a scene has claimed the dead
  player, so the latch must stand down for it.

§75's latch stays exactly as it was, with its scope now written down: it stops a game over being
cancelled by **teardown belonging to the scene that just ended** — the second `EndGrab` from a
debug escape landing inside `ShowGameOverSequence`'s one-second delay. It was never meant to
outlive that window, and everything that legitimately claims the dead player releases it.

**What went wrong in the reading.** The evidence for "bug" was that a prompt on screen disappeared
and the run carried on. Both halves are also true of the intended behaviour, and nothing in the log
distinguishes them — the distinguishing fact is a design decision that lives in §8, not in any
line the run prints. §76's own §73-style caution ("this is the answer to a question, not a
failure") was the right instinct applied to the other finding in the same entry and not to this
one. **Before calling a mod behaviour a bug, find the entry that put it there.** The serpent and
`patchaudit` findings in §76 are unaffected.

Mod **2.4.0**, both installs deployed, `patchaudit` and `cfgaudit` clean.

---

## 78. #14's strand: the mod restarted a grab and then killed it, one line apart

The 0.5 s hitch after a grab ends. The probe named the leaf in §73's run —
`StopGrab is nulling a live grabCoroutine while state=Grabbing`, from
`EnemyReactivationHelper.ApplyGrabEndCooldown` — and the missing half was *why the AI was in
Grabbing at all* on a path that had just reset it to Idle.

`ReactivateComponent` does this, in this order:

```
currentState = Idle              // SpinningEnemyAI's branch
ResumeAiBehaviour(ai)            // -> vanilla ResumeAIBehavior()
ApplyGrabEndCooldown(ai)         // -> StopGrab()
```

and vanilla's `ResumeAIBehavior` re-picks a state by distance:

```
if (distance > detectionRange)  TransitionToIdle();
else if (distance <= grabRange) TransitionToGrabbing();      <- here
else if (...spinMaxRange && CanSpin()) TransitionToSpinning();
```

At the end of a grab the player is standing exactly where the scene left them, which is inside
`grabRange`. So `ResumeAIBehavior` transitions to Grabbing and `StartGrab` starts a **fresh, live**
`grabCoroutine` — and the next statement kills it. `StopGrab` stops the coroutine and nulls the
handle without transitioning anything, and `SpinningEnemyAI.UpdateStateMachine` has no case for
Grabbing, so nothing but `AiStateGuard` can leave the state. Its 0.5 s recovery **is** the hitch.
The mod was fighting itself across two consecutive lines.

**Fix: never call `StopGrab` on an AI that is still in Grabbing.** Both live-AI call sites take the
guard — `ApplyGrabEndCooldown` and `GrabEndHelper.StabilizeBossGrabEnemy`. Letting the coroutine run
is safe and is the point: `GrabSequence` waits, clears `isAttemptingGrab`, nulls its own handle and
transitions to Spinning or Idle by itself, and the attempt it makes on the way is refused by the
player's post-grab immunity (`CanBeGrabbed` false), which `SpinningEnemyAI` re-tests — §46 audited
it as one of the classes that does.

`ClearStaleCoroutineHandles` deliberately does **not** take the guard, and the comment there now
says why: it runs from `ReactivateComponent` on an object that was just `SetActive(true)` after
being hidden for a scene, so its handles are stale by construction — no coroutine survives the
deactivation. Skipping the call there would leave the non-null handle that `StartGrab` refuses to
overwrite, which is the bug that method exists for. **The same call is right on one path and wrong
on the other, and which one it is depends on whether the object has been deactivated since.**

`IsGrabbing` resolves the state by enum **name**, not number: Grabbing is 2 on `SpinningEnemyAI` and
3 on `EnemyAI` and both dragons, so a constant would have been wrong for one of them. `AiStateGuard`
is keyed on the raw int because that is what the boxed field hands back, and `EnemyAiAudit` exists
to catch that table drifting; there was no reason to add a second numeric table to audit when the
name is available at the call site.

One line to watch for, on the enemy the probe named:

```
[AI-GUARD] kept 'Plantasha_Enemy's live grab: StopGrab skipped while state=Grabbing
```

with no `[AI-GUARD] unstuck ...` following it. Mod **2.4.0**, both installs deployed, `patchaudit`
and `cfgaudit` clean. Not yet play-tested.

---

## 79. Escape delays retuned: 20 s, and 40 s for the chaser bosses

`EndGrabDelaySeconds` 30 → **20**, `EndGrabDelaySecondsChaserBoss` 90 → **40**, both as coded
defaults, and the live config moved onto both numbers — it had been sitting at 15 and 90.

The old pair was never played at as a pair. 30 was written as "the intended pace" against a live 15
that `release.py`'s own SHIPPED comment called impatience while testing, and 90 for a dragon or
wendigo was set when a chaser boss grab was the rarest scene in the game; it is not any more. 20 is the pace actually wanted, and
40 still makes a boss grab the long one without turning it into a wait.

The live config now **agrees with the defaults** for both, so `("Gameplay", "EndGrabDelaySeconds")`
came out of `release.py`'s `SHIPPED` table: that table is only for settings whose live value
deviates, and an entry left there would have kept forcing 30 into the release after the deviation
it existed for was gone. One fewer thing that has to be remembered.

`cfgaudit` clean, `release.py --check` clean and no longer rewriting this setting, both installs
deployed.

---

## 80. Every peek scene went silent: 0.3.1 renamed the entries into jokes

Reported as "none of the peek scenes are playing their funscript in the gallery". The log names the
failure on the first line of it:

```
[PEEK-STEP] enemy='It'll Fit... See!' key=it_ll_fit_see anim='Loop' -> it_ll_fit_see_loop
[ALIAS-GAP] no mapping for 'it_ll_fit_see_loop' - add it to GalleryAliases
[EDI-SKIP] it_ll_fit_see_loop -> it_ll_fit_see_loop (not in Definitions.csv)
```

That is `SendMenuGalleryStep`'s format, i.e. `PeekGalleryMap.Resolve` returned nothing and the code
fell through to the generic enemy-name slug builder. All eleven peek entries did it, each with its
own invented name: `full_vaginal_nelson_loop`, `gobbled_down_to_the_sack_loop`, `snussy_ray_loop`,
`making_puppies_loop`, and so on.

**0.3.1 rewrote the peek entries' `enemyName` into flavour titles**, and `enemyName` was one of the
only two things the resolver matched on. The other, `enemyID`, is just `"P1"`..`"P11"` — the peek
tab's own numbering, which never matched anything in the map either. So every lookup missed, and
the fallthrough produced a plausible-looking slug for a row that cannot exist. The gap was
**announced** (`ALIAS-GAP`, `EDI-SKIP`, and a line per scene in `PncEdi-missing-definitions.log`)
rather than silent, which is the rule from §2 working.

### What the entries actually carry

Read out of `sharedassets0.assets` rather than guessed — `EnemyGalleryEntry` is a ScriptableObject
and MonoBehaviour typetrees are not shipped, so this is the by-hand raw parse from
`learnings/asset-inspection.md`:

| enemyID | asset name | display name (0.3.1) | peephole controller | script |
|---|---|---|---|---|
| P1 | `ImpThreeWayGalleryData` | It'll Fit... See! | `ImpThreeWayGallery` | `peek_imp_three_way` |
| P2 | `Nun&MimicGalleryData` | Full-Vaginal-Nelson | `Mimic&NunGallery` | `peek_nun_mimic` |
| P3 | `PlantBJGalleryData` | Gobbled Down to the Sack | `PlantBJGallery` | `peek_plant_bj` |
| P4 | `WendigoRideGalleryData` | Wendigoon Press | `WendigoRidingGallery` | `peek_wendigo_ride` |
| P5 | `NunsThreewayGalleryData` | Nun Two It | `NunsDuoGallery` | `peek_nuns_threeway` |
| P6 | `GooperGloryHoleGalleryEntry` | Feedin' Time | `GooperPilloaryGallery` | `peek_gooper_pillory` |
| P7 | `ZombieBJpeekscene` | Getting Brain | `ZombieBJGallery` | `peek_zombie_bj` |
| P8 | `GravyBathingGallery` | Soggy Biscuits | `GravyBathingGallery` | `peek_gravy_bath` |
| P9 | `Gargoyle FuckfestGallery` | Gargirl Fuckfest | `GargoyleFuckFestGallery` | `peek_gargoyle_fuck_fest` |
| P10 | `Serpent Prison Style` | Snussy Ray | `Serpent Prison Style Gallery` | `peek_serpent_prison` |
| P11 | `BlindedBeastRide` | Making Puppies | `Blinded Beast Ride Gallery` | `peek_werewolf_ride` |

Two facts that matter beyond this fix: a peek entry leaves `animatorController` **null** and carries
its peephole on `grabAnimatorController`, and `availableAnimations` is **empty** — the step's
animation name is always `"Loop"`, which is why the clip route (`PeekClipMap`, written for the
in-world peepholes whose clips are named `Peephole_*`) could never help here.

Guessing the mapping from the titles was not on: "Soggy Biscuits" is the Gravy bath and "Snussy Ray"
is the serpent, but "Making Puppies" against "Full-Vaginal-Nelson" is a coin toss, and **a wrong
scene is worse than a missing one**. The asset dump decides it.

### The fix: match on names the project keeps, not names it writes for the player

`PeekGalleryMap.Resolve` now takes four keys and tries them in this order:

1. the entry asset's own name (`((Object)entry).name`),
2. the peephole animator controller's name,
3. `enemyName`,
4. `enemyID`.

Asset names first because they are what a project renames last; the display title third because
0.3.1 just demonstrated what it is worth; `enemyID` **last**, because `P1`..`P11` is a position, and
a peephole inserted in the middle would silently hand every later scene its neighbour's script.

All 22 asset and controller names are in `AddBuiltInDefaults`, so the mapping works even against a
stale live config, and the same list is now the coded default of the `PeekGalleryMap` setting. The
"no peek map" log line lists every key it tried rather than two of them.

`PeekGalleryMap.Heuristic` is now unreachable for this build — all eleven resolve exactly. It stays
as the last resort for a build this table has not seen.

Mod **2.4.0**, both installs deployed, `cfgaudit` and `release.py --check` clean. Not yet
play-tested: walk the peek tab and every entry should log
`[PEEK-STEP] asset='...' -> peek_*` with no `ALIAS-GAP` and nothing new in
`PncEdi-missing-definitions.log`.

---

## 81. First play of the 0.3.1 set: two fixed, two queued

The gallery versions of §71's and §67's thirty unheard scripts, played for the first time. Four
findings; the two that are a number are done, the two that are a curve are not.

### `Serpent_Loop` ran backwards — the sleeve rule lost to the device

Felt as inverted in `Serpent_Loop_Gallery`, and the gallery twin is `_scaled_from` the gameplay
master, so both were.

`serpent_cleavage` returned its measurement **negated**, on §39's sleeve reading: the shaft passes
*through* her cleavage and the tip emerges above it, so the frame showing the most tip should be
the frame with the most of it inside her. `grabs031.serpent_loop` then passed `deep_is_max=True` on
top of the same reasoning. On the device it reads as a mouth-on-tip stroke, where the visible flesh
is the deep end.

The sign is flipped in **`proxies.serpent_cleavage`**, not only in the generator, so the sweep and
the script agree about which way is deep: `Serpent_Loop` goes from `INV -1.00` against its own
proxy to `ok +1.00`, and the gallery twin to `+0.98`. Flipping the generator alone would have left
the analyser calling the shipped curve inverted forever, and the next session correcting it back.

Both docstrings keep the sleeve argument, marked as played-and-rejected rather than deleted. It is
the reasoning that has to be re-made for the next scene of this staging, and what this case shows
is that the rule decides nothing on its own once a play exists. **Timing is objective, polarity
is not** — and this is the first time the project has had the instrument that reads it.

### `ambient_serpent_wall_blowjob` held to the bottom half

17 px of head travel on a scene where the player never moves, written full-range, read as a stroke
the picture does not contain. The series is untouched and the shape - a four-frame dwell and a
pull-off, §48's `Nun_Cum` shape - is unchanged in time and in proportion; only the band it is
written into is halved, `[0,0,0,0,35,100]` to `[0,0,0,0,18,50]`. Peak drops 800 -> 400 u/s.

That is the tier-A judgement the TODO said only a play could settle, settled the way it was
expected to go: the swell was real, its size was not.

### Queued, not done

- **`goonshroom_2` and `_3` should climb.** `goonshroom_1` is right; the three are meant to escalate
  the way `imp_1/_2/_3` do, and today they are three takes on one intensity. The imp set is the
  reference for what the climb should feel like.
- **`BlindedBeast_Cum_T` needs movement during the cum hold.** Currently one late buzz burst placed
  by whole-frame difference. The suggestion from the play is a real proxy: **the shaft's shake**,
  which is visible in the frames and is not what the current measurement tracks.

Everything else played as good: `goonshroom_1`, `Serpent_Cum`, both Blinded Beast stages, the
other dioramas and all the peek scenes.

`animsweep` 93/93 timing ok with no new polarity flag, `speedcheck` clean (no point under the
100 ms floor), both variants rebuilt, both installs deployed.

---

## 82. Release 2.5.0 — the 0.3.1 port, cut

The archive built for game 0.3.1 has existed since §71 and was never published; §75-§81 then
changed real behaviour on top of it. This section cuts the version that ships.

### Why 2.5.0 and not 2.4.1

2.4.0 means "the 0.3.1 port, as of §71-§74". What sits on top of it is not a patch series:

- **§75** the game-over prompt survives our own teardown,
- **§76** the Black Serpent — 0.3.1's seventh AI class — reactivates after its own grab,
- **§77** a grab taking the prompt down is the death rule, not a bug (a corrected rule, not a code
  change),
- **§78** both live-AI call sites skip `StopGrab` while the state is `Grabbing`, ending #14's
  0.5 s hitch,
- **§79** escape delays retuned to 20 s, and 40 s for the chaser bosses,
- **§80** all eleven peek entries resolve by asset name rather than by display title, which 0.3.1
  renamed into jokes,
- **§81** `Serpent_Loop`'s polarity and `ambient_serpent_wall_blowjob`'s range.

New enemy handling, a fixed input path and a retuned mechanic are minor-version work. The version
is bumped in the two hand-maintained files — `code/edimod/Properties/AssemblyInfo.cs` (three
attributes) and `code/edimod/PncEdi/Plugin.cs` (`BepInPlugin`) — which is what `plugin_version()`
cross-checks before it will name an archive.

### What was verified before the cut

| check | result |
|---|---|
| `patchaudit.py` | 151 Harmony patches, 23 typed reflections, 79 untyped Traverse members — every target still exists |
| `cfgaudit.py` | 138 entries, each in the section its `Bind()` names |
| `slugharness` | every animator state resolves; the 50 `-` rows are deliberate skips |
| `animsweep.py` | 93/93 timing ok, no polarity flag |
| `gallerydiff.py` | 21 of 44 rows play a different-length gallery animation, and all 21 have their own row — 0 still share a script |
| `speedcheck.py` | no point under the 100 ms floor |
| `deploy.py --check` | both installs up to date |
| `release.py --check` | clean; config rewritten through `SHIPPED` (`Debug`, `ShowHeatBarDuringGrab`, `HeatLockAutoHealRate`) |

`speedcheck`'s "exceed Handy 1: 76/101" is the masters being read against the Handy 1 limit, which
is what the `handy1` variant exists to solve; it is not a release finding.

### What is deliberately not in it

- **The two queued curve changes from §81** — `goonshroom_2`/`_3` climbing, and a shaft-shake proxy
  for `BlindedBeast_Cum_T`. Both are new measurement work, and neither is a defect in what ships.
- **§78's fix is not play-tested.** It is a strictly narrower guard than what preceded it — the
  skip only applies while the state is already `Grabbing` — so shipping it is safer than shipping
  the version that kills the grab it just restarted, but the `[AI-GUARD] kept` line has not been
  seen in a running game.
- **Vibration feel across the 71 pre-0.3.1 rows.** Unjudged since before the port; unchanged here.

The archive is `dist/PNC0.3.1-PncEdi-2.5.0.zip`, reproducible from the commit it is built from —
`render_readme` stamps the commit's own date rather than today's, and every input but the game is
pinned.

---

## 83. The GoonShroom cling tiers climb — 2.5.1

§81's play named the first of its two queued curve changes: `goonshroom_1` is right, and `_2`
and `_3` read as three takes on one intensity rather than the escalation the imp set has. This
does that, and takes the version with it.

### What the imps escalate is rate, not depth

The reference had to be read before it could be copied, because "more intense" has two obvious
readings and only one of them is what `imp_1/_2/_3` do:

```
        strokes/s   point gaps      range
imp_1       2.0     125 uniform     0-100
imp_2       3.5      87-160         0-100
imp_3       5.9      53-145         0-100
```

Every tier reaches a true 0 and a true 100. **Depth is constant and stroke rate is what climbs** —
one extra stroke per extra imp, which is also what is on screen. So the shroom tiers get the same
treatment on their own 750 ms cycle: one dip per cycle, then two, then three, for 1.33, 2.67 and
4.00 strokes/s. That is 1 : 2 : 3 against the imps' 1 : 1.75 : 2.95.

### The measurement still anchors the primary stroke

`GS_CLIMB` in `code/grabs031.py` carries the added beats, and the first three points of every
cycle are still the tier's own measurement — the crest at f0 and the hard dip at f2 (250 ms):

```
goonshroom_2   0:100  125:77  250:0  |  375:84  500:8   625:74          2 dips/cycle
goonshroom_3   0:100  125:72  250:0  |  350:90  450:5   550:92  650:6   3 dips/cycle
```

Only the recovery half is authored, which is the half the sprites spend slowly climbing back and
where the tiers' measured difference (56/73/89 against 42/62/83 at f3-f5) was too small to feel.
Those values stay in `GS_TIERS`, so tier 1 still uses its own and deleting `GS_CLIMB` reverts the
whole change. The gallery twins are `_remap_by_frame`'d from the masters and followed on the same
`--write`; `variants.py --write` re-emitted `handy1`.

### What it costs, and where the limit actually bites

`animsweep` polarity stays `ok` on both, and their correlation against the proxy drops from
`+1.00` to `+0.69` and `+0.70` — the primary stroke still tracks, the added ones do not track
anything, and that is the honest number for an authored addition. `imp_2` sits at `+0.54` and
`imp_3` at `-0.31` for the same reason, so neither goes into `proxies.AUTHORED`: the measurement
is still doing real work here.

Masters peak at 672 and 940 u/s, under the 960 a Handy 2 at max overclock manages. The gallery
twins replay the same curve on the viewer's 8/9-faster clock and so peak at 1056 with four gaps at
88 ms — the clip being faster, not a choice, and `imp_3_Gallery` is at 1119 already.

**On a Handy 1 the tier-3 climb is rate only.** Three dips in 750 ms leaves 125 ms per half
stroke, and 364 u/s covers 45 units in that, so the limiter lands `goonshroom_3` at 46 units of
range against `goonshroom_2`'s 68. No shape fixes that — it is what the hardware can do at four
strokes a second — and several were tried: mixed 90/125 ms gaps and a 60-140 ms spread both still
came out at 51. The `detailed` masters escalate in rate *and* keep full depth; `handy1` gets the
rate.

### 2.5.1

Content-only against §82's 2.5.0 — no code change, and `patchaudit`, `cfgaudit`, `animsweep`
93/93, `gallerydiff` (0 shared scripts) and `release.py --check` are all where §82 left them.
Still queued from §81: `BlindedBeast_Cum_T`'s shaft-shake proxy, which is a new measurement rather
than an authored curve.

---

## 84. `localhost` is not `127.0.0.1` on Windows — 2.5.2

The mod did nothing on a real Windows install. Under Proton the same build, the same config and
the same gallery worked. The two logs from the Windows session settle it between them.

### The mod's log is perfect and means nothing

`BepInEx/LogOutput.log` reads like a clean run. The alias table loads (`361 shared + 53
in-game-only`), the AI audit passes, the gallery hooks fire, and the one scene that was opened
resolves all the way through:

```
[05:05:02.955] [GALLERY-STEP] enemy='Imp' key=imp anim='Imp 1' -> imp_1
[05:05:02.956] [EDI] Play imp_1_Gallery  (alias of imp_1)
```

Seven `[EDI] Stop` and a pause/resume pair around an alt-tab are logged over the same minute. So
`NameRemap`, `GalleryAliases`, the `?seek=` parse and `GalleryRegistry.IsKnown` all did their job —
everything this project normally gets wrong was right.

Edi's own log from the same machine and the same minutes has **three** `Player event:` lines:

```
05:01:45.652  Player event: Pause, until resume: False        <- Edi's own startup
05:01:45.708  Player event: Diagnostic logging active...
05:05:56.446  Player event: Pause, until resume: False        <- Edi shutting down
```

Nothing between 05:04 and 05:05:32. Not the `Play`, not one of the seven `Stop`s. Meanwhile Edi
was plainly healthy: `Hosting started`, content root `...\PNC 0.3.1 Win\Edi`, `Discovered 202
assets`, every gallery row added. **Not one HTTP request from the mod ever arrived.** That single
comparison rules out the entire naming chain that §52, §71 and §80 were about, and points at the
transport underneath it.

### `localhost` resolves to `::1` first on Windows

Edi serves on `127.0.0.1:5000` — IPv4 loopback, and only that. The mod's `Url` default was
`http://localhost:5000`. Windows' resolver returns `::1` ahead of `127.0.0.1` for `localhost`, so
the POST goes to `[::1]:5000` and is refused. Wine's resolver hands back `127.0.0.1` first, which
is the whole reason the Proton install has always worked — the bug was invisible for as long as
the only machine testing it was the one that cannot reproduce it.

The fix is the config value: `Url = http://127.0.0.1:5000`, and the same string as the `Bind()`
default in `Plugin.cs` so a fresh install gets it too. **Verified in play on Windows** on
2026-08-22, by booting into it and setting the value by hand: the scripts play.

**A hostname is a policy decision, not an address.** `localhost` is two addresses with an ordering
rule attached, and the rule differs per platform; a server bound to one of the two is reachable by
name only where the rule happens to agree. Where both ends are ours and the address is fixed,
write the address.

### Why it took a second log to find

`FireAndForget` calls `Http.PostAsync(url, ...)` and never awaits the returned `Task`. Its
`try`/`catch` therefore only sees synchronous throws; a refused connection, a DNS failure, a proxy
or a timeout all fault the task instead, where nothing observes them. `[EDI] Play <name>` is then
logged unconditionally, *after* the call. So the mod's log claims a send whether or not a byte
left the process, and no amount of reading it could have found this.

That is a separate defect and is left open in `TODO.md`: a `ContinueWith(..., OnlyOnFaulted)` that
logs a warning keeps the call non-blocking while making the failure visible. It is not folded into
this section because it is a behaviour change and this one is a string.

Worth keeping: **when the mod's log is flawless and the behaviour is not, read the other side's
log.** Edi writes `Edilog<date>.txt` beside `Edi.exe`, and its `Player event:` lines are the only
proof that a request arrived at all.

### 2.5.2

One string in `Plugin.cs`, the matching value in `com.edi.pnc.cfg`, version in `Plugin.cs` and
`AssemblyInfo.cs`. No behaviour change beyond the address. 2.5.1 was never published, so 2.5.2
supersedes it; `dist/PNC0.3.1-PncEdi-2.5.2.zip` is the archive that went out on 2026-08-22.

One thing the release only showed once it was built: `code/dist/README.txt.in`, which `release.py`
renders into the archive, still told players the `Url` default was `http://localhost:5000`. Anyone
following that settings table would have set the unreachable address back by hand — so **a value
with a default lives in more places than the code that binds it**, and the shipped README is one
of them. Found by reading `PncEdi-README.txt` out of the finished zip rather than the template.

---

## 85. A POST nobody watches — 2.5.3

§84's bug survived a whole Windows session behind a log that read as perfect, because
`[EDI] Play <name>` is written whether or not a byte left the process. This closes that.

### Why the old `try`/`catch` could never fire

`FireAndForget` called `Http.PostAsync(url, ...)` and dropped the returned `Task` on the floor.
An `HttpClient` does its work *inside* that task, so the only thing the surrounding `catch` can
ever see is a throw from the call itself — a malformed URI. A refused connection, a DNS failure,
a proxy rejection and a timeout all complete the task in a failed state instead, long after the
method has returned, where nothing observes them. The mod then logged the send unconditionally.

The fix is a continuation, not an `await`: awaiting would put the game's frame behind a network
round trip. `ContinueWith` schedules a callback on a thread-pool thread when the task finishes,
so the call site still returns immediately, and reading `t.Exception` inside it is also what
marks the failure observed rather than leaving it for the finalizer.

### `OnlyOnFaulted` is the wrong filter — it misses the timeout

`TODO.md` proposed `ContinueWith(..., OnlyOnFaulted)`. That was tested against a dead port, an
unroutable address and a bad URI before it was written into the mod, and the unroutable address
printed nothing: **`HttpClient` enforces its own `Timeout` by cancelling the task, not by faulting
it.** A timed-out POST ends `Canceled` with a null `Exception`, and an `OnlyOnFaulted`
continuation never runs at all. Our client has `Timeout = 2 s`, so "Edi is not answering" — one of
the two failures actually worth seeing — would have stayed as silent as before.

`NotOnRanToCompletion` covers both terminal states. The continuation reports
`t.Exception.GetBaseException().Message` when there is one and, when there is not, names the
timeout with the client's own value:

    EDI Play imp_1_Gallery failed: Connection refused (127.0.0.1:5999)
    EDI Pause failed: no response within 2s - is Edi running?

The general rule, worth more than this method: **a cancelled task is not a faulted task.** Any
continuation filter that only looks at faults has a hole in it wherever a timeout or a
`CancellationToken` can reach.

### One sender instead of four

`SendPause`, `SendResume` and `SendStop` each carried their own `PostAsync` and their own
`try`/`catch` of decompiler-generated `BepInExWarningLogInterpolatedStringHandler` scaffolding —
four copies of the same defect. They now call `FireAndForget(url, what)`, which takes a label so
the warning names the request that failed (`Play imp_1_Gallery`, `Pause`, `Resume`, `Stop`).
That is 89 lines out for 46 in.

One behavioural difference falls out of it. In the old `SendPause` and its siblings the state
updates sat *inside* the `try`, so a synchronous throw skipped `LastSent` and the `[EDI]` debug
line. They now always run, which matches what the send path for `Play` already did and keeps the
0.25 s repeat suppression consistent — the failure is logged either way now, which it was not
before.

`OnApplicationQuit` is deliberately left as it is: it blocks on `.Wait(1500)` because a
fire-and-forget POST would be lost when the process exits, and a faulted task throws out of
`Wait` into the `catch` that is already there.

### 2.5.3

`Plugin.cs` only, plus the version in `AssemblyInfo.cs`. 2.5.2 is the published archive; this is
the first change on top of it, so the bump is so a warning in someone's log identifies the build
that produced it. No release built.

---

## 86. The goonshrooms call each other in — 2.5.4

Reinforcement was the last imp-only piece of the grapple. §66 had already made the *cling
dispatch* follow whichever family is attached, so a goonshroom grapple plays `goonshroom_1/2/3`;
what still did not follow was the spawner, so a goonshroom grapple stayed at however many walked
into you while an imp grapple called in a third every 5 s.

### The two hardcoded imps

`ImpGrappleReinforcement` — now `GrappleReinforcement` — assumed imps twice:

- **The session gate.** `ImpGrappleGate.IsImpGrappleSession` returns false unless *every* clinging
  enemy is `IsImpEnemy`, so a goonshroom grapple never got past the first check.
- **The spawn.** `SpawnAndAttachRoutine` read `Tools/SpawnImpNameHint`, so even reached, it would
  have called in an imp.

Both are now the family off `GrappleEnemyProtection.ResolveGrappleFamily` — the same resolution the
cling dispatch uses, read off `GrappleScreenobject.grapplingEnemies`. `IsImpGrappleSession` is
untouched: it still gates the scene-blocking patches, where "are these imps" is the question being
asked, and its `IsImpEnemy` is deliberately broader than an `EnemyRemap` lookup.

A family with no plan spawns nothing and logs it once, the same shape as `GrapplePrefixMap`'s
missing-prefix path. A gap that announces itself; not another creature's pacing borrowed silently.

### Two things vanilla settles, read out of the IL

**A grapple cannot be mixed.** `GrappleScreenobject.StartGrapple` returns false when
`isGrappling` and the candidate's `ChargingEnemyAI.grappleAnimatorController` differs from the
`activeGrappleController`. So the first readable clinger names the whole session, and resolving a
family off one enemy is not a heuristic — it is exact. (`GoonShroomGrappleScreen`, with
`GoonShroomGrapple_One/Two/Three`, is the goonshrooms' own controller; that is what keeps them
apart from the imps'.)

**Three is a hard ceiling, and it is not ours to raise.** `maxGrappleCount` is a *serialized*
field defaulting to 3, and `StartGrapple` refuses at it. Above it there is no grapple UI animator
state and no cling scene, since those are named prefix + count. So the ask's "escalation that
builds rather than tops out at three" cannot be more grapplers — it has to be pacing.
`ResolveCeiling` reads the live `maxGrappleCount` through Traverse rather than assuming 3, and
takes the lower of it and the configured ceiling.

### What makes the goonshroom feel different

A ramp. `GrappleReinforcementInterval` is the wait for the *second* clinger; each one already
attached past the first multiplies it by `GrappleReinforcementRamp`.

| | interval | ramp | 1 → 2 | 2 → 3 |
|---|---|---|---|---|
| imp | 5 s | 1 | 5 s | 5 s |
| goonshroom | 8 s | 0.5 | 8 s | 4 s |

Imps are the flat drumbeat they have always been — `Ramp = 1` is exactly the old arithmetic, so
2.5.3's imp behaviour is unchanged. The goonshroom is slow to commit and then closes fast. The
wait is clamped to 0.5 s at the bottom and the ramp to 0.1–4, so a hand-edited config cannot turn
the tick into a spawn loop.

New keys live in a `[GoonShroom]` section, which `cfgaudit.py` enforces against the `Bind()` call.
`Tools/SpawnGoonShroomNameHint` sits with the other spawn hints instead, because that is what it
is — no hotkey is bound to it; reinforcement is its only caller.

### The spawned one has to be stowed by hand

Vanilla deactivates a grappler in `ChargingEnemyAI.PerformGrabAttack`, i.e. on the charge that
*led* to the grapple. One spawned straight into `StartGrapple` never charged, so without
`StowAttachedImp` it stands around in the level while its overlay clings to the player. That was
already true for the imp path; it is now commented rather than implied.

`EnemyInactiveAutofix` needs no change: `IsAttachedGrappler` tests membership of
`grapplingEnemies`, which is family-agnostic already, so a spawned goonshroom is skipped like a
spawned imp.

### Not touched

`GrappleDeathSequence` stays imp-only. It only ever begins on `IsImpGrappleSession`, it forces the
spawner on with its own `Imp/GrappleDeathImpInterval`, and it exists to reach vanilla's trio
overflow — a mechanic that needs `trioGrabAnimatorController` on the prefab. Whether the goonshroom
carries one is a runtime question nobody has asked yet.

Not play-tested: no session has run on 2.5.3 either.


## 87. The Black Serpent's camera grab, and what it taught the filler ladder — 2.5.5

Two asks from 2026-08-22, and they turned out to be one problem: a set of scripts that a live
signal switches between while the player is in no scene at all.

### The mechanic: hypnosis is an approach, and its one variable is distance

`BrawlerEnemyAI.canHypnotise`, in the game's own tooltip: *"it drags the player's camera onto
itself while it's on-screen and advances until it lands a grab."* `LateUpdate` calls
`CameraController.RotateTowardPosition` at `hypnosisLookSpeed` while the loop clip runs;
`HandleHypnotisingState` walks the serpent at the player and calls `LandGrab` the moment
`distanceToPlayer <= grabRange`. Read off the shipped prefab:

| field | value |
|---|---|
| `hypnosisStartRange` | 8 m |
| `grabRange` | 2 m |
| `maxHypnosisDuration` | 6 s |
| `hypnosisCooldown` | 20 s |
| `hypnosisLookSpeed` | 120 °/s |

So the whole scene is a 6 m approach with a 6 s cap on it, ending either in a grab — which plays
`Serpent_Loop` — or in the serpent breaking off.

**§71's decision to skip `serpent_hypnosis_*` was right and stays.** Its reason was that the three
clips sit on the enemy's own controller beside Idle and Walk with no grab screen behind them, so a
sexual script over a combat mechanic would be a gap that is neither inert nor visible. What made
that binding was the *dispatch*: an animator state says "hypnotising" and nothing about how close
the thing is, so a table entry would have played the same curve at 8 m as at 2 m. The states are
still `-`. The ladder is dispatched by distance instead, and the comment there now says which of
those two reasons is doing the work.

### What is on screen, measured

`Black_Serpent_Hypnosis_Loop`, 8 frames at 8 fps = **1000 ms**. The silhouette is pinned — top
edge 374–381 px on a 381 px sprite, 1.8%, under `motion_proxy`'s 3% jitter floor — so the body is
not the proxy. `motion_map` puts every bit of real change in one place: the spiral hovering over
her head. Its bright-pixel count, its radius and the phase of its first angular harmonic are
**identical at frames k and k+4** and differ at every other lag, so the spiral's period is 4
frames = **500 ms**, run twice per clip.

That settles the whole timing question without a judgement call. The device period is 500 ms, the
file is two cycles — the two-cycle convention every grab loop in this set already uses — and
because the file length is also the clip's, a phase preserved across a tier switch is a phase in
the animation as well. Polarity does not arise: a spiral turning at a constant rate has no deep
end, and the guide's rule for motion that circles rather than strokes ("switch direction at each
extreme so the device keeps moving") is exactly the triangle that got written.

Three tiers, amplitude only — 30, 60, 90 — because the spiral does not speed up as the serpent
closes and neither should the script. 90 over 250 ms is 360 units/s, just inside a Handy 1's 364,
so the ladder is playable on the slowest device in the set without slew limiting.

### The real problem: every switch restarted the device

`SendPlay` POSTs a different row name, Edi re-slices that file and plays it **from the top**. A
player hovering on a tier boundary therefore gets a new script several times a second, and the
0.25 s repeat suppression does not help — it only covers the *same* name, and a flap alternates
two. This is not a serpent problem. `RefreshFillerForCurrentHeat` runs every frame and the seven
filler rows are picked by a bare `percent >= threshold`, so heat resting on 25% has been doing the
same thing for as long as the ladder has existed.

Three things fix it, and all three had to be true at once.

**1. One time grid per ladder, one anchor, amplitude as the only difference.** The six inherited
filler rows already agreed on a shape — a zigzag whose gaps widen through the cycle — and agreed
on nothing else: eight, nine or ten points, six different start positions (0, 6, 8, 10, 12, 18),
six different grids. They are now generated by `code/ladders.py` on the average of their own grids
(170/190/200/210/240/260/310/420 ms), every row anchored at 0 at both ends, differing by peak
amplitude and by one thing that keeps the two families apart: damage jolts to the bottom on every
trough, arousal swells over a floor that drops as heat rises. Length stays 2000 ms.

**2. The switch carries the phase.** Edi's `EdiController.Play` is
`Play/{name}` with `[FromQuery] long seek`, and — read out of `DeviceBase.CompletePlayback` —
its own loop restart passes `elapsed % duration` back through that same parameter. So **a seek
biases the first pass only and the row loops from 0 afterwards**, which is precisely what a
phase-preserving switch needs and not something to be assumed. `SendPlay(..., preservePhase:
true)` now sends `?seek=<phase>` when the outgoing and incoming rows have the same loop length,
which `GalleryRegistry` learned to record while it was already parsing `Definitions.csv`. Same
grid plus same phase means a switch is a change of amplitude mid-gesture rather than a jump back
to the top. Mismatched lengths, an unknown row, or an alias carrying its own authored `?seek=`
all fall through to a plain Play — the behaviour that was there before.

**3. Hysteresis on both sets of thresholds.** A bucket is entered at its threshold and left only
once the signal falls a clear margin below it: `FillerIntensityHysteresis` (0.05, i.e. 5
percentage points) and `SerpentHypnosisHysteresis` (0.13 of the approach band, about 0.8 m of the
shipped 6 m).

The ask also floated *letting the current cycle finish before the switch lands*. It is not needed
and would have been worse: deferring to the seam costs up to a full loop — 2 s on the filler
ladder — before the device reacts to a hit, and the seek does the same job with no delay at all.

### Dispatch: an override, not a second path

The hypnosis ladder is resolved inside `GetFillerGallery`, ahead of the damage and heat maps,
rather than through a dispatcher of its own. It inherits every gate the filler already has — grab,
grapple, death, menus, the stop/resume hotkeys — and cannot race `GrabHooks` when the grab
finally lands. The hypnotist is `BrawlerEnemyAI`'s own private static `currentHypnotist` (set in
`StartHypnosis`, cleared in `StopHypnosis`), so there is no scene search and no chance of reading
the wrong serpent when two are alive.

`RefreshFillerForCurrentHeat` used to short-circuit on "neither percentage moved" and only then
resolve a gallery. That could not see a change coming from anywhere but the two meters, and a
tier that moves with distance is exactly such a change. It now resolves unconditionally and
compares the *name* — which is also one `PlayerStats` lookup per frame instead of two.

### Tier boundaries are fractions, not metres

`SerpentHypnosisTierFractions` splits the band between the prefab's own `hypnosisStartRange` and
`grabRange`, read off the live component. Empty means even splits, so three tiers break at 4 m and
6 m today and keep meaning that if the serpent is ever retuned. The tier list is a config string
of any length; the code derives the boundary count from it.

### The invariant needed a checker

A ladder's property is invisible in any one file. A hand-edited `filler_cum_50` looks perfectly
reasonable on its own and only steps the device against its neighbours, and nothing in the tree
would have said so — `deploy.py --check` answers "is the game running the working tree", not "is
the working tree still a ladder". `python3 code/ladders.py --check` now answers the second,
compares every row against what the generator produces and exits 1 on drift. Same rule as always:
a gap has to be inert and visible.

### What a session has to judge

Everything above is measured or read out of IL. Two things are not:

- **`filler` is busier.** It was one 0→40→0 every 1200 ms; on the shared grid it is four pulses to
  40 every 2000 ms — the same amplitude at about twice the travel per second. That is the price of
  putting the idle state on the ladder, and whether it reads as restless is a play.
- **Whether the tiers escalate.** 30/60/90 is a defensible spacing, not a measured one.

Mod **2.5.5**. `cfgaudit`, `patchaudit`, `slugharness` and `ladders --check` clean, `animsweep` 93/93, both installs
deployed. Not play-tested — nor is 2.5.4, which this sits on top of.



## 88. A reference video per scene, rendered rather than captured — tooling

Asked for on 2026-08-22: a frame-accurate reference video per scene, named for its funscript, so
another scripter can work against a video whose timing *is* the game's and hand back a curve that
needs no retiming. `code/refvideo.py` writes 93 of them into `Edi/_reference/videos/` — every row
in `animsweep.MAP`, which is every gallery row that answers to an animation.

It is a render, not a capture. `animcheck.clip_frames` already returns the sprite list, the hold
and the sample rate out of the shipped assets, and that is the same call the whole measurement
chain is built on, so there is nothing here that could drift against the numbers already in
`TIMING-AUDIT.md`. No screen recording, no dropped frame, no audio-versus-video phase — the whole
of `learnings/reference-video.md` exists because capture was once the only source, and this closes
the last reason to reach for it.

### The video runs at the clip's own sample rate

6, 8, 9 or 10 fps across this set, one video frame per sprite frame. That is the only rate at
which nothing is duplicated and nothing is dropped: frame k of the file is frame k of the game.
`--multiple=N` emits N identical frames per sprite for a player that handles a 6 fps file badly,
which keeps the property because it is an integer multiple. Every file is all-intra (`-g 1`), so
stepping frame by frame in a player lands on the frame rather than on the last keyframe.

The length is the animator's hold, not `frames / fps`. Those differ for exactly one clip in the
set — `GooperGrabScreenCum`, 14 frames at 10 fps held for 1500 ms, so its last frame stays up for
the final 100 ms — and the video holds that frame rather than stretching every frame by 7%. The
ask predicted "the two Gooper ones"; both carry the second sprite curve that causes it, but only
the cum one is actually held past its own frames, on 0.3.1 and on 0.2.1 alike. `animsweep`'s
header said "the two" too, and now says which.

### Sprites needed registering, and bottom-left alignment is not it

Every measurement tool in this tree pastes frames against a shared bottom-left corner, because
sprites are alpha-trimmed per frame to different sizes (§33, and `learnings/funscript-proxies.md`
states it as a rule). That is fine for a proxy and wrong for a picture: **the trim is not
symmetric**, so a bottom-left stack puts a horizontal jitter on screen that the game does not
have. `GhoulGrabStart`'s six frames lose 9 to 16 px off their left edge; `PlantashaGrab` varies by
10 px.

Unity keeps what is needed: a sprite's on-screen extent is its full `m_Rect` cell anchored at
`m_Pivot`, and `m_RD.textureRectOffset` is where the trimmed pixels sit inside that cell.
`refvideo.sprite_layout` works in pivot-relative coordinates and so is correct even for a clip
whose frames come from cells of different sizes.

**The measured curves are unaffected, and that was checked rather than assumed.** Across the
scenes with a registered proxy the vertical offset range is 0 px everywhere — the shared bottom
edge is exactly right — and the horizontal proxies (`imp_tip`, `nun_hood`) sit on clips whose
horizontal range is 0 px as well. `plantasha_shaft` is the one that takes a band as a fraction of
each frame's own width on a clip that moves 10 px; its curve was verified against the frames at
r >= +0.90 and is not being re-derived here, but that is where to look first if it is ever
questioned.

### The claim is checked, not asserted

`refvideo.py --verify` decodes every file back and asks, for each video frame, which sprite frame
it is closest to. "Frame-accurate" that nothing checks is a claim, and the check found its own
subtlety: **15 of the 93 clips list a pixel-identical sprite twice** — `DragonFaceSit` opens with
`face_sit-Sheet_0` on two keyframes, `Gravy_Cum` repeats `BJ cum-Sheet_2_2` five frames later,
`Zombie_Cum` ends on a held frame. No decoder can separate those, and nothing is wrong with the
file, so the test is that the expected frame is *among* the closest rather than uniquely so. All
93 pass; codec error at crf 14 is under 1 of 255.

`--check` reports what would be rendered without writing, and both modes name what they skip:
the ten ladder rows (`code/ladders.py` builds those against each other, not against a scene) and
`ambient_wendigo_hole`, the legacy row whose scene is really `peek_wendigo_ride`. 93 + 10 + 1 =
the 104 rows in `Definitions.csv`, so the arithmetic itself says nothing was quietly dropped.

Each `<row>.mp4` has a `<row>.json` beside it with the loop length, the stroke period, the frame
times and the `Definitions.csv` slice, plus an `index.csv` and a `README.md` for whoever is handed
the folder. The output is 21 MB, untracked and regenerable — `Edi/_reference/` is already ignored
except for `source-scripts/`. **It is not in the release archive and is not meant to be**: decided
on 2026-08-22 to zip and post the folder by hand, because it is material for scripters rather than
something a player installs, and `release.py` shipping 21 MB nobody playing the game reads would be
the wrong default.

No mod change; the plugin is untouched at 2.5.5.


## 89. Multi-axis, and the links to Edi itself

A scripter wants to work on multi-axis. Nothing here blocked that, but three things made it harder
than it needed to be, and all three are cheap.

### The mechanism, read out of Edi rather than guessed

Edi's source is at `github.com/NoGRo/Edi` and the rule in this project is to read it rather than
reverse-engineer behaviour. Its links now sit in `PROJECT.md`, `code/README.md` and
`learnings/edi-integration.md` — the source, the release/documentation thread, and the "how to
integrate your game" guide — because they were folklore in this repo and folklore is where
reverse-engineering starts.

**An axis is a filename token, not a row.** `FunScriptFile.axis` takes the last dot-separated token
of the filename without its extension and parses it against the `Axis` enum;
`DiscoverExtension.Discover` strips that token back out of the variant it computed, so the folder
still names the variant; `FunscriptRepository.ReadGallery` files each script into
`gallery.AxesCommands[axis]` under the same row name. So `nun_grab.twist.funscript` beside
`nun_grab.funscript` in `detailed/` needs **no `Definitions.csv` row, no config entry and no mod
change**, and the row's slice applies to every axis of it. `OSRPosition` maps the axes onto TCode
channels (L0 stroke, L1 surge, L2 sway, R0 twist, R1 roll, R2 pitch, V0 vibrate, A0 valve, A1
suction); DG-Lab reads the e-stim three. The full note, with the traps, is in
`learnings/edi-integration.md`.

Two facts a scripter needs before starting: **an axis nothing writes rests at 50, not 0**
(`OSRScript`, except `Default` and `Vibrate` which rest at 0), so only what moves needs a file; and
**an axis file is inert on hardware that lacks the axis**, so a Handy is unaffected and multi-axis
can go in one scene at a time.

### The tooling was axis-blind, which is the kind of gap this project keeps banning

`speedcheck.py` and `variants.py` both walk `Definitions.csv` and open `FileName + ".funscript"`, so
an axis file was **invisible to both** — never speed-checked, never mirrored into `handy1/`. Not
wrong, but silent, which is the failure mode the project's own rule names: a gap must be inert and
visible.

- `speedcheck.py` now discovers `<row>.<axis>.funscript` siblings, lists each on its own line, and
  applies the device ceilings **only to the linear axes**. That is not a simplification: the cap is
  `mm/s ÷ stroke mm`, arithmetic with no meaning on an axis measured in degrees. Non-linear axes are
  still reported for point spacing, which every device cares about.
- `variants.py` copies per-axis scripts into `handy1/` **unchanged** rather than slew-limiting them,
  and says so per file. A Handy 1 has one axis and ignores the rest, so the copy is inert — but it
  keeps the two variant folders in parity, which means a device pointed at `handy1` can never find a
  row missing an axis its master has. It also reports any per-axis file in a variant with no master
  in `detailed/`.
- `release.py` and `deploy.py` already glob `*.funscript`, so axis files ship and deploy with no
  change. Checked rather than assumed.

### The reference videos now say where the lateral motion is

`refvideo.py`'s sidecars gained a `motion` block: the screen-space centroid of whatever differs from
the median frame, per frame, in **both** axes, plus the travel in pixels. The stroke proxies answer
"how deep"; this answers the question multi-axis actually starts from — *does anything in this scene
move sideways, and when*.

**This is only measurable because §88 registered the frames properly.** A bottom-left stack carries
up to 16 px of horizontal trim jitter, which is the same order as the motion being looked for, so on
the old alignment the question could not be asked at all. `index.csv` carries `travel_x_px` and
`travel_y_px`, and the ranking is legible on its face: `Gravy_Start` at 224 px and the two riding
scenes behind it, against `ambient_mimic_wall_fuck` at 0.4 px, which is a scene pinned against a
wall.

Screen space is not device space, and the sidecar says so: whether a horizontal travel is sway or
surge depends on the camera, and a rotation shows up as neither. The tool measures; the scripter
decides.

No mod change; the plugin is untouched at 2.5.5.


## 90. The videos are for someone who has never seen this project — tooling

The reference folder from §88 read like an extract of this repo's notes: row names, ladder rows,
`textureRectOffset`, a sidecar of JSON per scene. Every word of it true, and all of it noise to the
person it is for — a scripter who wants to open a video and write a multi-axis script for it. Two
changes, both about removing steps rather than adding information.

### A file is now as long as the script should be, not one loop

Rendering one animation loop was the purest thing to do and it pushed arithmetic onto the reader:
`ambient_gargoyle_ledge_fuck` loops every 400 ms and its script is 3200, so scripting the video got
you an eighth of a row. Files are now the loop repeated up to the row's length and cut on a frame
boundary, so **the video is the deliverable's length** and the instruction is "script the whole
video". `--one-loop` still renders a single loop.

The cut is at `round(ms * fps / 1000)` because 36 of the 93 rows only land on a whole frame after
rounding - a 9 fps frame is 111.1 ms and `Definitions.csv` stores whole milliseconds. The error is
under 0.005 of a frame everywhere. Note the length is a whole number of **strokes**, not always of
loops: `ambient_imp_gangbang` is 3125 ms against a 1250 ms loop, because that loop holds two
identical strokes and the row is five of them. The repeat is seamless either way, which is exactly
why the clip could be split in the first place (§33).

### The page in the folder is written for the reader, not the repo

`readme_text` now generates a page that says what the files are, how to name what you write, how
extra axes work, and then **a table of all 93 scenes** - length, loop, fps, frames, strokes,
sideways travel - so nothing has to be opened as CSV or JSON to begin. `index.csv` and the
per-scene sidecars are mentioned once, at the bottom, as optional.

Three facts a stranger needs and could not guess are on that page: **every axis of a scene must be
the same length**, because a short axis file does not loop on its own - `ScriptBuilder.TrimTimeTo`
pads it by holding its last value while the rest of the scene keeps going; **an unwritten axis rests
at 50**, not 0; and **a dot in a filename means an axis**, so filenames must not carry one for any
other reason.

A filtered run (`refvideo.py Nun_Grab`) now leaves `index.csv` and `README.md` alone and says so,
rather than rewriting the whole-set files from the handful of rows it touched.

The folder is 38 MB now that files carry their full length, still untracked and regenerable, and
still verified frame by frame - `--verify` passes on all 93.

No mod change; the plugin is untouched at 2.5.5.


## 91. What a session felt, and one enemy that was never there — 2.5.6

A Linux run on 2026-08-22 produced six notes and two asks. Four of them were answerable from the
tree; the rest need the log lines that only another session can produce, and are written up in
`TODO.md` with the exact line to look for rather than guessed at here.

**The idle filler moved twice as much as it used to, and §87 did it.** The inherited `filler` was
one 0-40-0 stroke per 1200 ms — 66 units/s of travel — while the six intensity rows were already
eight points per 2000 ms. §87 put all seven on one grid, which is what makes a tier switch
stepless, and left `filler` at its inherited *amplitude* on the intensity rows' *density*: four
pulses where there had been one, 128 units/s. That is the whole complaint, and it is arithmetic
rather than taste.

The fix could not be density, because a shared grid is rule 1 of a ladder and the reason the set
exists. So the amplitude is now whatever reproduces the travel rate that was accepted before:
**20, giving 64 units/s against the inherited 66.** The other six rows were checked the same way
and left alone — they land within rounding of their old figures (damage_75 323 → 323,
cum_75 302 → 296, cum_50 198 → 190), because the grid was averaged from them in the first place.

**The serpent's hypnosis did not read as different from the filler, and tier 1 was the reason.**
It was 30, i.e. *below* the filler it replaces. The ladder does not interrupt a silent device, it
interrupts the idle one, so its bottom rung has to be a step up from that. Tiers are now
**40/65/90** rather than 30/60/90: 160 units/s against the idle filler's 64. Shape was already
distinct — a constant-rate triangle at 500 ms against a decelerating zigzag at 2000 ms — but shape
is not what a stroker communicates; travel is.

**No goonshrooms appeared in several runs, and that was us.** `EnemySpawnShuffle` is a *prefix* on
`EnemySpawner.GetEnemyPrefab` and `ArenaEnemySpawner.GetEnemyPrefab`: it replaces the spawner's own
choice outright, returning `false` so vanilla never runs. Its pool was collected from six hardcoded
`CollectDebugHint` calls — imp, gargoyle, gooper, nun, zombie, plantasha — with `IsNormalEnemyKey`
listing the same six a second time. Both lists predate game 0.3.1. So the goonshroom, which 0.3.1
added, could not be spawned by any spawner in the game while the shuffle was on. Not a rarity
problem, an absolute one, and invisible: the mod was doing exactly what it was told.

The pool is now the config entry **`Gameplay/EnemySpawnShufflePool`**, defaulting to the six plus
`goonshroom`, with `IsNormalEnemyKey` reading the same list instead of repeating it. Each key
resolves to its existing `Tools/Spawn<Key>NameHint`; a key with no hint is skipped and logged
rather than silently dropped. Chaser bosses stay refused by `IsTrustedShufflePrefab` whatever the
list says. **The lesson is the general one:** a mod that *replaces* a vanilla choice inherits the
duty to keep up with vanilla's content, and nothing announces when it has not.

**Shaking a grappler off never brought the device back down.** The cling dispatch had a start
branch and an `else if (num2 > _impTier)` escalate branch and nothing else, so a three-imp grapple
shaken back to one kept playing `imp_3` until the grapple ended — the device claiming more than was
happening. The attached count was never the problem: `RemoveOneGrappler`'s postfix already calls
`ReleaseImp`, so `GetAttachedImpTier` drops correctly. Only the dispatch was one-way.

There is now a matching drop branch, and it is deliberately not the mirror of the escalate one. The
count is read every frame and dips for a frame or two while a shaken-off grappler is released and
again while its replacement attaches, so a lower count has to *hold* before it is believed:
**`Imp/GrappleTierDropHoldSeconds`, 0.35 s.** A count that comes back up inside the hold cancels the
pending drop without sending anything. The log line is `[IMP] drop tier=1 count=1 -> imp_1`.

**A miniboss tier, asked for on the same day.** The escape gate already had two tiers — 20 s for
anything that walks, 40 s for the chaser bosses — and the horny locks had two as well: one lock for
an ordinary grab, straight to the limit for a chaser boss. The Blinded Beast, which is harder to be
caught by than anything in either group, was paying an imp's price in both. Three settings, in
`Gameplay`: **`MinibossEnemyKeys` (`blinded_beast`)**, **`EndGrabDelaySecondsMiniboss` (30)** and
**`HeatLockMinibossLocks` (2)**. The keys are the ones `Naming/EnemyRemap` produces, so the list
reads like every other enemy list in the config. `ResolveEscapeDelaySeconds` checks the tier the
same two ways it already checked the chaser-boss one — the live grab enemy, then the interact
scene's key — so the timer holds whichever path is running.

The repeat guard is why the extra locks are added in a loop rather than by passing a count:
`AddLockForFirstScene` keys its guard on the source, so the second and third calls for one grab
would refuse themselves. The first call carries the guard and the rest go through unguarded.

Audits after all of it: `cfgaudit` 155/155, `patchaudit` clean, `ladders --check` clean,
`animsweep` 93/93, `speedcheck` unchanged in shape, `release --check` builds. Both installs
deployed at **2.5.6**.


## 92. The log was there the whole time — 2.5.7

§91 answered four of the 2026-08-22 notes from the source and said the other three needed another
session. **That was wrong, and wrong in an avoidable way: nobody opened the log.** All three were
already answered in `BepInEx/LogOutput.log` and `PncEdi-missing-definitions.log` from the run that
produced the notes. The rule this project keeps writing down — *a gap must be inert and visible* —
had done its job at every one of these; the visible part was simply never read.

**The GoonShroom gallery: `enemy='Goon Shroom'`, with a space.** From the run, in full:

```
[GALLERY-STEP] enemy='Goon Shroom' key=goon_shroom anim='GoonShroom 1' -> goon_shroom_goonshroom_1
[ALIAS-GAP] no mapping for 'goon_shroom_goonshroom_1' - add it to GalleryAliases
[EDI-SKIP] goon_shroom_goonshroom_1 -> goon_shroom_goonshroom_1 (not in Definitions.csv)
```

`EnemyRemap` matches by case-insensitive substring, and its entries were `GoonShroom_Enemy` and
`GoonShroom`. The gallery menu hands the hook the enemy's **display name**, which for 0.3.1's
goonshroom is `Goon Shroom` — and `"goon shroom"` contains neither. So `ResolveEnemyKey` fell
through to its slug fallback, produced `goon_shroom`, and every one of the five gallery rows slugged
to `goon_shroom_goonshroom_*` and played nothing. Fixed with one entry: `Goon Shroom=goonshroom`.

**Why four days of audits missed a five-row gap.** `slugharness` reported those exact rows resolving
cleanly the whole time, because `Emit` called `BuildGallerySlug(key, state)` **directly** while the
game calls `ResolveEnemyKey(name)` first and passes the result. The harness was asking the question
with the answer already substituted in — and its `GalleryStates` table was keyed on resolved forms
(`"goonshroom"`) rather than on the display names the gallery route actually supplies. Both are
fixed: `Emit` resolves first, and the goonshroom row is keyed `"Goon Shroom"`. The other rows keep
their resolved-form keys and a comment says plainly that they therefore still do not test their own
remap, with the four display names confirmed from `[GALLERY-STEP]` lines listed for whoever
replaces them. **A harness that skips a step cannot fail at that step**, and this one had skipped
the step that broke.

**The serpent loop desync: its grab-screen animator never restarts.** The handoff line is

```
[GRAB-ANIM] controller='BlackSerpent GrabScreen' clip='BlackSerpent GrabScreen' t=335.68
```

`t` is normalized time in whole clip cycles, so the serpent's grab screen was **335 loops deep and
68% through a cycle** when the grab began, while `Serpent_Loop` was dispatched from position 0.
Every other grab-screen controller in the session — eleven of them, `AltGhoulGrabScreen`,
`BlindedBeastGrabScreen`, `WeaponsMimicGrab`, `Plantasha_GrabScreen`, both gargoyles — reports
`t=0.00`. So this is one enemy's fault and not a general one, which is exactly why nothing else in
the set sounded wrong. §91's reasoning about the phase carry was right and beside the point: the
desync was never between two scripts, it was between the script and the animation.

`SendPlay` now takes the animator's normalized time and clip length and seeks the row to the
animation's own phase. It is not simply `frac(t)`: a script in this set is not always one clip
cycle long — grab loops are two by convention — so the phase is taken across the *script*, using
`cycles = round(scriptMs / clipMs)`. A ratio that is not near a whole number means the script and
the clip are not describing the same loop, and the seek is dropped rather than guessed. Inert at
`t=0`, so the other eleven controllers are untouched. The new line is `[EDI-PHASE]`.

**The jerky filler: the two families flapping at the same tier.** 279 filler dispatches in the
session, **39 of them less than a second after the one before**, and the pairs name the fault:

```
  5  filler_damage_50 -> filler_cum_50        4  filler_damage_25 -> filler_cum_25
  2  filler_cum_50 -> filler_damage_50        4  filler_cum_25 -> filler_damage_25
```

That is not a tier change at all — it is the arousal and damage rows at the *same* tier, alternating.
`FillerIntensityPriority = Higher` resolved to a bare `_lastDamagePercent > _lastCumPercent`, read
every frame, with no hysteresis; both meters move continuously, so whenever they were close the
device swapped families several times a second. The two families share the grid and differ in their
**floor** (damage jolts to 0 on every trough, arousal swells over a raised one), so a flip changes
how deep every trough goes while nothing the player did has changed.

This is precisely the failure that `ResolveIntensityGallery` was given hysteresis for — one level
up, and missed at the time. It now reuses the same `FillerIntensityHysteresis` setting: the leading
meter keeps the lead until the other is clear of it by the margin. **The lesson generalises: adding
hysteresis to a threshold is not finished until every comparison in that decision has it**, because
the flap simply moves to the one that does not.

**Three more open items closed by the same file, at no cost.** §85's POST failure logging: **zero**
`failed:` lines in the session, which was the expected result and is now an observed one. §78's
`#14` guard: `[AI-GUARD] kept Plantasha_Enemy's live grab: StopGrab skipped while state=Grabbing`
appears, with **no** `[AI-GUARD] unstuck` after it. And the one-way cling ratchet §91 fixed blind is
confirmed empirically — 5 escalations to tier 2, 3 to tier 3, and not one drop in the whole run.

**The practice change is the point of this entry.** The mod writes `[ALIAS-GAP]`, `[EDI-SKIP]`,
`[GALLERY-STEP]`, `[GRAB-ANIM]` and a dedicated `PncEdi-missing-definitions.log` so that a fault
announces itself; §91 read the source instead and got one of three right. **Read the log from the
run that produced the notes, before reading the source** — it is the cheapest evidence in the
project and it was sitting at `game-linux/BepInEx/LogOutput.log` the entire time.

Audits after: `slugharness` 169 rows, **zero UNMAPPED**; `cfgaudit` 155/155; `patchaudit` clean;
`ladders --check`, `animsweep` 93/93 and `release --check` all unchanged. Both installs at **2.5.7**.


## 93. The first item off the 2.5.7 list — the GoonShroom gallery plays

Confirmed in play on 2026-08-22 (Linux, 23:55-23:56 session), the first of the seven confirmations
the 2.5.7 handoff asked for. §92's one-line `Goon Shroom=goonshroom` remap entry does what it was
meant to: all five GoonShroom gallery rows resolve and dispatch.

```
[GALLERY-STEP] enemy='Goon Shroom' key=goonshroom anim='GoonShroom 1' -> goonshroom_1
[GALLERY-STEP] enemy='Goon Shroom' key=goonshroom anim='GoonShroom 2' -> goonshroom_2
[GALLERY-STEP] enemy='Goon Shroom' key=goonshroom anim='GoonShroom 3' -> goonshroom_3
[GALLERY-STEP] enemy='Goon Shroom' key=goonshroom anim='Loop'         -> goonshroom_loop
[GALLERY-STEP] enemy='Goon Shroom' key=goonshroom anim='Cum'          -> goonshroom_cum
```

`key=goonshroom` on every line — the failure signature named in the handoff was `key=goon_shroom`,
with the underscore, and it does not appear. Each is followed by its `[EDI] Play` with the expected
alias (`goonshroom_1_Gallery`, `GoonShroom_Start_Gallery` for the loop, `GoonShroom_Cum_Gallery`),
and the whole run carries **zero** `ALIAS-GAP`, `EDI-SKIP` or `failed:` lines.
`PncEdi-missing-definitions.log` gained no new entries; its last five `goon_shroom_goonshroom_*`
rows are from the 22:10 run, before the fix was deployed.

Two other things the same short session showed in passing: `[INPUT] backend repaired ->
NewInputSystem (was NullInputSystem; BepInEx probed before the keyboard existed)` — the §72 repair
firing on schedule — and `[AMBIENT-SCAN] 1 audio source(s): 1x goonshroom gangbang` alongside the
gallery rows, so the ambient path sees the scene too.

The session was gallery-only, with no gameplay in it, so nothing else on the 2.5.7 list moved:
items 2 through 8 of the handoff all still want a run.


## 94. Two guesses retired: the peek heuristic, and "assume there are more"

Desk work, no gameplay involved. Both items were the same shape — a place where the project was
carrying an assumption instead of an answer — and both are now settled in a way a future game
build re-checks by itself.

**`PeekGalleryMap.Heuristic` is gone.** It matched keywords: `"imp"` plus any of `three` / `peep` /
`3` meant `peek_imp_three_way`, `"zombie"` plus `bj` meant `peek_zombie_bj`, seven scenes in all.
Since §80 gave all eleven peek entries an exact asset key (the ScriptableObject's own name and the
peephole controller) it has been unreachable, and `PeekClipMap` resolves a peephole this table has
not seen from config rather than from code. So it was dead — but the reason to delete it rather
than leave it is what it would do if it ever ran again:

- **`imp_3` is one of the imp *cling* rows**, and it matches the imp clause (`"imp"` and `"3"`).
- **`Resolve`'s result is also read as a predicate.** `SceneEscapeGate`, `HeatLockSystem` and
  `CameraSwapHooks` all ask `IsPeekScript(PeekGalleryMap.Resolve(...))`, and `HeatLockSystem`
  asks it of *every clip on the animator* in a loop. A false positive there does not merely play
  the wrong row, it tells the escape gate and the heat lock that a grab is a peephole.

Only the alias stage running first keeps those apart today. The file's own comment already said
the right thing about a different stage — *a wrong scene is worse than a missing one* — and the
heuristic is that rule's counterexample sitting in the same method. `Resolve` now returns null,
and `SendPeekGalleryStep` already prints all four keys it tried, so the miss is inert and visible
in the way the rest of the project's gaps are.

**Every `heat == 0` test vanilla has, counted.** `learnings/grab-and-ai-mechanics.md` said "assume
there are more" after §11 (overheat cleared only at exactly 0) and §31 (the cum cooldown likewise),
both of which were found by tripping over a looping animation. Assuming was the wrong tool: the
assembly can be asked. `python3 code/patchaudit.py --heat` now scans the IL for every comparison
of `currentHeat` / `CurrentHeat` / `maxHeat` against `0.0` and prints a verdict per site, checked
against a `HEAT_ZERO_REVIEWED` table in the script.

Ten sites on 0.3.1, and **no third fault**:

| sites | verdict |
|---|---|
| `GrabScreen::HandleHeatBuildup` | §31, patched |
| `PlayerStats::HandleOverheatingStates` | §11, `ClearOverheatAtFloor` |
| `get_CanPerformActions`, `get_CanDash`, `CanAttackNow`, `IsAttackLocked`, `CalculateTotalMovementMultiplier` | all five reached **only while `hasBeenOverheated`**, so §11's fix at that flag already covers them |
| `HandleHeatCooldown` | benign — `heat > 0` gates the cooldown tick, which `CoolHeat`'s clamp re-floors |
| `UpdateAnimationBools` | benign — sets `HasAnyHeat`, and at the floor the player does have heat |
| `OnValidate` | editor-only |

The middle row is the finding worth keeping. Five separate "no attacking / no dashing / no acting
until heat is 0" gates would each have needed patching on their own terms; they are all behind one
boolean, and §11 fixed the boolean. **Look for the flag the tests share before patching the
tests** — and the count is what makes that visible, because a per-symptom hunt would have reached
them one bad session at a time.

One thing the scan turned up at the other end of the range, not a fault:
`GrappleScreenobject::CheckTrioGrabOverflow` fires at exactly `CurrentHeat >= MaxHeat`, which is
why `GetFullLockHeat` parks a full lock one point *below* the cap. The ceiling has the same
brittleness as the floor and was already handled by accident of design.

The audit is the durable part. A site the next game build adds prints `NEW ... UNREVIEWED` and
fails the run; a reviewed site that build removes prints `gone`. "Assume there are more" is
replaced by a command that answers it.

Audits after: `cfgaudit` 155/155; `patchaudit` clean and `--heat` 10/10 reviewed; `slugharness`
169 rows, zero UNMAPPED; `ladders --check` unchanged. `animsweep` was not re-run — it reads sprite
and clip data, which neither change touches. Mod still **2.5.7**; the DLL was rebuilt and deployed
to both installs.


## 95. The setting a diagnosis depends on stops being a manual step — tooling

`WriteUnityLog = true` has now been the reason a session started blind twice (§56, §72), and both
times the fix was to set it by hand in the game's `BepInEx/config/BepInEx.cfg` and write a note
saying to check it next time. The note is what failed. `deploy.py` has forced `[EDI] Debug = true`
into every dev install since it existed, for exactly this reason; the BepInEx-side setting that
makes the game's own throws visible was left to a person.

`deploy.py` now forces two keys into each target's `BepInEx.cfg` on every deploy:

    [Logging.Disk]
    WriteUnityLog = true        # game-side throws reach LogOutput.log at all
    Enabled = true              # the log file is written at all

**It edits the file, it does not deploy one.** That distinction is the whole design. Everything
else `deploy.py` writes is a payload built from the working tree and copied over, but BepInEx
rewrites `BepInEx.cfg` from the *running version's* own `Bind()` defaults on every shutdown —
comments, key order, and which keys exist at all come from the runtime, not from us. A template in
the repo would therefore pin one BepInEx version's idea of the file into every install and drift
the moment the pinned pack moves. So `force_setting()` rewrites one key inside one section and
leaves every other byte alone, preserving per-line endings because the Windows install's copy is
mixed CRLF/LF and a uniform rewrite would show as a diff on every deploy. Verified against the
real file: flipping `WriteUnityLog` to `false` makes `--check` exit non-zero, a deploy restores it,
and the result is byte-identical to the original — two changed lines, `[Logging.Console] Enabled`
untouched by the `[Logging.Disk] Enabled` force.

If a target has no `BepInEx.cfg` at all — a fresh install, which is the case the old note was
written for — it gets a two-key seed rather than a copy of a full config. BepInEx binds every
setting it knows on the next launch and writes the file back complete, keeping the values it
finds, so a two-line file becomes a correct full config for whatever version is installed.

**`release.py` is unchanged and still ships no `BepInEx.cfg`.** The two ends stay set
independently, the same way `Debug` is: a player gets whatever stock file BepInEx writes on first
run, and these two installs are never quiet. `--check` covers the file too, so "is what I am about
to launch actually the working tree" now includes "will it log".

The rule this leaves, in `learnings/debugging-and-diagnostics.md`: **a diagnostic that has to be
re-enabled by hand will one day not be.** Both dev installs already read `true`, so this deploy
changed nothing in them — which is the point at which it was worth writing, rather than after the
third time.


## 96. Two seconds of loop after a cum, and a log line that stops blaming the wrong file — 2.5.9

**The post-cum grace (`Gameplay/PostCumGraceSeconds`, 2 s).** Under a horny lock the heat floor is
`maxHeat * locks / total`, so at 13 or 14 of 15 it sits one or two units below max. §11's
`CumCooldownEndsAtLockFloor` ends the cum at that floor; vanilla then refills those one or two units
in a fraction of a second and `TriggerMaxHeatAnimation` fires again before the grabbed loop has
played through once. On screen it is a flicker. On the device it is worse, because loop and cum are
different gallery rows: two scripts alternating several times a second. Full lock was already
handled — `FullLockHoldsCum` keeps the cum on screen where the floor is exactly one unit down — and
this is the tier below it, which had nothing.

TODO's note proposed suspending the heat floor for a moment. **That would not have worked**, and the
reason is worth keeping: the floor is read by `EnsureHeatBounds` on every tick, so heat would cool
below it during the grace and then be *snapped back up* when the grace expired — a two-unit jump
straight into the next cum, which is the jerk this is meant to remove.

The lever used instead is vanilla's own `heatIncreaseBlocked`, the flag `TriggerMaxHeatAnimation`
sets for the duration of a cum and `OnMaxHeatAnimationComplete` clears. Holding it two seconds
longer is that flag meaning exactly what it already means, and heat simply sits still at the floor
while the loop plays. Three things make it safe to hold a vanilla flag:

  * `HandleHeatBuildup`'s build branch is its **only** reader — decompiled and checked, not assumed.
  * `EndGrab` clears all four heat flags unconditionally, so the worst a grace that somehow outlived
    its deadline could do is stop heat building until the grab ends.
  * The tick re-asserts the flag while the deadline is in the future and clears it exactly once
    when it passes, so a grace can only ever end, never latch. (Re-asserting rather than setting it
    once is necessary: vanilla clears the flag itself at the end of the cum, which is *before* the
    deadline.)

`OnMaxHeatAnimationComplete`'s postfix was split so this had a single place to hook: `HoldCum`
returns whether the cum was kept on screen, and only "we did not hold it" arms a grace. The prefix
now also captures vanilla's `heatFullyCooled` **before** the original runs, because the whole vanilla
method is `if (heatFullyCooled) { ... }` — without that read, a call that changed nothing looks
identical to the one that actually ended the cum, and a grace armed on a no-op would block heat in
the middle of a loop that was building fine.

**The `not in Definitions.csv` message was blaming the wrong thing** (three call sites: the
missing-definitions log, `EDI-SKIP`, and `GalleryAliases`' startup warning). `GalleryRegistry.IsKnown`
tests the registry, which is the hardcoded seed list *plus* every row read from `Definitions.csv` —
so the message named one of two sources, and it read as "the file lacks this row" when the more
likely cause is that no file was found at all: `GetDefinitionPaths` tries three locations and all
three are allowed to be absent. The messages now say "no such row in the gallery registry" and name
what was actually read — `.../Edi/Gallery/Definitions.csv (N row(s) beyond the built-in seed, M
known in total)`, or `no Definitions.csv found`. That distinction is the whole diagnosis: a missing
file makes *every* non-seed row report as unknown at once, and the old message sent you looking for
one row.

**The Black Serpent hypnosis band, read but not changed.** The 2026-08-22 run's two readings outside
the band (`9.9m of 8.0-2.0`, `12.3m of 8.0-2.0`) are the mechanic, not a fault: `BrawlerEnemyAI`
*starts* hypnosis at `distanceToPlayer <= hypnosisStartRange` (8 m) and ends it only past
`loseTargetRange` (18 m) or `maxHypnosisDuration` (8 s), with the gaze-pull and the advance gated on
`InHypnosisLoop() && hypnosisInView` rather than on distance. So tier 1 legitimately covers 6 m to
18 m. The options and a recommendation (keep it, fix the comment) are written up in TODO; no code
was written, because which one is right is a judgement about how the device should feel while a
player kites, and that is a play.

Audits after: `cfgaudit` 156/156, `patchaudit` clean and `--heat` 10/10 reviewed. Mod **2.5.9**,
deployed to both installs. `animsweep` not re-run — nothing here touches sprite or clip data.


## 97. The shaft does not shake; the fluid does — `BlindedBeast_Cum_T`'s hold re-measured

The last queued curve change from §83, and the last item on §81's play. The note read: *its one
late buzz burst was placed by whole-frame difference, not by anything visibly moving; the play
suggests the real proxy is the shaft's shake during the hold.*

**Half of that is right.** The whole-frame difference did put the burst in the wrong place. But the
shaft does not shake, and it is worth saying how flatly: across all fourteen hold frames (f9-f22)
the pink mask spans **x 224-255 in every single one**, and its top edge moves between 183 and 186 px
— 3 px on a 270 px frame, under `motion_proxy`'s 3% jitter floor. `learnings/funscript-proxies.md`
already has the rule for this: reproducing a wobble that size is scripting pixel noise and calling
it measurement. Scripting the shake as asked would have produced a curve with nothing behind it.

What *does* move through the hold is the **fluid over the player's head**, and it moves the whole
time:

    frame       9   10   11   12   13   14   15   16   17   18   19   20   21   22
    fluid px    9   20   37   77  120  240  246  255  268  291  267  281  308  315
    drip to y 227  227  229  231  233  251  254  254  254  254  254  254  254  256

(near-white, desaturated pixels inside the centre column below the shaft tip; `drip to y` is how far
down the canvas the lowest such pixel has run.)

The surge is f12-f14 — +40, +43 then +120 px, with the drip reaching the floor at f14 — and the old
curve had **nothing** there. Whole-frame difference reads 2.11 and 1.48 across those two frames,
indistinguishable from the 0.7-2.3 floor, because a 120 px splash is nothing against 480x270. The
single burst it did place (f19-f21) sits on the smallest of the three events. This is the failure
mode `funscript-proxies.md` opens with, in a new costume: *answer "what moves at all" before
choosing what to measure* — a whole-frame number cannot, because it averages the thing that moves
into the frame that does not.

The hold is now three bursts sized to the fluid's own steps: 0<->50 at 111 ms on the surge (450 u/s,
`shared_zombie`'s reference shape, and §48's rule that the lever is amplitude rather than more
pulses), 0<->30 on f17-f18, 0<->40 on f20-f21 where the old single burst was. Positions either side
are untouched: the f0-f9 approach still comes off `beast_pink`'s centroid and the f23-f27 cum is
unchanged.

The finding that generalises, and which `learnings/funscript-proxies.md` now carries: **a proxy that
sees nothing is not evidence that nothing happens.** The clip was already flagged as one no single
proxy measures end to end, and the hold was scripted on the one number available for it rather than
on a proxy chosen for the hold itself. Choosing one took a mask and fourteen frames.

`BlindedBeast_Cum_T` 27 acts, peak 450 u/s; the gallery twin re-derived by `_remap_by_frame` to 3111
ms and 510 u/s, clamped to 369 by `variants.py` for handy1. `animsweep` 93/93 ok, `gallerydiff` 0
rows sharing a script, `speedcheck` no over-limit points on either variant. Both installs deployed.
No mod change — this is gallery data only, so it is still **2.5.9**.


## 98. The debug installs stop being quiet twice over — tooling

§95 forced `WriteUnityLog` and `[Logging.Disk] Enabled` and deliberately stopped, leaving two
questions as preferences rather than work: whether a run's log should survive the next launch, and
whether `Ambient/DiagnosticMode` belongs on in a dev install. Both are now decided the same way
§95 decided its pair — as a property of *being a debug install*, set on the deploy side, so
neither depends on what is committed.

**A run's log now survives.** BepInEx's `AppendLog` defaults to `false`, so every launch truncates
the previous session. That has already cost real evidence once: the 2026-08-22 run was overwritten
by a short launch the same evening, and what §92 read out of it survives only as the figures quoted
in that entry — the hypnosis lines TODO item 12 refers to cannot be re-read. `AppendLog = true`
joins `BEPINEX_FORCED`, one growing file per install.

The alternative was rotating in `start-pnc-linux.sh`, one file per session named by date, which is
tidier and was rejected anyway: it only covers launches that go through the script, and the launch
that destroys the log worth keeping is exactly the casual one that does not. A guard with a hole in
it where the failure lives is not a guard. Growth is the cost, and it is the cheaper one — a log
that is too long is a `grep` away from being the right length, and a log that was truncated is
gone.

**`DiagnosticMode` is on in both installs.** It is what identifies a box-identified diorama whose
audio matches no `Patterns` entry — the scene plays, but `AmbientReleaseGaze.NoteCandidate` declines
a null `AudioSource`, so the look-to-release never arms, and the log says
`box D13 -> ambient_nun_watersports (no ambient pattern matched here)`. That item has been sitting
in TODO §4 waiting for someone to remember to turn a setting on before walking six dioramas, which
is the same shape of note §95 called out as the thing that fails.

The mechanism was already there. `deploy.py` had a single-purpose `force_debug_logging()` pinning
`[EDI] Debug = true`; it is now `force_debug_settings()` over a `MOD_FORCED` list, the mod-config
twin of `BEPINEX_FORCED`:

    MOD_FORCED = [("EDI", "Debug", "true"),
                  ("Ambient", "DiagnosticMode", "true")]

**Production is untouched, and by a different route for each key.** `Debug` is pinned to `false` in
`release.py`'s `SHIPPED` table, because live and default both say `true` and the release still has
to differ. `DiagnosticMode` needs no entry at all: `build_shipped_config` renders from the working
tree, where the value stays at its documented default of `false`. Forcing happens only on the way
into a target, so neither key leaves a diff in `BepInEx/config/com.edi.pnc.cfg`. Verified: the
shipped config renders `Debug = false` and `DiagnosticMode = false`, `release.py --check` reports
the same three deviations it did before, `cfgaudit` 156/156, and both installs read `true` for
both.

The cost is honest and worth stating: `DiagnosticMode` dumps every playing `AudioSource` and
`SpriteRenderer` within `DiagnosticRange` every 2 s, and with `AppendLog` on, `LogOutput.log` now
grows across sessions rather than resetting. The session-opening greps (`ALIAS-GAP`, `EDI-SKIP`,
`failed:`) do not care how much is around them. One line out of `MOD_FORCED` reverts it if a
session ever wants the quiet.

Both TODO items in §4 close with this. No mod change — this is deploy tooling only, so it is still
**2.5.9**.

## 99. The first real run of 2.5.9, and five defects its log named — diagnosis

2.5.8 and 2.5.9 had never been played. This is the session that played them: 40 minutes on Linux,
2026-08-23, the first log to survive its own successor thanks to §98's `AppendLog`. Clean of
`ALIAS-GAP` and `EDI-SKIP`, no new lines in `PncEdi-missing-definitions.log`, and the five
`failed: Connection refused` all predate Edi starting.

**Confirmed working and closed:** the goonshroom cling climb (§83) and the filler at 20 (§91) by
feel; the post-cum grace (§96) with six clean `post-cum grace 2.0s` / `grace over` pairs at floors
18.8 through 93.8; the grapple tier drop (§91), which now logs `[IMP] drop tier=2 count=2` for
both imps and goonshrooms where the 2026-08-22 run had eight escalations and no drop at all; the
serpent seek (§92), seven `[EDI-PHASE] Serpent_Loop aligned to animation` lines; and the family
flap (§92), down to 60 sub-second dispatches across forty minutes from 39 in a single session.
97 of 295 dispatches carried an `@<n>ms` phase carry.

Five things it found. **Four are unfixed and are the open list in `TODO.md`** — they are written
up here because the diagnosis is the expensive half and it is done.

### The pause flag survives a quit to the menu

Reported as "pausing in a grab scene did not pause the script, twice, both soon after being
grabbed". The grab is a coincidence. Both occurrences read:

    [15:12:06.271] [PAUSE] in-game pause menu opened -> Edi/Pause      GamePaused = true
    [15:12:07.263] [SCENE] '' -> 'MainMenu'                            quit to menu FROM that menu
    [15:12:14.141] [SCENE] '' -> 'Floor1'                              a new run
    [15:12:54.181] [GRAB-START] prefab='Gargoyle' key=gargoyle
    [15:12:59.643] [PAUSE] in-game pause menu closed -> Edi/Resume     <- the pause keypress

Quitting to the menu from the pause menu never calls `PauseMenuManager.ResumeGame`, so
`PauseHooks.GamePaused` stays `true` across the scene change and into the next run. The next real
pause hits `PauseGame_Postfix`'s `if (!GamePaused)` idempotence guard and is swallowed; the next
unpause fires `ResumeGame_Postfix` and sends a `Resume` nothing asked for. Hence the lone "closed"
line with no "opened" before it - the tell, and visible three times in this log.

The fix is one line in `Plugin.OnSceneChanged`, which already sees every transition and logs
`[SCENE]`.

### The grapple gate is still imp-only

    [15:09:48.935] [IMP] escalate tier=3 count=3 -> goonshroom_3
    [15:09:49.128] [IMP-GRAPPLE] blocked grab during imp grapple: GoonShroom_Enemy

`ImpGrappleGate.ShouldBlockNonImpSceneFor` asks `GrappleEnemyProtection.IsImpEnemy`. §86
generalised grapple *reinforcement* over the clinging family and left this gate behind, so during
a **goonshroom** grapple the goonshroom's own grab counts as an interloper and is refused - three
times in this run. The gate is right in principle and its other four refusals this session
(`Gargoyle`, `Hood_Enemy` x4, `Zombie_Enemy_ALT`) are correct; it needs to compare against the
running grapple's family rather than against imps.

### The imp's grab resolves no animations, so nothing is dispatched

Reported as "at 100 heat it kept playing imp_3 instead of switching". Not the grapple loop -
`Imp/GrappleLoopDelaySeconds = 0` is deliberate and documented, because vanilla has no generic
grapple loop and `imp_1/2/3` already loop. The failure is at the moment max heat converts the
grapple into a real grab:

    [GRAB-START] prefab='Imp_Enemy ALT 4' key=imp anims=0
    [GRAB-ANIM] controller='Imp_Grab_Screen' clip='Imp_Grab_Loop' hash=-1816323100
    [GRAB-INIT] skipped: no grab animations resolved

Every other enemy in the session resolved 2 or 4; the imp resolves **0**, because imps are
grapple-driven and their scene data sits in `GrappleScreenobject` rather than in the AI's
`grabScreenAnimations`. `DescribeGrabAnimatorReadiness` therefore refuses, `FireCurrentGrabStep`
sends nothing, and the device holds whatever was last dispatched - `imp_3`. Twice this run, at
15:20:00 and 15:31:37.

Everything needed is already present: the animator names its own controller and clip, and
`imp_loop=imp_grab_loop` is in `GalleryTable`. The fix is a fallback from the animator's current
clip when `CurrentAnims` is empty, which generalises to any enemy whose grab data lives outside
that field.

### The hypnosis ladder is crossed faster than a device can render

The tiers and the hysteresis are correct. The band is not:

    [15:32:36.050] tier 1/3   10.2m
    [15:32:36.464] tier 2/3    6.0m     +0.41s
    [15:32:36.622] tier 3/3    4.0m     +0.16s

Tier 3 lands **160 ms** after tier 2. And nothing enforces a dwell, so honest boundary crossings
flap: `2 -> 1 -> 2 -> 1` in 1.6 s at 15:28:06, on real distances of 4.8, 6.8, 6.0, 6.8 m. Each
switch is an HTTP POST and a fresh script upload. §87 built this ladder to switch without a seam;
what it did not anticipate is that the serpent closes 8 m to 2 m in under a second.

Two independent levers - a minimum dwell per tier, which fixes the flap whatever the tier count,
and two tiers instead of three, which fixes the 160 ms gap. The dwell is the one to do first
because it stands alone. This also settles the §87 band question from a new direction: the
argument for re-basing was a stale config comment, and is now that the authored approach is
crossed too fast to register.

### The Handy is on the wrong variant, and that is not the whole story

`Edi/EdiConfig.json` has the Handy on `Variant = detailed`, where **76 of 104 rows exceed the
Handy 1 speed limit** and `Serpent_Loop` peaks at 656 u/s against 364. `handy1` exists to clamp
exactly this. But the device is a Handy 2 with overclock (960 u/s), which `Serpent_Loop` is
comfortably under - so the variant is worth fixing and does not explain the stutter. The dispatch
storm above is the better candidate, and the two share a session.

### Not defects

`Imp/GrappleLoopDelaySeconds = 0` is correct, per above. The hypnosis readings outside the 8 m
band are correct: hypnosis starts inside `hypnosisStartRange` (8 m) but ends only past
`loseTargetRange` (18 m) or after `maxHypnosisDuration` (8 s), read out of `BrawlerEnemyAI` and
recorded in `TODO.md` item 12. The
`[GRAB-HIDE]` census grew to eleven prefabs, all still `vanilla still destroys it`, so §73's
deferred path remains untested. And the Plantasha spin-death (#2), unreproducible since
2026-08-15, did not recur under a deliberate attempt and is retired.

## 100. The rooms the game actually authored — spawn composition, `grappler-bias`

§91 added the goonshroom to `EnemySpawnShufflePool` because a session had found none anywhere.
That was the right fix for the symptom and it hid the cause: **the shuffle should not have been
choosing at all.**

### What vanilla does

There is no biome enemy list, and no global table. `EnemySpawner.GetEnemyPrefab` and
`ArenaEnemySpawner`'s identical twin pick uniformly from **that spawner's own** serialized
`enemyData[]`, then uniformly from the chosen `EnemyData.prefabVariants[]`. The spawn table is
per-spawner scene data, authored per room, and rooms are placed procedurally - so a floor's
character is a shuffle of rooms, not a mix rolled fresh at each spawn point.

`code/spawntables.py` is new and reads it out of the assets. Against 0.3.1, 67 of 70 spawners
carry a table and all but three live in `sharedassets1` (Floor1). They are deliberately uneven:

    GoonShroom, GoonShroom, GoonShroom                          a goonshroom nest
    GoonShroom, Black Serpent, GoonShroom x7                    a bigger one
    Imp   /   Imp, Imp   /   Imp, Imp, Imp, Nun                 imp rooms
    Gargoyle, Gooper, Imp, Black Serpent, Gargoyle x4, Imp x2, Gooper
                                                                a repeat IS the weight

Census across every table: Gargoyle 39, Nun 38, Imp 34, Gooper 28, Zombie Enemy 28, GoonShroom 18,
Black Serpent 11, PlantEnemy 10. **`Blinded Beast` is an `EnemyData` asset that appears in zero
spawner tables** - no normal spawner can produce one, which is why reaching it costs a session and
why a debug spawn key for it is not a convenience but the only route.

One more thing the same read settled, because it contradicts the field name: the spawn *count* is
`int spawnCount = availablePositions.Count` - **one enemy per surviving spawn point**.
`enemiesToSpawn` gates nothing; `ValidateSetup` only clamps it against itself. Mean room is 2.06
spawn points, and 26 of 67 spawners have exactly one.

### What the mod was doing to it

Both `GetEnemyPrefab` prefixes returned `false`, so vanilla's pick never ran. Every spawner in the
game rolled the same seven-key pool, and **every authored composition was discarded** - the nests,
the single-enemy rooms, the repeat-weighting. That is why runs read as uniform, and it is the same
defect that made the goonshroom unspawnable, just less visible: an absolute failure is noticed and
a flattening is not.

### `Gameplay/EnemySpawnMode`

Default `grappler-bias`: keep vanilla's table and only re-weight it. Entries named in
`GrapplerSpawnKeys` (`Imp;GoonShroom`, the clinging family, which is what has cling scripts behind
it) get `GrapplerSpawnWeight`; everything else stays at 1. **A room whose table holds no grappler
returns null and vanilla's own roll runs untouched** - identical by construction rather than by
care, which is the only kind of identical worth claiming.

`pool` selects §91's behaviour and `vanilla` patches nothing. The debug `SpawnShufflePoolKey`
keeps using `EnemySpawnShufflePool` in every mode, so that tool is unaffected.

`GrapplerSpawnWeight` is **1.5**, deliberately gentler than the 2 first written, because it lands
on top of two other multipliers: the lock-scaled spawn count (§101) and grapple reinforcement,
which spawns up to two more grapplers once a grapple starts. It also compounds with vanilla's own
repeat-weighting - a table listing `Imp` twice rolls imp 2.25x as often as a name listed once, not
1.5x - which is in the config comment.

### The tool

`code/spawntables.py` needs `TypeTreeGeneratorAPI` beside UnityPy: MonoBehaviour fields are not in
the shipped type trees, so the trees are generated from `Managed/` at run time. One trap is worth
knowing before touching it - **asking the native generator for a class it cannot find leaves it in
a state where the next call segfaults the interpreter**, exit 139, no Python traceback. So every
tree is generated up front and no class outside `Assembly-CSharp` is ever requested.

## 101. Two numbers nobody had checked — the auto-heal unit, and the spawn ceiling

Both came out of one question: does the extra spawning trade against the HP regen? Neither figure
survived being looked at.

### `HeatLockAutoHealRate` is in hundredths, and the release had the mechanic switched off

`ApplyHeatScaledAutoHeal` multiplies the setting by a hard-coded `0.01`:

    float num4 = Mathf.Pow(1f - num3, 2f) * 0.01f;
    float num5 = Mathf.Max(0f, Plugin.CfgHeatLockAutoHealRate.Value) * num4;

So the setting is **hundredths of HP per second**, while its own description read "Auto-heal HP
per second at 0 heat" - wrong by a factor of 100. Both the `0.01f` and the `1f` default are in
`code/PncEdi-v2.0.8-original.dll`; this is inherited, not introduced here. `PlayerStats.maxHealth`
is 100.

§58 found `120` in the live config, read the description rather than the formula, called it
"120 HP/s auto-heal - a testing tweak, near-invincibility" and marked the setting `DEFAULT` in
`SHIPPED` so releases would carry the coded `1`. Redone against the formula:

| rate | real HP/s at 0 heat | to refill the 100 HP bar |
|---|---|---|
| 1 - what shipped from §58 to 2.5.2 | 0.01 | **2.8 hours** |
| 120 - this install, all along | 1.2 | ~83 s |

`120` is not near-invincibility; that would need about 10000. It is a modest regen that decays
quadratically and is near zero in a hot fight, and it is almost certainly the original author's
tuned value for a setting measured in hundredths. **The revert turned a working mechanic off, and
every release since - 2.5.2 included, the posted archive - has shipped it that way.**

`SHIPPED` now declares `"120"` explicitly rather than `DEFAULT`, so it cannot silently revert
again, and the description is corrected in `Plugin.cs` and the config to say *hundredths* with the
worked numbers. The coded `Bind` default stays at `1f` deliberately: changing a default is how a
setting silently moves in every existing user config on next launch. Shipping the right value in
the config file reaches new installs and upgraders alike, because the release zip carries
`BepInEx/config/com.edi.pnc.cfg` and extracting over an install overwrites it.

The audit could never have caught this. `release.py --check` printed `HeatLockAutoHealRate:
120 -> 1` as a **success** line - the guard's job is to stop a local tweak leaking, and it did that
correctly. It has no opinion on whether the destination is a sensible number. The rule that leaves:
**a guard that proves two values differ says nothing about whether either is right.**

### The spawn ceiling was a product nobody had written down

    SpawnMultiplier = max(1, SpawnCountMultiplier) * (1f + 1.2f * CurrentLockProgress)

Base 2 times a ramp to 2.2 is **4.4x at full lock** - against a mean vanilla room of 2.06 spawn
points, a nine-enemy room where the game authored two. The interesting number was emergent, so
nobody had ever decided it.

Replaced with an interpolation between two stated ends:

    Mathf.Lerp(SpawnCountMultiplier, SpawnCountMultiplierAtFullLock, CurrentLockProgress)

`Gameplay/SpawnCountMultiplierAtFullLock` is new and defaults to **2.5**. Both ends are now
settings, changing the base no longer drags the ceiling with it, and the ceiling is clamped never
to fall below the base - a ceiling under its floor would shrink rooms as a run got harder.

Interpolating on *progress* rather than on the lock count is what makes the per-character
behaviour right, and it was already the case: `CurrentLockProgress` is `locks / GetTotalLocks()`
and the total derives from the character's own max heat. So the ends are fixed and the step size
is not - a 13-lock character ramps in thirteenths, a 5-lock one in fifths, both landing on 2.5x.

| locks | at 0 | midway | full | full, before |
|---|---|---|---|---|
| 5 | 2.00x | 2.20x | **2.50x** | 4.40x |
| 8 | 2.00x | 2.25x | **2.50x** | 4.40x |
| 13 | 2.00x | 2.31x | **2.50x** | 4.40x |

A full-lock room drops from about nine enemies to about five. Low-lock rooms are unchanged.

Left alone and worth knowing: `RelaxSpawnFilters` divides the spawner's `minDistanceFromPlayer` by
the multiplier at `Awake` (vanilla 3 m, now 1.5 m at no locks and 1.2 m at full, floor 0.5 m), so
slightly more of a room's own points survive filtering than vanilla would allow and enemies can
appear closer than the level intended. The multiply is a clean multiple of vanilla; the base it
multiplies is a little wider than vanilla's.

## 102. Three of §99's four defects, and what the log said that §99 did not

§99 diagnosed five defects from the 2026-08-23 run and fixed none of them. This is the first
three, all in the plugin. The fourth (the hypnosis ladder's minimum dwell) is a judgement about
how the ladder should read and wants a play, not an edit, so it stays open.

Two of the three turned out to differ from §99's diagnosis once the log was read again rather
than the summary of it. That is the same lesson as §92 and it keeps being worth the ten minutes:
the diagnosis in a handoff is a claim about the log, and the log is still there.

### `GamePaused` survived a quit to the main menu

Quitting from the pause menu never calls `PauseMenuManager.ResumeGame`, so `PauseHooks.GamePaused`
stayed `true` into the next run. `PauseGame`'s `if (!GamePaused)` guard then swallowed the next
real pause, and the next unpause sent Edi a `Resume` nothing had asked for. The tell in a log is a
`[PAUSE] ... closed` with no `opened` before it.

`PauseHooks.ResetForNewScene()` clears it, called from `Plugin.OnSceneChanged` beside the dozen
other per-scene resets - that method already sees every transition, so there is no new hook and no
new place for the state to leak.

It clears the flag and nothing else. `OnSceneChanged` already ends by either stopping Edi (a menu
scene) or starting the filler, so a `Resume` from here would be a second and contradictory
instruction on the same transition. And the clear is guarded by `if (GamePaused)` so that the
abnormal path logs: an unconditional assignment is a line shorter and silent, and silence is what
made this cost a session in the first place.

### The grapple gate asked the wrong question, but not quite the one §99 named

§99 read `[IMP-GRAPPLE] blocked grab during imp grapple: GoonShroom_Enemy` as the gate refusing a
goonshroom its own grab, and prescribed comparing against the running grapple's family. The first
half is right. The prescription alone would not have fixed it.

The run's twelve blocks are three situations, not two:

| blocked | during | verdict |
|---|---|---|
| `Gargoyle`, `Hood_Enemy NoTape`, `Zombie_Enemy_ALT1` | a real imp grapple | correct - a different enemy interrupting a cling |
| `GoonShroom_Enemy` **joining** an imp grapple | a real imp grapple | also correct: the grapple UI has one animator per count and one cling family behind it, so a mixed grapple is not a thing the game can render |
| `GoonShroom_Enemy`'s **own grab** | a goonshroom grapple, 1 ms before `[GRAPPLE-END]` | the defect |

The third one narrows the cause in a way the summary did not. `GrappleEnemyProtection.IsImpEnemy`
returns **false** for a goonshroom - there is no `[GRAPPLE-ATTACH] GoonShroom` anywhere in forty
minutes, against twelve for imps - so `IsImpGrappleSession`'s per-enemy loop would have returned
false and the gate would never have fired. It fired anyway, which means `grapplingEnemies` was
already empty and the method fell through to its `grapple.GrappleCount > 0` fallback. So the
family comparison §99 prescribed reads that same empty list and returns null: the fix as written
would have changed nothing about the one line that was actually wrong.

`ShouldBlockNonImpSceneFor` is now `ShouldBlockNonGrappleSceneFor` and asks the running grapple for
its family, with two things §99 did not call for:

- **The family is sticky.** `ActiveGrappleFamily()` caches the last readable answer for as long as
  the grapple runs, cleared on `EndGrapple`, `ForceEndGrapple` and scene change. That is what
  covers the teardown window, where the list is empty but the grapple is still running.
- **An unknown family declines to block.** Blocking on a guess is exactly what produced the wrong
  refusal. The cost of erring the other way is one stray scene inside a window that only exists
  while a grapple is already ending.

When the running family is `imp` the gate still consults `IsImpEnemy`, which reads `galleryEnemyID`
and the raw object name as well as the key and so catches imp variants a key lookup alone misses.
It simply cannot stand in for the other families any more.

Two deliberate extras. The `CameraSwapTrigger` prefix now blocks interact scenes during *any*
cling rather than only an imp one - nothing about replacing the on-screen cling was ever
imp-specific. And the log tag is now `[GRAPPLE-GATE]`, naming the family in each line
(`blocked grab by X during a goonshroom grapple`); grep the next run's log for `IMP-GRAPPLE` and
expect nothing.

`GrappleDeathSequence` still calls the imp-only `IsImpGrappleSession`, deliberately: it arms a game
over, and that path has only ever been played against imps. Generalising it is a behaviour change
that wants its own run rather than a free ride on a gate fix. `IsImpGrappleActive` was left unused
by the change and deleted.

### The imp's grab dispatched nothing, and the answer was on the next line

Every imp grab logged `[GRAB-START] prefab='Imp_Enemy ALT 2' key=imp anims=0`, because imp scene
data lives in `GrappleScreenobject` rather than in the AI's `grabScreenAnimations`.
`DescribeGrabAnimatorReadiness` refused on the empty array and the device held `imp_3` through a
scene that had moved on:

    [GRAB-START] prefab='Imp_Enemy ALT 2' key=imp anims=0
    [GRAB-ANIM] controller='Imp_Grab_Screen' clip='Imp_Grab_Loop' hash=-1816323100 t=0.00
    [GRAB-INIT] skipped: no grab animations resolved

The middle line is the fix. `Imp_Grab_Loop` slugs to `imp_grab_loop`, which `slugharness` confirms
is a real in-game row, and `ResolveGrabStepName` already falls back to `ResolveClipName` when the
array cannot name the step. The array being empty was never fatal; it was just never asked past.
So the empty array now yields a refusal only when the animator cannot name a clip either
(`no grab animations resolved, and the animator names no clip`).

Two things that had to move with it, both because reaching the code below the gate used to imply
the array existed:

- `FireCurrentGrabStep`'s secondary loop over `CurrentAnims` was unguarded, so the first anims=0
  grab through the relaxed gate would have thrown a `NullReferenceException` out of a Harmony
  patch and into the game's own call stack.
- The new probe is wrapped in try/catch for the same reason: `GetCurrentAnimatorStateInfo` on an
  animator mid-teardown can throw, and a throw inside a patch is the game's problem, not ours.

`[GRAB-INIT]` appends `(from the animator's clip; no grab animations)` when the fallback fires, so
the two paths are distinguishable in the next log instead of reading identically.

### Found on the way, not fixed

`GrappleEnemyProtection.AttachImp` gates on `IsImpEnemy`, so a goonshroom gets no keep-alive: shake
one off and vanilla destroys it where an imp is stowed and released near the player. §86
generalised the *reinforcement* over the clinging family and left the protection imp-only. The
log's asymmetry is the evidence - twelve `[GRAPPLE-ATTACH]`/`[GRAPPLE-RELEASE]` pairs for imps,
none for goonshrooms.

### Tooling, on the way past

The venv the asset tools need moved from a scratch directory under `/tmp` into the repo at
`.venv/`, with its four packages pinned in a tracked `code/requirements.txt`. The pins are not
ceremony: UnityPy decodes the sprites and pillow decodes their textures, so both decide what pixels
`animsweep`, `gallerydiff` and `refvideo --verify` compare a funscript against, and an unpinned
upgrade could move a measured number with nobody touching a script. `.venv/` needs no `.gitignore`
rule to stay untracked - the file is an allowlist, so a new top-level directory is invisible until
it is opted in. Every `<venv>/bin/python` in a docstring or a doc is now `.venv/bin/python`.

## 103. The device was never a Handy 2 — a naming error, and the two totals it hid

The stutter reported on 2026-08-24 came with a correction: the device is a **Handy 2 Pro**, not a
Handy 2 with overclock, which is how every note in this project had recorded it. The obvious
reading of that — `speedcheck.py` has no profile for the user's hardware, so every "under the cap"
claim in the tree was made against a device nobody owns — turned out to be wrong, and the correction
is worth more than the fix.

**The numbers were the 2 Pro's all along.** `learnings/funscript-authoring.md` already says where
they came from: the device's own slider-overclocking menu, taken deliberately in preference to
review articles that quote 800 mm/s. That menu was on the 2 Pro. So 125 mm, 450 mm/s stock,
1200 mm/s at max overclock (960 u/s) and the 15 mm/s floor are all measurements of the actual
hardware; what was wrong was the key they were filed under. `handy2` and `handy2_oc` are now
`handy2pro` and `handy2pro_oc`, the docstring names the right device, and **no measurement moved**.
Nothing needed re-deriving, which is the opposite of what the TODO item predicted.

This is the same failure mode as §92 and §102 in a different medium: the summary of a fact had
drifted from the fact, and reading the source of the figure rather than the note about it settled
it in one pass. The rule the project already has — *do not re-derive a verified number against a
build it was never measured on* — nearly caused the reverse error here, throwing away good numbers
because their label was wrong.

Also removed: `--variant handy2pro` in the docstring, which named a gallery folder that has never
existed. The gallery has `detailed/` and `handy1/`.

### The two totals nobody was printing

`speedcheck.py` computed a per-row over-ceiling count for **every** device in `DEV` and summarised
exactly one of them — the Handy 1. The `>H2oc` column was on screen for every row and had no bottom
line, so the five rows that exceed the overclock ceiling had never been counted. Two summary lines
now exist:

- **exceed 2 Pro OC — 5 of 104**: `Gravy_Cum`, `imp_3`, `Zombie_Cum`, `imp_3_Gallery`,
  `goonshroom_3_Gallery`. Four are accents and are **meant** to be there: the authoring rule is to
  judge a script by its median, and a deliberate snap the motor renders as "as fast as you can" is
  content, not a defect. `imp_3` is the one the docs already single out — p95 1519 u/s over 37
  segments, sustained rather than accented.
- **under 2 Pro OC min — 5 of 104**: `imp_3_Gallery`, `peek_gravy_bath`, `GoonShroom_Cum_Gallery`,
  `GoonShroom_Cum`, `Wendigo_Start_Gallery`. `DEV_MIN` had been in the file since the ceilings were
  written and was **read by nothing**. Below the floor the motor does not track smoothly, so a
  crawling ramp fails as surely as an impossible one — in the other direction, and in a shape that
  matches the word "stutter" better than a ceiling breach does.

A hold is not a floor violation: `dp == 0` means the device was asked for no motion at all, so only
commanded motion too slow to track is counted.

**None of this is a diagnosis of the stutter**, and it is not claimed as one. No log has been read
for that report yet. What changed is that the speed question can now be asked against the right
device, and two of its three answers are visible instead of implicit. TODO item 5 carries what is
still open.

## 104. The stutter is Edi's seeked loop — one defect, verified against the protocol

The 2026-08-24 report, given properly: *"when rapidly changing between the serpent hypnosis
scripts, the following serpent loop is laggy and stays laggy — skipped strokes — but shows
correctly on the Edi preview device, and after transitioning to cum and back to the loop it plays
normally again."* Every clause is load-bearing, and together they name the bug.

**It is not the variant, not the ladder's dwell (open item 4), and not a script.** "Correct on the
preview, wrong on the hardware" puts the fault downstream of Edi's own timeline — `PreviewDevice`
is a separate simulated device that never touches the Handy path — so no curve-content theory
survives contact with the report, including the ceiling breaches §103 had just surfaced.

### The defect

`Edi.Core/Device/Handy/Devices/HandyV3Device.cs`, in `SelectLoopPointsFromSeek`, reachable **only
when `seek > 0`** on a `Loop=true` row.

To start a loop mid-cycle the method rotates the point list: it begins at the point *before* the
seek and appends the head shifted by `+duration`. What it never appends is the closing point that
re-joins the cycle. An unseeked loop does not need one, because a well-formed looping script
already carries its own closing point at `t == duration` — `serpent_loop` runs 0…1750 with position
0 at both ends. **The rotation drops exactly that structure**, so the buffer ends one inter-point
gap early.

`Serpent_Loop` is 15 points on a flat 125 ms grid over 1750 ms. At `seek=493` the rotation yields
`[375…1750] ++ [0,125,250 shifted +1750]`, a buffer running 375 → 2000: **1625 ms of buffer for a
1750 ms loop, short by exactly one 125 ms gap, 7.1%.**

That matters because of what the device does with `loop`. `HspPlayRequest` carries a bool and no
period, and the Handy's own protocol says what the bool means
(`Edi.Core/Device/Handy/Protocol/constants.proto`):

```
bool loop = 6;  //true if the buffer is looping after the last point
uint32 first_point_time = 8; //time of the first point in the buffer
uint32 last_point_time = 9;  //time of the last point in the buffer
```

The device wraps at the last point back to the first, so the loop period **is** the buffer span.
A seeked entry therefore runs a 1625 ms cycle against a 1750 ms animation, dropping one segment
every wrap — "skipped strokes", literally — and drifting 125 ms per cycle against the screen.

**Nothing corrects it afterwards.** There are exactly two syncs per playback, "initial" and
"follow-up"; a looping playback gets no periodic correction. So it stands until the next `Play` —
the "stays laggy" in the report. And `SelectLoopPointsFromSeek` returns early on `seek <= 0`, so an
unseeked Play is immune: `Serpent_Cum` (seek 0) then `Serpent_Loop` (seek 0) rebuilds a correct
buffer, which is the recovery the report describes.

Upstream has two tests on this path, `LoopSeekStartsWithOneRotatedPlayChunk` and
`LoopSeekStreamsEveryPointThroughEndAndBeforeSeek`. Both assert the *chunking* of the rotated
buffer — its first and last `t`, where the streamed remainder picks up — and neither asserts that
the buffer closes the cycle. The same one-gap shortfall is visible in the test's own fixture
(160 points at 100 ms, seek 12000: buffer 11900 → 27700, 15800 ms for a 15900 ms loop). So this is
uncovered rather than intended.

### Three theories that died, and one claim retracted

Recorded because they are the obvious ones and each cost real time:

- **A per-play upload race.** The `bundle.*.csv` files under the Wine prefix look like a
  whole-gallery upload, so a four-Play burst looks like four uploads colliding. They are dated
  6 Aug and belong to a different device implementation; `HandyV3Device` streams points.
- **An append-only device buffer.** `TailIndex` grows monotonically across the whole 40 minutes,
  which looks like stale points accumulating. `StartPlayback` passes `flush: true` on every play.
- **An operator-precedence bug in the resync — retracted.** `SynchronizePlaybackAfterDelay`
  computes `startTime + elapsed % duration`, which reads like a missing pair of brackets, and the
  run showed 57 of 378 sync pushes sending a time past the row's own duration — `filler_cum_25` at
  `seek=1874` pushed to 3497 against a 2000 ms loop. **Neither is a defect.**
  `ElapsedPlaybackTime` is `wallclock + SeekTime` (`DeviceBase.cs:366`), so `elapsed` is plain
  wallclock and the expression is the right position *in the rotated coordinates the buffer
  actually uses*. A value past `duration` is normal there, not evidence of anything. The census
  proves only that we seek often — 81 of the run's 309 plays.

  What is left of it is small and secondary: the model wraps at `seek + duration` while the buffer
  wraps at `first_point_time + duration`, and those differ by `seek - first_point_time` (118 ms in
  the serpent case, always under one point gap). Worth a sentence in a report, not a headline.

### What is proved, and what is not

The chain is **code plus protocol plus symptom**, not a measurement: `HspState` carries
`first_point_time` and `last_point_time`, but Edi does not log them, so the run's log contains no
direct observation of the device's actual loop period. Every other link is verified — the rotation
arithmetic against the real script, the loop semantics against the vendor's proto, the seek-0
immunity against the reported recovery.

The decisive experiment is behavioural and cheap: **enter a looping row with no seek and see whether
the stutter is gone.** That is the same lever as the mitigation below, so trying it costs nothing
extra.

### What it means for us

**The trigger is ours; the bug is not.** §87 made ladder switches carry the playback phase with
`?seek=` deliberately, on the reasoning that deferring to the loop seam would cost up to a full
cycle of latency. That reasoning still holds — but every mid-flight switch lands on this path.
Rapid switching is *correlated* with the trigger rather than being it: a single slow seeked entry
breaks identically. The filler ladder is hit harder than the hypnosis tiers.

Open item 4 (the ladder has no minimum dwell) is now dual-purpose: fewer switches means fewer
seeked plays. It does not fix this and must not be sold as fixing it.

Nothing is changed on our side yet. TODO item 5 carries the decision.

## 105. The device says it: a seeked loop is 1625 ms of buffer for a 1750 ms loop

§104 named a defect from code and protocol; the no-seek test build in `test/no-seek-into-looping-rows`
did not clear the stutter, and it was demoted to "real but not the cause". **That demotion was
wrong.** `code/handystate.py` asked the device what it was holding, and the answer is the
prediction, on the hardware, to the millisecond.

The run of 2026-08-23 18:09-18:14, main's build, the device polled at 2 Hz:

| our dispatch | device buffer | span vs the true loop |
|---|---|---|
| `Play Serpent_Hypnosis_3@275ms` | `first=250 last=1000`, 5 points | 750 of 1000 - one 250 ms gap short |
| `Play Serpent_Loop@428ms` | `first=375 last=2000`, 15 points | **1625 of 1750** - one 125 ms gap short |
| `Play Serpent_Cum` (no seek) | `first=0 last=3375`, 28 points | correct |
| `Play Serpent_Loop` (no seek) | `first=0 last=1750`, 15 points | correct, and it played fine |

`serpent_loop` is 15 points on a 125 ms grid over 1750 ms. Seek 428 puts `firstAtOrAfterSeek` at
t=500, so `startIndex` is t=375 and the rotated tail is `1750, 1875, 2000`. The device reports
`first_point_time=375`, `last_point_time=2000`. Because `loop` means "the buffer is looping after
the last point" and `HspPlayRequest` carries no period, the device's cycle **is** that 1625 ms
span: one segment dropped per wrap, identically every wrap, for as long as the playback lasts. The
broken buffer sat unchanged for twenty seconds; the unseeked entry after `Serpent_Cum` replaced it
with `0 → 1750` and the complaint stopped.

That also settles the symptom's shape, which is what made the diagnosis hard. **It does not
drift** - the report was insistent on that, and it is the tell. A clock or latency fault drifts;
a short loop repeats the same wrong thing forever. Every theory that predicted drift was dead on
arrival and the reporting detail said so before any measurement did.

### Why the no-seek build did not clear it

Not because the theory was wrong: because **Edi seeks on its own**, and the mod's gate only
covered `SendPlay`. The 17:51 session's Edi log carries `Player event: Resume [Serpent_Loop] at
385` after a pause, and a `Handy playback ... Seek: 386` with it. Pause and resume rebuild a
rotated buffer with no help from us, so the fault returned inside a build that had suppressed
every seek the mod could send. A mod-side mitigation therefore **cannot** close this; only the
upstream fix can.

### The scope is wider than the serpent

The same run shows rotated buffers on the filler ladder - `first=1270 last=3010` and
`first=1580 last=3270`, both 9-point rows whose true duration is 2000 ms - which is the "issues
outside of the serpent playback as well" in the report. Any `Loop=true` row entered with a seek is
affected, and 81 of 309 plays in the earlier run carried one.

### The fix, upstream

`SelectLoopPointsFromSeek` closes the cycle by appending `points[startIndex]` shifted by
`+duration`, so the buffer spans a full period and the device's wrap lands where the script's own
closing point does. Everything needed to report it is here: the two tests on that path
(`LoopSeekStartsWithOneRotatedPlayChunk`, `LoopSeekStreamsEveryPointThroughEndAndBeforeSeek`)
assert the chunking and never the closure, and the test fixture itself carries the shortfall -
160 points at 100 ms with seek 12000 gives a buffer of 11900 → 27700, 15800 ms for a 15900 ms
loop.

`code/handystate.py` is what turned this from argument into measurement, and the reason it was
needed is worth keeping: Edi synchronises a playback twice, both inside its first 1.6 s, and never
looks again. The device had been answering `GET v3/hsp/state` the whole time and nobody was asking.

## 106. The stutter was Edi's, in four places, and is now filed upstream

§104 named a defect from code and protocol and was demoted when a test build did not clear the
fault. §105 proved a second from the device and it did not clear it either. The answer came from
measuring the hardware rather than reading the source, and it is four defects in one method,
`HandyV3Device.SelectLoopPointsFromSeek`, all reachable only when a looping gallery is played with
a seek:

1. **The rotated buffer is never rebased to zero.** The device wraps to 0 rather than to
   `first_point_time`, so the cycle becomes `last_point_time` and its opening stretch holds no
   points at all - the device stops there, once per loop. **This was the jerkiness.**
2. **`SeekTime` stays in the gallery's coordinates** while the buffer is rebased. It feeds
   `ElapsedPlaybackTime`, which feeds the playback sync, so every sync pushes the device a whole
   anchor away - permanently, since a looping playback is synchronised twice inside its first
   1.6 s and never again. **This was the desync, and it was ours: introduced by fixing 1.**
3. The buffer is one inter-point gap short of a period (§104).
4. The script's closing point collides with its shifted opening point (§105).

### What settled it

`code/handystate.py`, polling `GET v3/hsp/state` at 2 Hz. Playback time slipped against wall time
by exactly `first_point_time` on every rotated buffer and not at all on buffers already starting at
zero - five for five, 4 to 47 ms out. After the fix, a seeked entry sits 50 ms from its intended
phase against 39 ms for an unseeked one, and the serpent loop ran 30 samples clean.

**Two source-derived diagnoses were confidently wrong before that.** Both were internally
consistent, both were written up, one was built and shipped as a test binary. The user's own
observation that the fault *did not drift* had already ruled out every timing theory; taking that
literally would have saved a day. The rule is in `learnings/debugging-and-diagnostics.md`: for a
fault on the far side of a device protocol, measure the device.

### Filed upstream

**NoGRo/Edi issue #14, PR #15**, from a fork on the `Anyplace5985` account. Before filing, the
question "is this really ours?" was answered properly: `DeviceBase.Resume()` resumes a looping
gallery at `CurrentTime`, so **pause and resume reaches every one of these with no integration at
all**, and `CompletePlayback` re-seeks every cycle for any looping gallery larger than the device
buffer. `SelectLoopPointsFromSeek` exists in no other device - Buttplug indexes its command list
instead - so there is no cross-device contract we were violating. Our own 154 seeked dispatches in
a session were all inside `[0, duration)`. We exercise the path hard; we do not cause it.

### Still on our side

The release pins Edi v1.0.4 by checksum, so **anything shipped today still carries the bug**. When
upstream releases a build with the fix, `release.py --update-edi` prints the new constants and the
pin moves deliberately. Until then `game-linux/Edi/Edi-fixed.exe` is a local build of the PR branch,
sitting beside the pinned `Edi.exe` rather than over it, and is not shipped.

## 107. Shipping a patched Edi, on purpose and with an expiry date

§106 left players on stock Edi v1.0.4, which stalls and desyncs the device on every pause and
resume. The fix exists, is filed as NoGRo/Edi PR #15, and is in no released build. So the archive
now ships **v1.0.4 plus that PR**, built from the branch, until upstream releases one.

`release.py` grew `EDI_PATCH_PR`, `EDI_PATCH_SHA256` and `EDI_PATCH_SIZE` beside the upstream pin.
The patched build lives in the same cache as the upstream download, under a name that says what it
is (`Edi-v1.0.4-pr15.exe`), and is checksummed exactly like the upstream one - so a release stays
reproducible and a rebuild that is not bit-identical fails loudly instead of shipping quietly.

**It cannot fall back on its own.** A missing patched build is a hard failure that prints the
publish command, not a silent revert to a stock Edi that still has the bug. That is the one
outcome worth engineering against, because it fails invisibly: the archive would look fine and
play badly.

**Reverting is one line — `EDI_PATCH_PR = None`** — and that is the intent as soon as a released
Edi carries the fix. `--update-edi` then re-pins upstream as before.

### What players are told

The archive README says the bundled Edi is patched, what the fix is for in one sentence, and links
the PR and the issue. Nothing is hidden behind a version string: `@EDITAG@` renders as
`v1.0.4 (patched, PR #15)`.

**Worth knowing, and deliberately not resolved here: Edi has no licence file.** Not a permissive
one, not a restrictive one - none, so no redistribution right is granted at all. This project
already shipped the unmodified `Edi.exe` on the same footing; shipping a modified build goes a step
further, since it puts a binary carrying someone else's name into players' hands with changes they
did not make. The mitigations are transparency and brevity: the change is a public PR, the README
names it, and the arrangement is designed to be deleted. If the author would rather it were not
shipped at all, that is a request to honour immediately.

## 108. Two defaults and a pin: the zero-lock spawn floor, and what the dev installs were running

Three small things, each of which had been wrong for a while without anything saying so.

**The spawn multiplier at zero locks was 2, not 1.** §101 turned `SpawnCountMultiplier` from a flat
multiplier into the *zero-lock end* of a ramp and left its value at 2, the number it had carried
when it meant something else. So an unlocked room spawned double before the run had started, and
the 2.5x ceiling sat on top of a floor nobody meant to raise. The default is now **1**, and the
description says what the setting is rather than what it used to be. Reported from play as "spawn
count multiplier seems to be 2 at 0 locks, should be 1", and it took reading `Plugin.cs:685` rather
than any investigation - the bug was the number, in the open.

`RelaxSpawnFilters` divides `minDistanceFromPlayer` by the same figure, so this also restores
vanilla spawn distance in an unlocked room. That is a second behaviour change riding on one
default, and it is the wanted one: at 1 the mod stops touching a room the player has not made
harder yet.

**Nothing logged the ramp.** Below 1x `ExpandSpawnPositions` returns without touching anything, so
"the floor is vanilla again" and "the patch never ran" looked identical in a log. `[SPAWN] wave
x1.00 at lock progress 0.00: 5 -> 5` now names the multiplier, the progress and both ends of the
point list, once per wave. The first run after the change read `x1.00` at no locks and `x2.50` at
full lock, which is the whole setting verified in two greps.

**The two dev installs were testing a stock Edi.** `deploy.py` fetched the Edi payload through
`release.py`'s `fetch_edi()`, which returns the *patched* build when `EDI_PATCH_PR` is set (§107) -
but its freshness check compared the file on disk against `EDI_SIZE` / `EDI_SHA256`, the **upstream**
pin. A stock `Edi.exe` matched, deploy declared it current, and neither install ever received the
patch. The hand-placed `game-linux/Edi/Edi-fixed.exe` was the workaround for a gap nobody had
named.

`release.py` grew `edi_pin()`, returning size, checksum and a label for whichever Edi actually
ships, and `deploy.py` pins against that instead. Both installs now run the patched build as their
own `Edi/Edi.exe`, so what is launched and what ships are one binary. `STALE_EDI` deletes
`Edi-fixed.exe` from any target that still has it - a 221 MB stale copy of a build nobody launches
is exactly what a later session runs by mistake. The revert in §107 loses a step: delete the cache
file, set `EDI_PATCH_PR = None`, and the next deploy puts stock Edi back by itself.

## 109. The goonshroom's cum never played, and one space in a parameter name is why

Reported after the 2026-08-23 run and left deliberately uninvestigated (TODO, "Also open,
smaller"): reach max heat with goonshrooms attached, the scene plays, heat resets to the floor -
and never builds again. The first two suspects recorded there, a goonshroom path missing its
imp-only counterpart and `PostCumGraceSeconds` leaving `heatIncreaseBlocked` set, were both wrong.

**`GoonShroom_GrabScreen` names its animator parameter `Max Heat`. Every other grab screen in the
game names it `MaxHeat`.** `Assembly-CSharp` contains the literal `MaxHeat` exactly once - the last
line of `GrabScreen.TriggerMaxHeatAnimation` - and `Max Heat` not at all. `Animator.SetBool` on a
parameter that does not exist is a silent no-op; Unity does not warn in a build.

The consequence is not cosmetic, because vanilla ends a cum on an **animation event carried by the
cum clip**:

    TriggerMaxHeatAnimation:      maxHeatAnimationPlaying = heatIncreaseBlocked = isCoolingDown = true
                                  grabScreenAnimator.SetBool("MaxHeat", true)     <- no-op here
    (cum clip plays, its event) -> OnMaxHeatAnimationComplete: clears all three

No transition, no clip, no event. `heatIncreaseBlocked` stays true for the rest of the grab, and
`TriggerMaxHeatAnimation` early-returns on `maxHeatAnimationPlaying`, so no later cum can fire
either. The grab is wedged until `EndGrab`. It also means `GoonShroom_Cum` had **never played in
gameplay** - the row existed, was scripted, and only ever ran in the gallery.

**The log had already answered this before the source did**, in a line §102 added for exactly this
class of failure:

    goonshroom: releasing the cum (animator in 'GoonShroom_GrabscreenStart')
    imp:        releasing the cum (animator in 'Imp_Grab_Cum')  -> OnMaxHeatAnimationComplete fired

`GrabScreenHeatParam` mirrors the bool onto whatever name the controller actually uses, so vanilla's
own state machine runs and vanilla's own event fires. Nothing reimplements the cum; the patch only
delivers a message the game is already trying to send. It is written as general name normalisation
rather than a goonshroom special case, because a no-op `SetBool` is invisible and the next stray
space would cost the same session to find again. The mod's own two `SetBool("MaxHeat", ...)` sites
mirror through the same helper, and the postfix that clears the alias is pinned with
`HarmonyPriority(800)` so it cannot race `FullLockHoldsCum`'s re-assert on the same method.

Confirmed in play: `GrabscreenCum` reached, `OnMaxHeatAnimationComplete fired`, grace, heat
building again, and `[EDI] Play GoonShroom_Cum` in the dispatch census for the first time.

**The rule this earns**: a symptom that looks like game state stuck is worth one look at the
*asset* before any look at the code path. Two sessions' worth of suspects were all code.

## 110. What the Blinded Beast key found: two spawn-resolver defects, and a correction to §100

TODO item 6 asked for a Blinded Beast hint and key. The key itself was one config entry and one
binding. Getting it to spawn anything took two fixes, and finding out why corrected a claim this
project had already written down as airtight.

**It spawned a glory hole.** Six times, logged as success:
`[SPAWN] blinded_beast: spawned interactive 'GloryHoleCamera'`. `FindBestInteractiveTemplate` added
its `+5` / `+3` ranking bonuses to `ScoreInteractiveTemplate`'s **zero** - "this does not match the
hint at all" - and the final `num > 0` test then accepted it. Any hint matching nothing resolved to
an arbitrary `CameraSwapTrigger`. Pre-existing and inherited; a new hint that matched nothing was
simply the first thing to walk into it. Bonuses now apply only to a positive score.

**The prefab was unreachable by every route the resolver had.** `Blinded Beast` (the name carries a
space) is in no spawner's flat `enemyData[]`, has no live instance to find, and its AI component is
the **base `EnemyAI`** rather than one of the five subclasses `CollectLiveEnemyPrefabs` searches by
name. A base-class pass was added, and did not help either - because
`Resources.FindObjectsOfTypeAll` is *everything currently in memory*, not everything in the build,
and nothing on an ordinary floor had ever loaded the asset. `EnsureResourcesEnemyDataLoaded` now
does one `Resources.LoadAll<EnemyData>("")` - nine assets, once - before the scan, and the beast's
own `EnemyData` (`prefabVariants = ["Blinded Beast"]`) resolves through the route that was already
written for it.

**§100 is wrong where it is quotable.** It says Blinded Beast appears in zero vanilla spawner
tables, "so no normal spawner can ever produce one". The first half is true; the conclusion is not.
The Resources container holds `arena spawn groups/floor 2 spawngroups/BlindedBeastMiniBoss`, and
that asset references the beast's `EnemyData`. A Floor 2 arena group can spawn one.
`code/spawntables.py` reads each spawner's flat table and never looked at the group assets, so the
census it printed was complete for what it read and misleading about the game. *(Fixed in §114: it
reads the groups now, and the beast is the game's only group-only enemy.)*

Three things then got their first observation in play, all previously untestable because the enemy
could not be produced on demand:

- **Both stages resolve.** `blinded_beast_loop` and `blinded_beast_loop_t`, dispatching
  `BlindedBeast_Start`/`_Cum` and the `_T` pair. `GrabVariantSuffixes` against
  `BlindedBeastTransformedGrabScreen` works, which had been reasoned about but never seen.
- **The miniboss cost works** (§91): `scene +grab Blinded Beast (miniboss 2/2) -> 2/8`, four grabs
  to full lock.
- Its own grab screen names `MaxHeat` correctly, so §109's goonshroom really is the only one.

## 111. The debug keys, cut down to the number row

Eleven enemies, twelve keys, three of which did not spawn enemies and several of which answered
questions that are closed. Cut and re-laid-out, by decision, after a run showed which were
which.

**Removed: `SpawnBaphometKey`, `SpawnGravyKey`, `SpawnGloryHoleTrapKey`.** All three aimed at
`CameraSwapTrigger` scene objects rather than enemies. Baphomet had probably never worked: its
scoring path explicitly rejects the `TrapCameraSwapTrigger` it would otherwise have matched, so
before §110's fix it can only have been the zero-score bug handing it something. With the three
bindings gone the interactive-spawn path had no legitimate caller, so it went too -
`TrySpawnInteractiveAtPlayer`, `TryTeleportToInteractive`, `FindBestInteractiveTemplate`,
`ScoreInteractiveTemplate`, `ResetInteractiveTrigger`, `MatchesBaphHint`, `GetAnimatorClipKey`,
`GetAnimatorClipKeyContains`, `GetGalleryEntryId`, and the `InteractiveOnly` / `InteractiveFirst`
binding fields. `LogSpawnFailure` no longer prints a `CameraSwapTrigger` census that can no longer
explain anything.

**Worth knowing before it is missed: Gravy's shopkeeper is a real `ProjectileEnemyAI` enemy.** The
key was `InteractiveFirst`, so it tried the peep camera first and the enemy second; removing it
removed the only on-demand way to get that enemy. Deliberate, and one binding to restore if it is
wanted.

**Removed: `SpinAiDumpKey` (F9) and all of `SpinAiDiag.cs`.** Built for bug #14, Plantasha going
inert after a scene - fixed in §78, played clean on 2026-08-23, and the related #2 retired. Every
patch in it was checked for behaviour first: pure logging, no `SetValue`. It was also the loudest
thing in the log by a wide margin, **860 `SPIN-AI` lines** in a forty-minute run, more than every
other tag combined.

**Removed: `DumpTriggersKey` (F5)**, whose stated purpose was finding a second Baphomet hole, and
whose `InteractDiag.DumpAllTriggers` went with it. **Removed: `DumpNearbyKey` (F4)** - superseded
rather than obsolete, since it was the one-shot form of `AmbientProximity.DiagnosticDump` and
`DiagnosticMode`, forced into both dev installs by every deploy since §98, runs that same dump
every two seconds. The automatic caller was confirmed still wired before the manual one went.
**Removed: `NextAmbientKey` / `PrevAmbientKey` (F2/F3)** and `FreeCam.TeleportToAmbient` with them.
The freecam itself (F1) stays.

**The mimic is the chest mimic, and the old config said the opposite.** `MimicEnemy` carries
`chestSprite`, an outline that fades in inside `interactionRange`, and a grab that springs on
Interact - it *is* the interactable chest. Its two prefabs, `Mimic` and `Weapons Mimic`, are the
common-chest and weapon-chest disguises. The "wall mimic" label came from `MimicWallFuck` /
`MImicWallFuckD8`, which are the **D8 diorama** - a sprite, an animator and an audio source, with no
`MimicEnemy` on them and no AI. A scene, not an enemy. Both the code comment and the config
description now say what the class is.

**The dragon and the wendigo share one key**, cycling like any other prefab variant, because they
are one mechanic: both are refused by the spawn shuffle, and both take
`EndGrabDelaySecondsChaserBoss` and a full lock-out instead of ordinary grab handling.

The result is ten enemies on the ten digits, reading in a deliberate order - ordinary walkers, then
the clinging family, then the heavies, then the mimic last because it is a trap rather than a
walker:

    1 Zombie   2 Plantasha   3 Gargoyle   4 Gooper   5 Nun
    6 Imp      7 GoonShroom  8 Blinded Beast   9 Chaser boss (dragon/wendigo)   0 Mimic

    .  random from the shuffle pool        Q / Keypad+  escape grab / end grab
    F1 freecam                             Keypad x / - add / remove heat
    Ctrl+1 / Ctrl+2  filler on / off

`B`, `G`, `M` and every function key but F1 are free. Nothing behavioural was lost: roughly 500
lines of dead diagnostic code and eight keys went, and no fix went with them.

## 112. The hypnosis ladder: two tiers, a minimum dwell, and only while the camera is pulled

The last of §99's four defects, plus one the same run's report named without naming it as a defect.
Mod **2.5.10**.

**Three tiers were one too many.** The band is the prefab's own 8 m down to 2 m, and a serpent
closing it at walking pace gives three tiers about a second each; the 2026-08-23 log has tier 3
landing 160 ms after tier 2. A step that short does not register as a step, so the ladder was
spending its resolution on detail the device could not deliver. `SerpentHypnosisGalleries` now defaults to
`Serpent_Hypnosis_1;Serpent_Hypnosis_3` - far and close, the two ends of the existing amplitude
range, so the contrast per step doubles. **Nothing was regenerated and nothing was deleted.**
`Serpent_Hypnosis_2` is still generated by `code/ladders.py`, still a row in `Definitions.csv`, and
still on the shared grid; the tier count is whatever that config setting names, so going back to
three is an edit to one line and not a rebuild. `ladders.py --check` still reports three rows,
which is correct - it checks the ladder is coherent, not which of it is in use.

The boundary followed for free: `Boundaries` splits the band evenly when
`SerpentHypnosisTierFractions` is empty, so two tiers break at 0.5 of the band, 5 m on the shipped
serpent, with no fraction to configure.

**A minimum dwell, which is not the same thing as the hysteresis already there.** Worth being
precise about, because the two look interchangeable and are not. Hysteresis is in *metres* (as a
fraction of the band): it asks whether a boundary crossing is real, and refuses one that is only a
player shuffling on the line. It cannot help when the crossing is real and simply arrives faster
than the device can express it - which is the other half of what the run showed, honest crossings alternating
`2 -> 1 -> 2 -> 1` inside 1.6 s as the serpent advanced and the player backed off. The dwell is in
*seconds*: once a tier is entered it holds for `SerpentHypnosisMinDwell` (1.5 s) however far the
serpent has moved in the meantime. The approach is slow enough that the ladder still lands where
the distance says it should; it has only spent long enough getting there for the step to register.

It is measured on `Time.unscaledTime`, not `Time.time`. A dwell in game seconds would stop
expiring the moment the pause menu freezes the timescale, which is the same trap the pause handling
hit in §102.

**And the script now stops when the camera is released.** Reported as part of the run and easy to
read as a tuning note rather than a defect: the device kept playing while the player was turned
around, when nothing was being done to them. Vanilla is unambiguous about the difference and keeps
the answer in one private bool. `HandleHypnotisingState` sets
`hypnosisInView = IsPlayerDead || IsInPlayerView()` every tick, and `LateUpdate` pulls the camera
only when it is true - it also gates the advance on it,
`followerEntity.simulateMovement = flag && hypnosisInView`. So a serpent hypnotising a player who
has turned their back is still *hypnotising*, is not *pulling*, and is not even *advancing*.
`SerpentHypnosis.InPlayerView` reads that field by reflection and the ladder returns null when it is
false, which drops the filler back in.

Reading vanilla's field rather than recomputing visibility is the point: the device is gated on
exactly the same answer the camera is, one frame fresh, with no second view test that can disagree
with the first. It takes the same posture as `InHypnosisLoop` on a rename upstream - a missing field
returns true, widening the window rather than silently killing the ladder.

**Not done, and named here so it is not rediscovered:** `code/patchaudit.py` does not see these
reflections at all. It scans `AccessTools.*` and `Traverse`, and `SerpentHypnosis` reaches the game
through bare `typeof(BrawlerEnemyAI).GetField(...)`, so `currentHypnotist` has never been audited
either and `hypnosisInView` now joins it. Two members, both with fallbacks, but the audit's whole
claim is that it covers every reflected member and here it does not.

**Judged by measurement, not by feel.** The second half of the item was left as a judgement to be
made with the device, and was decided ahead of one. What the run's numbers
already showed - a 160 ms tier and a flap - is enough to rule out three tiers; whether two *read*
is what the next run answers.

## 113. Funscripts are not audio: the hearing metaphor out of the whole tree

A terminology correction, and worth a section because it had spread far enough through the tree
that the next pass would have copied it.

A funscript is device motion. It is **played**, or **examined for feel**; there is nothing in one
to hear. The project had nonetheless been writing "the listening pass", "heard as good", "chosen by
ear", "a listen is the only instrument that reads it" since §34, and the metaphor was self-
sustaining - every new entry copied the vocabulary of the last one, including §112 earlier the same
day.

The replacement lexicon, applied across `CHANGELOG.md`, `TODO.md`, `learnings/`, `code/README.md`,
`code/TIMING-AUDIT.md` and the docstrings in `proxies.py`, `ladders.py`, `scenes031.py`,
`grabs031.py`, `rederive.py`, `authored.py` and `impgrab.py`:

| was | is |
|---|---|
| the listening pass | the feel pass |
| a listen | a play |
| heard | played, or felt |
| by ear | by feel |
| (in)audible, of device motion | (im)perceptible |

**What was deliberately left alone: everything about actual sound.** The ambient system really does
key on audio - `AmbientProximity` reads each diorama's `AudioSource.maxDistance`, its log line says
`hear '<pattern>'`, `HearingRangeMultiplier` scales exactly that, and a diorama audible through a
wall is a real thing the §63 presence gate exists to stop driving the device. Those, and "where Edi
is listening" for a socket, are literal and stayed.

Three shipped funscripts carry the phrase in their metadata comment (`baphomet_start`,
`baphomet_cum`, `gravy_loop2`, all written from a cue in §40), so those were rewritten too - not for
the reader, but because `code/authored.py` emits that string and a regeneration would otherwise come
back dirty. Actions compared equal before and after; only the comment moved.

## 114. Five small open items closed at once — mod 2.5.11

None of these needed a run to decide, and all of them had been sitting in `TODO.md` as "known, not
fixed". They are unrelated to each other; what they have in common is that each was a place where
something claimed more coverage than it had — a keep-alive that covered one family and a game
version ago, a death sequence that covered one family, an audit that covered two of three
reflection routes, a spawn census that covered one of two spawn routes, and a display gate that
covered the config setting but not the scene.

### The grapple keep-alive is gone, because the game grew its own

`GrappleEnemyProtection` kept a shaken-off grappler alive instead of letting vanilla destroy it,
stowed it while the grapple ran and put it back near the player afterwards. Every gate into it
asked `IsImpEnemy`, which is a question about *one* family, and game 0.3.1 added a second
grappler — so the log showed a plain asymmetry: twelve `[GRAPPLE-ATTACH]`/`[GRAPPLE-RELEASE]`
pairs in the 2026-08-23 run, every one an imp, none a goonshroom, in a run full of goonshroom
grapples.

The first answer was to generalise it. The right question was the one asked of any workaround:
*does the game still do the thing this works around?*

    // game 0.2.1, GrappleScreenobject.RemoveOneGrappler
    grapplingEnemies.RemoveAt(index);
    if (gameObject != null) Object.Destroy(gameObject);

    // game 0.3.1, same method
    grapplingEnemies.RemoveAt(index);
    ReleaseGrappler(enemy, shakeSign);

0.3.1's `ReleaseGrappler` puts the enemy at the player's position plus the stored offset and a
clearance push, then calls `ChargingEnemyAI.ThrowAfterGrapple`: `SetActive(true)`, every child
collider and renderer re-enabled, charge flags cleared, `currentState = AIState.Idle`, and a
rigidbody throw. That is the mod's entire release path and a physics throw on top of it, for every
clinging family — `StartGrapple` reads `grappleAnimatorController` off `ChargingEnemyAI`, so every
grappler is one and every grappler gets it.

So the mechanic was not missing for goonshrooms; it was **overriding vanilla for imps**, and had
been since the port. The mod stowed the enemy (`SetActive(false)`) in a `RemoveOneGrappler` prefix,
vanilla's release then ran against a deactivated object, and the mod's postfix teleported it beside
the player — replacing a throw the game shipped with a teleport nobody has ever compared it
against, because the interception hid it.

**Deleted rather than defaulted off**, which trades against the standing rule that every
behaviour change ships with a config for the old behaviour (`learnings/working-practice.md`, now
annotated). The test is whose behaviour the flag would choose between: two of ours is a setting,
ours against the game's own current one is a decision. An off-by-default
`KeepImpsAfterGrappleShake` would have preserved a dead workaround as a supported option. `KeepImpsAfterGrappleShake` is gone, and with it the attach
list, the stow/release cycle, the collider and rigidbody state dictionaries, the
`GetSpawnPositionNearPlayer` teleport, and five of the seven `GrappleHooks` patches
(`PerformGrabAttack`, both halves of `RemoveOneGrappler`, `EndGrapple`'s prefix, and the
`DestroyRepresentativeAfterGrab` bypass — that last one was not even gated on the setting, so
"off" would not have been off). `GrappleEnemyProtection` is now `GrappleEnemies` and holds four
things: `ResolveGrappleFamily`, `IsImpEnemy`, `IsClingingNow` and `StowSpawnedGrappler`.

Two of those replace state the mod used to keep:

- **`IsClingingNow`** answers the question all four keep-alive callers actually had — the autofix,
  the waker, the hider and the grab protection each mean *leave a clinging enemy alone*, because
  vanilla deactivates one and they would otherwise "rescue" it. It now reads the game's own
  `grapplingEnemies` list instead of a parallel list of ours, which is one list rather than two
  that can disagree. `ClingingTier` does the same for the cling scene's `prefix + count`;
  `Plugin` already fell back to `GrappleCount`, so the dispatch is unchanged.
- **`StowSpawnedGrappler`** is the one thing the mod still has to do to a clinging enemy, and only
  ever to its own spawn: vanilla deactivates the world model in `PerformGrabAttack`, and a
  reinforcement enemy spawned straight into a grapple never charged, so nothing deactivated it and
  it stands in the level while its overlay clings. It records nothing for a restore — whichever
  way the grapple ends, vanilla owns the other side.

**Where vanilla still destroys, and the mod now lets it:** `EndGrapple` clears whatever is still
clinging when the grapple ends any other way, the trio-grab overflow destroys the
non-representatives, and `DestroyRepresentativeAfterGrab` destroys the representative once its grab
scene ends. That last one is the "minor difference" this trade accepts, and it is the game's own
ending for its own scene.

**This is a feel change and it needs the run:** vanilla's throw has never been played here. A
shaken-off imp now flies rather than reappearing beside you, and there will be no
`[GRAPPLE-ATTACH]` / `[GRAPPLE-RELEASE]` lines at all.

### The grapple death sequence was imp-only, and that was a hole rather than a policy

The same session first recorded "stays imp-only" as a deliberate decision, on the grounds that it
arms a game over and had only been played against imps. That reasoning inverts once you ask *why
the sequence exists*.

It exists because the clinging enemies block the death. A grapple owns the screen and no grab can
start while one runs, so at 0 HP with something attached there is nothing to play the death as —
which is why the sequence holds the player dead instead of reviving them to 1 HP, locks the
struggle, calls in the rest of the pile and forces vanilla's trio overflow to escalate into a grab
scene that can be the death. **That argument is about grapplers, not about imps.** With
goonshrooms attached the sequence declined and the old revive-to-1-HP path took over — which is
being invulnerable while grappled, the exact behaviour it was written to replace. The gap was
worse than the widening.

Vanilla is family-neutral here and always was, and this was read rather than assumed:
`TriggerTrioGrabOverflow` takes `trioGrabAnimatorController`, both camera offsets and
`grabScreenAnimations` off whichever clinger it picks, and a UnityPy pass over every
`ChargingEnemyAI` in the build says the goonshroom prefab carries
`trioGrabAnimatorController = GoonShroom_GrabScreen` exactly as the five imp variants carry
`Imp_Grab_Screen`.

So `TryBegin` now asks `ImpGrappleGate.ActiveGrappleFamily()` for any resolvable family instead of
`IsImpGrappleSession` — which is deleted, since nothing else called it. An unreadable family still
declines: this is not a sequence to begin on a guess. `RequiredImps = 3` became `MaxGrapplers`,
read off the serialized `maxGrappleCount` (`StartGrapple` refuses past it, so a hardcoded 3 would
stall the sequence forever on a prefab tuned to 2), and `PrepareSpawnedImp` became
`PrepareSpawnedGrappler`. The reinforcement plan for the family provides the pacing, and a family
with no plan is the one way this can now stall — which is the right way, because `Tick`'s
bail-outs force the overflow and then force-end the grapple, and the game over is presented either
way.

**One dependency worth naming:** the sequence forces heat to max to trigger the overflow, so the
goonshroom's grab screen is entered at max heat — and that controller is the one whose parameter
is `Max Heat` rather than `MaxHeat`. §109's `GrabScreenHeatParam` is what makes its cum clip fire.
Without that fix this death would reach the scene and the scene would sit on its loop.

### `patchaudit.py` could not see a third of the mod's reflection

It scanned `AccessTools.*` and `Traverse` only. Bare `typeof(T).GetField(...)` is the same failure
mode — a cached `null` and a feature that quietly stops — and there were **ten** of those across
four files that had never been audited at all: `CameraSwapHooks` (4), `GrabHooks` (2),
`SerpentHypnosis` (3, including §112's `hypnosisInView`) and one on `UnityInput`, which is not a
game type and is skipped like any other.

They are checked as hard targets. Three of them fall back to a wider gate rather than throwing
when the member is gone, and that is the argument *for* failing the audit rather than against it:
the fallback is exactly what makes the loss invisible in play. `obj.GetType().GetField(...)` is
deliberately not matched — the type is a runtime value, so there is nothing to check it against.
Validated the way this file demands: run against 0.2.1 first, where the only two failures are the
known 0.3.1-only `GalleryTabController` members, and none of the ten new targets adds a false one.

### `spawntables.py` read half the spawn system

An `ArenaEnemySpawner` with any valid `spawnGroups[]` does not roll its flat `enemyData[]` table at
all: `SpawnEnemiesCoroutine` picks one `ArenaSpawnGroup` by weight and `SpawnGroupCoroutine`
spawns exactly that group's entries, one per named `ArenaSpawnPoint`. The flat table is only the
fallback for an arena with no group — and **all four arenas in 0.3.1 have groups**, so the census
was reading the fallback path for every one of them.

The script now reads the group assets, prints each one with its entries, prints each arena's
groups with their weights and whether they are enabled, and counts a second census over the group
route. Two lines fall out of it directly:

    === reachable by one route only ===
      group only: Blinded Beast
      table only: Nun

which is the correction §100 needed. "The Blinded Beast appears in zero vanilla spawner tables" was
right; "so no normal spawner can ever produce one" was not — `LargeArena Floor 2` runs
`BlindedBeastMiniBoss`, a one-entry encounter, and a second group on that arena (`Gooper&Serpent`)
is present but disabled. It is the only enemy in the game reachable by the group route alone,
which is worth knowing precisely because the old census would have said the same thing about any
future one.

One trap inside the groups themselves: `Plant Duo` pins two prefabs (`Plantasha_Enemy` and
`Plantasha_Enemy ALT1`) and leaves the entry's `EnemyData` null. Keyed by prefab name those invent
two species that appear in no table and so read as group-only. The census resolves a pinned prefab
back to whichever `EnemyData` lists it as a variant, and prints the pin beside the enemy rather
than instead of it.

### The horny lock readout in the main menu

`HeatLockSystem.UpdateDisplay` gated on `Enabled` — the config setting — and nothing else, and
`ResetForScene` calls it on **every** scene change. So arriving at the main menu rebuilt the canvas
there, and "Horny X/Y" with the diorama gauge under it sat over the menu.

`TODO.md` listed two candidate tests and asked for one to be chosen from a real run's `[SCENE]`
lines. The lines say the scenes are `MainMenu`, `Floor1` and an empty name for the boot scene —
and both candidates are lookups that a new level or a renamed menu falls off silently: a scene-name
list, or a `MainMenuManager` in the scene. The test used instead is the player. Every level has a
`PlayerStats`; no menu has one; so `InGameplayScene()` asks for it, and the answer stays right for
a scene nobody has seen yet. The lookup is the same `FindAnyObjectByType<PlayerStats>` that `Tick`
already runs every frame while `_player` is null, so it costs nothing new. `SetAmbientGauge` takes
the same gate — it calls `EnsureDisplay`, so without it a gaze in progress across a scene change
would rebuild the canvas the menu had just lost.

**It is a display gate and nothing else.** The locks keep their values across the hide; nothing on
this path touches them.

### Version

Bumped to **2.5.11** rather than folded into 2.5.10. 2.5.10 exists for §112's hypnosis changes and
has not been played; letting two independent change sets share one version number would make the
next run's report ambiguous about what it was actually testing. That run now covers both.

`animsweep` 93/93, `cfgaudit` clean, `patchaudit` clean on 0.3.1 with the ten new targets included,
both installs deployed.

The keep-alive was written against 0.2.1 and 0.3.1 had replaced the behaviour it worked around;
the death sequence was excluded from the goonshroom on the grounds that it had only ever been played
against imps. The two rules that came out of this session are in
`learnings/porting-a-new-game-version.md` (a workaround outliving its cause) and
`learnings/grab-and-ai-mechanics.md` ("only ever played against X" as a reason to test).

## 115. The source cleanup, part one — the tooling and Plugin.cs

**No behaviour changed anywhere.** Every audit was captured before the pass and diffed after:
`patchaudit`, `cfgaudit`, `speedcheck`, `spawntables`, `animsweep`, `gallerydiff`,
`ladders --check`, `release --check`, `deploy --check` all produce byte-identical output, the
0.2.1 sweep still reads 63/63, `refvideo --verify` still decodes all 93, and the DLL rebuilds
clean with the same 9 pre-existing warnings. This is the "code cleanup and a better layout" item
from TODO §3, taken as far as it goes without a decision from the user, and it does not touch the
question that needs one (whether to un-ILSpy the rest of the tree — see below).

### `PNC_GAME_DIR` meant two different things

The real defect the tooling cleanup turned up. `animcheck.game_data_dir()` read it as a game
*install* and globbed `*_Data` beneath it, resolved against the repo. `spawntables.py` read it as
the `_Data` folder itself, resolved against the **working directory**, defaulting to
`game-linux/PNC 0.3.1_Data`. PROJECT.md documents the first. Both spellings are written down in
this repo, so both had to keep working.

`code/pncpaths.py` is now the only place either question is answered. It holds `ROOT`, `GALLERY`,
`DEFINITIONS`, `DETAILED`, `ASSET_FILES`, `game_dir()`, `game_data_dir()` and
`definitions_rows()`. `game_data_dir()` accepts an install or a `_Data` folder — one `Managed/`
test separates them — and a relative `PNC_GAME_DIR` is resolved against the repo rather than the
working directory, so it means the same thing from anywhere. `animcheck` keeps `ROOT`, `FILES`
and `game_data_dir()` as re-exports, because `refvideo` and the sweeps reach the assets through
it already.

What that replaced: nine copies of
`ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, eight hand-built paths to
`Definitions.csv` (three of which opened it with their own `utf-8-sig` spelling), and two
readers of `PNC_GAME_DIR`.

**And ten dead `sys.path` lines.** Every tool opened with
`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`, which does nothing — Python
already puts the running script's own directory at `sys.path[0]`. The one line that was *not* a
no-op was `animsweep.py`'s `sys.path.insert(0, os.path.join(os.getcwd(), "code"))`, and it is
precisely why that tool only ran from the repo root. Removing all ten and adding none is what
makes every tool run from any directory; that was the "ties it to being run from the repo root"
complaint in TODO §3, and it wanted deleting rather than packaging.

**Deliberately not done: making `code/` a package.** It would have changed every documented
invocation in PROJECT.md, `code/README.md`, the learnings files and the CHANGELOG from
`.venv/bin/python code/animsweep.py` to `-m`, for no gain the shared module does not already
give. `release.py`, `deploy.py` and `patchaudit.py` keep their own pathlib `ROOT` — they are the
shipping path and were not worth touching for symmetry.

### Plugin.cs was 1846 lines holding three jobs

`Plugin` is now a `partial class` across three files. Nothing else in the tree changed: every
`Plugin.CfgX` and `Plugin.SendPlay` in the other 63 files resolves exactly as before, and
`cfgaudit.py` greps the whole directory so it still sees all 150 binds.

| file | what |
|---|---|
| `Plugin.cs` | 1164 lines: the runtime — `Awake`, `Update`, `SendPlay`, the filler ladder, the pause markers |
| `PluginConfig.cs` | the 150 `ConfigEntry` fields and `BindConfig()` |
| `PluginPatches.cs` | `ApplyPatches()` — the Harmony registration list |

`Awake` went from 398 lines to 13 and now reads as the startup order it is. The 150
`((BaseUnityPlugin)this).Config.Bind<T>` casts became `Config.Bind<T>` on the way past — the same
decompiler artefact as the already-listed `((BaseUnityPlugin)this).Logger` -> `base.Logger`, and
it is on the re-apply list in `code/README.md` with the others.

### The silent-registration trap is now a check

Giving the registration list its own file was worth doing for one reason beyond legibility.
Patches are registered per class rather than by an assembly-wide `PatchAll()`, so a new patch
class does nothing until it is named there — and the failure is completely silent. §109's fix was
written correctly, built, deployed, and had no effect for a whole run because of exactly that.

`patchaudit.py` now checks it, on every invocation, exiting 1 on a gap: every class in the tree
carrying a `[HarmonyPatch]` member must be named in `ApplyPatches`, and every registration must
have a patch class behind it. It reads 32 and 32. Verified by deleting the `GrabScreenHeatParam`
registration — the very patch §109 lost — and watching it report 31 against 32 and exit 1.

The four patches that may legitimately fail on a build that moved their target now go through one
`TryPatch` helper rather than four hand-decompiled `try`/`catch` blocks with
`BepInExWarningLogInterpolatedStringHandler` scaffolding inside them; about sixty lines of noise
went with them, and the warning text is unchanged. **`TryPatch` is not for quietening a patch
that ought to bind** — a patch that silently declines is the failure mode this project keeps
paying for, which is what the new audit is about.

### Still open, and still needing a decision

The rest of TODO §3's cleanup item is untouched on purpose: the decompiler idiom through the
other 63 files (`text3`, `num2`, `(Object)(object)x != (Object)null`), which trades against
`code/README.md`'s standing "match the decompiler idiom" rule and its re-apply list, and what
happens to `PncEdi-source-stale-2026-05-30/` and `PncEdi-v2.0.8-original.dll`. Cleaning as each
file is touched keeps the audits meaningful; one sweeping pass is what nothing can check.

## 116. The decompiler idiom, removed — and the rule that protected it, retired

**Decided by the user, and it is what unblocked this:** there will be no future re-decompile of
this mod. The "match the decompiler idiom" rule in `code/README.md` and its re-apply list existed
only to keep a re-decompile a diff rather than a merge, so both are gone. §115 had left this open
as the one part of the cleanup needing a decision.

**No behaviour changed.** The whole pass is proved by an IL diff, described below.

### What came out

| | |
|---|---|
| `//IL_0033: Unknown result type (might be due to invalid IL or missing references)` | 371 |
| `(Object)(object)x == (Object)null` -> `x == null` | 619 |
| `((Object)x).name` / `((Component)x).transform` / `((Behaviour)x).enabled` / `((MonoBehaviour)x)` | 322 |
| `BepInEx*LogInterpolatedStringHandler` scaffolding -> `Plugin.Log?.LogWarning($"...")` | 12 blocks, ~130 lines |
| a blank line between every field declaration | 381 |
| `val` / `val2` / `component3` / `instance2` renamed after their declared type | 258 |
| `text` / `num` / `array` renamed after their initialiser | 51 |

The log blocks are the clearest gain. Each was eleven lines of
`new BepInExWarningLogInterpolatedStringHandler(17, 1, out flag)` and casted `AppendLiteral` /
`AppendFormatted` calls to say `Plugin.Log?.LogWarning($"Die patch error: {ex}")`, and eleven of
the twelve compile back to *exactly* the same handler calls — that scaffolding is simply what the
compiler emits for `$"..."` against a type with a handler overload.

The config parse that appears in eight files went from `array` / `text` / `num` / `text2` /
`text3` to `entries` / `entry` / `eq` / `key` / `target`, which is the difference between reading
it and decoding it.

### Three casts were load-bearing

They are the only three of 941 that did not compile after removal, and they are not arbitrary:

- **A cast whose operand is itself `(object)` is a generic type parameter being boxed.**
  `((Behaviour)(object)val).enabled` and `((Component)(object)val).gameObject` in
  `EnemyReactivationHelper.WakeDisabledAiType<T>` are a `T : MonoBehaviour`; the box is how a
  type parameter reaches a base class at all.
- **`((Component)ai).gameObject` in `EnemyGrabGate`** is a real downcast: `ai` is declared
  `object` there.

The generic case carries a silent hazard, now in `learnings/unity-runtime.md`: `x == null` on a
type parameter does not resolve to `Object.op_Equality`. Nothing in the tree ended up in that state,
and the check below is what says so rather than an argument.

### The proof: a normalised IL diff

Reading 941 rewrites is not a check. Decompiling is:

    ~/.dotnet/tools/ilspycmd BepInEx/plugins/PncEdi.dll > before.cs      # before touching anything
    # ...edit, rebuild...
    ~/.dotnet/tools/ilspycmd BepInEx/plugins/PncEdi.dll > after.cs
    # both through the same filter - drop `//IL_` lines, collapse `(Object)(object)` to
    # `(Object)` - then diff

Both sides go through the same filter because removing a redundant cast removes a real
`castclass` instruction, so ILSpy legitimately reprints `(Object)(object)root` as `(Object)root`.
That is a spelling, not a behaviour. Anything that is *not* a spelling survives the filter.

**The whole pass moved that diff by 58 lines**, and every one is accounted for: `bool flag =
false` printed as `default(bool)` where the `out` variable moved, one parenthesisation of
`val?.enemyPrefab`, and one deliberate change in `GalleryHooks.LogGalleryWarning` where
`AppendLiteral(message)` became `AppendFormatted<string>(message)` — identical output, and
unavoidable, because `AppendLiteral` cannot take a variable in real C#.

The opcode histogram agrees: 619 `castclass` gone, every branch total preserved
(`blt` 177 -> 177, `br` 444 -> 444, `brfalse` 1378 -> 1378, `brtrue` 1013 -> 1013, only the
long/short encoding shifting as methods shrank), and **no opcode appearing or disappearing** — in
particular no `ceq`, which is exactly what the generic-`T` hazard above would have produced.

Every audit is clean afterwards: `patchaudit` (32/32 registered), `cfgaudit` (150 entries in
their bound sections), `speedcheck`, `spawntables`, `animsweep`, `gallerydiff`, `slugharness`,
`ladders --check`, `release --check`, `deploy --check`.

### Still open

**About 1300 locals are still ILSpy's** — *closed in §123* — almost all `text`, `num`, `flag` and `array`, more than
half of them in `Plugin.cs`, `HeatLockSystem.cs`, `AmbientProximity.cs`, `EnemySpawnShuffle.cs`
and `DebugEnemySpawn.cs`. `string`, `int` and `bool` carry nothing to name a variable from, so
each one is a judgement about what the expression means — a hand pass, not a transform. Renaming
changes no IL whatever, so the diff above stays the check for it.

`code/PncEdi-source-stale-2026-05-30/` and `code/PncEdi-v2.0.8-original.dll` are untouched and
still want a decision before strangers read the tree.

## 117. One parser for the `key=value` config format

Asked directly whether §115 and §116 had applied any design pattern. They had not — everything
structural in them was extract-method, extract-module and separate-concerns-by-file, which is the
honest answer and also the right work. So the tree was read again looking specifically for a
place where a *pattern* earns itself, and there was exactly one worth doing.

### The duplication

Nine settings use the `key=value;key=value` format — `EnemyRemap`, `GalleryAliases`,
`InGameAliases`, `DioramaAmbientMap`, `PeekGalleryMap`, `PeekClipMap`, `ClassHeatMultipliers`,
`HeatPotionLockRemoval`, `GrabVariantSuffixes` — and **six classes each carried their own copy of
the same fifteen-line parse loop** — seven, once §118's test-writing turned up another in
`PeekGalleryMap.ParseInto`.

The copies did not differ in how they parsed. They differed in what they did with the pair
afterwards: `NameRemap` lowercases both sides into an ordered list, `ClassHeatMultipliers` parses
a float and clamps it, `PeekGalleryMap` slugs the key, `HeatPotionLocks` keeps the longest key
that is a substring of the item name, the other two fill a dictionary. **The format was
duplicated; the intent was not** — which is what makes this an extraction rather than a
framework.

`ConfigMap.Pairs(raw, separators)` is an iterator yielding well-formed `(key, target)` pairs, and
each caller does its own thing with them in three to five lines. Casing, slugging and number
parsing are deliberately *not* in it: folding those in would be the abstraction the extraction is
meant to avoid. `ConfigMap.SortLongestKeyFirst` came out with it, because "longest matching key
wins" is a promise several of the config descriptions make to the user and it had three
implementations.

**155 lines out, 64 in, plus a 72-line file with the format written down once** (and ~20 more out
with the seventh site). A format with
seven implementations is a format that can drift in six of them, and this project has already
paid for one config-matching bug (§92, `Goon Shroom` with a space).

### Proving it, when the IL diff cannot

§116's check does not apply here: this changes the compiled code on purpose. Two things stand in
for it.

**`slugharness` output, byte-identical over all 170 rows.** It compiles the mod's real
`NameRemap.cs` and `GalleryTable.cs`, so every animator state in the game still resolves to the
same gallery row through the same route. It needed `ConfigMap.cs` added to its `Compile` list,
which is the one piece of real coupling the extraction created.

**A differential test of the parser against the six loops it replaced.** Every `=`-bearing value
out of the live `com.edi.pnc.cfg` plus twenty-four edge cases the shipped config does not happen
to contain — `a=b=c`, `a==b`, `=x`, `x=`, `;;;`, a duplicate key, a key differing only in case,
CRLF separators, padded whitespace, `"k=v with spaces and = inside"` — run through all six
shapes, old and new, and compared: **37 inputs, 0 differences.**

The equivalence argument behind that, worth keeping because it is what made the extraction safe
to attempt: every copy already dropped an entry with no `=`, or with an empty side, and every
caller that did *not* explicitly require a non-empty target was parsing it as a number, where an
empty string fails `TryParse` anyway. The one caller that slugged an **untrimmed** key,
`PeekGalleryMap`, is unaffected because `NameRemap.Slug` collapses non-alphanumerics and trims
`_`, so `Slug(x) == Slug(x.Trim())`.

### Patterns considered and not applied

- **A base class or interface over the map classes.** They share a format, not a lifecycle:
  `GalleryAliases` has two tables and a validation pass, `PeekGalleryMap` caches on the raw
  string and has three resolve routes, `HeatPotionLocks` never builds a table at all. A common
  base would have to be `protected abstract void Accept(key, target)` and would buy nothing the
  iterator does not.
- **A registry/strategy object for the Harmony patches.** §115's `ApplyPatches` already reads as
  a list, and the gated block plus the interleaved `EnemyAiAudit.Run()` / `Hotkeys.AuditBindings()`
  calls mean a pure data table would need escape hatches immediately. `patchaudit.py` checking
  the list is worth more than making it a table.
- **`GrappleReinforcement`'s per-family `Plan` struct** is already a strategy table and needed
  nothing, and `DebugEnemySpawn.SpawnBinding[]` is already a data-driven registry. Both were left
  alone.

The general rule this session kept landing on: in a mod this size the win is almost always
*deleting a duplicate*, not *introducing an indirection*.

## 118. A test suite, and the boundary of what one can cover here

    dotnet test code/tests/PncEdi.Tests.csproj        # 103 tests

The project had no test infrastructure at all. It had *audits* — `patchaudit`, `cfgaudit`,
`slugharness`, `animsweep`, `speedcheck` — which answer "does the mod still bind to the game" and
"does every scene resolve", and they have earned their keep. What none of them answers is whether
a given function still does what it did, which is the question a refactor asks and the question
§117 had to answer with a throwaway script.

### The boundary, decided first

Most of this mod is Harmony patches over live game objects: a patch fires when the player is
grabbed, reads a `GrabScreen` off the scene, pushes a row name at Edi. None of that exists
without a running game and mocking it would test the mocks. **What is pure logic is steps 2-4 of
the pipeline in PROJECT.md** — the part between the game handing over a name and the HTTP call:

| file | what is pinned down |
|---|---|
| `ConfigMap.cs` | the `key=value;key=value` format all nine map settings share |
| `NameRemap.cs` | name → enemy key, and (key, animator state) → slug |
| `GalleryRegistry.cs` | `Definitions.csv` loading, `IsKnown`, `LoopMs`, `?seek=` stripping |
| `GalleryAliases.cs` + `GalleryTable.cs` | slug → row, in-game vs shared, gap reporting |
| `DioramaGalleryMap.cs` | `D13` → `ambient_*` and the three routes to it |
| `PeekGalleryMap.cs` | four exact keys in order, then the clip-name fallback |
| `ClassHeatMultipliers.cs` | the one setting parsed as a number |

**That is where the bugs have actually been.** §92 (the gallery menu passing `Goon Shroom` with a
space, four days of five dead rows), §80 (0.3.1 rewriting every peek display name into a joke,
which took every peek scene off the device), §96 (an unknown row and a missing file logging the
same thing), and the substring-guessing fallback that hid gaps for months
(`code/NAMING-AUDIT.md`). Each is a named test now.

### How it is wired

It compiles the mod's **real** source files, never copies — the rule `slugharness` has followed
since §71, for the same reason: a test against a copy tests the copy. `Stubs.cs` stands in for
`Plugin`, which is a `BaseUnityPlugin` and cannot exist outside a game; the naming layer only
asks it for a config value and somewhere to log. Two real assemblies are referenced, the same two
roots the mod builds against — BepInEx from the pinned in-repo pack, and
`UnityEngine.CoreModule` + `Assembly-CSharp` from the game through `game-windows`.

`Edi/Gallery/Definitions.csv` is copied into the test output, because
`GalleryRegistry.GetDefinitionPaths`'s third candidate is `AppContext.BaseDirectory/Edi/Gallery/`
— which is how the tests get the real 104-row table with no game running.

`xunit.v3` 3.2.2 and `Microsoft.NET.Test.Sdk` 18.8.1, pinned to what is already in the local
NuGet cache because the Edi clone uses them, so a restore needs no network.

**Everything under test is `static`**, since the mod is a plugin and its tables are process-wide.
The suite therefore runs single-threaded and every configuration-touching test starts by clearing
the whole layer. A flaky suite is worse than none.

The two rules the suite is written to — expectations as ground truth rather than snapshots, and
reading the live `com.edi.pnc.cfg` and `Definitions.csv` rather than a fixture beside them — are in
`code/tests/README.md`.

### It was mutation-tested, and that found a hole

103 passing tests prove nothing until one fails:

| mutation | caught by |
|---|---|
| `SortLongestKeyFirst` reversed | 3 tests |
| split on the **last** `=` rather than the first | 3 tests, incl. the live-config target check |
| `StripCloneSuffix` removed from `ResolveEnemyKey` | **nothing** |

The third was a real gap: the clone strip was tested on the function directly but never through
the fallback path a runtime-spawned *unknown* enemy takes, where it decides whether the slug ends
up as `brand_new_enemy` or `brand_new_enemy_clone`. One line closed it, and the mutation is
caught now. Mutate something before trusting a new test here.

### And it found a seventh parser

Reading `PeekGalleryMap` closely enough to test it turned up a copy of the `key=value` loop that
§117 had missed — `ParseInto`, beside the `ResolveByClip` copy that was converted. It is on
`ConfigMap.Pairs` now, so §117's count is **seven** call sites, not six.

## 119. What the 2.5.11 run found, and the one bug that could end a run without ending it

The first play of 2.5.11 (2026-08-24, Linux, ~10 minutes on the sewers floor). Three of the seven
things it was sent to check came back clean; the other four are below, and two of them were not on
the list at all. **The mod is 2.5.12 for this**, because three of the fixes change what a player
sees.

The whole session was read out of `LogOutput.log` before any source was opened, and the three
standing greps were clean — no `ALIAS-GAP`, no `EDI-SKIP`, and the only `failed:` lines are the
three EDI calls at launch before Edi was up. Everything below came out of the log's own tags.

### The soft lock: a game over the player could see, and could not answer

Reported as "the Blinded Beast was able to go for repeat grabs after game over, interrupting the
ability to return to the main menu". The log has the whole cycle, four times over, ~6 s apart:

    [14:37:53.668] [GAMEOVER] presentation released by ShowGameOverPanel
    [14:37:54.365] [GRAB-START] prefab='Blinded Beast' key=blinded_beast anims=2
    [14:37:54.365] [PLAYER-REVIVE] ok - keeping the scene gallery, no filler
    [14:37:54.365] [GAMEOVER] cancel from guard (waitingForInput=False hasShownGameOver=True)
    [14:37:54.366] [HEAT-LOCK] scene entry survival set HP to 1 from grab
    [14:37:54.366] [HEAT-LOCK] scene penalty -37 HP from grab

`hasShownGameOver=True` with `waitingForInput=False` is the whole diagnosis. Those two bools are
different states and the mod was treating them as one:

- **`isWaitingForInput`** is the *press any key* prompt. Tearing that down with a grab is the mod's
  own death rule (§8, §13) working as designed: at 0 HP the player stays grabbable, and the grab
  that lands becomes the death scene. `ReleaseGameOverPresentation`'s comment says so explicitly.
- **`hasShownGameOver`** is set by `ShowGameOverPanel` and means the *panel* is up — the one with
  Restart and Main Menu on it. Vanilla latches it and never re-enters: `OnPlayerDied`,
  `ShowGameOverPanel` and `Update` all guard on it, because from here the run is over and the
  player is choosing between two buttons.

`ShowGameOverPanel_Postfix` released the mod's commit latch at exactly that moment — "nothing is
left to protect" — so every cancel path went live again against a panel that was on screen.
`EnsureSceneEntrySurvival` then did what it is written to do: revived to 1 HP, cleared
`PlayerDead`, and called `CancelGameOverPresentation`, which does
`gameObject.SetActive(false)` on `gameOverPanel`. It deleted the panel the buttons were on. The
scene penalty killed the player again, a fresh game over committed, the panel came back, the beast
grabbed again 0.7 s later, and around it went. The run was not frozen — the player could walk — it
simply had no exit any more.

**Why this prefab and not the others.** The Blinded Beast is the first enemy in the project's
history to set `hideInsteadOfDestroyOnGrab`, which §73 has been waiting on since 2026-08-18. The
log carries the first `vanilla hides it (hideInsteadOfDestroyOnGrab) - mod keep-alive stands down`
line ever printed. Vanilla's own hide-and-restore keeps the beast alive and re-grabbable in place,
with none of the mod's `EndGrabEnemyCooldownSeconds` between grabs, so it is the one enemy that
could land a grab every six seconds onto a presented game over. The dragon and the wendigo did the
same thing later in the run — the log has `cancel from guard ignored - committed game over is
presenting` all through their grabs — which is what "the dragon had some issues with the grab" was.
One defect, two families.

**The fix is one predicate in one place.** `DragonGrabGameOverGuard.GameOverPanelIsUp()` reads
`hasShownGameOver` off the live `GameOverScreen`, and:

- `GrabEndHelper.CancelGameOverPresentation` refuses while it is true. Every route into the cancel
  funnels through that method — the survival revive, the `GameOverScreen.Update` postfix, both
  teardown paths — so one refusal covers all of them.
- `HeatLockSystem.EnsureSceneEntrySurvival` declines outright, rather than leaving the player alive
  at 1 HP behind a panel they had already answered.

`GameOverScreen` is a per-scene component, so a reload starts with the field false again and there
is nothing to leak into the next run. The prompt is untouched: `isWaitingForInput` is deliberately
NOT part of the predicate, because the grab-becomes-the-death-scene handoff is the thing that
tears the prompt down and it is meant to.

### Grab scenes with no audio: not load, one family

Reported as "sometimes grab scenes don't have audio? maybe this is due to too much stuff going on".
It is not load. The log throws `Can not play a disabled audio source` seven times, every one of
them within a millisecond of a scene hide, and the split by prefab is total:

| grabs | warned |
|---|---|
| Blinded Beast ×5 | 5 |
| Dragon ×2, Wendigo ×2 | 1 each |
| GoonShroom ×3, Hood_Enemy, Imp, Weapons Mimic | 0 |

Exactly the families whose enemy GameObject is switched off for the duration of its own scene —
the Blinded Beast by vanilla, the chaser bosses by the mod's path. A `Play()` on a source under a
deactivated object warns and is silent.

**Not fixed this session, deliberately.** What the C# cannot say is *which* source the game meant
to play: the clip is assigned at runtime, so it is null in the assets and null in any census taken
too late. Two instruments went in instead, and one run with them names it:

- **`[GRAB-AUDIO]`** at grab start, before anything hides — every AudioSource on the grabbing
  enemy with its object, clip, `activeInHierarchy`, `enabled` and `isPlaying`.
- **`[SCENE-HIDE]`** now counts the AudioSources on the objects it hid. A hide carrying none rules
  the mod's hider out and leaves whoever else switched the object off.

### The serpent had no key, and the row was re-cut to give it one

The one system in the mod that could not be tested on demand. `SerpentHypnosis` is all of what
2.5.10 is for, and the Black Serpent — in eleven vanilla spawner tables and the `Gooper&Serpent`
arena group — could be *met* but never asked for. `SpawnSerpentNameHint = black
serpent|blackserpent|serpent` resolves the same way the other ten do (spawner tables, then live
enemies, then `Resources`), and `BrawlerEnemyAI` is already in `EnemyAiTypes.All` so
`CollectByEnemyAi` reaches it.

It first went on Minus, as an eleventh key for an eleventh enemy. **That was the wrong shape and it
was re-cut**, because §111's row is ordered by *what the enemy is* and appending to the end throws
that away:

    1 Zombie   2 Plantasha   3 Gargoyle   4 Gooper   5 Nun     ordinary
    6 Black Serpent                                            its own thing - the hypnotist
    7 Imp      8 GoonShroom                                    the clinging family
    9 Blinded Beast   0 Chaser boss (dragon/wendigo)           miniboss, then boss
    M Mimic                                                    furniture, not a walker

The serpent lands between the ordinary enemies and the grapplers, which is where it belongs: it is
neither, and it is the only enemy that attacks by taking the camera. Everything from the imp
upwards shifts one right, and **the mimic comes off the digit row entirely onto `M`** — it does not
walk up to you, it waits, and it was only ever on `0` because `0` was the tenth key rather than
because it was the tenth enemy. The row now holds exactly the ten walking enemies in encounter
order, which is a thing you can read rather than a list you have to remember.

`M` is free: `KeyCode.M` appears nowhere in `Assembly-CSharp.dll`. Minus is free again too — worth
knowing, because `Hotkeys.IsUnreachableKeyCode` exists on account of it. `SpawnGloryHoleTrapKey`
once shipped as KeyCode 223, in the hole between Delete (127) and Keypad0 (256) where
`Input.GetKeyDown` can never produce a value, and the physical key that reports as `Minus` (45) is
the one that used to carry it.

### Two DebugEnemySpawn bugs the run exposed for free

**The variant number in every `[SPAWN]` line was unreliable.** `chaser_boss variant 1/2 'Wendigo'`
followed by `chaser_boss variant 1/2 'Dragon'` — different prefabs, same index. `IndexOfVariant`
reconstructed the index by undoing the advance, `(stored - 1) % Count`, which is not an inverse
once the counter wraps: after the last variant the stored value is 0, indistinguishable from "no
entry yet", and its `value <= 0` guard then reported the last variant as the first. Every
two-variant key was stuck on `1/2` for both halves of its cycle — the mimic, the gooper, the nun
and the chaser boss all show it. `PickNextVariant` hands the index back through an `out` now, so
nothing is reconstructed. **The spawn was always correct; only the number beside it lied.**

**The mimic spawned mostly inside the floor.** `TryGetSpawnTransform` raycasts the floor and puts
the prefab's *origin* there, which is only the same thing as standing on it when the pivot is at
the feet. The two mimics are wall furniture, authored around a pivot in the middle of the chest.
`SeatOnGround` measures the instance's own renderer bounds after Instantiate and lifts it so the
art sits on the floor — lift only, never lower, with a 5 cm floor, so a prefab that deliberately
floats and one whose pivot is already right are both left alone. Measuring beats a per-prefab
offset table: it is right for anything added later.

### `code/dioramaaudit.py` — the ambient patterns, answered without a run

The open diorama item (TODO §4) was "a box-identified diorama whose audio matches no `Patterns`
entry", and it was going to cost a walk past six dioramas. It is decidable from the assets, because
both halves of `MatchPattern` are static data — but not in the same place, which is why this needed
writing rather than grepping:

**An AudioSource's `m_audioClip` is null in almost every shipped scene.** The clip is assigned at
runtime by script, so following the sources gets you nothing; the clip *names* have to be read from
the AudioClip assets themselves. The tool checks each alias against both name sets — the 239 clip
names in the build and the 98 objects carrying a looping AudioSource — because `MatchPattern`
accepts either, and applies its actual rule: longest alias wins, exact scores +1000, so entry order
does not matter and `imp gangbang 2` correctly beats `imp gangbang` on the same clip.

**All sixteen patterns resolve.** Fifteen to a clip name; `dragon squat ride` only to an object
name, `Dragon Squat ride`, which is the fragile one — nothing else in the build backs it up, so a
rename upstream takes D10 dark and this tool is where that would show. The run agrees from the
other direction: `AMBIENT-SCAN` matched five of the six 0.3.1 dioramas live. **D15
`serpent wall blowjob` was never walked past**, and is the only one still unconfirmed in play —
though its clip exists and its alias matches it exactly.

The limit is worth stating because it is the tool's whole boundary: this proves an alias *can*
match something in the build, not that the particular source at a particular diorama is the one it
matches. Only a run answers that, and `AMBIENT-SCAN` is where.

### Why the ambient audio detection still existed, and what it does now

Asked directly, once `dioramaaudit.py` had shown all sixteen patterns resolving: **why do we still
need the audio detection at all?** The box has carried the answer since §65 — a
`GalleryUnlockTrigger` holds the game's own galleryID, `DioramaAmbientMap` turns it into a script,
and where the two disagree the mod already logs `trusting the box`.

Reading it rather than assuming: **two things came out of the pattern match, and only one of them
still had to.**

- **Which diorama this is.** Superseded. Every 0.3.1 diorama has a box, the box outranks the audio,
  and the pattern is the half that can be wrong.
- **What to measure a look against.** Not superseded, and this is what was actually holding the
  pattern list up. `AmbientReleaseGaze` needs a *Transform*: an angle to face (`IsFacing`), an
  `isPlaying` liveness test, and the position that keys which *instance* of a repeated diorama has
  been spent (`IsReleaseSourceUsed`). A box is a volume — several are 5 m across and D10 is 15 m
  deep — so its centre is a poor stand-in for where the art is.

And the reason a missing entry cost anything at all is one line in `Rescan`: it keeps a source only
`if (patternMatch.Pattern != null)`, so an unclaimed diorama contributed **no source**, and
`NoteCandidate` declines a null one. Playback worked; the one-time release could never arm.

**`AnchorInBox` closes the class rather than the instance.** `Rescan` now also keeps the looping
sources no pattern claimed, and when the box has identified a diorama but nothing was matched, the
release anchors on the nearest playing loop *inside that box*. `Patterns` is left doing only the
job that is genuinely still its own — identifying a diorama the game does **not** register with a
box — and a missing entry now costs a log line:

    box D13 -> ambient_nun_watersports: anchoring the release on 'audio bj' clip='nun watersports'
      inside the box, since no Patterns entry claimed it

It reads the pre-scanned list rather than searching the scene, because this runs per frame and
avoiding `FindObjectsByType` there is why `Rescan` exists. Peek holes are excluded on the way in,
the same test the matched list uses — they are left to the interact path.

**`dioramaaudit.py` keeps its point, with a smaller one.** A dead alias is still worth catching,
and `dragon squat ride` matching only an object name is still the fragile case. What it no longer
guards is a *silent* loss.

### And four HarmonyX warnings that are not a defect

    Could not find method for type ProximityDragonEnemyAI and name StopSpin

Four of these per chaser-boss spawn, on both dragon AI classes: `StopSpin`, `StopCharge`,
`StopShooting`, `StopSpinLoopSound`. `EnemyReactivationHelper.ClearStaleCoroutineHandles` drives
them through `InvokeIfExists`, which is built for exactly this — they are `SpinningEnemyAI` and
`ChargingEnemyAI` methods and `DragonEnemyAI` genuinely has none of them (`ilspycmd -t DragonEnemyAI`
lists `StopPathfinding`, `StopAttack`, `StopGrab`, `StopIdleMovingSound` and nothing else). The
warning is HarmonyX's `AccessTools` being loud about a lookup the mod is allowed to miss. Left
alone; `patchaudit.py` is right not to flag it, because an `InvokeIfExists` miss is the documented
behaviour and not a silent loss.

## 120. What the 2.5.12 run found: the guard that was one stage too late

The first play of 2.5.12 (2026-08-24, Linux, sewers again — beast, serpent, chaser bosses, mimic,
goonshrooms and zombies). `ALIAS-GAP`, `EDI-SKIP` and `failed:` all zero. **The mod is 2.5.13 for
this.** The run also produced the first rotated log: §119's launcher change had landed, so the
2.5.11 session survived as `BepInEx/logs/LogOutput-20260824-132009Z.log` while this one was written
into a file of its own — which is the first time two runs could be read side by side without
counting lines.

### The game over was still unanswerable, and §119 guarded the wrong stage

§119 made `CancelGameOverPresentation` refuse while `hasShownGameOver` is set. Every cancel in this
run reads `hasShownGameOver=False`. The flag only latches in `ShowGameOverPanel`, which vanilla
runs when the player presses a key at the prompt — so the guard protects the panel, and the player
never got to the panel.

    15:31:24.137 [GAMEOVER] presentation committed from scene entry survival from grab
    15:31:25.152 [GRAB-START] prefab='Blinded Beast'
    15:31:25.153 [GAMEOVER] presentation released by Revive
    15:31:25.153 [GAMEOVER] cancel from guard (waitingForInput=True hasShownGameOver=False)
    15:31:25.153 [HEAT-LOCK] scene entry survival set HP to 1 from grab

One second, four times over. Vanilla's `ShowGameOverSequence` waits `delayBeforePrompt` (1 s) before
raising the prompt at all, so the prompt existed for a few frames before the next grab took it.

**The latch was defeated by the thing it was there to stop.** `_gameOverPresentationCommitted`
makes every cancel path inert — but `PlayerStats.Revive` releases it first, and the grab is what
calls Revive. That release is not a leak; it is the death rule (§8, §13, §77): at 0 HP the player
stays grabbable and the grab that lands becomes the death scene. What was missing is that the rule
only makes sense *before* the death has been shown. Once the prompt is up, the death has been
presented and the answer is the player's.

So `ReleaseGameOverPresentation` takes `respectPrompt`, the revive path passes it, and a release
that arrives while `isWaitingForInput` is set is refused. `GameOverIsThePlayersToAnswer()` — the
panel, or a prompt the mod itself committed — replaces the panel-only test in both places that had
it, so `EnsureSceneEntrySurvival` also stands down rather than reviving the player behind a prompt
they were about to answer.

The proof that the rest of the chain is sound is in the same log: the goonshroom death at 15:38:28
ran all the way to `[GAMEOVER] presentation released by ShowGameOverPanel` and a clean exit to the
main menu. Nothing re-grabbed during it.

### Why it re-grabbed in a second, and the instrument that will say next time

The beast is the one prefab that sets `hideInsteadOfDestroyOnGrab`, so `[GRAB-HIDE]` reads *mod
keep-alive stands down* and vanilla's `EndGrabHidden` owns the restore — it sets `lastGrabTime =
now` and nothing else. The mod's `EndGrabEnemyCooldownSeconds` (10) is applied on top by
`StabilizeAfterGrabEnd`, from an enemy captured in an `EndGrab` prefix as
`IsGrabbed ? GrabbingEnemy : null`.

On the hiding path that capture can be null: the enemy has moved to `GrabScreen.hiddenEnemyToRestore`
by then, and `EndGrab` nulls `grabbingEnemy` itself. A null enemy means the cooldown is applied to
nothing, silently. The prefix now falls back to `hiddenEnemyToRestore`, and `ApplyGrabEndCooldown`
logs what it wrote:

    [GRAB-COOLDOWN] Blinded Beast: next grab no earlier than +10.0s (its own grabCooldown is 5.0s)

That line is the fork the next run resolves. If it is present and the beast still returns in a
second, the beast is reaching its grab by a route that never consults `lastGrabTime` —
`EnemyAI.TryGrabPlayer` gates on `grabInDamagingState` and `hasGrabbedThisAttempt` alone — and the
fix belongs there instead. Either way the game over now survives it.

### The hypnosis ladder: played, kept, and cut to the two rows it actually uses

2.5.10's ladder finally got a run, and it works: 16 `[HYPNOSIS]` lines, both tiers, phase carried
across each switch (`Play Serpent_Hypnosis_3@136ms`), no crossing closer than the 1.5 s dwell.

Two things came out of it. **The middle rung is gone.** The ladder dispatched `Serpent_Hypnosis_1`
and `_3` and left `_2` in the gallery, unplayed and still on the shared grid — a row nothing
dispatches is a row that drifts out of a ladder without anything noticing. `HYPNOSIS_ROWS` is two
entries now, `Serpent_Hypnosis_2` carries the close amplitude (90) that `_3` had, and `_3` is
deleted from `Definitions.csv` and from both variants.

**And the tier was being dropped by a blink, not by distance.** Tier 2 held 1.16 s at 15:33:26 and
went back to `filler_damage_50` while the serpent was still hypnotising — `hypnosisInView` is
answered per frame and flickers on a step to the side or the serpent's own walk cycle. Hysteresis
and the minimum dwell both work in the distance axis and neither covers it. `SerpentHypnosisViewGrace`
(1.5 s) holds the current row through a lost pull; only a pull that stays lost hands the device back
to the filler.

### Deleting a gallery row does not delete it from an install

Cutting `serpent_hypnosis_3` exposed a hole in `deploy.py`: every write there is skip-unchanged,
which means add-or-replace and never remove, so both installs kept a funscript the working tree no
longer had. Edi plays rows rather than files, so nothing could have dispatched it — the cost is
that "what is in this install" stopped being answerable from the repo. `prune_gallery` deletes
`.funscript` files under `Edi/Gallery/<variant>/` that the payload does not carry, and `--check`
counts them like any other difference. Scoped to the gallery: nothing else in a game directory is
the deploy's to delete.

### Two spawn defects, both from measuring the wrong thing

**The mimic floated 1.28 m.** §119 taught `SeatOnGround` to measure renderer bounds rather than
trust the pivot, and passed `true` to `GetComponentsInChildren<Renderer>` so a body renderer that
spawns briefly disabled still counts. That also hands back the mimic's grab-screen art, which
hangs well below the body as inactive objects: the lift was measured to the bottom of something
nobody can see. Every other enemy in the run lifted 0.06 m. Renderers now have to be `enabled` and
`activeInHierarchy` to vote.

**The dragon spawned under the floor.** `chaser_boss variant 1/2 'Dragon' at (-13.23, -1.80, 24.90)`
with the player at y = -0.60. `TryGetSpawnTransform` casts 12 m down from 3 m above the spawn point
and takes the first hit, and in the sewers the point a few metres ahead is often over the water
channel rather than the walkway. From the chair that reads as the key not working. A hit more than
1 m below the player is no longer accepted; the player's own Y is the fallback, which is what the
code did before the snap existed. The variant numbering from §119 is confirmed correct in the same
lines — `1/2 'Dragon'` then `2/2 'Wendigo'`.

### The Blinded Beast became unspawnable mid-run

Key 9 spawned a beast at 15:30:44 and then reported `no prefab found` eight times from 15:36:35 on,
in one unbroken session. §110 made the beast reachable by loading the `EnemyData` folder, because
nothing in an ordinary floor ever references it — but `EnsureResourcesEnemyDataLoaded` threw the
returned array away and latched a bool. `Resources.LoadAll` hands back references and nothing else
held them, so Unity's next unused-asset unload collected the lot, and the latch guaranteed they
were never reloaded. The array is held in a static field now, and the guard is "do I have them"
rather than "did I once ask".

### The silent grab scenes: answered, and it is vanilla

§119's instruments settled it in one run. On beast grabs there is **no `[SCENE-HIDE]` line at all**
— the mod's hider stands down for that prefab — and `Can not play a disabled audio source` fires
anyway. Where the mod does hide (`hid 11 enemy object(s) carrying 22 audio source(s)` on the
goonshroom pile) there is no such warning, because by then the clip is already playing. So the
disabled source is vanilla's own `hideInsteadOfDestroyOnGrab` teardown, not ours. `[GRAB-AUDIO]`
also names what to fix: two sources per enemy, one of them `clip='<null>' playing=True`, assigned
at runtime, which is why the assets say nothing about it. Still open, but no longer a guess.

## 121. One command for the thirteen checks — `code/check.py`

PROJECT.md's "Checking your work" table had grown to thirteen entries with four different
invocations (`python3`, `.venv/bin/python`, `dotnet test`, `dotnet run --project`). Running them
all by hand after a change is a minute of copy-paste; what actually happened is that a session ran
the two or three it remembered, and the rest were run when someone thought of them. `code/check.py`
runs the lot, in dependency order, and returns one exit code.

It adds no new check. What it had to add is an understanding of **how each tool reports failure**,
because they do not agree — and this is the part worth knowing before adding a fourteenth:

- **`gate`** — the exit code is the verdict. `dotnet test`, `patchaudit`, `cfgaudit`,
  `ladders --check`, `dioramaaudit`, `deploy --check`, `release --check`, `refvideo --verify`.
- **`grep`** — the exit code is *always* 0 and the verdict is a word in the output. `slugharness`
  prints one row per (enemy, animator state) pair and `UNMAPPED` in the last column is the gap;
  `animsweep` prints `OFF` in its time column. A runner that wrapped these by exit code would
  report green forever — worse than not wrapping them, because it looks like coverage.
- **`report`** — there is no verdict to compute. `gallerydiff` and `speedcheck` answer a question a
  human reads (which rows differ from gameplay; which are too fast for which device). They run
  under `--full`, their summary lines are printed, and they fail the run only if the tool crashes.

`handystate.py` is the one entry left out: it polls the Handy over the network for as long as you
let it. It is an instrument, not a check.

Two tiers, because 10 s of gates after every edit is affordable and 70 s of asset sweeps is not:
`check.py` is the fast tier, `--full` adds `animsweep`, `dioramaaudit`, `gallerydiff`, `speedcheck`
and `refvideo --verify`. `--deploy` runs a full deploy *first* — after would be pointless, since
`deploy --check` is itself one of the steps.

**A missing prerequisite is a `skip` with a reason, never a pass.** No `.venv`, no game install, no
`dotnet` or `ffmpeg` on `PATH` — the step prints why and the command that fixes it, and the summary
counts skips separately from passes. This is the same rule as `[ALIAS-GAP]` and `cfgaudit`: a gap
has to announce itself rather than look plausible.

Each verdict path was checked against a step built to trip it (`gate` fail, `UNMAPPED`, `OFF`,
report, both skip reasons) and against one real mutation — renaming `[Ambient] DiagnosticMode` in
the live config, which `cfgaudit` caught and reported through the runner with its full output. The
first `--full` run was 11/12: `deploy --check` reported `game-linux` stale, which is real drift and
not the runner's doing — BepInEx rewrites the install's config header on every launch (`v2.5.13`
against the working tree's `v2.5.10`), so any game session since the last deploy makes the install
differ. `python3 code/deploy.py --no-build` is the answer, and it is exactly what the step exists
to say.

## 122. What the 2.5.13 run found, and one rule replacing another: protect, do not block

The first play of 2.5.13 (2026-08-24, Linux, sewers — beast, serpent, mimics, chaser boss).
**The mod is 2.5.14 for what came out of it.**

### The game over is answerable

§120's move — refuse the release while the prompt is up — held. Twice in the run:

    17:15:47.394 [GAMEOVER] presentation committed from scene entry survival from grab - cancels ignored until it is consumed
    17:15:54.617 [GAMEOVER] presentation released by ShowGameOverPanel

No `released by Revive`, no `cancel from guard`, and both deaths were answered by the player at the
panel. The 2.5.12 pair does not appear at all.

What it exposed is that the mod had two different answers to the same question. The game over now
lets the re-grab happen and protects what is on screen; everywhere else the mod tried to stop the
re-grab from happening. **The first one is the rule now** — it is in
`learnings/grab-and-ai-mechanics.md`.

### The 10 s enemy cooldown was written, ignored, and is now off by default

§120 left the cooldown instrumented so one grep could decide whether anything was left to fix. The
line is there, on every grab end:

    17:14:46.473 [GRAB-COOLDOWN] Blinded Beast: next grab no earlier than +10.0s (its own grabCooldown is 10.0s)
    17:14:48.754 [GRAB-START] prefab='Blinded Beast' key=blinded_beast anims=2

**2.28 s**, and the same margin at 17:15:19 → 17:15:21.5. So §120's fallback capture through
`hiddenEnemyToRestore` works and the write lands — the Blinded Beast simply reaches its grab by a
route that never reads `lastGrabTime`. Vanilla's own `grabCooldown` on it reads **10.0 s**, not the
5.0 s the §120 handoff assumed, which means vanilla ignores its own number on that path too.

The obvious next move was to gate `EnemyAI.TryGrabPlayer` the way `NunGrabTuning` gates
`TransitionToAttacking`. **That is the move not taken.** Under the rule above, a re-grab is not the
defect; a re-grab taking a prompt away was, and the latch already holds that. So
`EndGrabEnemyCooldownSeconds` defaults to **0** — vanilla's own timing stands, and the knob remains
for anyone who wants an enemy held off longer than the game would. The log line says which of the
two happened rather than always printing a number:

    [GRAB-COOLDOWN] Blinded Beast: vanilla's own grabCooldown of 10.0s stands - no floor forced

`EndGrabImmunitySeconds` was left at 4 deliberately. It reads like the same kind of block and is
not one: vanilla's `GrabScreen.GrabImmunity` sets `CanBeGrabbed = true` at T+1 regardless, so
anything above 1 has never done anything (measured in §44). Lowering it would have been a change to
the config file and not to the game.

### The mimic fix was correct and measured one frame too early

Both mimics still logged `lifted 1.28m` with §120's visible-renderer filter in place. `Instantiate`
runs `Awake` and stops; `Start` — where an enemy deactivates its own grab-screen art — has not run
when the same frame measures the bounds, so every hidden child is still `activeInHierarchy` and the
filter has nothing to reject. `SeatOnGround` now runs one frame later, off `Plugin.Instance`, and
names the renderer that decided the floor:

    [SPAWN] mimic: lifted 0.06m so its art sits on the floor rather than through it (lowest visible renderer 'Sprite')

The name is there because twice now the size of the lift alone could not separate a correct seat
from a measurement against art nobody can see.

### Confirmed and closed by the run

- **The hypnosis ladder holds through a blink.** `the pull stopped - holding Serpent_Hypnosis_2 for
  up to 1.5s` at 17:17:16.701, `the pull resumed inside the grace - the ladder kept the row` 0.59 s
  later, with no filler in between. Both tiers played.
- **The Blinded Beast stays spawnable all run.** §120's `EnemyData` hold works; key 9 was pressed
  repeatedly and spawned every time.

## 123. The 1300 ILSpy locals, named

§116 left one thing behind on purpose: about 1300 locals still called `text`, `num`, `flag` and
`array`. Those were the ones a transform could not do. `string`, `int` and `bool` say nothing
about what a variable *is*, so every one of them is a judgement about what the expression means -
a hand pass, file by file, not a rewrite rule.

It is done. Every ILSpy-named local in the tree now has a name from its meaning:
`float num` in `ArmPostCumGrace` is `graceSeconds`, `num3` in `ApplyHeatScaledAutoHeal` is
`heatFraction`, `text2` in `SendPlay` is `row`, `flag` in `Plugin.Update` is `galleryBlocks`.
Two mechanical sub-rules covered the tail once the judgement calls were made by hand: a local
read straight out of `Traverse.Field("x")` takes `x`'s own name, and one read from
`Plugin.CfgFoo.Value` takes `foo`. Those two were scripted with block-scope detection and then
compiled; everything else was read first.

Seven redundant ILSpy locals went with them. Six are `array2 = array` foreach caches - the
compiler re-creates them, so they cost no IL and the diff does not move. The seventh, `string
text3 = text2;` in `AmbientProximity.Tick`, was a real local copy and is the only behavioural
line this pass touched, in the sense that it changes the IL at all; what it does is identical.

**The proof is §116's harness, and it is worth stating what it can and cannot see.** Decompile
before, decompile after, strip `//IL_` lines, collapse `(Object)(object)`, diff. A local rename
is invisible to it - local names live in the PDB, not in the IL - so a zero diff after a
rename-only pass is exactly what you want and also exactly what you get for free. The 33 lines
this pass does move are therefore the interesting ones, and all of them are accounted for:

- the one real local copy above (4 lines),
- the parameter renames in `MatchesSpawnHint`, `MatchesHint` (`text` -> `name`) and
  `AppendHeatModLine` (`text` -> `stats`). Parameter names *are* metadata, so they show in a
  decompile where a local does not. All three are private and called positionally.

`dotnet test` 103/103 and `check.py` 7/7 at every checkpoint, which is the other half of the
proof: `NameRemap`, `GalleryAliases`, `GalleryRegistry` and `ConfigMap` are the files most
touched here and they are the files the suite covers.

**What this closes.** The last item of §115-§118's cleanup. What is still open from that stretch
is one decision, not one pass: what happens to `code/PncEdi-source-stale-2026-05-30/` and
`code/PncEdi-v2.0.8-original.dll` before strangers read the tree.

## 124. What the 2.5.14 run found: a constant mistaken for a measurement, and a gap that was never the mod's

The first play of 2.5.14 (2026-08-25, Linux, caverns — mimics, serpent, beast, goonshroom pile).
Clean of `ALIAS-GAP`, `EDI-SKIP` and `failed:`. **The mod is 2.5.15 for what came out of it.**

Three things were reported: the mimics still spawn slightly above the floor, the hypnosis ladder
does not follow distance closely enough, and the goonshroom pile's start scene has no audio. The
first and third are fixed here. The second is a design question and is section 3 below.

### The mimic lift was a constant of the sprite sheet, not a measurement of the art

Both variants logged `lifted 1.28m ... (lowest visible renderer 'Sprite')` again, with §122's
one-frame deferral in place. Reading the prefabs settled in one pass what two runs of log could
not:

    Mimic            [CapsuleCollider, Animator, MonoBehaviour]
      Sprite         [SpriteRenderer, MonoBehaviour]

**There is no hidden art on the mimic at all** — root and one child. §120's visible-renderer
filter and §122's deferred frame were both correct fixes to a problem this prefab does not have,
which is why neither moved the number.

Where 1.28 comes from is `Renderer.bounds` on a SpriteRenderer, which is the sprite's whole
`rect` and not its picture. Both sheets are 256x256 at 100 pixels-per-unit with a centred pivot,
so the quad is 2.56 m tall and hangs 1.28 m below the origin **whatever is drawn in it**. That is
why both variants agreed to the centimetre across three runs: they were reporting half a frame.

The picture inside the frame is 46.08 px up from the frame's bottom edge (`m_RD.textureRectOffset`)
against a pivot at 128 px, so the ink starts **0.819 m** below the origin. `SeatOnGround` now
measures that instead, through a new `VisibleBottom`, and keeps `Renderer.bounds` for anything
that is not a sprite.

**Vanilla was asked what the right answer is, and it agrees.** `ChestSpawner.SpawnMimicAtPosition`
does `Instantiate(prefab, spawnPos.position, ...)` with no seating maths — the height is authored
by hand into the `ChestSpawnPoint` transform. Read out of the shipped rooms those points sit
**+0.810 m** (dungeon blood hall) and **+0.800 m** (CavernGasChoice) above the `FLOOR` objects
beside them, while an `Enemy Spawnpoint` sits exactly on the floor. 0.81 typed by a level
designer, 0.819 computed from the sprite: the same number from two directions.

### The clinging family's grab screens are silent, and it is vanilla's asset gap

The reported symptom pointed at the mod's own hider — the run shows `[SCENE-HIDE] hid 6 enemy
object(s) carrying 12 audio source(s)` on the goonshroom grab, and deactivating an object silences
its sources with no warning, unlike the `Can not play a disabled audio source` the Blinded Beast
produces. That was wrong, and reading `GrabScreen` rather than guessing is what showed it:
`audioSource = GetComponent<AudioSource>()`, on the GrabScreen's own GameObject. The enemy's
sources were never the ones playing.

What is actually missing is in the assets, on both halves of the path:

- `grabScreenAnimations` (`animationName` -> clip, walked by `CheckAnimationStateSound`) is
  populated on the zombie, nun, Blinded Beast, serpent and both mimics, and **empty on
  `GoonShroom_Enemy` and all five `Imp_Enemy` variants**;
- `grabStartSound`, `grabLoopSound` and `grabEndSound` — the fallback `PlayGrabAudio` uses when
  that array is empty — are **null on all three GrabScreen instances in the game**.

So the two families with an empty array fall through to a fallback that has nothing in it. The
goonshroom is silent through its cling as well: its `grappleLoopOne/Two/Three` are null where the
imp's carry `imp grab 1/2/3`. Vanilla's own tooltip on the field names the case it was for —
"Used when a trio-grab overflow escalates from GrappleScreen to GrabScreen" — which is exactly the
pile that went silent.

The clips exist and are simply unreferenced: `Goonshroom gangbang sex`, `Goonshroom Gangbang cum`,
`Imp Gangbang grab sound`, `Imp Gangbang grab CUM sound`. `GrabScreenAudioFill` is a postfix on
`GrabScreen.ResolveGrabAnimations` that fills `currentGrabAnimations` from
`Gameplay/GrabScreenAudioFill` **only when the enemy handed back an empty one**, so a family that
authored its own is never touched. Same shape as §109's `Max Heat` mirror: deliver the message the
game is already trying to send.

**One thing about it is unproven and instrumented rather than assumed.** `Resources.FindObjectsOfTypeAll`
only sees *loaded* assets — §110's whole lesson — and nothing in the build references these clips,
so whether they are resident is a question only a run can answer. Two sources are tried in order:
any clip the enemy already holds a reference to (its `grappleLoop*` fields), then the loaded-asset
sweep by name. **With the shipped defaults the first never fires** - the imp's grapple loops are
`imp grab 1/2/3` against a config asking for `Imp Gangbang grab sound`, and the goonshroom's are
null - so both families rest on the sweep and neither is a control for the other. A name that
resolves to neither is logged once and left silent, which is what vanilla does today. The tell in
the next run is one of two `[GRAB-AUDIO]` lines: `filled 2: GoonShroom_GrabscreenStart->...` or
`no loaded clip for ...`.

### Confirmed by the run, nothing to do

- **Re-grabs are vanilla's and the presentation holds** (§122's rule). Nothing stolen.
- **The grapple death sequence on a goonshroom pile**, never played before: `[GRAPPLE-DEATH] begin
  at 3 goonshroom(s)`, `[PLAYER-DEATH] during grapple — letting scene play out`, and the heat
  cycled and released through `Max Heat` as §109 intended.
- **Shaking off a grappler** under 0.3.1's own throw, also never played before: no complaint.
- **Both chaser bosses** spawned and cycled.

### Both fixes played, 2026-08-25

**The mimic seat is right.** Four spawns, all four `lifted 0.82m ... (lowest visible renderer
'Sprite')`, and the chest sits on the floor on screen. 0.819 computed from the sprite, 0.81 typed
into the level, 0.82 measured in play.

**The clips are resident, and the fill lands.** The open question was whether
`Resources.FindObjectsOfTypeAll` could see assets nothing in the build references. It can:

    [GRAB-AUDIO] 'GoonShroom_Enemy' authored no grab-screen sounds - filled 4: GoonShroom_GrabscreenStart->Goonshroom gangbang sex, ...
    [GRAB-AUDIO] 'Imp_Enemy ALT 2' authored no grab-screen sounds - filled 4: ...

Both families, both scenes stepping `Start` -> `Cum` -> `Start` with their funscripts, zero
`Can not play a disabled audio source`. Note `anims=` on `[GRAB-START]` now reads 4 for these two
where it read 0 - that diagnostic counts the array the fill wrote.

**And it is audible.** `filled 4` only says the array was written, and `DIAG-AUDIO` could not
settle it either way - that sweep reports sources within 15 m of the player, and `GrabScreen`'s
AudioSource turns out to be on an object called `GrabScreen`, so its absence there was never
evidence. A postfix on `CheckAnimationStateSound` prints the source vanilla actually selected, once
per clip change, with the settings that can silence a playing source:

    19:33:51.221 [GRAB-AUDIO] the grab screen source is on 'GrabScreen' clip='Goonshroom gangbang sex' playing=True volume=1.00 mute=False spatialBlend=0.00 maxDistance=500 mixer=SFX listener=1.00
    19:33:51.948 [GRAB-AUDIO] the grab screen source is on 'GrabScreen' clip='Goonshroom Gangbang cum' playing=True volume=1.00 mute=False spatialBlend=0.00 maxDistance=500 mixer=SFX listener=1.00

Confirmed by ear in the same run. The instrument stays: it prints for every family, so the working
ones (`Serpent Sex`, `NUN sex`) are the control the fill never had, and a future regression on
either side of the line shows up as one changed field rather than as silence with no explanation.

One cosmetic thing, left as it is: the fill writes all four configured entries to whichever family
is grabbed, so the imp's array carries the goonshroom's two states and vice versa. Harmless -
`CheckAnimationStateSound` matches on the animator's state name and those never collide - and it
is why the line says `filled 4` rather than `filled 2`.

### What the run left open, and §125 answers

The two-tier hypnosis ladder follows distance too coarsely. Not latency: the run switched tiers
1.50 s and 1.86 s apart, which is the 1.5 s dwell and nothing else. With two tiers over the
8 m-to-2 m band there is exactly **one** step, at 5 m, so three metres of approach either side of
it produce no response at all. §125 is what replaced it.

## 125. Distance drives the device, not the playlist

The hypnosis ladder had two answers available and both were bad. More tiers is the move the
2026-08-23 run already rejected - a step too short to register is not a step - and one flat script
throws the approach away entirely, which is the thing the feature exists to have.

**The third option was in Edi all along and nothing in this project had costed it.**
`POST /Edi/Intensity/{max}` scales `device.Max` between the bounds configured for the device:
`DevicePlayer.Intensity` sets the property, `DeviceBase` debounces the write 100 ms
(`rangeTimer`) and calls `applyRange()` in place, and `HandyV3Device.applyRange` sends
`SetStroke(Min, Max)`. Nothing on that path re-dispatches the gallery. So amplitude can move
while a row keeps playing - which is the one thing `SendPlay` has never been able to do.

### Measured, because §106 is what happens when it is not

Two diagnoses derived from Edi's source were internally consistent and wrong, and one was built
and shipped before a run disproved it. So this was benched against the hardware before a line of
mod code was written: `code/intensitybench.py` plays a row, steps the intensity, and after each
step reads the device's own `v2/slide` and `v3/hsp/state`. Against a Handy 2 Pro on 2026-08-25,
with the patched Edi this project ships (v1.0.4 + PR #15, §107) - so the binary measured is the
binary that runs:

    intensity 100 -> slide {'min': 0, 'max': 100}   current_time=2536
    intensity  70 -> slide {'min': 0, 'max': 70}    current_time=4748   phase -16 ms
    intensity  40 -> slide {'min': 0, 'max': 40}    current_time=7033   phase +14 ms
    intensity  20 -> slide {'min': 0, 'max': 20}    current_time=9245   phase +22 ms
    intensity  40 -> slide {'min': 0, 'max': 40}    current_time=11449  phase -17 ms
    intensity  70 -> slide {'min': 0, 'max': 70}    current_time=1682   phase  +1 ms
    intensity 100 -> slide {'min': 0, 'max': 100}   current_time=3874   phase -16 ms

The range follows exactly and the playback phase stays within **22 ms** of prediction across six
changes, one of them across the loop seam. `min` stays 0, so what intensity scales is amplitude
anchored at the bottom of the stroke - which is exactly the property `ladders.py` builds the
hypnosis rows to have (shared grid, shared anchor, differing amplitude, §87). The device supplies
it directly.

**Two readings of this bench were wrong before one was right, and the mistake is worth keeping.**
The first run used `Serpent_Hypnosis_1`, a **1000 ms looping row**, with a 4 s hold - so
`current_time` sampled somewhere in [0, 1000) every time and the naive `t < previous` restart test
was measuring the loop wrapping. `v3/slide` also 404s: Edi writes the range with `PUT v2/slide`
even on the v3 device. The tool now probes the endpoint, reads the row's duration out of
`Definitions.csv`, and separates a wrap from a restart by predicting `(previous + elapsed) %
duration` from the wall clock - a wrap lands on the prediction, a restart lands near zero.

### What it replaces

`SerpentHypnosisContinuous` (default **on**) plays one row - `Serpent_Hypnosis_2`, the loudest of
the ladder, because intensity only ever scales *down* - and drives intensity from the band
fraction, `SerpentHypnosisIntensityFar` (44) at `hypnosisStartRange` to
`SerpentHypnosisIntensityNear` (100) at `grabRange`. 44 of that row's 90-unit peak is 40 units of
travel, which is what the old far tier played, so the band starts where the ladder did.

The tiers, the hysteresis and the minimum dwell are all unused on this path and stay only for
`SerpentHypnosisContinuous = false`. They have nothing to do: there are no boundaries to flap
across, and no crossing that can arrive faster than it can be felt, because there is no crossing.
The view grace stays and means what it always did - a lost pull holds what is playing, which here
is the last intensity as well as the row.

Two rate limits, and they are the shape of the transport rather than taste:
`SerpentHypnosisIntensityStep` (3) stops a walk down the band becoming sixty POSTs a second, and
`SerpentHypnosisIntensityInterval` (0.15 s) sits just above Edi's own 100 ms debounce, below which
a write is discarded before it reaches the hardware anyway.

**Intensity is global to the channel, not a property of a row, so whatever lowers it owns raising
it.** `SerpentHypnosis.Reset` restores 100 and is called every frame no serpent is hypnotising and
again on the scene change; `Plugin.SendIntensity` drops a repeat of the value it last sent, so
that costs nothing when there is nothing to undo. A hypnosis that ended at 44% and did not put it
back would leave every later scene quieter with nothing on screen to say why.

### Played the same evening, and what the log said

Four approaches, walked in and out at both speeds. The mechanism works end to end: intensity
tracks distance at the 150 ms interval in 3-6% steps, `44%` at the far edge climbing to `97%` at
2.3 m, the view grace holds the last value through a lost pull, and every approach that ended
restored 100%. Nothing in `ALIAS-GAP`, `EDI-SKIP` or `failed:`.

**One defect, and it is the seam between the two hand-backs.** The row and the range were being
handed back together, and they should not be:

    19:07:26.793 [HYPNOSIS] the pull stayed stopped - the ladder gives the device back
    19:07:26.793 [EDI-INTENSITY] 100% (the serpent gave the device back)
    19:07:26.793 [EDI] Play filler
    19:07:26.884 [EDI-INTENSITY] 84% (serpent at 3.8m of 8.0-2.0)
    19:07:26.885 [EDI] Play Serpent_Hypnosis_2

The grace ran out and the approach resumed **91 ms** later, so the device played one
full-amplitude filler stroke that belonged to neither scene. The row hand-back has to be instant
because something has to be playing; the range does not, because for a tenth of a second whatever
is playing sounds right at either range and wrong only if the wait drags on.
`SerpentHypnosisIntensityRelease` (0.75 s) delays the restore, and any intensity write cancels a
pending one. A scene change still restores immediately - there is no next approach to wait for.

### The second run reached the grab, and the grab found the leak

A serpent landed one twice - the seam the ladder was designed around and had never reached. The
approach itself is now clean end to end: `44%` at 8.4 m ramping in even 6-7% steps at the 150 ms
interval to `97%` at 2.3 m, then

    19:18:02.589 [EDI-INTENSITY] 97% (serpent at 2.3m of 8.0-2.0)
    19:18:02.659 [GRAB-START] prefab='Black Serpent Enemy' key=serpent anims=2
    19:18:02.660 [EDI] Play Serpent_Loop@775ms
    19:18:17.794 [EDI] Play filler_cum_50
    19:18:18.548 [EDI-INTENSITY] 100% (the serpent gave the device back)

**`Serpent_Loop` played the whole 15 s grab at 97%.** The range only came back 0.75 s after the
*filler* did, because the ladder is ticked from the filler refresh and the filler refresh does not
run during a grab scene - so nothing asked the ladder anything for fifteen seconds, and its
`Reset` never ran.

Nothing was audibly wrong, and that is the reason to fix it rather than to leave it. The grab
lands at `grabRange`, where the ramp is at its top by construction, so this particular leak is
invisible **by luck of where the band ends**. Widen the band downward -
`SerpentHypnosisIntensityFar` is the tuning knob this section recommends - or get grabbed by
something else mid-approach, and it is a nun scene at 44% of its authored travel with nothing on
screen to say why.

So the rule is now stated where it belongs: **any row that is not the approach's own takes the
range back with it.** `Plugin.SendPlay` tells `SerpentHypnosis.NoteRowPlayed`, which *arms* the
hand-back rather than performing it - which keeps the flap fix, since a `filler` dispatched
between two halves of one approach arms a release the resuming approach then cancels - and
`Plugin.Update` runs the countdown, because the case that needs it is precisely when the ladder is
not being asked anything.

**Confirmed the same evening**, on both routes out of an approach:

    19:32:44.676 [EDI] Play Serpent_Loop@1254ms
    19:32:45.422 [EDI-INTENSITY] 100% (the serpent gave the device back)      0.746 s

    19:33:19.443 [HYPNOSIS] the pull stayed stopped - the ladder gives the device back
    19:33:20.193 [EDI-INTENSITY] 100% (the serpent gave the device back)      0.750 s

0.75 s where it was 15.9 s, and the same delay whether the approach ended in a grab or in the
filler.

### Judged better, and the tiers are gone

Confirmed by feel on 2026-08-25, and the old system came out rather than staying as a fallback.
What went:

- `SerpentHypnosisGalleries`, `SerpentHypnosisTierFractions`, `SerpentHypnosisHysteresis`,
  `SerpentHypnosisMinDwell` and the `SerpentHypnosisContinuous` switch itself - five settings for
  a mechanism with no callers left;
- `PickTier`, `Boundaries` and the local `Split` in `SerpentHypnosis.cs`, with `_tier` and
  `_tierEnteredAt`. The view grace stays and is the only thing left holding state across frames
  besides the intensity itself;
- `Serpent_Hypnosis_1` from the gallery, both variants, and `Serpent_Hypnosis_2` renamed to
  **`Serpent_Hypnosis`** - a numbered row implies a set, and there is no set. `deploy.py` pruned
  the four dead funscripts out of both installs on the next run (§120's deletion path).

`SerpentHypnosisContinuousGallery` became `SerpentHypnosisGallery`, and `ladders.py` keeps the row
because its shape is still measured against `Black_Serpent_Hypnosis_Loop` - that is what the
module is for - but its `--check` no longer claims a ladder invariant over it. Peak stays 90:
intensity only scales down, so the authored row has to be the loudest the approach will ever be,
and the far end of the band is that row at 44%.

`check.py --full` 12/12 after the removal.

### Considered and rejected: migrating the filler ladder too

The obvious next question, asked the same evening. The answer is no, and the measurement is here so
nobody re-derives it.

**Half of it would be free.** The four damage rows are one row scaled, provably:

    filler_damage_75 x 0.55 -> [0, 45,  8, 52,  2, 55, 13, 48, 0]
    filler_damage_25           [0, 45,  8, 52,  2, 55, 13, 48, 0]

Byte identical, and x0.75 lands on `filler_damage_50` to within one unit on two points. `filler`
itself is the same row at amplitude 20.

**The cum half cannot be done at all**, and it is not a near miss:

    filler_cum_25   peaks 45 52 55 48   troughs 34 31 36
    filler_cum_75   peaks 82 95 100 88  troughs 23 14 32

The troughs move the *opposite* way to the peaks. That is the authored difference between the two
families - damage jolts to the bottom on every trough, arousal swells over a raised floor that
recedes as heat climbs - and `Intensity` moves only `device.Max`, leaving `Min` at whatever the
user configured. Scaling moves both ends together and cannot open a ladder that widens from both.
Best case is seven rows becoming four, not one.

**And the objection that decides it even for the damage half: two owners of one global knob.** The
invariant today is *the range is 100 unless the serpent is approaching*, with any foreign row
reclaiming it. The filler plays for most of a session; if it holds the knob too, that becomes "the
range is whatever the filler last left", and the serpent's ramp from 44% would ride on an unknown
baseline with both writing the same global.

The serpent migration paid because its ladder failed on both counts at once: rows differing only
in amplitude, and a signal that sweeps the whole band in a second or two. The filler fails neither
the same way - damage arrives as discrete hits, where a step is the right gesture, and heat builds
over seconds, where four steps are not visibly coarse. What intensity bought the serpent - a
switch that does not restart - the filler already has from §87's `?seek=` phase carry. If the ramp
does not read as an approach, the lever is the two ends - `SerpentHypnosisIntensityFar` 44 and
`SerpentHypnosisIntensityNear` 100 - and widening the far end downward is the cheap experiment.
What is *not* available is making it faster as it closes: the row is a constant-rate triangle by
design (§87, the spiral does not speed up), and Edi's API has no playback-rate control to add one.

## 126. Three open checks closed without a run, and one retired as unreachable

Nothing was built here. Four things were open on 2026-08-26 that each looked like they needed a
session at the keyboard, and three of them turned out to be already answered - two by earlier play,
one by the assets. The fourth is not a check anyone can run, in this build or any build shipped so
far.

**The serpent's continuous ramp reads as an approach.** §125 shipped it with one judgement
deliberately left to a later play; that play had already happened. `SerpentHypnosisIntensityFar`
(44) and `SerpentHypnosisIntensityNear` (100) stand as authored, and §125's own note on widening
the far end stays as the cheap experiment if it is ever wanted.

**D15 is closed by the fifteen boxes around it.** `serpent wall blowjob` has
still never been walked past in a logged session, and `code/dioramaaudit.py` already answers the
static half - its clip exists and its alias matches it exactly, as all sixteen do. Every diorama
that *has* been visited works. A trip made only to confirm the sixteenth is not worth its own
session; if a run ever reports D15 silent, that report is the action item and `AMBIENT-SCAN` in
that run's log is where it starts.

### The Blinded Beast's deferred path, and why its last item cannot be tested

§73's stand-down gives an enemy that sets `EnemyAI.hideInsteadOfDestroyOnGrab` to vanilla
entirely - the mod arms none of its keep-alive. The Blinded Beast is the only prefab that sets it
(§119), and three post-conditions of vanilla's restore had never been witnessed: the beast back and
idle in place after an escape, taking damage normally afterwards, and a kill landed during the grab
still killing it at `EndGrab`.

**The first two are in the 2026-08-25 log, from the other side.** A `[GRAB-COOLDOWN] Blinded Beast`
at 18:17:20 puts the grab's end on the clock; the `DIAG-SPRITE` census seconds later has the beast
in `BlindedBeast_attack_*` at 3.3 m; a fresh `[GRAB-START] prefab='Blinded Beast'` lands at
18:17:31. Restored, active, chasing, grabbing again - and grabbing again is a stronger statement
than idling, because it needs the AI, the colliders and the grab route all live.

**The third is unreachable, and the check is retired rather than deferred.** The flags were read out
of the build rather than assumed: a UnityPy sweep of all 20 enemy AI components in
`game-linux/PNC 0.3.1_Data` returns exactly one row with either grab flag set -

    Blinded Beast   EnemyAI   hideInsteadOfDestroyOnGrab=1   preserveHealthDuringGrab=1

- and `EnemyAI.EndGrabHidden` tests them in that order:

    if (preserveHealthDuringGrab) { ResetGrabTransientState(); currentState = AIState.Idle; ... }
    else if (remainingHealth <= 0f) { currentHealth = 0; TransitionToDead(); ... Destroy(gameObject); }

So for the only enemy that can reach that method, the death branch is dead code. Both flags live on
the same component, and the one that gates the kill is checked first.

**Grab-screen damage never reaches the enemy either.** `GrabScreen.OnPlayerAttackDuringGrab` -
reached from a melee weapon's `OnAnimationHit` while `IsGrabbed` - subtracts from the grab screen's
own `enemyCurrentHealth` float, and zeroing it calls `EndGrab()`, which restores the beast at the
health it walked in with. The number moves on the grab-screen bar and evaporates on restore. The
one thing on that screen that damages the real enemy is the thorns trinket, an `IDamageable`
`TakeDamage` at grab start, before anything is hidden.

That is worth keeping for a reason beyond this checklist: **"the enemy can be killed on the grab
screen" is a mechanic this build does not have**, and any future feature that assumes it - a heat
rule, a spawn rule, a game-over path - is assuming something the assets do not support. If a later
build clears `preserveHealthDuringGrab` on the beast, or sets `hideInsteadOfDestroyOnGrab` on a
prefab that leaves it clear, the death branch comes alive and this check comes back with it. The
sweep that produced the table above is kept as `code/grabflags.py` - `spawntables.py`'s type-tree
idiom over all seven AI classes - and is the way to re-ask the question, rather than reasoning from
what the C# could do. It is an instrument, not a check, so it stays out of `check.py`.

### One incidental

`check.py` reported `deploy` stale on a working tree nobody had touched. The drift was
`game-linux`'s own `com.edi.pnc.cfg`: the game had rewritten it at launch, bumping the version
header to 2.5.15 and reflowing the whitespace. `deploy.py --no-build` restored it and the run went
7/7. The rule is in `learnings/working-practice.md`.

## 127. The portable-patch fork, integrated: a mod manager, gameplay profiles, and custom enemies

`pncedi-portable-patch` is a fork of **2.5.2**, and three things in it were worth having. This
brings them across onto 2.5.15 rather than merging that tree: its baseline is thirteen versions and
a source refactor behind, so what came over is the *features*, adapted, and the diff against its
files was used as a reading aid rather than as a patch.

The rule applied throughout: **take what the fork does that this tree does not, and refuse what it
does differently for the same reason.** Three of its settings were rejected on exactly that ground,
and they are listed at the end.

### The mod manager

`PncModManager` is now a second plugin in `code/modmanager/`, and `BepInEx/plugins/` holds two DLLs.
It is an IMGUI window over BepInEx's own `ConfigFile`, so it edits every loaded plugin rather than
this one - which is why it stays its own assembly. F11, or a button cloned onto the main menu.

**Neither plugin references the other.** BepInEx loads plugin DLLs independently and in no
guaranteed order, so a hard reference would make PncEdi fail to load on an install where the
manager is absent or older. The link is one late-bound read of a public static property -
`ModManagerBridge` resolves `PncModManager.Plugin.IsOpen` by walking the app domain, caches the
`PropertyInfo`, and returns false when it is not there. It re-scans rather than latching a miss,
because PncEdi can easily be constructed first and latching would kill the bridge for the session
on exactly the installs that want it.

That flag exists because **`Update()` keeps running at `timeScale` zero**. Without it, every
keystroke typed into a settings field also lands on whatever hotkey shares that letter, and
FreeCam's bare WASD flies the camera while you edit a number. `SafeInput`'s three readers are the
funnel for every key this mod reads, so the stand-down sits there; `Hotkeys.IsDown` repeats it
because one of its branches goes to BepInEx's own `IsDown()` and does not pass through `SafeInput`.

**Live reload was dropped on the way in.** The fork's version `Assembly.Load`ed a rebuilt plugin
into the running AppDomain, reflection-wrote `PluginInfo.Metadata` and `.Instance`, and unpatched
Harmony by assembly. Mono cannot unload an assembly - its own documentation already said to restart
after structural changes - so what it actually bought was a way to leave a mod half-destroyed. A
development crutch, and not something a released build should carry.

`release.py` grew a `PLUGINS` table and `build_plugin(name)`; `deploy.py` ships both DLLs;
`PncEdi.csproj` builds the manager through a `ProjectReference`, so `dotnet build PncEdi.csproj`
stays the one command that produces and deploys everything and the two DLLs can never be from
different eras.

### Gameplay profiles

`Gameplay/Profile` is one switch - Vanilla, PressureAndRelease, GodMode, Custom - in place of
`Enabled`, `GodMode` and `EnableHeatLocks` having to agree. Several of their combinations are not a
game anyone wants; god mode with heat locks still accumulating is the obvious one.

**Custom is the default, and is exactly what the three switches meant before**, so an existing
`com.edi.pnc.cfg` behaves identically. `GameplayProfileTests` checks that row by row - it is the
property an upgrade turns on.

The truth table is `GameplayProfileRules`, which touches neither `ConfigEntry` nor Unity, so
`code/tests` can compile it; `GameplayProfiles` reads the live settings and hands them in, and owns
the part that needs a running game. Nine new tests, 112 total. The sixty-odd call sites that read
`CfgEnableGameplayTweaks.Value` and `CfgGodMode.Value` now read `Plugin.GameplayTweaksEnabled` and
`Plugin.GodModeEnabled`, so no call site knows profiles exist.

**Switching mid-run forced a change in `PluginPatches`.** The gameplay patches used to install
behind `if (GameplayTweaksEnabled)`, which was right while that answer could only change by editing
the config and restarting. It is wrong the moment the answer can change during a session: a patch
that is not installed cannot start working when the profile asks for it, so a run begun on Vanilla
would switch to Pressure and Release and get nothing, silently. They all install now and gate their
own bodies - which every one of them already did. Nothing is ever *un*patched on a switch either;
Harmony unpatching a running game is how you get half-patched state.

What a switch does still have to undo is the stats the outgoing profile wrote onto the player.
`ObserveVanillaStats` records what the game gave the player, unconditionally and before the gate,
and is guarded against god mode's own `PlayerMaxHealth` - observing that would make it the
"vanilla" figure to restore, and the god-mode health bar would survive a switch back to Vanilla for
the rest of the session.

Two smaller things came with it. `HandyIntensitySource` decides what `FillerCumGalleryMap` buckets:
heat reads poorly once locks hold the heat floor up, because it then reports how many locks are
held rather than what is happening, so `Automatic` switches to lock pressure under Pressure and
Release. And `ExpandSpawnPositions` rounds its fraction by *rolling* it instead of `CeilToInt` -
two spawn points at 1.25x want 2.5 enemies and were getting 3 every wave, so the first lock read as
a permanent +1 and the whole ramp between the two configured ends was spent at its top.

### Custom enemies

Packages under `BepInEx/custom-enemies/<name>/`: a manifest, PNG sprite sheets or a Unity
AssetBundle, funscripts, and rows the package adds to `Definitions.csv` itself. Two behaviours come
with the framework - a charm-circle witch boss and a wall-picture trap - both driven entirely by
manifest fields.

**The content is already out of the source**, which was the question worth asking. `code/` holds
the loader and the two behaviours; every enemy is data. `FemboyWitchController` is renamed
`CharmWitchController` to say so - the class was always generic and only its name named a package.

**Package content is neither tracked nor shipped.** The two that exist are 41 MB of third-party
artwork whose `SOURCE.txt` credits galleries and artists with no redistribution licence behind it.
Fine in a local install; not ours to put in an archive other people download. So `.gitignore` keeps
`_example/` and the README - the manifest format's own documentation - `deploy.py` copies whatever
packages the working tree holds into both installs, and `release.py` ships the framework and the
templates only.

The wiring on this side is small and each piece has a reason:

- `NameRemap` asks the registry through a delegate rather than calling it, so it stays one of the
  eight files `code/tests` compiles instead of dragging `AssetBundle` and the game's `EnemyData`
  in behind it. It asks *first*: a clone package's prefab is a copy of a vanilla enemy, so the
  table would happily match what it was cloned from and play that enemy's funscripts.
- `GalleryRegistry.Register` and `GalleryAliases.Register` let a package add rows and aliases.
  Registered aliases are kept apart from the parsed tables, because `Reload` clears those and a
  package loads once - folding them straight in would mean any later reload silently dropped every
  custom enemy's scenes. They lose to a config entry of the same key, so a user can still redirect
  a package's scene without editing the package.
- Packages join the existing weighted shuffle pool rather than getting a spawner of their own, so
  one draw decides between vanilla and custom and a disabled package simply stops being drawn.
  `IsTrustedShufflePrefab` lets a package vouch for itself: the filters there reject bosses,
  mimics and camera-swap triggers, and a package built on one of those bases would be rejected for
  what it was cloned from rather than for what it is.
- A charm circle owns the Edi channel while the player is inside it, so `AmbientProximity`, the
  filler refresh and `GoFiller` all stand down - the same rule as a grab, for the same reason: two
  rows fighting over one channel is not two scenes, it is neither.
- `SceneEscapeGate` takes a package's own `minimumSceneSeconds` ahead of every built-in rule, and a
  wall trap is exempt from `NearbyEnemyHider` because the trap *is* the scene.

`patchaudit.py` had to be fixed to see any of it. It attributed `[HarmonyPatch]` to the first
top-level class in a file, on the assumption of one class per file; the custom-enemy files declare
their manifest types first and the patch class last, so it blamed a data class for carrying patches
and called the real one an unused registration - two false failures for one correct file. It now
finds the enclosing class, which is what it always meant.

### Unity cannot decode H.264 on Linux

The witch's dream-cloud overlays were a black rectangle on Linux and fine on Windows, with nothing
in any log.

`VideoPlayer` has no H.264 decoder of its own. On Windows it hands the file to Media Foundation and
on macOS to AVFoundation, and the Linux standalone player has no equivalent to hand it to. What it
*does* carry on every platform is libvpx, so VP8 in a WebM container plays everywhere. The packages
ship H.264/AAC MP4, so `Prepare()` simply never completes - no exception, no warning, and a
transparent overlay with nothing in it looks like a design choice.

`PackageVideo` prefers a `.webm` sibling of whatever the manifest names, on *every* platform: one
package then works on both without the manifest saying so or an author thinking about it. Where
there is no sibling the declared file is used unchanged, and on Linux it logs once what is wrong
and what to run. `code/webmify.py` does the conversion - VP8/Vorbis rather than VP9, because VP9
support in Unity's player has moved between versions and platforms while VP8 has been there
throughout, and these are small overlay clips. `webmify.py --check` is a new gate in `check.py`, so
a package that would be blank on Linux fails a check rather than a session. The five witch clips
convert in 28 seconds and come out *smaller* than their MP4s.

### Considered and rejected: three settings this tree already decides once

Each is the fork's answer to a problem this tree also solved, and taking both would be §124's "one
rule where there were two" again:

- **`ClassLockCounts`**, a per-class table (Knight=6 … Ranger=9) fixing the old 5-versus-13 spread.
  `HeatLockScaleSource` + `HeatLockUnitsPerLock` already derive the lock count from the character's
  own capacity - the same fix for the same problem, as a rule rather than a list.
- **`BaseSpawnMultiplier` / `MaxSpawnBonus`**, a base times a ramp. That is precisely the shape
  `GameplayHooks.SpawnMultiplier` replaced with `SpawnCountMultiplier` and
  `SpawnCountMultiplierAtFullLock`, so that the ceiling is a setting rather than an emergent
  product nobody wrote down. The fork's own `Custom` branch still carries the old `1 + 1.2 *
  progress`, so importing it would have been a regression.
- **`HealthRegenAtFullPressure`**, a floor on regeneration at maximum pressure.
  `ApplyHeatScaledAutoHeal` already scales by `(1 - heat)^2` and locks raise the heat floor, so
  regeneration already falls away as pressure builds. A second lerp on lock progress would count
  the same pressure twice.

`MinotaurTeleport` and the fork's `SpinAiDiag` were left behind as well - debug travel and a
diagnostic dump, neither related to what was being integrated.

## 128. The port, reviewed — four things that do not survive this tree's layout

§127 brought roughly five thousand lines of custom-enemy code across on compile-correctness alone:
it built, `patchaudit` was clean, and the seams were hand-written and read. The bodies were not.
§127's own handoff said so, which is a note to a future session and not the same as having done it.
Reading them found four things that behave differently here, each of which could have shown up as
something other than what it was.

The general shape of all four: **imported code carries the assumptions of the tree it was written
in, and the assumptions this project makes are different.** Every one of them is fine where it came
from — a single install, no repo behind it, the gallery managed by hand — and none is a defect in
that setting. What follows is what each becomes once it is running here.

### The mod could destroy Definitions.csv

`UpsertDefinitions` ended in `File.WriteAllLines(csvPath, lines)` over the live gallery. That call
truncates the file the instant it opens the handle, so a crash, a full disk or an exception between
truncate and flush leaves a hundred-odd measured rows replaced by however much got written, with no
copy anywhere. The gallery is the thing this whole project is, so that is not a trade this tree
can take, whatever it saves in lines.

It now writes a sibling temp file and moves it into place, so the real file is only ever replaced
by a complete one, and takes a one-time `.pre-custom-enemies` copy before the first modification.
`File.Replace` is deliberately not used: it requires both paths on one volume and throws where the
game directory is a symlink onto another, which is exactly this repo's layout (§62).

### A package could silently repoint a real gallery row

A manifest naming a row that `Definitions.csv` already defined was treated as an *update* — the
existing line was overwritten. A package shipping a scene called `imp_grab_loop` would therefore
retarget that row at its own funscript for the life of the install, and the only symptom would be
the imp playing the wrong curve.

The fix needed an ownership test that survives a restart, because the obvious one does not: "rows
this run added" is empty on every launch after the first, so a package author editing their manifest
could never update their own row. Ownership is read off the file instead — **a row whose `FileName`
column names a funscript this package ships is this package's row**, whoever wrote it and whenever.
Everything else is refused, loudly, and that scene simply does not play. The same rule covers the
funscript files: a package script that would replace a *different* file of the same name is skipped.

### The mod and deploy.py were fighting over the gallery

`SyncFunscripts` copies into the **deployed** `Edi/Gallery`, which is `deploy.py`'s output. So after
one launch with a package installed: the game-side tree differs from the payload, `deploy.py
--check` reports both installs stale, the next deploy's `prune_gallery` deletes the package's
scripts as "no longer in the working tree", and the mod puts them straight back on the next launch.

Nothing breaks. What breaks is the *check* — permanently, and in the direction that trains you to
ignore it. `deploy.py --check` is the answer to "is what I am about to launch actually the working
tree", and the ninth session had already been caught once by a second writer to a deployed file
(the game rewriting its own `com.edi.pnc.cfg` at launch). A false stale that never clears is worse
than no check at all.

So the same result is assembled on **this** side instead. `release.custom_enemy_gallery` reads the
same manifests with real JSON, resolves each scene's row and each variant's funscripts, and
`definitions_with` merges them onto the repo's `Definitions.csv`; both land in the payload like
everything else. `prune_gallery` then sees the package scripts and leaves them, and `--check` is
honest and idempotent again — verified at 103 repo rows + 16 package rows = 119 deployed.

The runtime writer stays, because it is the only path for a player who drops a package into a game
install with no repo behind it. On a machine with this repo it now finds its rows already correct
and does nothing. That leaves two implementations of one rule, which is normally exactly what §124
says not to do — the difference is that these two have different callers and a way to notice
disagreement: if `deploy --check` starts reporting stale after a launch, the two have drifted, and
that is a specific, cheap signal rather than a silent divergence.

### A paused game kept playing

The wall trap and the runtime sprite visual are clocked on `unscaledDeltaTime`. That is deliberate
and correct on its own terms — a grab overlay has to keep animating through whatever the game does
to `timeScale` during a grab. But `Update` runs at `timeScale` zero, so behind the pause menu the
trap armed, pulled the player, captured them, and advanced animation stages **each of which POSTs a
row to Edi**.

That is the pause/resume desync of §104-§106 arriving from a direction those did not cover: they
were about Edi's own seek behaviour across a pause, and this is the mod dispatching new rows while
the player believes the game is stopped. §127 also added a second way in without noticing — the mod
manager holds `Time.timeScale` at zero for as long as its window is open, so editing a setting near
a wall trap was enough.

`PauseHooks.SceneClockHeld` is the one predicate for both, and the three clocks consult it. It is
deliberately *not* "use `Time.deltaTime` instead": that would also freeze these scenes during a
grab, which is the case the unscaled clock exists for. The question being asked is "is the game
logically stopped", and only the pause state and the manager can answer it.

### Five more, found and left alone

Recorded in `TODO.md` rather than changed, because none can lose data or corrupt state and each
would be a guess without a run behind it: `CustomGallerySection`'s static dictionaries are keyed by
Unity objects and never pruned; `InjectSpawner` rounds `spawnWeight` to whole prefab copies while
the shuffle pool uses the float, so one setting has two meanings; `CustomEnemyRuntimeData`'s comment
gives a reason for its own existence that is not the real one (the workaround is sound, the
explanation would mislead); `ResolvePending` instantiates a live scene enemy and only deactivates it
after `Awake` has run; and `RuntimeWav` rejects `WAVE_FORMAT_EXTENSIBLE`, which is a normal
container for the 16-bit PCM it accepts.

All four sat in files that had passed a build, a patch audit and a full `check.py` run, and none
of them is the kind of thing a check can see — a `WriteAllLines` is only a hazard once the file it
writes is the one this project is named after. What found them was opening the files.
`learnings/working-practice.md` carries both rules this earned: compiling is not reading, and a
project's checks cannot see the assumptions imported code brings with it.

## 129. §127 and §128 played, and what a log said that reading had not

The branch had never been launched. §128's review had read the ported code and fixed what reading
could find; §127's three features had been reasoned about and not once seen. The 2026-08-26 run put
all of them on screen, and the log of that run — `game-linux/BepInEx/LogOutput.log`, ten minutes,
1880 lines — answered more than the run itself did.

**Five of the six things on the handoff list worked on the first launch.** The mod manager opens on
F11 and on its cloned main-menu button; keyboard input stands down while its window is up; the
window and the game's own pause menu both hold the scene clock, so a wall trap cannot arm behind
them; profiles switch mid-run without god mode's health surviving the switch back; F9 spawns a
custom enemy from inside a run; and the witch's dream overlays play on Linux, which is the WebM
fallback of §127 confirmed. For a first launch of three features that is a better result than the
handoff expected.

The sixth did not work, and the log carried two more that nobody had reported.

### The pull that could never have pulled

F10 placed traps and they captured, but they never dragged anyone. The log says so plainly once you
know to read the pairs:

    [WallPictureTrap] pulling player into 'joker_wall' from 7.48m
    [WallPictureTrap] player escaped pull range for 'joker_wall'
    [WallPictureTrap] pulling player into 'joker_wall' from 7.50m

Engage, disengage, engage, at the radius boundary, with the distance never falling. Every capture in
the whole run happened at 1.28 m or 1.33 m — the player had walked in.

The cause is not in the trap. The player is `FirstPersonController : CMF.AdvancedWalkerController` —
Character Movement Fundamentals, an asset that does not simulate the player with forces at all. Its
`FixedUpdate` computes `velocity = movementVelocity + momentum` and hands it to `Mover.SetVelocity`,
which does `rig.linearVelocity = _velocity + groundAdjust`. **That is an assignment.** Anything
added to the Rigidbody between two physics steps — `AddForce`, an impulse, a velocity written
directly — is erased at the start of the next one before it has moved anybody. The trap was calling
`AddForce(pull, ForceMode.Acceleration)`, which is the correct call against a Rigidbody the engine
owns and a no-op against one this asset drives.

So the pull is applied on the far side of that assignment: `WallPictureTrapPull` postfixes
`Mover.SetVelocity` and adds each pulling trap's contribution immediately after CMF has written its
own answer. Same FixedUpdate, so nothing overwrites it; the next step recomputes CMF's half and this
adds its half again, so nothing accumulates either. The player keeps full control of everything
else, because the pull is a summand — walking away against a slower pull nets out as being dragged
while making headway.

Writing into the controller's `momentum` was the other candidate and is wrong here: momentum is what
CMF applies friction to, and this game's `groundFriction` is 100, so anything put there is gone
within a frame of touching the floor.

`pullStrength` keeps its authored meaning as an acceleration and is now integrated into a pull speed
rather than used as one, so the grab ramps instead of snapping. The ceiling is a new manifest field,
`maxPullSpeed`, defaulting to 5: **the player walks at 7**, so that is the number deciding whether a
trap can be escaped on foot, and it wanted to be a number a package author sets rather than an
emergent product of an acceleration curve. Every path that ends a pull now goes through one
`StopPulling`, which matters more than it looks — the pull persists until something clears it, and
two early returns previously only skipped a frame, which would have left an invisible drag on the
player for as long as the condition held.

### The gallery drift §128 predicted, and the reason for it

§128's handoff warned that `deploy.py --check` reporting stale after a launch would mean the two
row-building rules had drifted. It did, and they had:

    > joker_wall_massage,joker_wall_massage,0,520,gallery,true
    > joker_wall_cum,joker_wall_cum,0,1040,gallery,true

`release.custom_enemy_gallery` accepted `wall-trap.json` and then read `manifest["scenes"]` — but a
wall trap keeps its scenes under `animations`. The repo side therefore emitted **no rows at all** for
a trap package, leaving the runtime writer as the only source of them, and the two undid each other
on every launch. A permanent false "stale", which is exactly what that function's own docstring was
written to prevent.

Fixing the missing rows was three lines. What the fix uncovered was that the wall-trap registry had
its own private copy of the whole CSV merge, and the copy had drifted in three more ways:

- **no ownership rule.** It overwrote any row whose name matched, where the enemy writer refuses and
  warns — so a package could silently retarget a measured gallery row at its own funscript.
- **a bare `File.WriteAllLines`** over `Definitions.csv`, the truncate hazard `WriteDefinitions` and
  its backup-and-move exist to prevent, on a 120-row file.
- **no funscript content guard.** It copied over an installed script of the same name unconditionally
  where the enemy path compares content first and keeps the existing one.

Both package kinds now go through `CustomEnemyRegistry.MergeDefinitions` and share
`SameFileContent`. One writer, one rule, so a third package kind cannot reintroduce any of it.

`WriteDefinitions` also preserves the file's byte-order mark now. `File.ReadAllLines` strips a BOM
on the way in, so every write was silently changing the first three bytes of a file `--check`
compares byte for byte — a false "stale" earned by touching nothing that matters, and the same bug
class as the one above wearing different clothes.

### The format documentation, imported and re-checked against this tree

Four Markdown files came with the fork that this tree had never taken, and
`BepInEx/custom-enemies/README.md` had been pointing at one of them — `../../CUSTOM-ENEMIES.md` —
since §127, at a path that did not exist. They now live beside the packages they describe, as
`BepInEx/custom-enemies/CUSTOM-ENEMIES.md` and `WALL-PICTURE-TRAPS.md`, which is what makes that
link real; `release.py` ships any Markdown in that directory, and `.gitignore` tracks it.

**Every claim in them was checked against this tree's code, and fourteen do not hold here.** Each
was accurate where it was written; the pattern is worth naming because it will repeat with anything
else imported: *documentation describes the tree it was written in, and says nothing about having
travelled.* The ones that would have cost the most:

- **`GAMEPLAY-PROFILES.md`'s balance section describes the fork's retune, which this tree does
  not have.** Its class table (Knight 6 … Ranger 9) is that fork's replacement for the 5/8/10/13/13
  that `HeatLockUnitsPerLock` still derives here — §127 declined the table and kept the rule, so the
  document describes a balance nothing here implements. Its wave figures (1.25x to 2.25x) are not
  `SpawnCountMultiplier`'s 1.0 to 2.5 either, and it cites a `Gameplay - Pressure and Release`
  config section that does not exist in this tree at all.
- **`spawnWeight` documented as one rule when it is two** — §128 found this and left it; the
  documentation now states both paths and which one is live by default, which was the missing half
  of that note.
- **F10's range is 35 m here, not the documented 25**, and it destroys *every* trap of that
  package in the scene rather than "only the current instance". This tree's own config description
  said 25 m too, so both ends needed correcting.
- **"The first enabled trap is automatically placed"** — it is every enabled `autoPlace` package, up
  to `spawnCount`, and the roaming placer that actually puts most traps in a level was undocumented
  in its entirety.
- **A `SpinningEnemyAI` diagnostic on F12** that §111 deleted from this tree, a Unity installer
  script and a validator script that are not part of it, and a `maxHealth: 600` example against a
  package that ships 60.

`DEVELOPMENT.md` was not imported. It documents its own workspace — `src\PncEdi\`,
`scripts\build.ps1`, `verify.ps1`, a 2.6.0 version — which is a different repository's layout, and
`code/README.md` already covers that ground for this one. Shipping a description of another tree
would have been worse than the dangling link it replaced.

The player-facing half went into the shipped `PncEdi-README.txt`, which had never mentioned the mod
manager, gameplay profiles or custom enemies — it predates all three. `_example` gained a
`wall-trap.json.example`, and its `enemy.json.example` lost `"spawnWeight": 0.5` — a value that
does nothing on this tree's default settings, so as an example it taught the two-meanings confusion
the rest of this entry is about.

### Two the log found and this entry did not fix

Left open deliberately, in `TODO.md`, both with a named mechanism rather than a symptom:

- **An enemy re-grabbing on a half-second cycle.** Eight `[AI-GUARD] unstuck ... state=Grabbing with
  no coroutine` lines on the custom witch, in bursts after another enemy's scene ended.
  `ClearStaleCoroutineHandles` calls `StopGrab` with no `IsGrabbing` guard, justified by a comment
  that only holds when the object was actually deactivated — and `Reactivate` calls `SetActive(true)`
  unconditionally, so the autofix path reaches enemies that were never hidden. On one of those,
  killing a live `GrabSequence` strands `currentState` in `Grabbing` and only the watchdog recovers
  it, 0.5 s later, into an immediate retry. That is §78's strand, in the one place §78's own fix was
  not applied.
- **A trap capture is also processed as a vanilla enemy grab**, because `BeginCapture` goes through
  `GrabScreen.StartGrab`. The grab hook resolves the borrowed BlackSerpent animator, asks Edi for
  `joker_blackserpent_grabscreen`, and fills the trap's grab screen with goonshroom audio over its
  own capture clip. The Edi half is harmless only by luck: the row does not exist, so the `EDI-SKIP`
  is what stops it fighting the trap's own `Play`.

## 130. The re-grab loop, measured rather than reasoned about — and three package decisions

§129's handoff named a suspect for the half-second re-grab cycle: `ClearStaleCoroutineHandles`
calling `StopGrab` with no `IsGrabbing` guard, on the ENEMY-AUTOFIX path that reaches enemies which
were never deactivated. It was a mechanism, not a diagnosis, and the handoff said so: instrument it
first, one guard if confirmed.

**It was wrong, and one run's worth of instrumentation said so in a line.** A `GRAB-STRAND` log at
that call site, printing `activeInHierarchy` / `enabled` / the handle / the state, fired 49 times
across a run — and reported `grabbing=False` on every single one. That method has never produced
§78's strand and the guard would have fired zero times. Two things it did establish: every one of
the 49 ran on a *live* object, so the comment claiming a deactivation had made the handles stale
was false; and three of them tore down a genuinely live `grabCoroutine`, belonging to the enemy
whose own scene had just ended. Nothing was observed from those three, so the code stands and the
comment now says what was measured instead of what was assumed.

**The strand comes from the transition, not the teardown.** At `17:05:21.945` the witch logs a null
handle and a state that is not `Grabbing`; 1.7 s later she is `state=Grabbing with no coroutine`.
`AiStateGuard`'s own header already documented why: `TransitionToGrabbing` commits
`currentState = Grabbing` and *then* calls `StartGrab`, which early-outs on `!canGrab` — and
`CharmWitchController` sets `canGrab = false`, because a movement-only package borrows the base
enemy for pathing and holds every attack shut. `SpinningEnemyAI` has no case for `Grabbing` in
`UpdateStateMachine`, so nothing could leave it; the watchdog put her back in `Idle` 0.5 s later,
grab range transitioned her straight back, and that cycle is the visible lunging. Twenty unsticks in
one run, all the same enemy, in unbroken 0.5 s trains.

`GrabTransitionGate` declines the transition when the call meant to drive it is already certain to
decline — `canGrab` false, or no `grabScreen`. Both are readable before the commit; nothing about
the transition can change either. The state stays `Idle` or `Spinning`, which the switch handles.
Watching the invariant is still right for the general case (four routes in, and `AiStateGuard`'s
header explains why); this is the one case that is decidable in advance. Confirmed in the next run:
one `refused Grabbing`, zero `unstuck`.

### Three package decisions, from the same run

- **The witch's aura granted a full heat lock every 7 s of standing in it**, with no scene on
  screen. A lock is what the game charges for a scene it has shown, so this spent the run's health
  budget through a mechanism the player never saw. `lockIntervalSeconds: 0` now means heat-only, and
  that is what she ships with: pressure while you stand in the circle, which cools when you leave.
- **`spawnWeight` below 1 could not do anything**, which is §128's open note becoming a real
  complaint. `InjectSpawner` did `Clamp(RoundToInt(weight), 1, 10)`, so the witch's authored `0.2`
  rounded to 0, clamped back to 1, and put a boss in every room's table on the same footing as a
  zombie. `EnemySpawner.GetEnemyPrefab` picks uniformly and vanilla weights by repeating an entry,
  so the fix uses that idiom: scale the whole table until the fraction is expressible, leave it
  exactly as authored when nothing asks for one.
- **Each package now carries its own spawn weight in config**, `<id> spawn weight` beside its own
  on/off switch, defaulting to the manifest. A central map was written first and replaced: retuning
  how often something spawns is a player's decision, and a package is usually third-party content
  nobody should have to edit. It covers both spawn paths because both read one property.

### Considered and reverted inside the session

- **Retuning the wall trap's pull** (`pullStrength` 52 → 4, an explicit `maxPullSpeed` 1.5), plus
  hysteresis at the pull radius, ending the pull when the player is out of the front arc or behind
  cover, and the trap's instance id in its log lines. All four reverted by decision: the trap is
  to be left as it stands. The observation that produced them is still true and is recorded in
  TODO — the arc/line-of-sight check `return`s without clearing `_pulling`, and since §129 the pull
  is applied from a `Mover.SetVelocity` postfix, so it keeps dragging while that condition holds.
- **Making the witch's chase blink land inside `captureDistance`.** Built, then reverted: she is a
  summoner and the blink is an escape. Worth recording what it found, because it is not a bug -
  the chase blink searches ground between 2.34 m and 4.68 m while the capture fires at 1.2 m, so
  **her capture scene and its five dream videos are unreachable in normal play** unless the player
  walks into her. Two runs never saw her closer than 3.3 m.

## 131. The custom-enemy framework becomes its own plugin

Four and a half thousand lines of package loading, sprite animation, gallery section and two shipped
behaviours moved out of `PncEdi` into `PncCustomEnemies`, a third BepInEx plugin. The mod that talks
to a device and the mod that loads other people's enemies are now separable: delete the DLL and what
remains behaves as though packages never existed.

**The dependency runs one way and could not run the other.** A package's scenes *are* Edi content -
it registers gallery rows and aliases, plays rows, takes heat locks - so this plugin references
PncEdi and declares `[BepInDependency]` on it, which is also the load order the framework needs.
What was removed is the reverse: PncEdi now names no type of that assembly. Nine call sites did,
across six files, and every one of them went through `CustomEnemyBridge` - delegates the plugin
installs in its own `Awake`, each with a vanilla answer for "nothing installed them". The pattern
was already in the tree: `NameRemap.CustomEnemyResolver` has been exactly this since §127, for the
same reason.

**`InternalsVisibleTo` is what kept it cheap.** The alternative was promoting something like fifteen
members to public API - `Plugin.Log`, `SendPlay`, `GoFiller`, the registries, `HeatLockSystem` - and
a public surface invites binding. The moved code goes on using the same `internal` members it always
did. PncModManager deliberately gets no such grant: it configures whatever plugins are loaded and
knows nothing about any of them (§127).

`PncEdi.csproj` still builds everything, by two different mechanisms for two different reasons: a
`ProjectReference` with `ReferenceOutputAssembly=false` for the mod manager, which references
nothing here, and a `BuildCustomEnemies` MSBuild task for this one, because a ProjectReference in
this direction would be a cycle. Running it after `DeployPlugin` also means it compiles against the
`PncEdi.dll` just built. `release.py` builds each plugin into its own scratch directory, so the
reference path is a property (`PncEdiRefPath`) rather than the deploy directory, and the release
passes the freshly built one.

The plugin owns its settings: `com.edi.pnc.customenemies.cfg` carries the spawn hotkeys and every
package's on/off switch and spawn weight. `Tools / EnableDebugEnemySpawn` stays with the core mod -
one gate for every debug spawn key in the install is the point of it. `patchaudit.py` audits both
source trees and both registration lists, which is how the split is kept honest: a patch class in
the new tree that nobody registered fails the same check it always did.

## 132. The plugin boundary, and the check that keeps it honest

§131 split the mod into three plugins so they could move independently. That is only true if
changing one cannot silently break another, so this is where each one's responsibilities are
written down and where the gap in the enforcement got closed.

    PncEdi            the device integration and the gameplay rules. Owns the Edi channel, the
                      gallery registry and aliases, heat and locks, and every patch that shapes
                      vanilla combat. References neither of the others.
    PncCustomEnemies  package loading from BepInEx/custom-enemies/, sprite animation, the custom
                      gallery section, and the two behaviours that ship with it. References
                      PncEdi, because a package's scenes are Edi content.
    PncModManager     the in-game settings window. Edits whatever plugins are loaded, so it
                      references nothing and nothing references it (§127).

Most ways of breaking that boundary are already loud, and that is the point of how §131 split it.
The plugin is compiled by the same `dotnet build code/edimod/PncEdi.csproj` that builds the mod, so
renaming or deleting anything it uses is a build error in the same command rather than a discovery
weeks later.
`patchaudit.py` reads both source trees and both registration lists, so a game-side rename is caught
for both assemblies at once.

**One way was silent.** Every question PncEdi asks about packages goes through a delegate on
`CustomEnemyBridge`, and every delegate answers "vanilla" when nothing installed it - deliberately,
since that is what lets a player delete `PncCustomEnemies.dll` and keep a working mod. The
consequence is that dropping the *call* is invisible: a rewritten `GoFiller` that stops consulting
`EdiChannelHeld`, a tidied `SceneEscapeGate` that stops asking for a package's own scene length. It
compiles, every test passes, and the framework degrades into exactly the shape a missing DLL has -
so nobody would learn of it until a play session, and the report would be "the custom enemies are
behaving oddly", which is the expensive kind of bug.

`code/bridgeaudit.py` closes that: each delegate must be installed by the plugin and asked by the
mod, and a seam that has lost either end is named. It is a fast gate in `check.py`, and it was
checked by mutation - removing both readers of `EdiChannelHeld` fails it with the right sentence.
**Treat a `CustomEnemyBridge` call in PncEdi as load-bearing even though deleting it looks
harmless.**

Also fixed, from the run that confirmed §131: **`InjectSpawner` was injecting into spawners with no
authored enemies of their own.** Two of the twenty in that run reported `1 of 1 table entries (100%
per roll)`. An empty table is a room author saying nothing spawns here, so adding a package does not
season a mix - it makes that spawner a package-only spawner. Skipped now. This predates §130 and is
a good part of what "the spawn rate seems way too high" was.

**Not a defect, recorded so it is not re-investigated:** the goonshroom re-grappling the instant it
is shaken off is vanilla. §114 gave grappler lifecycle back to the game, and vanilla's
`ReleaseGrappler` → `ChargingEnemyAI.ThrowAfterGrapple` re-enables the enemy, clears its flags, sets
`currentState = Idle` and throws it a short way - so it lands beside the player as a live grappler
with nothing holding it off. The cadence is identical in the 2026-08-26 02:24 log, which predates
every change in §130 and §131. What made it visible was the witch: her boss pressure spawns
goonshroom reinforcements next to the player. A shake-off stand-down, shaped like
`EndGrabEnemyCooldownSeconds`, is the fix if it is ever wanted; it was not built, because it is a
gameplay change rather than a repair.

## 133. The learnings index gets a step that can be seen

`learnings/` is eleven files of rules this project paid for, and `CLAUDE.md` has asked every session
to "open the index before anything non-obvious" since it existed. Asked, and been ignored - this
session included. §130 worked out that committing a coroutine-driven state before its coroutine is
running is a latent hang by reading `AiStateGuard`'s header comment, when
`learnings/grab-and-ai-mechanics.md` had carried exactly that rule since §46. The same session
re-derived the CMF velocity-assignment trap from `WallPictureTrapPull`'s docstring, which
`unity-runtime.md` lists in its keywords.

Both times the source comment saved it, which is why this has cost little so far and is not a safe
place to stay: this tree is commented unusually well at those two spots, and the rules that live in
*no* single source file - most of what `learnings/` holds - have no such backstop.

The wording was the problem. "Open the index before anything non-obvious" is advice, and advice
loses to whichever file visibly contains the answer. `CLAUDE.md` now asks for something checkable
instead: **grep `learnings/` for the symptom or the identifier, and say in the reply what came back,
including when nothing did.** Both halves matter. A step that appears in the reply can be checked by
whoever reads it; a silent one is indistinguishable from a skipped one, because the answer looks the
same either way.

That is the same rule this project keeps arriving at from different directions - §96's
missing-definitions log, §109's patch registry, §132's bridge audit. **When the failure mode is
silence, the fix is to make something say a sentence.** It applies to documentation habits as much
as to code.

### The hole that first draft left, found by asking "so when is the index read now?"

A grep rule serves symptom-first lookup and silently retires the index, which serves the other
question: you are picking up an *area* and have no symptom to search for yet. That is what
"the ones that have cost the most time" is for, and no `grep` can produce it. Both entry points are
now written down as serving different questions rather than one replacing the other.

It also made the **keywords column load-bearing**. That column is the only part of the index
written in the vocabulary people grep with, which is what makes the index itself a first hit:
`grep -ril "SetActive" learnings/` finds `README.md`, `grep -ril "grabCoroutine"` does not. So
adding a claim now means adding its identifiers to its row - a claim whose words never reach that
column is findable only by someone who already knew which file to open, which is exactly the person
who did not need an index. The claims §130-§133 added were backfilled into three rows on the spot,
since the rule was one paragraph old and already being broken.

## 134. A package's capture stops being processed as an enemy grab

Both behaviours that ship with the custom-enemy framework capture the player the same way: they call
vanilla's `GrabScreen.StartGrab(gameObject, null, ...)` and hand it their own GameObject as the
"enemy". From `PncEdi`'s side that is indistinguishable from a goonshroom grabbing you, so the whole
grab pipeline ran on it — and every step of that pipeline is wrong for a scene the package owns.

The 2026-08-26 log had been saying so for three sessions. Every wall-trap capture logged:

    [GRAB-AUDIO] 'Joker' authored no grab-screen sounds - filled 4: GoonShroom_GrabscreenStart...
    [GRAB-ANIM] controller='BlackSerpent GrabScreen' clip='BlackSerpent GrabScreen' t=123.74
    [GRAB-INIT] joker/BlackSerpent GrabScreen -> joker_blackserpent_grabscreen
    [ALIAS-GAP] no mapping for 'joker_blackserpent_grabscreen'
    [EDI-SKIP]  joker_blackserpent_grabscreen (no such row in the gallery registry)

Three separate defects in five lines. **The name is an accident**: `joker` off the trap, and the
animator state off *whichever enemy was grabbed last*, because nobody swaps the grab-screen
controller for a package. It was harmless only because that name matches no row — `EDI-SKIP` is what
stopped it fighting the trap's own `Play joker_wall_massage`, 13 ms later. Adding the alias, which is
what `ALIAS-GAP` asks for, would have started a race for the channel; and the slug is not even stable
between captures, so there was nothing to add it *to*. **The audio fill** then wrote four goonshroom
and imp gangbang clips over the trap's own `joker_wall_capture`, giving the scene two soundtracks —
§124's fill doing exactly its job on an empty `grabScreenAnimations` that was never vanilla's asset
gap. **The heat lock** was the third, and it stays: a capture is an erotic scene and holds heat like
one, which is also what keeps the filler off the channel for its length.

The fourth item on that list turned out not to exist. The old handoff said a capture "takes the
−40 HP scene penalty", and it does not: `ApplySceneEntryPenalty` is gated on `IsFullLockDangerActive`,
so it fires at full lock and not per grab, and no `scene penalty` line appears anywhere near the
captures in that log. The 11% damage reading that seemed to confirm it was `1 - health/maxHealth` —
the player's standing HP, printed only when a `FILLER` line happens to fire — with a whole Gooper
fight between it and the previous sample.

### The seam already existed

`CustomEnemyBridge` gained a seventh delegate, `GrabSceneOwnerTest`, installed for both
`WallPictureTrap` and `CharmWitchController` and false when the plugin is not loaded. `PncEdi` asks it
in two places: `GrabHooks.StartGrab_Postfix` clears its live grab state and returns, and
`GrabScreenAudioFill` declines to fill. Clearing rather than merely returning matters — the per-frame
`STEP` poll in `Plugin.Update` dispatches off `CurrentAnimator`, so leaving a stale one behind would
have moved the defect rather than fixed it.

Nothing new was needed to keep that honest. `bridgeaudit.py` (§132) covers every field on the bridge
by construction, and it was checked the way this project checks a new test: both call sites were
replaced with `if (false)`, and it reported `GrabSceneOwnerTest is installed but nothing in PncEdi
asks it` and exited 1.

### Two things only a run could answer, and the instruments that answered them

**The witch's capture had never once fired.** §130 left it as "unreachable in normal play" on the
strength of blink distances. The gate is a horizontal distance against `captureDistance`, but whether
the player can physically get that close is a question about two colliders, and the only distances any
log carried were `DIAG-SPRITE`'s 3D ones. So the controller now reports its closest approach whenever
it improves by 10 cm:

    [CharmWitch] 'femboy_witch' closest approach 1.32m (capture at 1.20m)

Monotonic descent, stopping dead at 1.32 m across a whole run of trying. Twelve centimetres short, and
not by chance — that is where the colliders meet. `captureDistance` went to 1.8 in her manifest, a
data change needing no rebuild, and she captured on the next run.

**"Spells stop working at max heat"** was reported against a run with no instrumentation in it, and
the source alone cannot settle it. Vanilla disarms the player through one latch: `hasBeenOverheated`,
set the moment heat crosses `MaxHeat`, cleared only at *exactly* zero — and every heat-costing weapon
is gated on it through `CanAttackNow()` in `DualWieldingSystem.PerformAttack`. A lock floor makes zero
unreachable, which is why `ClearOverheatAtFloor` exists; but it clears through vanilla's
`ClearOverheatIfBelowMax`, which refuses while heat is above `MaxHeat`, and at full lock the floor sits
one point under the cap. Plausible, and only plausible. `HEAT-TRACE` could not adjudicate it because it
only runs *during a grab*, which is exactly when nobody is casting.

So `[OVERHEAT]` was added: `hasBeenOverheated`, `CanAttackNow()`, heat, floor and locks, logged on
change only. Two runs of it show the latch flapping at full lock — `275.2 → True`, `272.7 → False`,
over and over — and **clearing every single time**. The mechanism is real, the failure is not
reproducing, and the instrument is cheap enough to leave in until it does.

### A fix that was written from a measurement and reverted from a report

The first `[OVERHEAT]` run measured 51% of five minutes with attacks blocked, and that number bought a
fix: clear the latch outright at full lock, since a floor one point under the cap means vanilla's
"cool all the way down" can never be served. It was wrong, and what made it wrong is that the same run
had behaved fine from the chair. 51% is not a defect reading — it is what riding the cap looks like,
overheat and cool and overheat again, working as designed. The fix would have deleted the overheat
punishment from full lock on the strength of a number nobody had complained about. Reverted the same
session; the instrument that produced the number stays.

**And the number is narrower than it reads.** That run was a femboy-witch one, and her aura is what
pinned heat at the lock floor for half of it; ordinary play does not sit there. So 51% is not a
baseline for anything — it is one custom enemy's pressure, measured once. Recorded in §136's session,
after the figure was nearly reused as evidence that vanilla's attack-locked branch is the common
case. It is not.

**A measurement is evidence about a mechanism, not permission to change it.** The report is what says
something is broken, and this one said the opposite.

### The vanilla art underneath

With the naming and the audio fixed, the witch's capture came back with a second finding: her dream
video plays over a 76%-alpha backdrop, and the Black Serpent's grab scene was visible through the
remaining quarter — `cum cooldown ... (animator in 'BlackSerpent GrabScreen_Cum')` in the log, under
her video on screen. Same root cause as the nonsense slug: `ShowGrabUI` switches on `grabImage`, the
object the grab-screen animator draws into, and nobody swaps the controller for a package. The wall
trap never showed it because its overlay is opaque.

`PackageGrabArt.Hide` switches that object off at capture. It lives in `PncCustomEnemies`, not on the
bridge: a package driving vanilla's screen is the package's own presentation problem, and the plugin
already touches `GrabScreen` directly for `StartGrab` and `StruggleButton`.

**Its first draft also restored the art at the end, and that was a bug worth recording.** A capture
ends by calling `EndGrab`, which runs `HideGrabUI` and switches the art off; the package's teardown
runs *after* that, so the restore switched it straight back on with no grab left to contain it — the
serpent scene stayed on screen with the player free to walk around behind it, until the next grab
replaced it. There was nothing to restore in the first place: vanilla owns that field in both
directions. The file says so, so that nobody re-adds a restore that looks like tidiness.

## 135. Custom enemies get a distribution: text in git, media as its own download

`TODO.md` §6c had been open for three sessions as one question — what happens to the two packages
before the repo goes public — and it was one question only because the untracked set had never been
looked at closely. Measured, it is three things with nothing in common:

| | size | licence question | reproducible |
|---|---|---|---|
| third-party art and audio | 53 MB | **yes, the real one** | no, someone else's work |
| our funscripts | 1.0 MB, 36 files | none | only by re-measuring |
| manifests and `SOURCE.txt` | 6.8 KB, 4 files | narrow | no, hand-tuned |

One `.gitignore` line, `BepInEx/custom-enemies/*`, was throwing away all three. The middle row is
the finding: `femboy-witch/funscripts/detailed/` and `handy1/` are the same product as
`Edi/Gallery/detailed/`, authored and measured by this project the same way, and no third-party
licence touches them. They were being discarded as collateral of a rule aimed at the video beside
them. `SOURCE.txt` was the second oddity — a file whose whole purpose is attribution, existing on
one machine.

The manifests are the tuning problem §134 walked into without naming it: the witch's
`captureDistance` moved from 1.2 to 1.8 on a measurement, and that number lived in the changelog and
in two game installs and in no tracked file. They are mostly game-side values — `maxHealth`,
`detectionRange`, pivot, scale, `spawnWeight` — with a thin artist-derived layer of filenames and
atlas geometry, which is metadata *about* the art rather than the art.

**What was decided.** The forum this will be posted to is Eroscripts, where redistributing credited
gallery art with a script is ordinary practice, so the objection to shipping the media *to players*
was never the live one. It does not transfer to GitHub: a repo's history is permanent, so 53 MB
would sit in every future clone forever and a takedown would mean rewriting history rather than
deleting a file. The forum post is revisable; git history is not. So the media ships to players and
stays out of git, which sounds contradictory and is not — they are different stores with different
failure modes.

- **`.gitignore` is now deny-by-default under a package**, naming the three kinds of text back in.
  A media format nobody has thought of yet is ignored without anyone remembering to ignore it.
  40 files, 1.0 MB, no media.
- **`release.py --package <name>`** (or `all`) builds one archive per package, extracted over the
  game directory like the release itself, with a generated README carrying the package's own
  credits. The main archive stays framework-and-templates: ~89 MB rather than ~142 MB, and a player
  opts into explicit third-party content instead of receiving it. The mode is thin because
  `custom_enemy_files(packages=True)` already existed for `deploy.py` — the release had simply
  never called it.
- **The format docs point at the downloads.** `CUSTOM-ENEMIES.md` gained a "Getting a package"
  section: the two real packages are named as the worked examples the document describes, and a
  clone is told it has a package's text with no media beside it.

**Three guards, because a player cannot run this repo's checks.** No `SOURCE.txt`, no archive — a
package that ships someone's art ships its credits. An MP4 with no WebM beside it fails the build,
the same rule `webmify.py --check` applies to the working tree. And the H.264 masters are not
shipped at all:

**`PackageVideo.ResolvePath` tries the `.webm` sibling first and unconditionally**, before its own
`NeedsWebm` platform test — so once a WebM exists, the MP4 beside it is never opened on *any*
platform, Windows included. The Linux branch below it is only reachable when no sibling is there.
In the witch's package that was 35 MB of a 51 MB download that nothing would ever read. Dropping
them took that archive from **52.6 MB to 16.8 MB**. The MP4-without-WebM guard is what makes it
safe: no master is dropped unless its replacement is present. The masters stay in the working tree.

**Unnamed files are reported, not dropped.** A package directory is also a working directory, and
the build now lists what the manifest never names. It does not exclude them, because absence from a
manifest does not prove disuse — the WebM itself is found by sibling convention, so "ship only what
is named" would drop exactly the file Linux needs.

That report found nine, and reading them is the reason only one was deleted:

- `portrait-before-dark-edges.png` is **byte-identical to `portrait.png`** (same SHA-256), a
  duplicate under a working name. Deleted; it lost nothing.
- `portrait.png` is the undarkened original of the wired `portrait-dark.png` — a source, not a
  duplicate. Kept.
- `loop.png`, `intense.png`, `aftermath.png` (972×1674) and `climax.png` (2592×3348) do not divide
  by the 384×408 cell the wired sheets use, so they are a superseded generation. Kept: superseded
  is not the same claim as dead, and the media is untracked, so a deletion here has no undo.
- **`start-v2.png` is 1536×816 — exactly 4×2 of 384×408, the same geometry as the wired
  `cum-v2.png`.** It is not leftovers: it is an authored stage of the current generation that the
  manifest simply never lists, and `SOURCE.txt` records post 16185689 under the role "start".
  Deleting it would have thrown away a ready stage. Recorded, not acted on.
- the two MP3s are the sources their WAVs were converted from, and `SOURCE.txt` carries the pages
  they came from. Kept.

The lesson is the one the report was built around: a file's absence from a manifest says where to
look, not what to do.

## 136. The port to game 0.3.2, where vanilla had already fixed one of our open items

Game 0.3.2 landed on 2026-08-25 and this is the port, done on branch `port-0.3.2` against the
procedure in `learnings/porting-a-new-game-version.md`. Nothing in it has been played yet.

**The installs were unpacked and both were incomplete.** `PNC 0.3.2 WIN` was missing
`sharedassets0-3` and `UnityPlayer.dll`; `PNC 0.3.2 Linux` was missing `sharedassets1-3` and
`UnityPlayer.so`. Neither would have launched, and the interesting part is what that would have
looked like from inside the audits: `patchaudit` reads `Managed/Assembly-CSharp.dll`, which was
present and complete in both, so every static check would have come back clean about a game that
could not start. The zips in `../game-builds/` were intact — 234 files, 2.35 GB — and re-extracting
fixed it. **Verify an install against its archive by size, not by existence**, before believing any
audit run against it:

    unzip -l "<the>.zip" | ... | while read sz f; do [ "$(stat -c%s "$f")" = "$sz" ] || echo "$f"; done

**Step 1 came back clean, both halves.** `patchaudit.py` was run against 0.3.1 first, as the
learnings file insists, and reproduced the §46 AI audit exactly; then against 0.3.2, where all 170
Harmony patches, 30 `AccessTools` reflections, 10 bare `typeof()` reflections and 96 untyped
`Traverse` members still resolve. 558 types parsed on both builds. Nothing the mod names was
removed or renamed — every difference on the 37 types it touches is an addition.

**The member diff is a readable map of the patch notes**, which is the argument for running it
with `--compare` rather than alone:

| what changed | which patch-note line |
|---|---|
| `ChargingEnemyAI` gains `regrappleCooldown`, `shakeOffStunDuration`, `stunEndTime`, `lastGrappleReleaseTime`, and an `AIState.Stunned` | "Changed grapple enemy behavior" |
| `DualWieldingSystem` gains `UpdateAttackWatchdog`, `CheckSlotWatchdog`, `RecoverStuckAttack`, `attackWatchdogTimeout` | "Fixed an issue making weapons unable to swing" |
| `EnemyGalleryEntry.enemyHint` / `HasHint`, `DioramaGalleryUI.DisplayHint` / `hintText`, `PeekScenesUI` the same | "Added hints to all locked gallery entries" |
| `GrappleScreenobject.ConsumeByGrab` | "Fixed issue with sweeper grab cooldown timing" |

**Vanilla shipped §132's answer.** `TODO.md` item 3 recorded the goonshroom re-grappling the player
the instant it was shaken off, and §132 closed it as *not a defect* — the game had no cooldown there
and the mod was not causing it. 0.3.2 adds exactly that cooldown, and more of it than the report
asked for: being shaken off now sets `currentState = AIState.Stunned` for `shakeOffStunDuration`
(3 s), and `ShouldCharge()` refuses for `regrappleCooldown` from `lastGrappleReleaseTime` —
explicitly ahead of the `chargeCooldown` test and, per its own tooltip, never skipped for a
vulnerable player, "so escaping always buys the player a window". The item closes as fixed
upstream.

**The 0.3.1 mechanism, now that the fix names it.** `ShouldCharge` skipped the `chargeCooldown`
test entirely when `IsPlayerVulnerable` — which is just `playerStats.IsAttackLocked()` — and the
same flag also dropped the `minChargingDistance` requirement from the range test. So a zombie
thrown down beside an attack-locked player could charge from point-blank on the next frame, with
both of the gates that would normally have stopped it disabled by the one condition. That is a
sharper account than §132's "vanilla has no cooldown there", and it is the version worth
remembering: the instant re-grapple was not an absent rule but two rules suspended together for
exactly the player who could not answer them.

The new gate is per-instance. `lastGrappleReleaseTime` is stamped in that enemy's own
`ThrowAfterGrapple`, and `RemoveOneGrappler` releases exactly one grappler per successful shake, so
each shaken-off grappler starts its own window and every other one in the room is unaffected.

**Two numbers and one creature in this section were wrong, and §138 corrects them from the assets:**
the window is **4 s**, not 8 — 8 is what `ChargingEnemyAI` initialises the field to and every prefab
overrides it — and it is the **imps and the goonshroom**, never the zombie, which is a plain
`EnemyAI` in every build this project has run and cannot be grappled at all. It is also the cleanest case this project has of the §132 discipline paying: an
observation that was carefully *not* patched, because it was vanilla's, and the next release fixed
it in vanilla.

**One config now has less reach than its name claims.** `ZombieGrappleChargeRate` divides
`chargeCooldown` to make zombies re-engage faster. That still works for an ordinary charge and does
nothing at all for the window after an escape, because `regrappleCooldown` is tested first and our
tuning does not touch it. Whether the mod should scale it too is a gameplay decision, not a port
one, so it is left alone and written down in `TODO.md`. (**Also wrong**: §138 found the knob reaches
no enemy at all — `ApplyZombieGrappleTuning` wants a `ChargingEnemyAI` whose key is `zombie`, and no
such prefab exists.)

**`AiStateGuard` deliberately does not watch `Stunned`.** The guard exists for states
`UpdateStateMachine` has no case for, which can only be left by a coroutine finishing; `Stunned`
has a case, and leaves on a plain `Time.time >= stunEndTime`. Guarding it would cut short three
seconds of helplessness the game now grants on purpose. Two things made this cheap to be sure
about:

- `patchaudit --ai` reports `unhandled: ... Stunned` and flags it as needing a guard entry. That
  is a **heuristic false positive**: the check counts a branch as handled only if it calls
  `Handle*`, and Stunned's branch calls `TransitionToChasing`/`TransitionToIdle` directly. The same
  line has always over-reported `PreparingCharge` for the same reason, on 0.3.1 too — which is why
  the control run matters. Reading the decompiled method settled it in one pass.
- `StuckStates` is keyed by the **numeric** enum value, and 0.3.2 *appended* `Stunned` after `Dead`,
  so `PreparingCharge` and `Charging` are still 2 and 3. That is luck, and the mod does not rely on
  it: `EnemyAiAudit.AuditStateValues` asserts those names still sit at those numbers at startup, and
  it was written (§46) for precisely the build that would insert one instead. It passes on 0.3.2.

**The two remaining additions need nothing.** Vanilla's new attack watchdog has no counterpart in
this mod to fight — the `EnemyReactivation*` hooks on `DualWieldingSystem` are about waking enemies,
not about stuck swings — so the "weapons unable to swing" fix arrives unopposed. And the gallery
hint field is safe for custom enemies by accident of Unity: `EnemyGalleryEntry.enemyHint` has a
field initializer of `"Found in:"`, so a `ScriptableObject.CreateInstance` entry built by
`PncCustomEnemies` gets that value rather than null, and `HasHint()` — which tests for exactly that
string — returns false. No throw, and no hint drawn. Giving packages a real hint is a format
question, not a port one.

**The assets did not move.** `check.py --full` is 14/14 against 0.3.2: `animsweep` 93/93,
`gallerydiff` unchanged at 21 different-length rows all of which already have their own gallery row,
`refvideo` 37 s and clean, `slugharness` resolving every animator state. 0.3.2 touched no animation
this project scripts.

**The mod is 2.6.0 for this**, a minor bump with no feature in it. The number tracks the game
underneath rather than the mod's own surface: 2.5.15 is a build for 0.3.1 and 2.6.0 is a build for
0.3.2, and a patch bump would have said "same game, small fix" about an archive that will not run
against the game the last one was for. `plugin_version()` cross-checks all four declarations, so
the bump is two files.

**What the port actually changed in this tree**: the two symlinks, `GAME_VERSION` in `release.py`,
the version in `AssemblyInfo.cs` and `Plugin.cs`, the install paths in `PROJECT.md`,
`code/README.md`, `deploy.py`, `pncpaths.py` and `spawntables.py`, and the `AiStateGuard` comment.
No behaviour. Both installs are deployed and `check.py` is 9/9.

## 137. The documents put back inside their own boundaries

No code changed. `TODO.md` had grown from §70's 126 lines to **1207**, and almost none of it was
open work: closed items kept in place with a strikethrough and a "confirmed in play" note, a handoff
per session going back six of them, and a "standing guidance" section that had quietly become a
second copy of `learnings/`. It is now **195 lines** — open, pending-a-decision and
deferred-by-choice items, one handoff, nothing else.

Nothing was deleted before the copy was found, which is §70's own rule. Everything struck through in
the old file already had its `§n` entry; what was *not* a record of finished work but a rule with
nowhere else to live was moved first:

| what | where it went |
|---|---|
| the debug key row (ten enemies on ten digits, §111/§119) | `PROJECT.md`, a new "Debug keys" section — it is reference, not work |
| "do not clean out `Edi/_reference/source-scripts/`" | `code/README.md`, beside the line that says the originals are archived there |
| a stale-deploy failure is usually the *game* rewriting `com.edi.pnc.cfg` at launch | `learnings/working-practice.md` |
| `x == null` on a generic `T` does not resolve to `Object.op_Equality` | `learnings/unity-runtime.md` |

The same pass over `CHANGELOG.md`, which is the narrative record and not a place to state rules:
six sections that had generalised their session into a standing rule now point at the `learnings/`
file that carries it (§114's two, §116's generic-null hazard, §118's suite rules, §119's
every-route rule, §122's stale deploy, §128's "compiling is not reading"). The evidence stays in the
entry; the rule lives once.

**Why it regrew, which is the part worth keeping.** The habit is to record an outcome where the work
was written down — so a finished item leaves a strikethrough rather than a hole, and each session
adds a handoff above the last. Sixty-six sections of that is how 126 becomes 1207. The counter-rule
is in `learnings/working-practice.md`: closing an item means deleting it from `TODO.md` once the
`§n` entry exists, and a rule stated inside a 9,000-line narrative is invisible to the grep
`CLAUDE.md` asks every session to run.

`check.py` 9/9 throughout; nothing in the tree that a check can see was touched.

## 138. The 0.3.2 port played, and what the log said about §136

The first run of 2.6.0 on game 0.3.2 (2026-08-27, Linux, ~21 minutes, 6,508 lines). **The port is
confirmed**: `[AI-AUDIT] ok`, one `[AI-GUARD]` line all session and **zero `unstuck`**, so the guard
is not fighting 0.3.2's new `Stunned` state; `[INPUT] backend repaired -> NewInputSystem` is the
known BepInEx-probes-before-the-keyboard line; no `[KEYBIND]` complaint and no throw. Serpent ramp,
witch aura, grapple tiers, escape, grab pipeline, game over, spawn and heat locks all behaved.

What the log found was four things §136 had wrong or had never been asked, and none of them is
about 0.3.2.

### The zombie is not a grappler, and never was

§136 wrote up 0.3.2's re-grapple window as the answer to the goonshroom re-grapple and then
described it in terms of *zombies*, and the handoff built a whole test around shaking one off. The
run reported "no 8 s window noticeable", which is exactly right: a UnityPy pass over every AI
component in all three builds says

    0.3.2  Zombie_Enemy / _ALT1   EnemyAI          grappler=False
    0.3.2  Imp_Enemy x5           ChargingEnemyAI  grappler=True  regrapple=4.0 stun=3.0
    0.3.2  GoonShroom_Enemy       ChargingEnemyAI  grappler=True  regrapple=4.0 stun=3.0

and the same for 0.3.1 and 0.2.1. A zombie is a plain `EnemyAI`: it cannot charge, cannot be
grappled, and can never reach `regrappleCooldown`. **And the window is 4 s, not 8** — 8 is what
`ChargingEnemyAI` initialises the field to, and every prefab overrides it. Both corrections are
folded back into §136 and into `learnings/porting-a-new-game-version.md`, which gains the rule
underneath them: a decompile shows a field's *default*, the asset shows its *value*.

**`ZombieGrappleChargeRate` therefore reaches nothing at all.** `ApplyZombieGrappleTuning` is a
postfix on `ChargingEnemyAI.Start` that then requires `key == "zombie"` — an intersection that has
been empty in every build this project has run, so the setting has never done anything. Its
description said "Zombie (ChargingEnemyAI)", which states the contradiction out loud and is the
generalisable half: **a patch gated on both a component and a key is dead the moment those two stop
overlapping, and it logs nothing.** The description now says it is inert; whether the knob is
deleted or repointed at the clinging family is a gameplay decision and is left in `TODO.md`.

### A package's gallery rows were being invented rather than read

`[EDI-SKIP] joker_massage` and `joker_cum`, against a manifest that declares `joker_wall_massage`
and `joker_wall_cum` and a gameplay path that plays them correctly. `GalleryHooks` builds the
gallery-viewer slug from display name + animation label, because in the menu that is all it has —
everywhere else the mod resolves an animator state, which a package registers.

The manifest is the only thing that knows, so it is now asked, through a fifth
`CustomEnemyBridge` delegate — `GalleryRowResolver`, vanilla fallback = today's slug, which is what
the witch's four unscripted dream videos still get. `bridgeaudit.py` guards it like the others, and
gained something while proving it: it only recognised **expression-bodied** accessors, so a helper
written with a block body read as "installed but nothing asks it". A check that fails on how a
method is spelled is a check people learn to override.

### The goonshroom drawn over every custom gallery scene

Reported from the chair as the witch's video playing under a stray goonshroom animation. The log
carries **31 `Animator.GotoState: State could not be found`**, paired 1:1 with the `[GALLERY-STEP]`
lines, and the assets say the rest:

- **`EnemyGalleryUI.grabDisplayModel` is null in the shipped prefab**, so `CustomGallerySection`'s
  `grabModel.SetActive(false)` and its whole save/restore have never hidden anything;
- what actually draws is the `grabSceneAnimator`'s object, **`Grabbed Animation Player`**, which the
  mod never touched;
- a custom entry inherits its `grabAnimatorController` from its base enemy
  (`FindController(definition.Template, ...)`), vanilla assigns it and calls `Play("Dream 1")` on
  it, the state does not exist — hence the 31 warnings — and the animator sits on that controller's
  default state, on top of the package's own art.

The animator's object is now stood down and its controller nulled for as long as the overlay owns
the panel, and both are put back on exit. `grabAudioSource` rides on the same object, which is
correct: a package brings its own sound (§134). **One part is still inferred rather than read** —
whether disabling the panel background is what lets `Character Display` show through as a second
witch — so a `[CustomGallery] panel stack:` line now prints the panel's children in sibling order.
One run answers it.

### An instrument that could not answer its own question

The `[OVERHEAT]` trace prints only when the latch or the attack gate *changes*, and this session
read nineteen such windows — 53.1 s of a 21-minute run — as evidence that item 2b had finally
reproduced. It is not: those lines carry heat at the two edges of a window and nothing in between,
so a window that opens at `100.1/100.0` and closes fourteen seconds later at `97.5` says nothing
about whether heat stayed at the cap or climbed to 130 and came back. Riding the cap is what the
game does, and the report said so. **This is the same mistake as §134's 51% figure**, made
by the same instrument, one session after the note warning about it was written.

So the instrument changed rather than the note. The defect is one predicate — `hasBeenOverheated`
while heat is **below** `MaxHeat`, which vanilla cannot produce, because crossing below the cap is
exactly when its own clear runs — and it now prints once a second for as long as it holds, so a real
occurrence has a duration in the log rather than two edges to argue from. Item 2b stays open and
not-reproducing.

### Two log lines that were 21% of the log

780 `[GAMEOVER] cancel ... ignored` (once per frame while the panel is up) and 609 `[GRAB-START]
ignored: game declined the grab` (once per enemy attack cadence in range) — 1,389 of 6,508 lines,
both restating one fact. `Plugin.DBGRepeat` logs the first, counts identical repeats and flushes
`...the line above repeated N more time(s)` when the message changes, with an explicit
`DBGRepeatEnd` at the real grab so the count reads next to the event it preceded. A log whose value
is that a person reads it end to end cannot spend a fifth of itself on two sentences.

### And the six HarmonyX warnings at every startup

`AccessTools.Field` logs a warning per miss, and `CustomEnemies.SetGalleryId` asks every
MonoBehaviour on a prefab for `galleryEnemyID`; `Traverse.Method(...).MethodExists()` does the same
for `StopSpin` in `EnemyReactivationHelper`. Both now ask reflection directly, which answers
silently, and both keep the call they guard on its original path. Nothing behavioural — it is noise
in exactly the place a reader starts.

`check.py` 9/9, `--full` 14/14, `dotnet test` 112/112, both installs deployed.

### Where §137's boundary ended up, and the check that was not kept

Asked whether §137 had left anything that would stop `TODO.md` becoming an archive again, the honest
answer was no: the rule was in four documents, which is exactly where §70 put it before the file
went 126 lines to 1207 anyway. A fast gate was written for it - `docaudit.py`, looking for
`~~strikethrough~~`, stacked handoffs and a line ceiling - and **removed as more machinery than
the problem deserves.** It is in "Tried and reverted" below.

The rule went into `CLAUDE.md` instead, which is the one document every session ingests whether or
not anyone thinks to look for it - the difference that matters, since the failure mode is a session
that never wonders about the boundary at all. It says what §70's four copies did not: closing an
item means *deleting* it, a strikethrough is not a deletion, and one handoff replaces the last. The
same paragraph now also says the CHANGELOG is narrative and not a home for rules.

## 139. The custom gallery screen, read instead of inferred

The confirming run §138 asked for, which took three launches because the first two fixes were built
on the one part of that screen nobody had ever looked at.

### What the panel actually is

§138 hid vanilla's grab art with `SetActive(false)` on the `grabSceneAnimator`'s object,
`Grabbed Animation Player`. The goonshroom went; so did the arrows, the exit button and the
animation-name text, because **they are children of that object** — and the code's own
`exitBtn.gameObject.SetActive(true)` cannot win against an inactive parent. Disabling only that
object's own `Image` brought the navigation back and put an opaque white sheet over the package's
video, because the art is not one component either.

The `[CustomGallery] panel stack:` line §138 added for a different question answered all of this
once it descended two levels and printed component type, enabled, alpha and rect size:

    0:CustomGalleryAnimation | >0:Backdrop <Image a=1.00 1920x1080> | >1:VideoDisplay <RawImage ...>
    1:Grabbed Animation Player <Image off a=1.00 1920x1080>
      | >0:Layer 2 <Image off> | >1:Layer 3 <Image off> | >2:Layer 4 <Image off>
      | >3:BackMenuButton [exit] | >4:PreviousAnimation [prev] | >5:NextAnimation [next]
      | >6:Animation Name [animText]

So: four full-screen images to hide, four navigation objects to leave alone, and **no
`Character Display` anywhere on this panel** — which was §138's other inference, and it was wrong.
The mod now disables every `Graphic` in that subtree except the navigation and its descendants,
resolved from `EnemyGalleryUI`'s own fields rather than by name, and restores exactly what it
disabled. `grabAudioSource` is stopped and disabled explicitly, because it rode on the object whose
deactivation used to silence it for free.

### The disable nobody restored

Every vanilla grab view opened after visiting one custom entry drew the pause menu through itself.
§138 had disabled the panel's own background `Image` — on the `Character Display` guess above — and
nothing ever put it back. It was also unnecessary: the overlay's `Backdrop` is an opaque black
*child* of the same panel, so it already covers that background. The line is gone rather than paired
with a restore, which is the cheaper of the two fixes and the one that cannot rot.

`learnings/unity-runtime.md` has the rule, and it is three rules: disable components rather than the
object, read the subtree before choosing which, and pair every disable with its restore in the same
state object.

### The instrument printed the fix working

`[OVERHEAT] STUCK:` fired five times — and each line is followed 4 ms later by
`hasBeenOverheated=False canAttack=True`. That is one frame: vanilla's clear refuses while heat is
above the cap, heat crosses below it, `ClearOverheatAtLockFloor` runs on the next frame. The
predicate §138 chose is still the right one, but **a fix that runs a frame later manufactures its own
defect-shaped transient on every ordinary trip below the cap**, and the reported defect — spells
unusable — is something that lasts. `STUCK` now requires the state to hold 0.5 s and prints
`held=Ns` with it. Item 2b stays open and not-reproducing; this is the third session to misread this
one instrument (§134, §138), and the answer was again to change the instrument rather than the note.

### What the run does confirm

`joker_massage` / `joker_cum` are gone: both step lines now read `-> joker_wall_massage (the
package's own row)`, so §138's `GalleryRowResolver` works through the manifest. `Animator.GotoState:
State could not be found` fell from 31 to **1** — the survivor fires inside
`OnViewGrabSceneClicked` itself, before any postfix can run, and is left alone rather than patching
vanilla's own assignment for one cosmetic line. `[AI-AUDIT] ok`, one `[AI-GUARD]` (the witch's
`canGrab` refusal), the known `[INPUT] backend repaired`. The repeat collapse holds: 31
`[GAMEOVER]`/`[GRAB-START] ignored` lines in 2,259, where §138 had 1,389 in 6,508.

**Edi was not running for this session** — 15 `EDI Stop failed: Connection refused` and a `Play`
failure for every row the run touched, so that run proved the naming half only. A second run with
Edi up closed it: zero `failed:`, and `Serpent_Hypnosis`, `Serpent_Loop`, `filler` and
`filler_cum_25` all sent and played. `check.py --full` 14/14 after the changes above.

## 140. Two reference targets deleted

One of the publishing items, decided rather than discovered.

**`code/PncEdi-source-stale-2026-05-30/` and `code/PncEdi-v2.0.8-original.dll` are gone.** The old
v1.0.0 tree was a reference for how the mod used to be written; the DLL was the untouched shipped
binary and the revert target if a rebuild ever went wrong. Neither had been read in months, both
would have needed a paragraph of explanation to a stranger. Neither is recoverable from this
repository: §143's squash took the published history down to one commit, so what is not in the
working tree is not anywhere. That is deliberate for the DLL in particular — it is someone else's
compiled mod, shipped under no licence, and a clone is not the place to keep redistributing it.
The three places that named them —
`PROJECT.md`'s layout tree, `code/README.md`, and `code/NAMING-AUDIT.md`'s confirmation of the
315-entry default — now say so rather than pointing at a path that is not there. The audit's claim
is unchanged: it was confirmed against that binary, and deleting the binary does not unconfirm it.

## 141. The publishing read-through, and the credit that was owed

A pass over every document with a publishing eye - `PROJECT.md`, `TODO.md`, `CLAUDE.md`,
`code/README.md`, the two audits, all of `learnings/`, and the `BepInEx/custom-enemies/` format
docs - looking for what would read wrongly to a stranger. What it did *not* find is worth stating
first: no author identity anywhere, no credentials (`code/dist/EdiConfig.json` ships `"Key": null`),
no first-person author voice, and nothing unfair about upstream or about the game's developer -
`working-practice.md` already carries "inherited code is not wrong, it is differently-assumed" as
its own correction.

**What it did find was that this project credits almost nobody.** Everything it is built on is
someone else's: the game, Edi, the PncEdi mod this tree continues from its shipped v2.0.8, the
`pncedi-portable-patch` fork the mod manager and the whole custom-enemy framework came from
(§127), and the five funscripts the gallery started as. Only the last of those was written down at
all, in a provenance table inside `learnings/funscript-authoring.md` - a file a player never sees,
in a document about how to write a curve. The shipped README went further in the wrong direction:
it says the scenes are "timed against the game's own animation rather than scripted to video",
which is true of the re-derived rows and reads as a claim about all of them, while some still
descend from those scripts through `retime.py`.

`CREDITS.md` is the answer, and it ships in the archive as `PncEdi-CREDITS.txt` alongside the
changelog, with a shorter CREDITS section in the README itself. **Two of the authors it credits
have no name in this tree** - the original mod's and the fork's - and the file says that out loud
rather than leaving the silence to read as a claim. There is deliberately **no LICENSE**: this is
built on other people's work and is not in a position to grant terms over it.

### Four things in shipped text that were simply wrong

- **The archive called its own Edi unmodified, twice.** `@EDITAG@` renders as
  `v1.0.4 (patched, PR #15)`, so "WHAT IS IN HERE" read `Edi v1.0.4 (patched, PR #15) (unmodified,
  from its GitHub release)`, and the footer said "Edi is by NoGRo and is redistributed unmodified".
  Both now point at the HOW IT WORKS paragraph that states what the build actually is - written
  without a version in it, so it stays true when `EDI_PATCH_PR` goes to `None` and that paragraph
  comes out.
- **"WHAT IS IN HERE" did not list `PncCustomEnemies.dll`**, which every release has shipped since
  §131 and which the section two above it describes.
- **`BepInEx/custom-enemies/README.md` sent players to the wrong plugin** for the package
  switches - "Post Nut Calamity EDI Integration", which is the core mod's `BepInPlugin` name. They
  are under `PNC Custom Enemies`, as the two format docs beside it say.
- **`CUSTOM-ENEMIES.md` named `PNC 0.3.1_Data`** for the folder to read the Unity version out of.
  It is version-stamped on Linux and not on Windows, so it now says `*_Data`. The version it
  claims, `6000.3.11f1`, was checked against both 0.3.2 builds and is right.

### And a hardcoded scratch path that was a portability bug

Four documents named an absolute path under one machine's home directory, or a scratch directory
under `/tmp` whose name carries a uid - a username and a uid in a public tree. Three were prose and
are now written machine-neutrally; `code/NAMING-AUDIT.md`'s was also stale, since the slug harness
has lived in `code/slugharness/` for some time.

The fourth was not prose. `code/animcheck.py --sheet` and `--motion` wrote their output to a
literal scratch path that exists on one machine, so both flags would fail for
anyone else - and they are the flags the tool's own docstring tells you to reach for first, before
picking anything to measure. It takes `PNC_OUT_DIR` now and defaults to `tempfile.gettempdir()`.

## 142. The release thread read, and what it corrected

§141 wrote `CREDITS.md` around a gap — two of the authors it credited had no name in this tree.
Reading the mod's own Eroscripts thread closed the gap and corrected the shape of the credit
itself, which was wrong in a more interesting way than being incomplete.

**There was never a single earlier mod with a single author.** `CREDITS.md` had said this project
continues "an earlier PncEdi mod, taken up at its shipped v2.0.8". What it actually took up was a
composite: every release on that thread pasted over each other in order, first to last, which is
why the v1.9.7 and v2.0.8 strings `code/NAMING-AUDIT.md` traces belong to no one person's build.
In order that is **everydayhandyuser**'s original integration (27 May), **edale**'s gallery-unlock
registry keys (28 May), **overkeks**' 0.2.1 edit with gameplay changes and source (31 May), and
**Dupli9d**'s patch (1 Jun) and horny-system build (4 Jun) — that last being the ancestor of this
mod's heat and lock mechanics. The `pncedi-portable-patch` fork §127 took the mod manager, the
gameplay profiles and the custom-enemy framework from is **Dupli9d**'s too, posted to the same
thread on 19 August.

The thread is also where this mod is released — `PNC0.3.1-PncEdi-2.5.2.zip` is a post on it — so it
is the URL `CUSTOM-ENEMIES.md`'s "Getting a package" section had been describing without naming
since §135. That publishing item is closed by having read the thread rather than by a decision.

### A credited author who was a Windows account name

The provenance table in `learnings/funscript-authoring.md` credited `zombie.funscript` and
`plantasha.funscript` to a short lowercase handle, dated 31 May. Nobody by that name posted on the
thread, and
neither file was ever attached to it. The name came from the `.ofsp` OpenFunscripter projects
beside those scripts, which carry absolute paths from the machine they were authored on — and the
segment that was read as an author is the **Windows account name** in
`C:\Users\<name>\Downloads\pnc edi integration\...`.

Two things follow, and only one of them is about this entry.

- **An identifier read out of a file is evidence about a machine, and only sometimes about a
  person.** The same path is genuine evidence for something else: those scripts were authored
  *inside the original release's own directory*, which is how they came to ship in it. That is the
  claim the file can support. Authorship is not.
- **It should not have been published either way.** A stranger's local account name is not
  attribution, and this repository is going public. The name is out of every document.

The scripts are now credited as what the thread supports: shipped inside everydayhandyuser's
original release, authored to video in OpenFunscripter, scripter not named. `mr_spunky` (the imp
scripts, and the play-through captures AniFS worked from) and **AniFS** (`ambient.funscript`,
`peek.funscript`, 6 Jun) were both already right.

**The two `.ofsp` files themselves still carry those paths and stay tracked, by decision** — a
decision re-taken in §143, once the squash meant the history no longer forced it. They are
OpenFunscripter originals, they never reach the release (`release.py` and `deploy.py` glob
`*.funscript`), and the alternative is editing or hiding an original for a string inside a binary
nobody opens. What actually mattered was the
credit, and that is fixed: the name is out of every document, and what the paths are evidence *for*
is written down in prose rather than resting on the files.

## 143. The CHANGELOG read through with a publishing eye

The last of the publishing items, and the one with no check behind it: ~9,700 lines of narrative
that `release.py` ships in every archive as `PncEdi-CHANGELOG.txt`, never once read as a whole by
anyone deciding what a stranger should see. §141 did that pass over every other document and found
four wrong claims in shipped text; this is the same pass over the file that was left out of it
because of its length. Read end to end, 143 entries.

**Most of it needed nothing**, which is worth stating before the four things that did: no
credential, no device name, no email, no key material, and the entries about other people's code
that carry the most weight — §104-§107 on the Edi loop-seek defect — were already measured, filed
upstream as an issue and a PR, and written with §107's standing offer to withdraw the patched build
on request.

**The entry warning about hardcoded paths contained one.** §141's own text quoted the offending
strings literally, so the username and the uid it existed to remove shipped inside the sentence
describing their removal. Both are now written machine-neutrally. `TODO.md` carried the same string
in its handoff and is fixed with it.

**The two history-rewriting entries are gone**, along with §140's second half. Their subject was
repository hygiene rather than the mod: what a player extracts from an archive is a record of how
scenes are timed and why a grab behaves as it does, and how this repo's own commit history was
tidied belongs to neither. §140 keeps the half that is real project record — the two reference
targets deleted and the three documents that pointed at them. **The numbering is closed up rather
than left with a gap** — what was §141 to §144 is now §140 to §143 — which the squash below makes
free, since no commit message is left citing the old numbers.

**Judgements of other people's work were rewritten to describe this tree instead.** §127-§129
imported the mod manager, the gameplay profiles and the custom-enemy framework, and reviewed what
came across; when that was written the fork's author was unnamed, and §142 has since named them —
so the same paragraphs now read as a critique of a person this project credits. Nothing in them was
inaccurate. What changed is where each sentence points: §128's four findings are stated as things
that behave differently under this tree's layout rather than as defects, with the framing it
already carried in one place applied throughout; §129's documentation list says *does not hold
here* rather than *was wrong*, and each bullet names the difference rather than the error. §2's
diorama scripts, §29's seven resolvers and §128's `WriteAllLines` lost the phrasing that graded the
choice rather than reporting it.

**And the second person is out.** Ten passages said "at your direction" or "at the user's
direction" — correct in a handoff between two people who know each other, and an address to
somebody the reader of a shipped archive is not. Each is now a decision without a second person in
it, which loses nothing: that a call was made deliberately is the load-bearing part, and that
survives.

### The account name that was in the tree, not in the prose

§141 read every document and §142 took a mistaken author credit out of all of them. Neither looked
at anything that was not prose, and one file was carrying the same string the whole time:
**`code/edimod/.vs/PncEdi/DesignTimeBuild/.dtbcache.v2`**, a 78 KB Visual Studio design-time build
cache, tracked since the initial commit and matched by no `.gitignore` rule. Inside it is
`C:\Users\<name>\Downloads\pnc edi integration\...` — the Windows account name §142 established
was never an author — repeated across a full listing of that machine's directory layout.

It is a build-tool cache: nothing reads it, nothing here has ever needed it, and it would have
shipped in the published repository. Untracked and deleted, with `code/**/.vs/` added to the
allowlist's deny side so the next machine to open the solution in Visual Studio cannot put it back.

**The two `.ofsp` files keep theirs, and that is now a decision rather than a consequence.** §142
kept them on the reasoning that the history carried the string whatever the working tree did; the
squash below removes that constraint, so the question was asked again and answered the same way.
They are OpenFunscripter originals of two inherited scripts, they never reach a release archive,
and the alternative is editing or hiding an original to change a path inside a binary nobody opens.

**The general form, which is the third time this project has paid for it:** a documentation pass
reads documents. `code/animcheck.py`'s hardcoded scratch path (§141) and this cache were both found
by something other than reading prose, and both had been sitting in a tracked file for months. What
would have caught this one is a grep for the identifier across *every tracked file* rather than
across the ones written in sentences.

### The build machine's path was inside every shipped DLL

The same grep that found the cache, run over the whole tracked tree rather than over documents,
came back with the three plugin binaries. A .NET assembly records the path of its own `.pdb` in the
PE debug directory, so each of `PncEdi.dll`, `PncCustomEnemies.dll` and `PncModManager.dll`
carried the absolute path it was built at — a username and this machine's directory layout — and
those three files are both tracked here and shipped in every release archive. Every published
build so far has had it.

`<PathMap>` fixes it at the compiler, rewriting the repo root to `./` in the debug directory and in
every source path recorded in the PDB. **The trap is that it is a literal string prefix match**, and
the first attempt did nothing: `RepoDir` is `$(MSBuildThisFileDirectory)..\..\`, which resolves to
a real but *unnormalised* path — `.../code/edimod/../../` — and that is not a prefix of anything.
`$([System.IO.Path]::GetFullPath('$(RepoDir)'))` is, and all three now read
`./code/edimod/obj/Release/...`. It costs nothing and makes the output reproducible across machines
as a side effect.

**What it does not do is remove the debug information**, which was the other candidate
(`DebugType=none`). Line numbers in a stack trace are worth more here than the few bytes, and the
path was never the reason to have symbols.

### The history squashed to one commit

The published repository is one commit. 142 of them went, and with them everything a rewrite was
the only way to reach: 92 past revisions of this file, each carrying the section this entry
deleted and the wording it rewrote; `code/PncEdi-v2.0.8-original.dll` and
`mod/single-mod/BepInEx/plugins/PncEdi.dll`, another author's compiled mod under no licence, which
every clone would otherwise have carried forever; the `.vs` cache above; and five commit messages
naming sections that no longer exist.

**What is lost is smaller than it looks, because this project never kept its record there.**
`CLAUDE.md` makes `CHANGELOG.md` the narrative record and `learnings/` the rules, and both ship in
the release archive; §135 had already decided the same thing from the other direction, keeping
package media out of git precisely because *the forum post is revisable and git history is not*.
What a squash costs is `git blame` and the ability to date a change more finely than its `§n`
entry, against a history nobody outside this machine has ever seen.

**And it is the last time this is cheap.** Nothing has been pushed, so there is no fork to strand
and no hash anyone else holds. Every later removal is a rewrite of a history other people have
copies of, which is the position §140 was written to avoid ever being in.

What was deliberately **not** cut is the process narrative — §92's log that nobody opened, §102 and
§139 correcting earlier readings of the same instrument, §134's measurement that bought a fix and
the report that took it back. It is written about the project rather than about anyone, it is the
reason several rules exist, and a changelog that records only what worked is the kind this project
has spent forty entries arguing against.

No code changed and no check can see any of this. `check.py` 9/9.

## 144. The dead zombie knob, deleted

The last item standing between the tree and a release build, and the smallest: what to do about
`ZombieGrappleChargeRate`. §138 established that it reaches nothing — `ApplyZombieGrappleTuning` is
a postfix on `ChargingEnemyAI.Start` that then requires `key == "zombie"`, and no zombie prefab is a
`ChargingEnemyAI` in 0.2.1, 0.3.1 or 0.3.2. The zombies are plain `EnemyAI`, so they neither charge
nor grapple, and the intersection the patch is gated on has been empty since before this mod was
recovered. §138 left three ways open: delete it, repoint it at the clinging family, or keep it and
say what it is.

**Deleted.** Repointing it at the imps and the goonshroom is a gameplay change rather than a repair,
and it would be a gameplay change written on release eve with no play behind it. Keeping it means
shipping a config surface with an entry that documents its own inertness — a knob that lies by
existing, which the next person has to re-derive the emptiness of before they can trust the rest of
the section. What came out: the `ApplyZombieGrappleTuning` method, the `ChargingEnemyAI.Start`
postfix that existed only to call it (its whole body was that one call), `CfgZombieGrappleChargeRate`
and its `Bind`, and the entry in `com.edi.pnc.cfg`. Nothing else referenced any of them — no test, no
tool, no other plugin. An existing install that keeps its own `com.edi.pnc.cfg` is left with the
line as an orphaned entry, which BepInEx preserves rather than strips — harmless, read by nothing,
and gone the moment the file is replaced by a deploy or a fresh extract.

The `SpinningEnemyAI.Start` postfix beside it is untouched and still does the gargoyle and plantasha
tuning; the deletion takes the mod's only patch on `ChargingEnemyAI.Start` with it, which
`patchaudit` is content with because a patch that is not there is not an unregistered one.

`check.py` 9/9, `dotnet test` clean, both installs deployed and current. The tree is now at the point
`release.py` was waiting for.

## 145. The plugin DLLs untracked, and a README for strangers

The three plugin DLLs under `BepInEx/plugins/` had been tracked since the repo began, on a reason
written into `.gitignore`'s own header: they are what `release.py --no-build` ships, and the only
artefacts a clone cannot rebuild without a game to compile against. That reason is true and it was
still the wrong call for a repo about to go public.

**What settled it was practice rather than size.** The repo is 1.4 MB, of which the DLLs are 560 KB
in a single copy, so the storage argument reaches nothing at this scale — it only bites if binaries
are committed on every source change rather than at releases. The argument that does reach is that
"do not commit build output" is close to universal in open source and is what the BepInEx/Unity
modding scene does: `bin/`, `obj/` ignored, the DLL distributed through a release rather than the
tree. Anyone who edits the source has to rebuild anyway (the build is one command and deploys
itself), and anyone who does not is a player, who gets the DLLs from the release archive. The
tracked copy was serving neither.

The half of that convention this project cannot follow is "the binary lives in Releases instead":
the archive goes to the eroscripts thread, and there is no CI. So the honest statement is that a
clone is a **source tree, not a runnable install** — which is now the first thing `README.md` says
after the download link.

**It cost one `git commit --amend`,** because the history was still one unpushed commit. That is the
whole reason this was decided now rather than later: after the first push it is a rewrite of a
history other people hold, and the same question becomes expensive to answer. `.gitignore` keeps its
deny-by-default shape — the `!BepInEx/plugins/` opt-in stays so the directory's rule is visible, with
nothing named back in under it — and the header comment now says why no binary is tracked instead of
why one was.

Three stale claims went with it: `.gitignore`'s header (which still said "the one binary", written
before the split into three plugins in §131), `deploy.py`'s comment on `plugin_dll` ("the one git
tracks"), and PROJECT.md's layout tree, which now labels `plugins/` as build output.

**And the repo had no `README.md` at all.** Every document in it is written for someone who already
owns the context — `PROJECT.md` is a map for a returning session, `code/README.md` a reference for
someone already building. Nothing was written for a stranger who has just cloned it, which is now
the only kind of reader the repo is about to acquire. The new file is the front door: what the mod
is, the release link for players who want none of this, requirements, the two symlinks, the
`--refs-only` bootstrap, the venv, and one section each for build, deploy, check and release. It
closes on what is deliberately absent and why — the game, the DLLs, BepInEx and Edi (pinned and
fetched), `EdiConfig.json` (device keys are credentials), and package media.

Two gotchas are in it because they are not guessable from the tree: **`game-windows` must point at a
Windows install**, since `ManagedDir` is hardcoded to `Post Nut Calamity_Data\Managed\` and the
Linux build names its data folder after the version; and `game-linux` is optional, because
`resolve_targets` skips a missing target with a printed reason rather than failing. `PROJECT.md`'s
"where to look for what" table and `CLAUDE.md`'s document list both gained a row for it — a public
README that drifts is worse than none, so the obligation to keep it current is written where
sessions read.


## 146. `TODO.md` untracked, and the documents that assumed it

`TODO.md` was tracked, and it is the one file in this repo written with no reader in mind — one
person's handoff to their next session, carrying half-formed diagnoses, what is annoying, and what
is not worth doing. Publishing it makes it one of two things: curated, which costs exactly the
honesty that makes it useful, or a private to-do list handed to strangers. Untracked, it stays what
it is.

`.gitignore` gains `/TODO.md` under the `!/*.md` opt-in that had been sweeping it in, with the
reason written beside it, and §145's amend trick does not apply — the file is in all three commits
by now, so removing it from history took an `--index-filter` over the branch rather than an amend.
Still the cheap side of the line, and for the same reason: nothing is pushed.

**The interesting half was the documents.** Four of them named `TODO.md` as a thing that is there:
`CLAUDE.md` ("start here to pick up work"), `PROJECT.md`'s where-to-look table, `CHANGELOG.md`'s own
header ("start there, not here"), and `README.md`'s read-next table, which after §145 was a link a
stranger could not follow. Each now says **check whether the working tree has one** and what to do
when it does not — the newest `§n` entry here is the state of play, which is true whether or not a
`TODO.md` exists. `learnings/working-practice.md`'s rule about the file regrowing is unchanged and
still worth having; it just no longer assumes the file.

The general shape, which is the part worth keeping: **a document that is untracked cannot be
referenced as though it were present.** The reference has to carry its own fallback, or the first
person to clone the repo hits a dead end that reads as a broken repo rather than a private file.
`README.md` says the absence is deliberate, in the same list as the game, the DLLs and the device
keys.

**A sweep over the rest of the documentation** for claims §144-§146 had made stale, and for two
that had been stale longer. Three documents gave the CHANGELOG's range as `§1`-`§143` or `§1`-`§144`
— a number that goes wrong at the next entry and had already gone wrong twice — so all three now say
"numbered `§1` upward", which cannot. `.gitattributes` explained its `* -text` rule by citing
`mod/single-mod`, deleted in §58, and a CRLF/LF split in two files that no longer have one; the rule
is still right and its reason is now the real one, `deploy.py`'s per-line preservation for the
Windows install's mixed `BepInEx.cfg`. `code/README.md` needed nothing: "nothing binary is tracked
here" was written of the `code/` tree and is now true of the repo.

The pattern in both: a document that pins a moving number, or names a file to explain a rule, goes
stale silently and is only found by someone reading it for another reason.


## 147. Two dead switches, found by checking a report against this tree instead of believing it

A player posted a bug list and a wishlist in the release thread. It was worth reading and it was
**not a report about this mod**: post 112 is a reply to post 80, by the author of the other build
in that thread, so every bug in it was observed on that fork. Only the follow-up replies here, and
on the same build. That was established after the first two items had already been worked, which
is why it is the first thing this entry says — the list is a set of leads, and a lead is checked
against this tree or it is nothing.

Checking them found two defects here anyway. Neither is the bug that was reported, both are real,
and both are a switch that reads as applied and changes nothing.

**A package's on/off switch did not reach the pool that actually picks the enemy.**
`CustomEnemyRegistry.ApplyEnabledState` re-injects every spawner's `enemyData[]` when the switch
moves, and that is idempotent and correct. It is also, while shuffle mode is on, irrelevant:
`EnemySpawnShuffle` keeps its own pool of prefabs and weights, rebuilds it only when the scene
handle changes, and its `GetEnemyPrefab` prefixes **replace** the spawner's pick rather than biasing
it (§91 is where that replacement came from). So a package switched off mid-run stayed in the stale
pool and kept being drawn until the next level load, and a spawn-weight change did nothing at all.
`ApplyEnabledState` and `ReinjectSpawners` now clear that cache through `EnemySpawnShuffle.ClearCache`,
which already existed for the scene change.

The asymmetry that makes this hard to see from the outside: a wall-picture trap never goes through
the shuffle pool, so *its* switch worked. Two packages, the same control, one obeys and one does
not, and nothing in either package explains it.

Two things found beside it and deliberately left. `SpawnWeight` clamps to `Mathf.Max(0.01f, ...)`,
so a weight of 0 is not off — it is one draw in a hundred, which is close enough to off to be
mistaken for it. And `InjectSpawner` derives its `vanilla` list from the spawner's *current* array,
stripping only our own entries, so the scale-up a fractional weight applies is not undone on
re-injection: toggling a fractional package repeatedly multiplies the table's length each time. The
odds stay right by construction; the array does not stay small.

**A service scene charged a lock and paid nothing back.** `HeatLockSystem.IsService` marks an
interact scene as one the player is *given* rather than charged for. It tested one hard-coded
fragment, `service`, which appears nowhere in this game — no clip, no trigger, and not once in
`Assembly-CSharp`. So the exemption had never fired. And `TryReleaseFromService`, the payout half,
had **no callers at all**: `NoteInteractSceneTriggered` used `IsService` only to decide whether to
skip charging, and nothing ever called the release. Two halves of one idea, one unreachable and one
that could never match.

Both are closed. The fragments are configuration — `Gameplay/ServiceSceneKeys`, defaulting to
`service;gravy;minothaur;minotaur` — which is also how a custom-enemy package gets to ship a
shopkeeper without a code change. `NoteInteractSceneTriggered` calls `TryReleaseFromService` on a
match instead of falling through to the charge. The payout is the existing once-per-source keyhole
release and `AmbientReleaseClearsAllLocks` already defaults to true, so Gravy — who heals in the
unmodded game — clears the horny meter rather than filling it, and cannot be farmed by walking back
to the same stool.

**Neither has been seen in play.** `check.py` is 9/9 and both installs are deployed, but the service
fragments were taken from `GalleryTable`'s slugs rather than from a log, so whether Gravy's trigger
or its clips actually carry one of them is still unconfirmed. That is the first thing to look at in
the next run.

**Two theories checked and killed, recorded so they are not re-derived.** The reported imp bug — the
three-attached cling script continuing over the downed scene — is not the grapple block re-sending
`imp_3`, which dispatches only on tier transitions; and it is not a missing `InGameAliases` entry,
because the in-game slug is `imp_grab_loop`, the full animator state name, which is a
`Definitions.csv` row and resolves correctly. The `imp_loop` slug that has no in-game alias occurs
only in the gallery, and `slugharness` says so. What is left is the grab dispatch not firing during
the trio scene, which is a question for a log rather than for the source.


## 148. Heat scaling read out of the IL, and filler that outlives the run

Two jobs, one static and one built, both out of the release thread's list (§147 for what that list
is and is not).

### The scaling report, answered from the assembly rather than from a run

Post 114's "horny levels do not scale with capacity" was measured on the other build, so the
arithmetic never transferred. The question worth answering here is the mechanism, and `ikdasm` over
`Assembly-CSharp.dll` answers all of it. `PlayerStats::maxHeat` has exactly three writers -
`SetMaxHeat`, `LoadSaveData` and the constructor - and the paths that reach the first are:

| writer | shape |
|---|---|
| `PlayerClassManager::ApplyStatModifiers` | `MaxHeat * heatCapacityMultiplier + bonusHeatCapacity` |
| `ArmorData::ApplyStatModifiers` | `MaxHeat + heatCapacityBonus`, **additive** |
| `BuffDebuffSystem::ApplyModifiersToSystems` | `baseMaxHeat + permanentMaxHeatBonus + cachedModifiers.heatCapacityBonus`, and only when that differs from the current value by more than 0.01 |
| `PlayerStats::LoadSaveData` | writes the field directly - the one bypass, and it sends no `SetMaxHeat` |

Three things follow, and none of them was written down before.

**Our multiplier is not applied twice, and the reason is a branch.**
`PlayerClassInitializer::ApplySelectedClass` tests `PlayerStateSaver.IsFirstFloor`: not the first
floor, it calls `LoadPlayerState()` and **returns**; first floor, it falls through to
`ApplyClassToPlayer()`. The two are exclusive, so `ClassHeatMultipliers.ApplyToPlayerHeat` - a
multiply in place, and therefore not idempotent - runs exactly once per run. The saved capacity
restored on later floors already carries it. `BuffDebuffSystem::ReinitializeBaseStats` is called at
the end of both paths, after our postfix, so its `baseMaxHeat` captures the multiplied figure and
its own writes agree with it.

**On every floor after the first, nothing calls `SetMaxHeat` at all.** `LoadSaveData` writes the
field, `CaptureBaseStats` then reads it back, and `ApplyModifiersToSystems` finds no difference to
write. So `HeatLockSystem.SetMaxHeat_Postfix` never fires on floors 2+, and `_baseHeat` is left
wherever the scene entry put it - either 0, from `ResetForScene`, in which case `GetScalingHeat`
falls back to the live `PlayerStats.MaxHeat` and is right, or 100, from the `PlayerStats.Awake`
postfix reading the prefab default before the save is restored, in which case `GetTotalLocks` is
`ceil(100/20) = 5` for every class for the whole floor. Which of the two happens is decided by
whether Unity's `activeSceneChanged` fires before or after that `Awake`, and **that is not
derivable - it has to be read off a log.**

The logs cannot answer it yet, and that is the finding: **every instrumented session this project
has ever recorded is `MainMenu -> Floor1`.** Sixteen Floor1 entries across every log in
`BepInEx/logs/`, no floor 2, ever. The floors-2+ path has never been observed. The `/5` that shows
up on each Floor1 entry before the class multiplier lands is the same transient and is corrected
there by the `SetMaxHeat` that floors 2+ do not get.

**The class-selection screen and the runtime disagree about armour.** `GetEffectiveHeatCapacity`
computes `(100 * heatCapacityMultiplier + bonusHeatCapacity + armorHeatBonus) * ourMultiplier`, so
the armour bonus is multiplied. At runtime it cannot be: `ApplyClassToPlayer` runs
`ApplyStatModifiers` first (our postfix with it), and only then `EquipStartingEquipment`, whose
`ArmorData::ApplyStatModifiers` **adds** its bonus to the already-multiplied figure. With the
shipped x2 the screen overstates capacity by the armour bonus - a class shown as 200 plays at 150.
Locks are counted off the real figure, so a player reading capacity from the screen and locks from
the meter sees exactly the mismatch that was reported, without either number being a bug on its own.

Not fixed here, because which of the two is right is a design question rather than a defect: making
the screen honest is one line in `GetEffectiveHeatCapacity`, and making the runtime match the screen
means re-applying the multiplier after equipment, which is a gameplay change.

### Filler in the main menu and while paused (request 4)

Two new `EDI` settings. `FillerInMenus` ships **on**; `FillerWhilePaused` ships **off**.

The asymmetry is deliberate. A menu is a gap between runs and the filler is what fills gaps, so
running there is the same behaviour the setting's name describes rather than an escalation - and
losing window focus still pauses, which covers the case the off default was really guarding
against, someone walking away. A pause is the opposite: the player has deliberately stopped, and a
device that carries on is the one thing they did not ask for.

`FillerInMenus` keeps the filler running on a menu scene. The stop that used to happen there was
right for a default and wrong as an absolute - section 8.4's rule was "a menu has no gameplay to
fill between", which is a statement about what the filler is for rather than about what a player
wants. `EndGalleryPlayback`, which that section added for the same reason, now routes through the
setting too rather than stopping unconditionally.
The routing had to move rather than the test: `GoFiller` is reached from a lost grab, a scene
ending, a reset and the hotkey, and in a menu every one of those means the same thing, so the menu
question is now asked in `GoFiller` itself and `OnSceneChanged` only caches the answer. The row is
the plain `FillerGallery` and deliberately not `ResolveFillerIntensity`: the damage and heat
percentages behind the ladder are whatever the run that just ended left in them, so a menu would
otherwise open on `filler_cum_75` because the last thing that happened was a death. For the same
reason `CanRefreshFillerForHeat` refuses while a menu is up.

`FillerWhilePaused` lets the filler play behind the pause menu. **Only the filler** - a grab, an
interact scene or any other real row still pauses, because those are scripts for something that is
on screen and has just stopped moving. `PauseHooks` now records whether the pause actually stopped
the device, so the resume has nothing to undo when it did not; sending `Edi/Resume` against a
playback that was never paused is the same contradictory instruction `ResetForNewScene` already
avoids. Losing window focus still pauses either way, which is the guard that makes the menu default
matter less than it looks.

`FillerEnabled` (Ctrl+1 / Ctrl+2) still wins over both.

**One thing is deliberately left half-answered, and it is the same ordering question as above.**
`learnings/unity-runtime.md`'s §114 rule says to ask for the object that defines a state rather
than for the scene's name, and `EndGalleryPlayback` does exactly that -
`FindAnyObjectByType<PlayerStats>() == null`. The menu filler cannot, because it is asked from
`activeSceneChanged`, and whether the new scene's `PlayerStats` exists at that instant is precisely
what is unknown. A predicate that turns on callback ordering is worse than one that turns on a
naming convention, so the name test stays and the two coexist on purpose.

Both are settled by one line, which is why it was added rather than argued about: `[SCENE] 'a' ->
'b' playerStats=yes|no baseHeat=N`, read before `ResetForScene` clears the second field. `yes`
means `Awake` has already run, which collapses the two predicates into the object test **and**
means `_baseHeat` is zeroed after the prefab default was recorded, so floors 2+ read the live
capacity back and there is no lock-scaling defect. `no` means the reverse on both counts.



## 149. Device variants named after devices, and a second stroker script after all

Out of the release thread again, but a different thread: the multi-axis scripting guide,
<https://discuss.eroscripts.com/t/multi-axis-scripting-in-ofs-tutorial-tips-and-resources/328979>.
It was read for its speed limits, which were reported as being much lower than this project uses.

### What the guide actually says, which is not what it was reported to say

Its caps, in units/s, soft then hard: Handy 400/500, Handy 2 600/700, **Handy 2 Overclocked
700/800**, OSR/SR6 600/700. The guide has **no Handy 2 Pro row at all**, and the one 2 Pro figure
anyone offers in the comments — 1200 *units*/s — is *higher* than the 960 u/s this project reads off
the device's own slider-overclocking menu (1200 mm/s over a 125 mm stroke). Its Handy 1 pair,
400/500 units/s, is likewise above that device's 364 u/s firmware ceiling.

**How much weight any of it carries is settled by the author's own reply.** A commenter asked the
obvious question — "have i been victim to fake news? i swear to god when the Handy 2 PRO released
that people were saying the hard cap speed limit was 1200 units" — and the answer was: *"Nah it's
just I don't have a Handy 2 so these limits are the ones I personally use. They're based on some
quick forum searching on ES, not in depth testing or anything."* Hearsay, then, and the author says
so. It is still worth having, because a conservative variant is worth having; it is not worth
weighing against a number read off the device.

**Which row to generate from is a judgement, and the first answer was wrong.** "Handy 2
Overclocked" looks like the row for this project's hardware, and the variant was built to its
700/800 before a second reading: **overclocking is a Handy 2 Pro feature** — the base Handy 2 does
not have it — so that row is most likely describing the very device the master is already authored
for. The folder is named `handy2`, so it carries "The Handy 2" row instead: **600 soft, 700 hard**.
Where two hearsay figures compete, the conservative one is the right way to be wrong. And a stock,
un-overclocked 2 Pro is 450 mm/s = 360 u/s, which is `handy1` territory rather than this folder's —
what sits between them is a 2 Pro overclocked *part-way*, which is exactly the choice the device's
own slider offers and needs no fourth folder.

Nothing there argues for limiting the master, then. What it does give is a **second stroker
variant**, which §36 considered and rejected — correctly, on the evidence it had, which was one
cap and a set of accents that a single cap could not tell apart from sustained speed.

### Soft and hard are different questions, and a token bucket answers both

A limiter with one number cannot serve a guide that quotes two. At 700 every deliberate accent is
flattened; at 800 almost nothing is limited. `variants.py`'s `slew` therefore carries a token
bucket, in position units of travel: each transition earns `soft × dt` of credit and spends what it
travels, the balance capped at `budget` and never negative, so a transition may cover
`min(hard × dt, soft × dt + bucket)`. Idle script, full bucket, one accent at the hard cap; script
already flat out, empty bucket, held at the soft cap. `soft=None` collapses it to the old
single-cap limiter exactly — `handy1` regenerated byte-identical in its actions, only its metadata
description changed, which is the regression check that the generalisation is one.

`budget` was measured rather than picked. Against the master's 2132 transitions:

| budget | rows changed | transitions over 700 | range units lost |
|---|---|---|---|
| 0 | 16 | 0 | 103 |
| 5 | 13 | 77 | 85 |
| 20 | 11 | 119 | 67 |
| 40 | 11 | 144 | 60 |
| 80 | 11 | 145 | 59 |

(That sweep was run at 700/800, before the row was re-chosen; the knee it identifies is a property
of the bucket, not of the caps.) 20 units — about 0.2 s of accent at the hard cap before the soft
cap takes over, a snap rather than a section. Past 80 nothing changes: the master has no sustained
run long enough to spend more. At the shipped 600/700, `speedcheck --variant handy2` confirms the
guide's contract exactly — **0 rows over 600 by median, 0 transitions over 700** — and 16 of the 102
scripts differ from the master, which gives up 107 position units of range in total. `imp_3`, the
row a player reported as shaking their desk, keeps its full 0–100 range throughout.

`speedcheck` learned the guide's pairs (`GUIDE`) and prints two summary lines against them, so the
new variant is checkable and not merely generatable.

### The folders are named after devices now

`detailed` named a quality tier; `handy1` named a device. A player picks a variant off their
hardware, so all three now do: **`handy2pro`** (the master, unlimited, for an overclocked 2 Pro),
**`handy2`** (600 sustained / 700 peak), **`handy1`** (364, firmware). The gallery, all three
custom-enemy package trees and `_example` moved with `git mv`; `pncpaths`, `variants`, `speedcheck`,
`release`, `handystate`, `animcheck`, `animsweep`, `ladders`, `rederive`, `refvideo`, `grabs031`,
both EdiConfig files and every document that named a folder followed.

**The rename has a cost, and it is worth stating because it will come up again.** The variant is a
folder name, so it lives in every player's `EdiConfig.json` — and 2.5.2, which is what is posted,
ships `detailed`. The archive README says so at the point where it tells you to set the variant and
again in troubleshooting; that was the chosen migration, over a compatibility symlink. Worse than a
config that breaks loudly is one that does not: `deploy.py` overlays and never removed the old
folder, so both installs kept a complete, still-resolving `detailed/` afterwards. A device left on
the old name would have played a gallery nobody maintains, silently. `deploy.py` now reports any
gallery variant folder an install carries that the tree does not build — reported, not deleted,
because a folder is a lot to remove on a name comparison and a player may have authored one.

### Packages get the variant too, and three of their masters are broken

A device pointed at a variant a package does not carry plays **nothing** for that enemy — §5567's
parity rule, one level up. `variants.py --write` now emits `handy2/` for every package from that
package's own `handy2pro/` masters. Package `handy1/` folders are left alone: those were authored by
hand against the Handy 1, not slew-limited, and regenerating them would throw that work away.

That pass found something nothing else could have. Three femboy-witch masters —
`femboy_witch_aura_0_b`, `_1` and `_3` — end `61128 ms` then `60000 ms`: a tail written out of
order, past the row's own duration. **No check in this project has ever had an opinion about them**,
because `speedcheck.analyse` drops `dt <= 0` pairs before it measures anything and packages are not
in `speedcheck` at all. It surfaced here because a negative `dt` inverts the limiter's clamp and
drags every position after it, which read as a *variant with more range than its master*. The
limiter now passes such a pair through untouched and names the file; the masters are what need
fixing, and a limiter quietly repairing its input would have hidden this a third time. **They are
still unfixed** — that is a scripting job, not a tooling one.

### State

`check.py` 9/9 with both installs deployed and current. The three witch masters above are open.


## 150. Softening a scene without editing its script

The other half of the thread's post 113 list: a player whose desk `imp_3` shakes was told to copy
the `handy1` variant over `detailed` as a stopgap. That is the wrong lever twice over - it swaps a
*speed* limit in to fix a *strength* complaint, and it does it by overwriting the masters.

The right lever already existed and was built for something else. §125 put the serpent's approach on
`POST /Edi/Intensity/{max}`, which moves `device.Max` in place without re-dispatching: the row keeps
playing, the phase holds within 22 ms, and the scene simply gets shallower. Everything the mod sends
that way goes through one function, so the player's own scaling belongs there and nowhere else.

**Two settings, both under `[EDI]` and both live from F11.** `MasterIntensity` (0-100, default 100)
scales everything; `RowIntensityScale` is `row=percent;row=percent` for the case that is actually
being reported, which is one or two rows rather than all of them - `imp_3=60;imp_3_Gallery=60`.

**They compose by multiplication, and that direction is the point.** `SendIntensity` now records
what the *scene* asked for and `ApplyIntensity` derives what the device is told:
`requested × master × row`. A serpent approach at 44% under a master of 50% is 22%, not 50% - a
player turning the master down can never make a scene louder than it asked to be. The two are
tracked apart because they answer to different things: a scene lowers the range for a reason of its
own and raises it when that reason ends, while the player's setting is a standing preference that
has to survive every one of those changes.

Two re-derivations keep it honest. `SendPlay` calls `ApplyIntensity` once the new row is live,
because the per-row scale belongs to the row and changes under scenes that never touch intensity at
all; and `Update` polls both settings, because the mod manager writes config live and a softening
you cannot feel until the next scene change reads as broken. Neither sends anything unless the
derived figure moved, and `_lastIntensitySent` now holds the *scaled* value, so the existing
dedupe still does its job.

What this deliberately does not do is answer the other half of that complaint. Edi's endpoint moves
only `Max`; `Min` stays where the device is configured, so this scales amplitude anchored at the
bottom of the stroke rather than narrowing it around its middle. Both config descriptions and the
archive README say so, and the README also says which complaint the *variant* folders answer
instead: too fast is a variant, too strong is these two knobs.

Unplayed. `check.py` 9/9.


## 151. The chaser bosses get an aura, and the ramp is rate-limited

The last of the release thread's feature requests (post 113's list, §147 for what that list is and
is not): the filler should build as the dragon's or the wendigo's approach closes in, instead of
playing the same way whether the boss is across the floor or behind you. `ChaserAura.cs`, and the
whole of it is `SerpentHypnosis`' §125 apparatus pointed at a second signal - one row, no tiers,
`POST /Edi/Intensity/{max}` moving the device's range in place while the filler keeps looping.

**"Speeds up" is not a thing this can do, and the request is better served without it.** Edi has no
playback-rate control - `Definitions.csv` can slice a file but not time-scale one, which is why the
twelve `*_Gallery` rows exist at all - so the only ways to make the filler *faster* are a second set
of files and a ladder to switch between them. That is precisely the shape §120 and §125 dismantled:
a ladder over a short band is coarse rather than slow, and adding rungs back is a move already
rejected. Amplitude has no such problem, moves continuously, and needs no seam. So the aura closes
in by getting deeper, and the funscript set gains nothing.

**The gate is the sound, which is what was actually asked for.**
`DragonEnemyAI.UpdateIdleMovingSound` plays `idleMovingSound` on `loopingAudioSource` while
`!isDead && !frozenByArena && (state is Idle or Chasing) && !isAttemptingGrab`, and stops it
otherwise. Reading `loopingAudioSource.isPlaying` is that whole predicate one frame fresh, the same
posture as reading vanilla's `hypnosisInView` rather than recomputing visibility. It also gets §47's
wendigo right on purpose rather than by luck - one parked in the level with its AI ticking, waiting
for its trigger time, is audible, and the request is about what you can hear.

**No scene search.** Both AI classes keep a public static `ActiveDragons`, added to in `OnEnable`
and removed in `OnDisable`, so the live set is two list walks of length 0 or 1 and an enemy the mod
itself hides leaves it unaided.

**The far edge of the band is a config number and the near edge is the prefab's.** The serpent could
take both from the mechanic (`hypnosisStartRange` down to `grabRange`); here the honest far edge
would be the looping source's `maxDistance`, but `InitializeComponents` sets only `loop` and
`playOnAwake` on that source, so its spatial settings come from the prefab - and where the game adds
the source at runtime, Unity's default is a *non-spatial* one claiming 500 m, which would put a whole
floor at the far value and hide the ramp. `ChaserAuraRange` is therefore an explicit 25 m, `0` means
"trust the source", and the `[CHASER-AURA]` line prints the source's own figure alongside so one run
says which it should have been. `grabRange` is the near edge, where the grab lands and its own scene
takes the device.

**The new idea is the slew limit, and it is what answers the objection the request arrived with.**
Post 113's own reply says driving intensity off a distance tends to read as jerky, and the serpent's
ramp escapes that only because its band is entered by a mechanic that starts at the far edge. This
band has no such courtesy: a loop starting or stopping, a chaser dying, one walking out of earshot,
a second becoming the nearest - each moves the target in one step. `ChaserAuraRamp` (45 %/s) caps
how fast the *held* value may move toward the target, so every one of those is a slide. It also
replaces hysteresis outright: a value that cannot step cannot flap, which is the same conclusion
§125 reached from the other direction and the answer §112 reached with a dwell.

**Two owners, one channel-wide number, and three rules that keep them apart.** The serpent outranks
the aura, which stands down while `SerpentHypnosis.OwnsIntensity` - it keeps slewing its held value
so it has somewhere sane to resume from, and sends nothing. The aura compares against
`Plugin.RequestedIntensity` rather than its own last figure, so a channel moved under it by anything
else is reasserted rather than believed. And leaving the band slews, while a real scene starting
takes the range back *at once* - §125's second run is what the alternative costs, a 15 s grab played
at the amplitude the last approach left behind. `Tick` runs from `Plugin.Update` for exactly that
case: a grab is when the filler refresh it would otherwise live in stops being called.

Documented where each audience looks: `PROJECT.md`'s dispatch walkthrough now says three things
write that endpoint rather than one, `learnings/edi-integration.md` carries the slew rule and the
two-owners rule, and the archive README says what a player will feel and which line turns it off.
It consults no gameplay profile and should not: it moves the device's stroke range and nothing
else, and `Vanilla`'s promise is that device playback stays on.

Ships on. Unplayed, like everything since §146; `check.py` 9/9 and both installs deployed.


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

The run also found six new things, none of which needed a further play session to build. One —
both installs' `EdiConfig.json` still pointing every device at the retired `detailed` variant, so a
Windows launch today would have played two packages and nothing else — was fixed the same day it
was found, from the deploy warning §149 added for exactly this, and needed no rebuild: `detailed`
-> `handy2pro` in both files' `Variant` entries, the stale regenerated `detailed/` folders deleted,
`deploy.py --check` clean again. Four more are fixed below. The sixth — a white screen after death,
now narrowed to one disabled `Animator` component rather than §50's unreadable ancestor — is a
visual bug in the game's own rendering and is deliberately left for a session of its own.

**The menu filler was silent after quitting to the menu from a paused grab**, because §148 made a
menu *play the filler* rather than stop Edi, and `PauseHooks.ResetForNewScene` still assumed the
scene change itself always resolved the device — clearing `Pause?untilResume=true` was left to
whichever of "the menu stops Edi" or "the filler starts" actually happened, and neither does that
job any more once a menu plays the filler instead of stopping it:

    17:05:39.503 [PAUSE] in-game pause menu opened -> Edi/Pause      (correct - a grapple was live)
    17:05:40.107 [PAUSE] scene changed while paused -> pause state cleared
    17:05:40.107 [EDI] Play filler                                   <- the device is still paused
    17:06:21.009 [FOCUS] regained -> Edi/Resume                      <- an alt-tab is what fixed it

`ResetForNewScene` now sends Resume when `_devicePaused`, ahead of the menu-filler dispatch in
`OnSceneChanged` — an ordering already true before this fix, since `PauseHooks.ResetForNewScene()`
was already called before the `_inMenuScene` branch; only the missing Resume itself needed adding.
`learnings/README.md`'s lesson 12 — *superseding a mechanism is not removing what rode on it* — is
this exact shape a second time, so the addition there is a citation of this case rather than a new
rule (see `learnings/game-scenes.md`).

**The chaser aura ran, and needed one config number rather than a rebuild.** The line the whole
feature was built to print:

    [CHASER-AURA] Dragon at 10.0m of 25.0-3.0 (its loop reaches 30.0m) -> 97%

The looping source's own `maxDistance` is 30.0 m — spatial and sane, not the 500 m the code feared
— which answers §151's open question, and answers it against `ChaserAuraRange = 0`: 30 m is wider
than the shipped 25 and would flatten the ramp further. The dragon's whole approach lived between
3.5 m and 13.6 m; against the shipped `25-3` band that is only 84-100%, a spread nobody can feel,
and every close approach hit 100 and released the device mid-chase. `ChaserAuraRange` is now **12**
in `BepInEx/config/com.edi.pnc.cfg`, which puts that same approach across the full 55-100 band, and
declared in `release.py`'s `SHIPPED` (coded default stays 25 — this is a measured live value, not a
new default). Judging it by feel is still a play question, same as §151 always said it would be.

One real defect rode along in the same log line: on the slew back up after a chaser goes quiet,
`ChaserAura.TargetFor` clears `_who` to `null` but leaves `_whoDistance` at its `float.MaxValue`
seed, and `Describe()` formatted it anyway —

    [CHASER-AURA]  at 340282300000000000000000000000000000000.0m of 0.0-0.0 (its loop reaches 0.0m) -> 60%

— the *send* was correct (the deliberate slew home), only the description was garbage. `Describe()`
now special-cases `_who == null` with its own wording, "no chaser audible, slewing back to 100%",
rather than formatting stale sentinel fields.

**The heat locks were cleared by entering the shop, so the service exemption paid out nothing.**
Found in play, both halves of it ten seconds apart:

    16:56:32 [SCENE] '' -> 'Stage1Shop'                     (locks were 5/8 on the floor before it)
    16:56:39 [HEAT-LOCK] queued clear-all release from service GloryHoleCamera after watchtime
    16:56:49 [HEAT-LOCK] peephole not spent, no locks held at payout from service GloryHoleCamera

`HeatLockSystem.ResetForScene` zeroed `_locks` on *every* scene transition, including
`Floor1 -> Stage1Shop`, so §147's service exemption — armed a few seconds after the shop loads,
paid out ten seconds after that — always found an empty set by the time it ran. `ResetForScene` now
takes the destination scene name and skips the `_locks = 0` when it matches `shop` (the same
substring convention `Plugin.IsMenuSceneName` uses for `menu`), so locks held on the way into a shop
survive it; the next real floor is not a shop scene either way, so it still clears there as
observed above. `GameplayProfiles.OnProfileChanged`'s call passes no scene name and clears
unconditionally, unchanged — a profile switch mid-run is not a scene the player walked into.

**The `[OVERHEAT]` instrument was misread a fourth time, by its own prescribed fix.** §139 gave the
`STUCK` line a 0.5 s dwell specifically so a fix-produced transient — the one frame between vanilla
failing to clear `hasBeenOverheated` and `ClearOverheatAtLockFloor` clearing it — would not read as
the defect. This run produced nine `STUCK` lines across four grabs, three of them past that
dwell's own threshold:

    17:02:15.829 [OVERHEAT] hasBeenOverheated=True canAttack=False heat=175.0/175.0 floor=19.4
    17:02:16.383 [OVERHEAT] STUCK: ... held=0.5s heat=150.3/175.0 floor=19.4 canAttack=False
    17:02:17.384 [OVERHEAT] STUCK: ... held=1.5s heat=99.8/175.0  floor=19.4 canAttack=False
    17:02:18.384 [OVERHEAT] STUCK: ... held=2.5s heat=42.3/175.0  floor=19.4 canAttack=False
    17:02:18.801 [OVERHEAT] hasBeenOverheated=False canAttack=True heat=18.1/175.0 floor=19.4

Every one of the four sequences ended the same way: the latch cleared within a fraction of a second
of heat reaching the lock floor. The `held=` window was the **cum-cooldown drain**, during which
the latch is *supposed* to hold — and that drain took up to 2.5 s here, well past the dwell meant to
absorb a one-frame transient. **A dwell of any length cannot separate "the fix is still running" from
"the defect is present", because both are just "the state has held for a while."** What can: the
defect is specifically *still latched after heat has reached the lock floor*, a state vanilla's own
clear should make unreachable. `TraceOverheatLatch` now gates `STUCK` on
`heat <= floor + StuckLatchFloorEpsilon` (0.05, float noise only) instead of on a duration, so it
stays quiet for the whole drain and fires only on the thing actually reported. `learnings/README.md`
lesson 21 and its home in `debugging-and-diagnostics.md` are corrected rather than merely cited —
the dwell they prescribed was itself the fourth misreading, not a fix to it.

All four are built and deployed to both installs (`check.py` 9/9 after each) but **none has been
played** — that is the next session's job, alongside the run's own `CHANGELOG` narrative for these
findings being this entry itself and a commit for the six files it touches
(`HeatLockSystem.cs`, `PauseHooks.cs`, `Plugin.cs`, `ChaserAura.cs`, `release.py`,
`BepInEx/config/com.edi.pnc.cfg`).


## 153. §152's four fixes played, a new pause defect found, and the chaser aura rebuilt as a real row

A second run, 17:57–18:12 on 2026-08-29, one log (`game-linux/BepInEx/LogOutput.log`, no rotation
since launch). Three of §152's four fixes are confirmed; the fourth prompted a redesign rather
than a confirmation, once played against.

**Item 3 (heat locks survive shop entry) holds on an independent run.** `'' -> 'Stage1Shop'
playerStats=yes baseHeat=100` at 18:08:41, five locks carried in from the floor before it, and at
18:09:05 `[HEAT-LOCK] clear all locks from service GloryHoleCamera -> 0/9 (was 5)` — a real,
nonzero payout. Closed.

**Item 5 (the `STUCK` gate) holds too, cleanly.** Two `STUCK` lines this run, both
`held=0.0s`, both clearing the same frame heat reached the lock floor — no more of the
multi-second holds `heat <= floor + epsilon` was built to stop misreading as the defect. One after
a `Mimic_Cum`, one after a crossbow shot following a mimic grab; both `hasBeenOverheated=False
canAttack=True` within 5 ms of the `STUCK` line. Closed.

**Item 1 (menu filler after quitting a paused grab) holds for the case it was built for, and
surfaced a second pause defect it was never built for.** Quitting to the main menu from a paused
grab now sends `Edi/Resume` before the menu filler, confirmed. But alt-tabbing *while the pause
menu is still open* replays the last grab script instead of staying silent:

    18:00:47.134 [PAUSE] in-game pause menu opened -> Edi/Pause          (_devicePaused=true)
    18:01:01.330 [FOCUS] lost -> Edi/Pause
    18:01:02.752 [FOCUS] regained -> Edi/Resume                          <- replays imp_2, menu still open
    18:01:06.555 [FOCUS] lost -> Edi/Pause
    18:02:18.120 [FOCUS] regained -> Edi/Resume                          <- again
    18:02:18.242 [PAUSE] in-game pause menu closed -> Edi/Resume         <- the real unpause, 122 ms later

`Plugin.OnApplicationFocus`'s regain branch calls `SendResume()` off its own `EdiPausedByFocus`
flag alone, with no read of `PauseHooks.GamePaused` — two independent pause sources stack (the
game's own pause menu, and alt-tab) and only the inner one is checked on the way back out, so a
focus regain undoes the *menu's* pause a full minute before the player actually closed it.
**Diagnosed, not fixed** — the next session's first job.

**Item 2 was never a bug, and became a design conversation instead.** `ChaserAura` fired exactly
as built — `[CHASER-AURA] Dragon at 8.6m of 12.0-3.0 ... -> 99%` down to `62%` before the dragon's
audio cut out for a grab — but "still no chaser script playing whatsoever" was the real complaint
underneath the report: `Edi/Intensity/{max}` can only ever cap a row's travel *down* from what it
was authored for, never past it, so the closest the aura could ever make the device feel was the
filler at its own ordinary depth. Asked directly: should the approach read as *more* than baseline
right at grab range, built as a real row rather than a squeeze. Also asked: could that row be
synced to the actual footfall, and does that work for both bosses — worth its own record, because
answering it needed the kind of measurement the "look at the scene, then measure" rule is for
rather than a guess.

**Wendigo needed no separate code at all — confirmed off the live assembly, not assumed.** There is
no `WendigoEnemyAI` class (`monodis --typedef` against `Assembly-CSharp.dll` lists none); a wendigo
is a reskinned `ProximityDragonEnemyAI` prefab, same as `ChaserAura` already walked. Tracing the
same prefab's actual serialized fields (the `TypeTreeGenerator` technique `spawntables.py` already
used, applied here to `DragonEnemyAI`/`ProximityDragonEnemyAI` directly rather than a spawn table)
confirmed `idleMovingSound` = `DragonWalk` on `Dragon`, `"Wendigo walk"` on `Wendigo` — and ruled
out a look-alike red herring: `Dragged Away Dragon Near` / `Dragged Away Wendigo`, found in the
same asset sweep, turned out to be a plain `playOnAwake, Loop=true` `AudioSource` sitting directly
on each GameObject, not bound to any `DragonEnemyAI` field at all — always-on ambience with a
10–30 m rolloff, not a scripted "near" cue, despite the name.

**Counting the beat needed a human ear, not just a better filter.** Onset detection against
`DragonWalk.wav` and `"Wendigo walk".wav` (pulled via `UnityPy`, archived to `Edi/_reference/audio/`
- gitignored, kept for re-measurement) never converged on its own: a spectral-flux detector tuned
tight enough to catch every footfall also caught the dragon's own noise (150 "onsets" where 43
stomps are real) and a low drone that swells and recedes between wendigo beats (up to 35 where 12
are real). Widening the detector's minimum gap to roughly the beat a human ear already suspected -
not narrowing it - is what resolved both, and only once the ear supplied the true count first:
**43 dragon stomps over 25.8 s (605 ms mean gap, std 19 ms) and 12 wendigo stomps over 7.2 s
(603 ms, std 37 ms)**, confirmed by ear against the detector's own settled answer. Two different
creatures landing on nearly the same cadence is recorded as a coincidence, not a rule for any
chaser this project adds later. `learnings/funscript-proxies.md` has the general lesson.

**`Dragon_Stomp` / `Wendigo_Stomp`, one cycle each at the measured period, peak 90** (the same
figure and the same reasoning as `Serpent_Hypnosis`: played instead of the filler outright, so the
authored row already has to be the loudest the approach will ever be). Shape is a judgement, not a
further measurement - nothing here measured a single stomp's own envelope, only when each one
lands - so it is peak-at-the-beat, a fast release, a slow settle, an easing climb back to the next
peak, the same idiom `shared_zombie`'s buzz already established (large fast strokes read as the
impact). `code/ladders.py`'s `CHASER_STOMP_ROWS` has the full reasoning and both rows' numbers;
`variants.py --write` generated `handy2`/`handy1` copies the ordinary way, no exceptions.

**`ChaserAura.cs` is gone, folded into a new `ChaserStomp.cs`.** Once a real row existed, the old
mechanism's own reason for touching the filler disappeared - a chaser close enough to be part of
either mechanism is now always playing its stomp row, never the filler, so there was nothing left
for an Intensity squeeze on the filler to be squeezing. The merge kept both of the old file's real
pieces and gave them one new one:

  - **The gate** (audible + within `ChaserStompRange`, 0 = trust the source's own `maxDistance`) is
    unchanged from `ChaserAura`'s, renamed.
  - **The intensity ramp** (`ChaserStompIntensityFar`/`Near`, `ChaserStompRamp`,
    `ChaserStompIntensityStep`/`Interval`) is unchanged in mechanism, retargeted to cap the stomp
    row's own travel instead of the filler's.
  - **The row itself is new**, phase-locked on first dispatch to the creature's own
    `idleMovingSound` `AudioSource.time` by reusing `Plugin.SendPlay`'s existing animator-phase
    machinery (`animNormalizedTime`/`animClipSeconds`) fed an audio clock instead - nothing in that
    math is Animator-specific, and `GalleryRegistry.LoopMs(row)` doubling as the beat period means
    the funscript's declared length and the phase math can never drift apart. Two measured offsets
    (`DragonFirstOnsetSec` 90 ms, `WendigoFirstOnsetSec` 60 ms) correct for the one thing that math
    cannot know on its own: the walk clip's *audio file* loops at its own t=0, not at a footfall.
  - **A hold the old file never needed.** `ChaserAura`'s own header said hysteresis and a dwell
    were both unnecessary, and it was right - a slewed number self-damps a flickering target for
    free, so nothing could flap. That reasoning does not survive the row: there is no way to slew
    between two different funscripts, so the same flickering `isPlaying`/range gate that the ramp
    shrugged off would have meant the device restarting the beat on every crossing. `ChaserStompGrace`
    (1.5 s, `SerpentHypnosisViewGrace`'s own default) holds the row across a lost gate the same
    shape the serpent's view grace already uses for a different flickering boolean. This is the
    fourth answer this project has given to a signal that crosses a boundary too fast to feel
    (§112's dwell, §125's abolition of the crossing, §151's slew, now a hold) - and the first time
    two different answers were both live in one mechanism at once, because a ramp and a row-switch
    are different kinds of thing being driven off the same gate.

**Config renamed wholesale, `ChaserAura*` -> `ChaserStomp*`, confirmed nothing has shipped to
players to need back-compat for.** `release.py`'s `SHIPPED` entry moved with it (still `LIVE`,
still 12 - the reasoning is unchanged, only the mechanism the number now describes).
`learnings/edi-integration.md` has the two reusable pieces: feeding `SendPlay`'s phase machinery a
non-Animator clock, and the slew-vs-hold distinction.

`dotnet build`/`dotnet test` (112/112)/`check.py` (9/9, cfgaudit and release both clean against the
rename) all pass and both installs are deployed. **The chaser stomp mechanism itself is desk-verified
only - not yet played.** Nothing from this session or §152 is committed; the working tree now also
carries a new `ChaserStomp.cs`, a deleted `ChaserAura.cs`, `PluginConfig.cs`, `SerpentHypnosis.cs`,
`ladders.py`, `release.py`, `Definitions.csv`, and six new funscripts across the three variant
folders, on top of §152's own six files.

## 154. §153's focus/pause defect fixed (twice), ChaserStomp played and retuned, and a silent lock-loss found

A 2026-08-30 session against `LogOutput.log` (03:06-03:27), driving §153's one open defect plus the
first play of the rebuilt chaser stomp mechanism.

**The focus/pause fix took two passes, because the first one only covered half the state space.**
§153's defect was `Plugin.OnApplicationFocus`'s regain branch calling `SendResume()` off its own
`EdiPausedByFocus` flag alone, with no read of `PauseHooks.GamePaused` - an alt-tab while the pause
menu was still open undid the menu's own pause a full minute early. The first fix guarded the regain
on `!PauseHooks.GamePaused`. Before it was ever played, a second look at `FillerWhilePaused` caught
what that guard breaks: opening the menu with the filler active leaves `_devicePaused=false` (the
filler keeps running, `PauseGame_Postfix` never sends a Pause) - but losing focus pauses it anyway,
because `OnApplicationFocus`'s own `SendPause()` call has never checked `FillerWhilePaused`. Blanket-
skipping the regain's Resume whenever `GamePaused` is true would leave that pause permanently stuck:
`ResumeGame_Postfix` also checks `_devicePaused` (false) and does nothing when the menu closes.
`PauseHooks` grew a `DevicePausedByMenu` accessor (`_devicePaused`, exposed) so the guard could ask
the sharper question - defer to the menu only when the menu is the one actually holding the device
paused, not merely whenever it is open. Played both branches (`Plugin.cs`, `PauseHooks.cs`):
confirmed correct.

**Playing the filler-active branch surfaced a second, unrelated design gap in the same code path.**
`FillerWhilePaused`'s whole feature was "leave whatever filler happens to be already playing running
across a pause" - which meant the pause menu could open on the last ladder rung or mid-chaser-stomp
rather than a neutral row, and if nothing had been actively dispatched that exact frame nothing
started at all, because the branch just `return`ed. `Plugin.PauseFillerForMenu`/`ResumeFillerFromMenu`
now force-switch to the plain `FillerGallery` row on open, saving the outgoing row and its loop phase
(`CurrentLoopPhaseMs()`, captured before the swap overwrites it) so the close can restore the exact
row at the exact position rather than whatever the ladder reads as fresh. `SendPlay` grew a
`seekOverrideMs` parameter for the restore, because `preservePhase`'s existing equality check
compares against the *outgoing* row at call time (the base filler), not the row being restored -
different question, needs its own answer. `CanRefreshFillerForHeat` now also stands down while
`PauseHooks.GamePaused`, so the ladder cannot recompute over the swap mid-pause; `ResetForNewScene`
clears the saved state on any scene change made while paused, so quitting to menu cannot leak it into
whatever loads next. Built and deployed; not yet played (found and fixed after this session's run,
in review rather than in-game). `learnings/edi-integration.md` has the reusable shape.

**`ChaserStomp` played for the first time, both bosses, and the phase-lock and grace both held.**
The beat landed with the audible footfall for both `Dragon_Stomp` and `Wendigo_Stomp`, and
`ChaserStompGrace` visibly did its job - repeated `out of range - holding ... for up to 1.5s` /
`stayed out of range - the stomp gives the device back` pairs in the log, no beat restarts from a
flickering gate. Dragon and Wendigo were briefly both in range at once during this session
(03:12:10, alternating dispatch every few ms) - real flapping, but only possible because this was a
test session with both bosses present; a normal floor spawns one or the other, never both, so this
is not a defect to chase.

**The intensity ramp itself read wrong, and not from ramp lag.** `ChaserStompIntensityNear` (100%)
was only ever reached at the chaser's own `grabRange` - a few metres, "basically touching" - so a
real approach spent almost all of itself between `ChaserStompIntensityFar` and something close to
100% off ramp momentum, never settling at the tuned far-edge value the log kept showing (91-99% just
inside a 12 m band whose far value is 55). `ChaserStompIntensityNearDistance` (new, defaults to 5 m,
clamped to at least `grabRange`) decouples "where the ramp saturates" from "where the grab lands" -
100% is now reached a few metres out and held from there in, not only at the instant of contact.
`ChaserStompIntensityFar` also dropped 55 -> 50. Both changed in `PluginConfig.cs`,
`com.edi.pnc.cfg`, and `ChaserStomp.cs`'s `IntensityTargetFor`; `release.py`'s `ChaserStompRange`
comment updated to match, no new `SHIPPED` entry needed since the cfg and the coded default now
agree. Not yet played with the new numbers.

**A real, silent bug: entering the shop cost 3 of 8 earned heat locks, with no log line for it.**
`[SCENE] '' -> 'Stage1Shop' ... baseHeat=100` at 03:22:13, locks 8/8 going in; the next lock-related
line, 45 seconds later, was `clear all locks from service GloryHoleCamera -> 0/8 (was 5)` - proving
the count had already silently dropped to 5 with nothing printed for it. Root cause is
`HeatLockSystem.RecordBaseHeat` (`HeatLockSystem.cs:575`): whenever the live `MaxHeat` differs from
the cached `_baseHeat` it clamps `_locks` down to `GetTotalLocks()` at the new capacity - a real
feature for when armour actually shrinks capacity mid-run, but it fired here off a transient,
unscaled reading. This is §148's still-open ambiguity (`learnings/debugging-and-diagnostics.md`) -
whether a scene load's first `MaxHeat` read lands before or after the locks' own scaling multiplier
reapplies - and §153's play only ever settled it for floor-to-floor transitions (correct ordering,
no defect). Shop entry takes the *other* ordering: `baseHeat=100` is the vanilla, unscaled figure,
`GetTotalLocks()` at that capacity is 5 - "five locks for every class", exactly what the learning
predicted - and the clamp cut real progress with nothing to show for it because the clamp path never
logs. **Diagnosed, not fixed** - the next session's first job. `learnings/debugging-and-diagnostics.md`
has the addendum to §148's entry.

`dotnet build`/`dotnet test` (112/112)/`check.py` (9/9, cfgaudit and release clean against the new
`ChaserStompIntensityNearDistance` key and the retuned defaults) all pass and both installs are
deployed. Nothing from this session or §152/§153 is committed. The session log (03:06-03:27) has the
evidence for all of the above and is preserved at
`game-linux/BepInEx/logs/LogOutput-20260830-preserved-shop-heat-lock-bug.log`.

## 155. §154's shop fix played wrong and re-diagnosed from timestamps, and ChaserStomp's ramp deleted in favour of the row's own grace

A desk session, no new play - working from §154's preserved log
(`LogOutput-20260830-preserved-shop-heat-lock-bug.log`) and a fresh decompile, not a new run.

**§154's shop fix was built on a theory nobody had actually checked against the log's own
timestamps, and it did not survive being played.** The fix skipped `RecordBaseHeat`'s clamp on the
first reading since a scene reset, on the theory that the shop's transient `baseHeat=100` arrives
*after* `ResetForScene` zeroes `_baseHeat` - consistent with how the printed log line read, never
checked further. Played: still clamped 8 locks to 5. Lining the two log lines' own timestamps up
(not just their printed content) found the theory backwards: `[HEAT-LOCK] capacity shrink clamp:
8 -> 5 locks` prints at `03:56:50.794`, **21 ms before** `[SCENE] '' -> 'Stage1Shop'` at
`03:56:50.815` - the clamp fires before `Plugin.OnSceneChanged` runs at all, while `_baseHeat` still
holds the previous floor's real value. Something in the shop's entry trigger calls
`SetMaxHeat(100)` synchronously in the *old* scene, and the shop then never sends a correcting
`SetMaxHeat` - `MaxHeat` genuinely stays 100 for the whole visit, so no amount of waiting for "a
truer second reading" could have worked either. `learnings/debugging-and-diagnostics.md` has the
generalised lesson: an ordering theory is still a guess until the timestamps are actually compared,
even when it is built by reading a log rather than by reasoning about which Unity callback runs
first.

The real fix defers the clamp instead of gating it on a reset. `RecordBaseHeat` now arms a pending
clamp (`_pendingClampTotalLocks`/`_pendingClampAt`) rather than applying it; `HeatLockSystem.Tick`
lands it after `PendingClampConfirmSeconds` (0.5s) with nothing to contradict it - a real mid-floor
armour shrink survives that window because nothing corrects it either, which is exactly how it
should behave - and `ResetForScene` discards any pending clamp outright on *any* scene change, since
a shop transition is precisely the case needing protection and a non-shop transition is about to
zero `_locks` outright regardless. The clamp also now logs unconditionally when it actually fires,
which is what caught the first fix's failure at all - without that line this would have shipped
believed-fixed. Built, `dotnet test` 112/112, `check.py` 9/9, both installs deployed. **Still
unplayed** - needs a shop-entry run, and ideally one genuine mid-floor armour-capacity change to
confirm the clamp still fires when it should.

**Separately, playtesting turned up a `ChaserStomp` band tuned too tight, and chasing that question
found the intensity ramp itself was solving the wrong problem.** `ChaserStompRange = 12` (from
§154) put the near-boundary experience inside the Wendigo/Dragon AI's own ambiguous
idle/not-quite-chasing zone rather than a zone it reliably holds while actually closing in -
confirmed off the log, which showed repeated 1-2s bursts of play followed by exactly
`ChaserStompGrace` later giving the device back, at distances reading as wandering rather than
approach. `ChaserStompRange` is now **0** (the honest `AudioSource.maxDistance`, 30 m for both
prefabs per the log's own `its loop reaches 30.0m`) rather than a hand-picked figure that can drift
out of sync with the prefab, and `ChaserStompIntensityFar` dropped **50 -> 30** (declared in
`release.py`'s `SHIPPED`) so the near end of the experience does not dilute across three times the
distance.

Widening the band raised the question of whether `ChaserStompRamp` (45%/s) could track a player
closing that distance in a dash or two, and the answer was no - for a reason that also applied at
the old, narrower range. `ChaserStomp`'s gate is distance **and** `loop.isPlaying`, a state boolean,
not a continuous reading; decompiling `DragonEnemyAI`/`ProximityDragonEnemyAI` with `ilspycmd`
found the boolean's real source: `GrabSequence` holds `isAttemptingGrab` (silencing the gate) for
exactly `grabAttemptDuration`, 1.5s, win or miss, every real grab attempt. The ramp was rate-
limiting *all* target movement to damp that boolean's flicker, but the same cap also throttled
genuine fast movement - a dash-speed approach is not noise, it is the event the mechanism exists to
track, and the ramp reported it late by design. `SerpentHypnosis`'s own history was already the
proof a continuous, distance-driven value does not need rate-limiting at all (no ramp, direct
jumps, measured accurate within 22 ms on real hardware) - the boolean, not the distance, was always
the thing that needed a guard. **`ChaserStompRamp` is deleted** (config entry and all); the
intensity target is now assigned directly off distance the instant the gate reads true, and held -
not slewed, not recomputed from a now-stale reading - across a lost gate for `ChaserStompGrace`,
releasing to 100% in one step once the grace expires, exactly mirroring how the row already hands
itself back. That made the grace's own value load-bearing for the first time, so it was measured
rather than left at its borrowed default: `ChaserStompGrace` was 1.5s, exactly equal to the measured
`grabAttemptDuration` - a coin flip on every single grab attempt, not a guard. It is now **2.0s**,
clearing the measured hazard with margin. `learnings/edi-integration.md` has the corrected general
shape (a slew answers a fast-moving number; a stuck state needs a hold, and the two are not the
same problem just because they move the same field).

Built, `dotnet test` 112/112, `check.py` 9/9 (`release.py`'s `SHIPPED` updated for
`ChaserStompIntensityFar`), both installs deployed. **Entirely unplayed** - needs a run near the new
wider band, and specifically several close-range grab attempts, to confirm the hold survives a real
1.5s windup without reading as flicker and that `IntensityFar=30` does not read as starting too
early across the wider band.

**And one more thing found but not yet chased: pausing/unpausing while a real (non-filler) scene's
script is playing was reported as a small desync.** Not reproduced from this session's log - every
`[PAUSE] ... closed -> Edi/Resume` in it is followed only by filler restores, never a stray re-`Play`
of a scene row. A real hazard exists in the source (`SendPause`/`SendResume` stamp `LastSent` to a
sentinel, which would defeat `SendPlay`'s own "same alias within 0.25s" dedupe for the next
legitimate re-dispatch of that row) but nothing ties it to the reported symptom yet. Needs a repro:
which scene, and whether an `[EDI] Play <row>` line appears within a second or two of the next
`Resume` line.


## 156. The three femboy-witch masters' backwards timestamps, fixed by tracing Edi's own loader

A desk session, no play needed - the fix is data-only and the loader's own filter proves it inert.

§149 found three `femboy-witch` `aura` masters ending with a tail written past the row's own 60s
duration - `femboy_witch_aura_0_b`, `_1` and `_3` each had a final action or two that read `at`
values above 60000, then one landing back at exactly 60000. `speedcheck.analyse` drops any `dt <= 0`
pair before measuring, so it never had an opinion, and packages are not in `speedcheck` at all;
§149 left the fix as a scripting job, and open question of whether the tail was a real closing
stroke that belonged before 60000 or noise to drop, deferred to reading `FunscriptRepository.cs`
first.

Read it (`Edi.Core/Gallery/Funscript/FunscriptRepository.cs` in the decompiled tree at
`../testing/Edi/`). `ReadGallery` filters `.Where(x.at >= StartTime && x.at <= EndTime).OrderBy(x.at)`
before anything else runs, so any action past a row's declared `endTime` (60000 for every `Aura`
scene, per `enemy.json`) is dropped before dispatch - never played, regardless of where it sits in
the file or whether it reads earlier or later than its neighbour. `inproveLoopAccion` then forces
`last.pos = first.pos` unconditionally on whatever survives the filter, so even the in-window
closing action's own `pos` value is moot. Both masters' in-window last action already sat at exactly
`at=60000` with `pos` equal to the first action's `pos` in every file - the honest wrap point was
never missing, just followed by dead data.

**The tail is noise, confirmed rather than guessed**, and turned out bigger than §149's own read: a
grep-by-symptom for `dt<=0` finds only a *decreasing* pair, but `femboy_witch_aura_0_b` had six
actions strung out past 60000 (60065-61128 ms), all increasing relative to each other, so
`speedcheck`'s filter would not have flagged them even if packages were in scope for it. The other
two masters had one stray action each. **Fix**: every action with `at > 60000` dropped from all
three `handy2pro` masters, verified against the loader's own boundary rather than a guess, and the
same defect found and fixed identically in the package's hand-authored `handy1` copies - those are
not derived from the master (`variants.py` only emits `handy2` for a package, `handy1` is authored
by hand per its own comment) so needed their own pass. `code/variants.py --write` regenerated the
package's `handy2` from the corrected masters. `dotnet test` unaffected (data-only), `check.py` 9/9,
both installs deployed. Played implicitly: `FunscriptRepository`'s filter means gameplay was never
different, before or after - this is a data-hygiene fix, not a gameplay one, and needs no run to
confirm.

`learnings/funscript-authoring.md` has the generalised rule and now closes its own open question:
Edi sorts by `at` and clips to `endTime` on load, so a written-out-of-order action is invisible to
Edi and to this project's own checks alike, and the only way to be sure a suspected tail is dead is
to trace the loader, not to guess from the symptom's shape.


## 157. §155's shop-lock fix and ChaserStomp retune both played and confirmed; a real pause-menu gap found and fixed alongside them

A play session, this time against the code §154-§156 had only built and deployed.

**§155's deferred heat-lock clamp is confirmed - the shop no longer costs locks.** Entered
`Stage1Shop` at 8/8 locks (`baseHeat=100` at 15:29:11); no `capacity shrink clamp` line fired at
any point during the visit (there was nothing to contradict the pending clamp, so `Tick` never
landed one), and the two `[OVERHEAT]` lines just before entry both still read `locks=8/8`. Left the
shop via `clear all locks from service GloryHoleCamera -> 0/8 (was 8)` - the full count survived.
No genuine mid-floor armour shrink happened to occur this session, so the clamp's other half (that
it still fires when it should) remains unexercised; nothing about that is now known to be broken,
it simply was not tested.

**The reworked `ChaserStomp` band plays well** - confirmed against Wendigo: intensity read 88% at
10.0m and 99% at 6.2m, both against `IntensityFar` unchanged at 30 and no ramp artefacts, and the
grace held cleanly across two `out of range - holding ... for up to 2.0s` windows before releasing
(one `stayed out of range - the stomp gives the device back` when the gap didn't close in time).
**`ChaserStompIntensityNearDistance` moved 5 → 6 m** on the strength of that same read - 100%
was still landing a little later than wanted, and the play call was to give it another metre.
`PluginConfig.cs`'s default and `com.edi.pnc.cfg`'s shipped value were moved together, so they
still agree and no `SHIPPED` entry is needed.

**Playing the pause-menu filler fix (§154) surfaced a real gap it never covered: pausing during a
real scene row didn't switch to the base filler at all.** `PauseGame_Postfix` only ever called
`Plugin.PauseFillerForMenu()` when `Plugin.FillerPlaybackActive` was true; anything else - a
GoonShroom cling loop, `GoonShroom_Start`, any real gallery row - fell through to the plain
`Plugin.SendPause()` branch, which is Edi's own pause: it freezes the row exactly where it is
rather than swapping to a neutral row, which is what the fix's own commentary had documented as
deliberate ("a grab ... still pauses"). Playtesting against a GoonShroom at the start of a floor
showed the filter row simply frozen in the menu rather than replaced - not the behaviour wanted.

Fixed by widening the gate to `Plugin.FillerPlaybackActive || Plugin.IsGalleryPlaybackActive` and
generalising `PauseFillerForMenu`/`ResumeFillerFromMenu` to save and restore either kind of row.
The save side now branches on which was active: `_lastFillerGallery` for filler, `_lastSentRow`
for a real row, into the same `_fillerSavedGallery`/`_fillerSavedPhaseMs` pair as before, plus a
new `_fillerSavedWasFiller` flag so the restore's `SendPlay` call passes the right `filler` flag
back rather than always claiming the resumed row as filler (which would have left
`IsGalleryPlaybackActive` and everything gated on it lying for as long as that row kept playing).
`FillerWhilePaused`'s config description is updated to match - it previously promised the opposite
of the new behaviour outright. Played and confirmed both directions: `saved goonshroom_3 at
948ms` / `restore goonshroom_3 at 948ms` and `saved GoonShroom_Start at 84ms` / `1003ms` with
matching restores, both against real gallery rows rather than filler.

**§155's open pause/unpause desync item is dropped rather than left open.** Not reproduced this
session either, and worked back through with the player: nothing in this session's or last
session's log ties an `[EDI] Play <row>` to a `Resume` line, and the report is now believed to have
been imagined rather than observed. The hazard in `SendPause`/`SendResume`'s `LastSent` sentinel
handling is still real in the source if it ever does show up again, but there is nothing left
pointing at it as the cause of anything, so it does not belong in the open list on its own.

`dotnet build`/`dotnet test` (112/112)/`check.py` (9/9, `cfgaudit` and `release.py --check` clean
against the `ChaserStompIntensityNearDistance` retune) all pass; `deploy.py --no-build` was needed
once more after the config-only change (a DLL-only patch does not carry a `.cfg` edit) and both
installs are current. No mod-level warning or error in this session's log; the two `EDI-SKIP`
lines it has (`gravy_minotaur_intro`, `gravy_minotaur_bjstart`) are the seed table's own
intentional `-` targets for fade/intro states (`GalleryTable.cs`), not gaps.

## 158. The gameplay-profile audit: `Vanilla` really is vanilla, and one display-only gap found instead

The open item asking whether `Vanilla` actually leaves combat, health, heat and spawning to the
game — never audited before, and flagged as likely to have gaps because a patch only obeys
`GameplayProfileRules`'s truth table if it *asks*. Read `GameplayProfileRules.cs` and
`GameplayProfiles.cs` first, then all 30 `[HarmonyPatch]` classes in `code/edimod/PncEdi`, tracing
what each does under `Vanilla` specifically rather than trusting a grep for `ConfigEntry`.

**The five configs the open item named as suspects turned out not to be gaps at all.**
`CumDamageGate`, `EnemyGrabGate`, `GrabEndHelper`'s reactivation cooldown, `HeatPotionLocks` and
`GrabScreenAudioFill` all read `Plugin.GameplayTweaksEnabled` (or `HeatLockSystem.Enabled`, which
resolves the same way) before doing anything - the original grep found the raw `ConfigEntry` reads
and stopped one level short of the indirection that gates them. Same for `ClearOverheatAtLockFloor`,
`CumCooldownEndsAtLockFloor` and `FullLockHoldsCum`, this time confirmed by reading the call sites
(`HeatLockSystem.cs:1498`, `:289`, `:129`/`:167`) rather than assumed inert because there is nothing
for them to act on. Everything else with no profile reference at all - `GrabHooks`, `GrabEndHooks`,
`PauseHooks`, `GalleryHooks`, `PathfindingSpamFix`, `InteractDiag`, `FreeCamHooks` - was grepped for
`PlayerStats`/`SetMaxHeat`/`SetHealth`/`TakeDamage`/`SpawnCount`/`EnemyAI`/`Multiplier`/
`CanBeGrabbed` and came back empty: device-playback, UI and diagnostic plumbing, correctly always
on. `GrabScreenHeatParam` is correctly unconditional for a different reason - it mirrors vanilla's
own `SetBool` onto a misnamed animator parameter so *vanilla's own* state machine transitions,
which matters even with every mod tweak off. `GalleryUnlockHooks` is a standalone cheat toggle,
deliberately never wired to the profile at all.

**One real gap did turn up, and it is not on the original list: `ClassSelectionHooks.cs`.** The
class-select screen's heat bar and "Max Heat (EDI ×N)" stat line call `ClassHeatMultipliers
.GetEffectiveHeatCapacity`/`GetMultiplier` with no profile check whatsoever - unlike
`ApplyToPlayerHeat`, the thing that actually writes the multiplier onto the player from
`GameplayProfiles.OnProfileChanged`, correctly gated on `ReleaseModeEnabled`. So under `Vanilla` or
`GodMode` the screen shows a scaled max-heat figure that can never happen in that run. The same
species of bug as the armour-bonus item already open from the release-thread feedback (post 112
item 3), a different cause: that one is the order two multiplies happen in, this one is a display
that never asks whether they happen at all.

**Left open by choice rather than fixed this session** - the fix (gate the three
`ClassSelectionHooks` postfixes on `GameplayProfiles.UsesClassHeatScaling`, falling back to
`GetVanillaHeatCapacity` unmultiplied) is small and needs no play to verify, but it shares a screen
and a decision with the still-open armour-bonus item, and doing them together beats doing them
twice. `TODO.md` carries both.

No code changed this session; nothing to build, test or deploy.

## 159. The 2.6.0 release build, and WebM package video confirmed on Windows

`check.py --full` ran 13/14, `deploy` the one failure — `--check` reported `game-linux: would
change 1 file(s)` with no `--verbose` to say which. `python3 code/deploy.py` wrote it; `check.py
--full` then ran 14/14. `python3 code/release.py` built
`dist/PNC0.3.2-PncEdi-2.6.0.zip`, 89.8 MB, sha256
`2230f0601a9c004677d7027bcafc896b5c0af2fa50dee84efd57c3da5b2f583e`.

The open question from the §158 handoff — whether the archive's WebM-converted package videos play
on Windows, only ever run on Linux before now — is answered: they do. Nothing else about the
release changed; §152-§158 is what ships as 2.6.0.

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

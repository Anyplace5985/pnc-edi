# Porting to a new game version

The audit procedure, and which parts of this mod a game update can break silently.

**Read this when:** the game updates

**Keywords:** patchaudit, AI audit, AiStateGuard, EnemyGrabGate, AIState enum, slug harness, ALIAS-GAP, clip durations, incomplete extraction, UnityPlayer.so, appended enum value, upstream fixes your not-a-defect, prefab value vs class default, regrappleCooldown, which prefabs carry the component

---

**Validate a static analyser against the build it is known to describe, before believing it about
a new one.** `code/patchaudit.py` was written to answer "does the mod still bind to 0.3.1" and was
run against **0.2.1** first, where the mod is verified working and the docs record the expected
answer. That caught three separate parser bugs, each of which would have produced a confident,
wrong finding: a class stack that only popped when another `.class` opened (so the first nested
coroutine type swallowed its parent's members), `ikdasm` never emitting a bare `}` — it writes
`} // end of class 'X'` — and a long return type wrapping a method signature onto a *third* line.
Only when the control came back clean was the new build's result worth reading. Same shape as
§48's "if the rule doesn't already explain most of the data, it isn't a rule".

**Do not answer a question about components by searching names.** "D8 has no unlock box" came from
grepping *GameObject names* for `*Unlock*`. It has one; the mod finds boxes by component type, and
several are on objects whose names say nothing. Parsing `m_Script` against the `GalleryUnlockTrigger`
MonoScript settled it in one pass and found the real answer — 9 boxes on 0.2.1, 16 on 0.3.1.

**Three ways into the game, and two of them fail silently.** A `[HarmonyPatch]` on a missing method
throws at patch time and takes the plugin down — loud. `AccessTools.Field` returns **null** and the
feature quietly does nothing; `Traverse.Create(x).Field("f")` returns an empty Traverse and reads
give `default(T)`. That asymmetry is why the audit checks all three rather than trusting the build
to fail.

**Enemy-specific behaviour and enemy-specific *content* are two separate assumptions, and gating
one does not gate the other.** 0.3.1 added a second grappler. The old
`ImpGrappleGate.IsImpGrappleSession` tested every clinging enemy and failed closed, so the imp
*gameplay* tweaks correctly stayed off — while the *dispatch*, gated only on `IsGrappling`, happily
played `imp_1/2/3` for a goonshroom. Same file, same feature, one half safe and the other borrowing
another creature's scripts. When adding a creature-specific rule, grep for the other places that
creature's name is assumed. (That gate is gone as of §114 — failing closed turned out to be the
wrong default for what it guarded — but the two-assumptions point is the durable half.)

**A tool that cannot see a layer should say which layer.** `code/slugharness` compiles the real
`NameRemap` and `GalleryTable` so it cannot drift from the mod — but the two-stage Blinded Beast is
resolved a layer above them, in `GrabHooks`, off a live controller name. The harness therefore
prints one row where the game produces two, and there is a comment at the table saying so. A
quietly incomplete coverage tool is worse than one with a stated hole.

**A game version can change a Unity *project setting* — no patch target moves, and everything
breaks.** 0.3.1 switched Player Settings' active input handling to the Input System package alone,
which turns every read of the legacy `UnityEngine.Input` class into a thrown
`InvalidOperationException`. `patchaudit` was clean, the slug harness resolved every state, and
five gameplay subsystems had not run once since startup (§72). **The audits check the mod's
*binding* surface — types, members, patch targets — and are blind to the runtime contract around
it.** Use BepInEx's `UnityInput.Current` rather than `UnityEngine.Input`, and check the settings
that decide how a Unity game talks to its host: input handling, the scripting backend, the
physics and time settings, the colour space.

**Verify a new install against its archive by file size before running any audit against it.**
Both 0.3.2 unpacks were incomplete — the Windows one missing `sharedassets0-3` and
`UnityPlayer.dll`, the Linux one missing `sharedassets1-3` and `UnityPlayer.so` — and neither would
have launched. What makes this worth a rule is how it presents: `patchaudit` reads only
`Managed/Assembly-CSharp.dll`, which was complete in both, so every static check comes back *clean*
about a game that cannot start. Existence is not the test; size is:

    unzip -l "<the>.zip" | ... | while read sz f; do [ "$(stat -c%s "$f")" = "$sz" ] || echo "$f"; done

**A game update can close one of your open items, and nothing tells you.** §132 recorded the
goonshroom re-grappling instantly as *not a defect* — vanilla had no cooldown there and the mod was
not causing it. 0.3.2 added the cooldown (`regrappleCooldown`, `shakeOffStunDuration`, an
`AIState.Stunned`), so the item closed upstream. **During a port, re-read your own "not a defect"
and "not reproducing" notes against the member diff**; they are exactly the observations a patch
release is likely to have acted on, and they are the cheapest items on the list to close.

**A field's shipped value is the prefab's, not the class default's — read the asset before quoting a
number.** §136 read `regrappleCooldown = 8f` and `shakeOffStunDuration = 3f` off the decompiled
`ChargingEnemyAI` and wrote "8 s" into three documents. The prefabs serialize **4.0** for the
re-grapple window (the stun really is 3). A decompile shows what the field is initialised to before
Unity overwrites it with what the designer typed, and every enemy tuning number in this game is
designer-typed. The scan is the same one `code/grabflags.py` does: generate the type tree, read
every `ChargingEnemyAI` MonoBehaviour, print the field.

**Check which prefabs actually carry the component before deciding a new mechanic applies to an
enemy.** §136 wrote up 0.3.2's re-grapple window as the answer to the *zombie* re-grappling, and a
whole test plan was built around shaking a zombie off. **The zombie is a plain `EnemyAI`** — in
0.2.1, 0.3.1 and 0.3.2 — so it cannot charge, cannot be grappled, and can never reach any of it.
Only the five imps and the goonshroom are `ChargingEnemyAI` with a `grappleAnimatorController`.
The class name in a config description (`ZombieGrappleChargeRate`: "Zombie (ChargingEnemyAI)") is a
claim about the assets that nothing checks, and this one had been false since before the mod was
recovered: `EnemyCombatTuning.ApplyZombieGrappleTuning` is a postfix on `ChargingEnemyAI.Start` that
then requires `key == "zombie"`, an intersection that has always been empty. **A patch gated on both
a component and a key is dead the moment those two stop overlapping, and it logs nothing** — the
same silent shape as §109's unregistered patch class.

**The reverse of a closed item: a new vanilla mechanic can quietly shrink the reach of a config
knob.** 0.3.2's `ShouldCharge()` tests `regrappleCooldown` *before* `chargeCooldown` and never skips
it, so a knob that divides `chargeCooldown` does nothing for the window after an escape. Nothing
fails, nothing logs. **When a diff adds a field next to one the mod writes, read the method that
reads both** — and then check the knob reaches any prefab at all.

**When a state is appended to an enum the mod keys by number, you got lucky, not safe.** 0.3.2 added
`Stunned` after `Dead`, so `AiStateGuard`'s `StuckStates[2]`/`[3]` still mean `PreparingCharge` and
`Charging`. `EnemyAiAudit.AuditStateValues` is what makes that checkable rather than hopeful — it
asserts the names still sit at those numbers at startup. Keep that pattern for any table keyed by a
value the game owns.

**`patchaudit --ai`'s "unhandled" line over-reports, and the control run is how you know.** It counts
a switch branch as handled only when it calls `Handle*`. `Stunned` leaves on
`Time.time >= stunEndTime` and calls `TransitionToChasing`/`TransitionToIdle`, so it is reported as
needing an `AiStateGuard` entry when it needs the opposite — guarding it would cut short a
deliberate three-second stun. The same line has always over-reported `PreparingCharge`, on 0.3.1
too, which is exactly what running the audit against the old build first makes visible.

---

## The procedure

0. Check the new install is completely unpacked - every file present *and* the right size against
   the archive it came from. §136: both 0.3.2 unpacks were missing `UnityPlayer` and half the
   `sharedassets`, and every audit below was clean anyway.
1. `python3 code/patchaudit.py --compare "<old install>" --ai` - every patch target and reflected
   member, a member-level diff of every type the mod names, and the CHANGELOG §46 AI audit.
   **Run it against the old build first**; it should come back clean and reproduce §46.
2. Dump animator states and clip durations, and diff them (`code/NAMING-AUDIT.md`,
   `code/TIMING-AUDIT.md`).
3. `dotnet run --project code/slugharness -- BepInEx/config/com.edi.pnc.cfg` - any `UNMAPPED` row
   is a gap. Add new enemies' states to its tables first.
4. `.venv/bin/python code/animsweep.py` and `code/gallerydiff.py` - the funscripts against the
   new clips.
5. Play once and grep for `[ALIAS-GAP]`, `[AI-AUDIT]`, `[KEYBIND]`, `[INPUT]`, `[TICK]`.
   `WriteUnityLog = true` is forced by `deploy.py` on every deploy (§95) — a game-side throw is
   invisible without it (§56, §72) — so this needs checking only in an install nothing deployed to.
6. Bump `GAME_VERSION` in `code/release.py`.

Worked examples: CHANGELOG §63-§69, the 0.2.1 -> 0.3.1 port; §136, the 0.3.1 -> 0.3.2 one, which
was a much smaller job and is the better read for what a *patch* release does to this mod.

**`patchaudit`'s IL parser reads the method name off the `.method` line as well as the lines under
it.** A declaration whose return type wraps puts the name on a later line, which is why the parser
deferred; a short one — `.method public hidebysig static void  RestartRun() cil managed` — carries
its own signature, and deferring unconditionally made every such method invisible. That reported
`RunRestartController.RestartRun` as missing from a build that has it (§75). Same shape as the
nested-type bug: **a BROKEN line is a claim about the parser until it has been reproduced on the
build the target is known to exist in.**

**Read the `[AI-AUDIT] GAP` lines the first time they appear.** The startup audit named
`BrawlerEnemyAI` in every 0.3.1 run from the port onwards — "can start a grab and was not in the
§46 audit", "runs its own state machine and was not in the §46 audit" — and the class stayed
missing from six helper lists until a player reported a serpent standing still (§76). The audit was
built for exactly this and it worked; what failed was that nobody treated its output as part of the
port. A GAP line is a task, not a warning.

**Anywhere the mod REPLACES a vanilla choice, it inherits the duty to keep up with vanilla's
content - and nothing announces when it has not (§91).** `EnemySpawnShuffle` is a Harmony prefix on
`EnemySpawner.GetEnemyPrefab` that returns `false`, so the spawner's own pick never runs. Its pool
was six enemy types hardcoded in two places, both written before 0.3.1. The result was that
0.3.1's goonshroom could not be spawned by any spawner in the game - not rare, absent - and it took
several player runs and a "is this something we caused?" to notice, because the mod was doing
exactly what it was told and said so in no log line. Two habits follow: **during a port, list every
patch that returns `false` or overwrites a `__result` and ask what new content it now excludes**;
and **prefer a config list to a hardcoded one for anything enumerating game content**, so the next
version's answer is a config line rather than a build.

**A port checks that the patches still bind. It does not check that they are still needed.**
`patchaudit.py` passed on every one of the grapple keep-alive's targets through the whole 0.3.1
port, because they all still exist - and the method they patch had changed its body underneath
them. 0.2.1 destroyed a shaken-off grappler; 0.3.1 releases and throws it, so the mod's workaround
was overriding a mechanic the game had grown for itself (§114). Nothing announces this: the patch
keeps working, keeps logging, and keeps the new vanilla behaviour from ever being seen.

**So for every workaround, ask what version it was written against and read that method on both
builds.** `patchaudit.py --compare` diffs members, not bodies; the two-second version is
`ilspycmd -t <Type>` against each install and a diff of the one method. Worth doing for anything
whose comment says the game "destroys", "ignores" or "refuses" something - those are the claims a
patch release quietly fixes.


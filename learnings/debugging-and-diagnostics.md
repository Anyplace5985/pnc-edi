# Debugging and diagnostics

How to find out what is actually happening, and the log shapes that lie to you.

**Read this when:** a fix does not work, the log looks clean but behaviour is wrong, or a hypothesis needs testing

**Keywords:** probe, instrument, log tag, silent gate, postfix, WriteUnityLog, dump every gate, audit itself, OVERHEAT, STUCK, dwell, transient, misread instrument

---

**A vague symptom becomes a fact when you split the log by the thing it happened to.** "Sometimes
grab scenes don't have audio, maybe too much stuff going on" sounds like load, and load is
unfalsifiable from the chair. The log had `Can not play a disabled audio source` seven times; the
useful move was not to read the warnings but to count them **per prefab** — all five Blinded Beast
grabs, one each for the dragon and the wendigo, zero across six goonshroom, nun, imp and mimic
grabs. A perfect split by family is not load, and it named the property those families share (their
enemy object is switched off during its own scene) in one pass. **Before theorising about a
"sometimes", tabulate it against every axis the log already carries** — prefab, family, scene,
which code path logged the line just before. §119.

**A Unity engine warning has no stack, so its only evidence is what it sits next to.** Those seven
warnings each land within a millisecond of a `[SCENE-HIDE]`, which is suggestive and not proof —
adjacency in a log is not causation, and two different systems hide enemies at that moment. The
answer was to make the adjacent lines carry the discriminator instead of arguing about it:
`[SCENE-HIDE]` now counts the AudioSources on what it hid (a hide carrying none rules the mod's
hider out entirely) and `[GRAB-AUDIO]` censuses the grabbing enemy's sources *before* anything
hides. **Where a warning cannot say who caused it, instrument the candidates so the next run
answers rather than the next argument.**

**A debug tool that never fires is indistinguishable from a feature nobody wrote.**
`SpawnChestTrapKey` was broken three ways, each concealing the next: an unreachable keycode, a
name hint that could not match its only candidate, and a silent failure path. It aimed at a mimic
chest that does not exist in the game at all. **Before debugging why a tool misbehaves, confirm it
has ever run once** — and prefer `InteractiveOnly` over `InteractiveFirst`, because the latter's
`!interactiveFirst` guards skip the failure log and return null quietly.

**A table read out of the game's IL cannot be re-derived at runtime, so make it audit itself.**
`AiStateGuard` and `EnemyGrabGate` encode three things that only exist in `Assembly-CSharp`'s
bytecode: which states have no `case` in a `switch`, which coroutine field drives each, and which
`StartGrab` callers re-test `IsGrabbed`. A game update can invalidate any of them, and the worst
outcome is not a crash — a renamed private field makes `AccessTools.Field` return null, the spec
ends up empty, and **the watchdog keeps running while watching nothing**. `EnemyAiAudit` runs at
startup and prints `[AI-AUDIT] ok` or names the drift: broken reflection, a new class declaring a
`GrabScreen` field or a `currentState` enum, or an `AIState` value whose name has moved (the
table is keyed on the number, so inserting a state silently repoints it). Same principle as
`[ALIAS-GAP]`: **a gap must be inert and visible, never silently plausible.** What it still
cannot see is a `case` appearing or disappearing — that is IL — so `code/README.md` keeps the two
`awk`/`grep` commands that redo the audit by hand.

**When flags are clean and behaviour is wrong, dump everything at once.** Seven §17b candidates
for #14 were eliminated by reading the disassembly — all correctly — and the real cause was in
none of them. A diagnostic that printed *every* gate (state, all coroutine handles, all bools,
the cooldown clocks, the `Can*` predicates) settled it on the first run, where testing
hypotheses one at a time had already cost three sessions. `code/edimod/PncEdi/SpinAiDiag.cs`,
`SpinAiDumpKey` (F9), needs `Debug = true`.

**When our log is flawless and the behaviour is not, read the other side's log (§84).** The mod
logged the alias resolve, `[EDI] Play imp_1_Gallery` and seven `[EDI] Stop`; Edi's own
`Edilog<date>.txt`, beside `Edi.exe`, had *no* `Player event:` line over those minutes while
plainly running and holding all 202 assets. One comparison ruled out the whole naming chain and
put the fault in the transport. `[EDI] Play` is written after an un-awaited `PostAsync` and so
claims a send whether or not a byte left the process — Edi's `Player event:` lines are the only
evidence a request arrived, and `Ignored not found [<name>]` the only evidence it resolved (the
HTTP status is 200 either way).

**Session-lifetime sets need a per-run reset.** `UsedReleaseSources` was never cleared, so
one-time releases stayed spent until the process exited — indistinguishable from the feature
being broken (§24).

**Instrument before widening tolerances.** Every "it still doesn't work" round that was
solved by guessing at thresholds was wasted; the one log line naming the blocking collider
ended the investigation immediately.

**Ship the probe, not the guess.** §54 shipped a fix built on an untested mechanism (an early
return in `EndGrab`) and had to be taken straight back out; the probe attached to it disproved
three of its four assumptions on the first run. When a mechanism cannot be read out of the
assembly, the deliverable is the log line, and the fix waits for it.

**Unity's own exceptions were never in the log.** `BepInEx.cfg` shipped `[Logging.Disk]
WriteUnityLog = false`, so game-side throws — including one part-way through a teardown, which
would abandon the rest of it — left no trace at all while `LogOutput.log` read perfectly clean.
Setting it to `true` was a manual step, and manual steps come back: §95 made `deploy.py` force it
(and `[Logging.Disk] Enabled`) into each dev install's `BepInEx.cfg` on every deploy, so the
setting a session depends on is no longer something a fresh install can quietly undo.
**A diagnostic that has to be re-enabled by hand will one day not be.**
Note that `[Error :BepInEx] Unable to start Unity log writer` on line 1 **does not mean the setting
failed** — that is `LogConsoleToUnityLog`, the opposite direction (BepInEx's output into Unity's
log). With `WriteUnityLog = true` the `[Info : Unity Log]` lines appear regardless of it (§56).

**A postfix firing does not mean the original did its work.** Harmony runs postfixes on early
returns, so `[GRAB-END]` in the log means "our patch ran", not "the game tore its UI down".
`GrabScreen.EndGrab` opens `if (!isGrabbed) return;` and only past that point calls `HideGrabUI`
and `RestoreAnimationController` — so a completely clean log sat next to a frozen screen (§54).
§50 is the same shape from the other end. **Log the state, not the call.**

**A gate that refuses without logging is worse than no gate.** Everything upstream of it still
looks healthy, so the log actively argues the opposite of the truth: the death-grab scene printed
`[GRAB-START]`, then `[GRAB-ANIM]` naming a real controller and a real clip, and no warning
anywhere — while the one gate between that and playback refused silently and the device ran filler
for thirteen seconds (§50). §47 is the same rule from the other side: a line that *claims* a save
it never made. Counting markers is what finds these — 26 `[GRAB-START]` against 25 `[GRAB-INIT]`
localised it immediately, so **log the step that precedes the dispatch, not just the entry**.

**An unguarded per-frame block fails whole, not in the place you are looking.** `Plugin.Update`
ran seven independent gameplay ticks in a row with no try/catch. The first of them threw on 0.3.1,
so the other six — the escape gate, its on-screen hint, both escape keys, the grapple death
sequence, two autofixes — had not run since startup, and the reported symptom ("escape does not
work") named none of the code that was broken. **Guard each tick separately and log the first
throw per site**, so one dead subsystem is one line in the log rather than five silent ones (§72).

**Count the noise before reading the signal.** The cause of §72 was in the log 10 994 times on
Windows and 75 306 times on Linux, in a line that had been dismissed as diagnostic spam. The
decisive step was not reading further but `grep -c` on the same string against the **old** build's
log, where it appears zero times. A message that is new in this version and appears tens of
thousands of times is the finding, whatever it looks like.

**When a UI element looks misplaced, log its screen-space rect before believing the screen.** Both
the escape hint and the game's own game-over prompt appeared cut off at the bottom on the native
Linux build; moving the window to another display and back fixed it — the compositor had placed the
window partly off-screen, and neither the game nor the mod was involved (§76). `ScreenDiag` now
prints `Screen.width/height`, the desktop resolution, the fullscreen mode and `safeArea` alongside
the element's world corners, once per run for each. Everything inside `0..Screen.height` with
`screen` matching `desktop` means the process placed it correctly and the problem is outside it —
which is a one-glance answer to a class of report that otherwise costs a session.

**Read the log from the run that produced the report, before reading the source (§92).** A
2026-08-22 session reported six problems. Three were answered from the source; the other three were
declared "needs another session" — and all three were already sitting in `BepInEx/LogOutput.log`
and `PncEdi-missing-definitions.log` from that same run. The GoonShroom gallery had been printing
`[GALLERY-STEP] enemy='Goon Shroom' key=goon_shroom` plus an `[ALIAS-GAP]` and an `[EDI-SKIP]` every
single time it failed, for four days. The serpent desync was one field on one line
(`[GRAB-ANIM] ... t=335.68` against `t=0.00` for all eleven other controllers). The jerky filler was
a `uniq -c` over the `[EDI] Play filler*` lines. **Every one of these instruments already existed
and had worked.** Reading the source first turns diagnosis into a search over everything the code
*could* do; the log says what it *did*.

Where they are: `game-linux/BepInEx/LogOutput.log` (needs `WriteUnityLog = true`),
`game-linux/BepInEx/PncEdi-missing-definitions.log`, and Edi's own `Edilog<date>.txt`. Three greps
worth doing before anything else — `ALIAS-GAP`, `EDI-SKIP`, `failed:`.

`LogOutput.log` is **the current run only** on a Linux dev install: `start-pnc-linux.sh` moves the
previous one to `game-linux/BepInEx/logs/LogOutput-<when that run last wrote>.log` before the game
starts, keeping the newest twenty, and the mod's missing-definitions log travels with it under the
same stamp. So a session's evidence is one file rather than a tail of a growing one, and an earlier
session's is still there to diff against. Rotation is spliced into the launcher by `deploy.py`
(`DEV_ROTATE`) and reaches no player. It only fires for launches that go **through that script** —
a hand-run `run_bepinex.sh`, or the Windows install under Proton, still appends to one growing
`LogOutput.log`, which is why `AppendLog = true` stays forced.

**Check what the logs have never seen before treating them as coverage (§148).** Every instrumented
session this project has ever recorded is `MainMenu -> Floor1` — sixteen Floor1 entries across every
file in `BepInEx/logs/`, and no floor 2, ever. That matters because the game takes a *different
branch* on later floors: `PlayerClassInitializer.ApplySelectedClass` calls `LoadPlayerState()` and
returns when `PlayerStateSaver.IsFirstFloor` is false, so `PlayerClassManager.ApplyStatModifiers`
and every postfix on it — ours included — runs on floor 1 only. A whole class of behaviour has
therefore never been observed, and "the logs say it is fine" was never a statement about it. One
`grep -ho "SCENE\] '[^']*' -> '[^']*'" logs/*.log | sort | uniq -c` is the whole check, and it is
worth running before a log-based argument rests on absence of evidence.

**Unity callback ordering is not derivable, and a diagnosis that turns on it is not finished
(§148).** Whether `activeSceneChanged` fires before or after a new scene's `Awake` decides whether
`HeatLockSystem._baseHeat` starts a floor at 0 (correct — the live capacity is read back) or at the
prefab's 100 (five locks for every class). Both readings are internally consistent and the source
supports neither over the other. The same shape as §106's device diagnosis: when two orderings give
two different answers, print one line and read it rather than reasoning about which Unity does.

**A harness that skips a step cannot fail at that step (§92).** `slugharness` reported the five
GoonShroom gallery rows resolving cleanly throughout, because its `Emit` called
`BuildGallerySlug(key, state)` directly while the game calls `ResolveEnemyKey(name)` first and
passes the result — and its input table was keyed on **resolved** forms rather than the display
names the gallery route supplies. It was asking the question with the answer substituted in. When a
harness and the game disagree, check that the harness enters through the same door: **its inputs
have to be what the game is actually handed, not what the game has already worked out.**

**Adding hysteresis to a threshold is not finished until every comparison in that decision has it
(§92).** The filler's per-bucket thresholds got hysteresis, with a comment explaining exactly why a
bare test flaps when a continuous meter rests on a boundary. The *family* choice one level up kept a
bare `a > b` and flapped for the identical reason — 39 switches under a second apart in one session.
The flap does not go away, it moves to whichever comparison was left bare.

**A handoff's diagnosis is a claim about the log, not a replacement for it (§102).** §99 read the
run and wrote four defects up as "the diagnosis is done, so each of these is an edit rather than an
investigation". Two of the three that were then fixed did not match. The grapple gate was the sharp
case: §99 prescribed comparing against the running grapple's family, which reads
`grapplingEnemies` — and the one wrong refusal in the whole run happened 1 ms before
`[GRAPPLE-END]` with that list already empty, so the prescribed fix would have changed nothing
about the line it was written for. The evidence that settled it was a *count* of a tag that was not
there: no `[GRAPPLE-ATTACH] GoonShroom` in forty minutes against twelve for imps, which ruled out
the path the summary assumed. Re-reading the log costs ten minutes and is the same move as reading
it the first time; the summary is a lead, and a lead is worth confirming before it becomes an edit.

**The answer to a refusal is often on the next line already.** Every imp grab in the run logged
`[GRAB-START] ... anims=0` and then `[GRAB-INIT] skipped: no grab animations resolved` — with
`[GRAB-ANIM] controller='Imp_Grab_Screen' clip='Imp_Grab_Loop'` printed *between* them, naming a
step that slugs to a real gallery row (§102). The gate was refusing while the instrument beside it
held what the gate said was missing. When a log line says a thing is unavailable, read its
neighbours before believing that nothing else knows it.


**A diagnostic line added for one bug will answer a different one — that is the return on writing
it.** §102 added the animator state to the "releasing the cum" line to tell two failure modes
apart. Two sessions later, that field alone root-caused the goonshroom heat wedge (§109): the imp
read `(animator in 'Imp_Grab_Cum')` and the goonshroom `(animator in 'GoonShroom_GrabscreenStart')`,
which collapses the search from "what is the mod doing to heat" to "why is this animator not
transitioning". Two suspects had been written into TODO before that, both about mod code, both
wrong. Prefer a diagnostic that names *state the code branched on* over one that says a branch was
taken.

**An absence in one instrument is not evidence unless you know what that instrument covers
(§124).** The clinging family's grab screens were silent, the fill that was supposed to fix it
logged `filled 4`, and `DIAG-AUDIO` listed nothing playing during the grab. That looked like proof
the fill had not worked. It was not: `DIAG-AUDIO` only reports sources within 15 m of the *player*,
and `GrabScreen`'s AudioSource is on the GrabScreen object. The fix was a second instrument that
reads the source directly - clip, `isPlaying`, volume, mute, spatialBlend, mixer group, listener
volume - which said `playing=True volume=1.00` and settled it. **Before reading a null result,
re-read the filter that produced it.**

**An instrument that prints for every case gives you a control for free (§124).** The same
`CheckAnimationStateSound` postfix prints for the families vanilla authored as well as the two the
mod fills, so one run shows `Serpent Sex` and `NUN sex` coming through the identical source with
identical settings as `Goonshroom gangbang sex`. That comparison is worth more than the fix: it
answers "is ours behaving like a working one" rather than "did ours produce a line". Prefer the
instrument that cannot tell whose case it is looking at.

**A number that is identical to the centimetre across three runs is a constant, not a measurement
(§124).** Both mimic variants logged `lifted 1.28m` in three consecutive sessions, through two
different attempted fixes. Two different prefabs agreeing that precisely is the tell: 1.28 was half
a 256-pixel sprite frame at 100 pixels-per-unit, so `Renderer.bounds` was reporting the quad and
not the art in it. **When a diagnostic reads the same for two things that should differ, suspect
the measurement before the subject.**

**Log the value even when the code path does nothing with it.** Below 1x, `ExpandSpawnPositions`
returns immediately, so "the spawn floor is vanilla again" and "the patch never ran" produced
identical logs — nothing. One line naming the multiplier, the lock progress and both ends of the
point list turned an unverifiable default into two greps (§108). A no-op path is exactly the one
worth announcing, because its silence is indistinguishable from failure.

**A success line is not proof of success — read what it says it did.** The new Blinded Beast key
logged `[SPAWN] blinded_beast: spawned interactive 'GloryHoleCamera'` six times. That is a success
message for the wrong object, produced by a scoring bug that accepted a zero match (§110). "The key
worked" and "the key did what it is for" are different claims, and the object name is the one that
settles it.

**When a fix does not work, distinguish "wrong diagnosis" from "never ran" before re-diagnosing.**
§109's mirror was correct and had no effect for a whole session because its patch class was not
registered (see `modding-harmony-bepinex.md`). The tell was in the timestamps: the one line it
produced landed at *grab end*, not at cum time, which meant a plain call site had produced it and
no patch had. Check when your evidence appeared, not just that it appeared.

**An audit's coverage claim is itself a thing to audit.** `patchaudit.py` says it checks every
patch target and reflected member, and it scanned `AccessTools.*` and `Traverse` only - so ten bare `typeof(T).GetField(...)` reflections across four files were checked by nothing
at all, while the tool reported clean (§114). When a tool's value is its exhaustiveness, grep the
*source* for the pattern it claims to cover before trusting the count.

**A documented fallback is a reason to fail the audit, not to exempt it.** Three of those ten fall
back to a wider gate when the member is gone rather than throwing. That is precisely what makes the
loss invisible in play: nothing crashes, nothing logs, the feature quietly widens. Absence is only
"expected" where the member is on a type the assembly does not contain and the code tests for it
(`*Exists()`), which is what the audit's `optional` set is for.

**A trace that only runs during a grab cannot answer a question about not being able to attack.**
`HEAT-TRACE` existed for two sessions and was the obvious place to look when "spells stop working at
max heat" came in — but it is gated on `GrabScreen.IsGrabbed`, which is exactly when nobody is
casting, so three runs of it carried nothing about the reported symptom. Before reaching for an
existing instrument, read what gates it; an instrument aimed at the wrong window is worse than none,
because its output looks like evidence (§134).

**When a gate is about a distance, log the distance, not the outcome.** The witch's capture had never
fired in play and two sessions guessed at why from blink distances and collider reasoning. One line —
her closest horizontal approach, printed whenever it improves by 10 cm — settled it in a single run:
`closest approach 1.32m (capture at 1.20m)`, monotonic, stopping dead at 1.32 across the whole run.
That is where the colliders meet, and no amount of source reading would have produced the number
(§134). The same shape as the `[HINT]` rect dump and `intensitybench.py`: **the instrument that pays
is the one that prints the quantity the gate actually compares.**

**An instrument must not print the fix working in the same words as the defect.** The `[OVERHEAT]`
latch line was rewritten in §138 to the one predicate vanilla cannot produce — `hasBeenOverheated`
while heat is *below* `MaxHeat` — and it was still misread on its first run: five `STUCK` lines,
each cleared 4 ms later by `ClearOverheatAtLockFloor`, i.e. the one frame between vanilla failing to
clear the latch and the mod clearing it. The predicate was right and the line was still wrong,
because **a fix that runs on the next frame makes its own defect-shaped transient, every single
time.** A `STUCK` line now needs the state to have *held* 0.5 s, and carries `held=Ns`. That is
three misreadings of one instrument in three sessions (§134's 51%, §138's 53.1 s, §139's five
lines): when an instrument is misread twice, change the instrument — the note beside it has already
failed. And prefer a predicate that names a **duration**, since the reported defect was "unusable",
which is a thing that lasts (§139).

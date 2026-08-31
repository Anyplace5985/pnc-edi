# Learnings index

Everything this project found out the hard way, split by topic so a session can load the one file
it needs instead of all of them. **This index is the only file worth reading in full** — it exists
so you can pick.

Each file is a list of claims. A claim is **bolded and stated as a rule**, then backed by the
concrete case that produced it, usually with a `§n` pointing at the CHANGELOG entry that has the
full story. If a claim looks abstract, the evidence under it is not.

## How to find something

**Grep this directory before you diagnose anything, and say what came back** — including "nothing".
`CLAUDE.md` carries that as a rule and §133 as the reason: for eleven sessions this index was
"open it when useful", and it was not opened. A step that shows up in the reply can be checked; a
silent one cannot be told apart from a skipped one.

**That rule is symptom-first, and this file serves the other question** — the one a grep cannot
answer, because you have no symptom yet. Read the table when you are picking up an *area*, and read
"the ones that have cost the most time" for what you do not yet know to search for.

**The keywords column is load-bearing, not decoration.** It is the only part of this index written
in the vocabulary someone actually greps with, which is what makes the index itself a grep hit:
`grep -ril "SetActive" learnings/` finds this file, `grep -ril "grabCoroutine"` does not. So when
you add a claim, **put its identifiers in its file's row here** — an API name, a log tag, a field
name. A claim whose words never reach this column is findable only by someone who already knew
which file to open, which is precisely the person who did not need an index.

- **Know the topic?** Take it from the table below.
- **Know a symptom or a name?** Grep. Every file is plain prose with the identifiers spelled out:
  `grep -ril "SetActive" learnings/`, `grep -rn "m_FileID" learnings/`.
- **Know the change?** The CHANGELOG `§n` references go the other way — from a rule back to the
  session that learned it.

## The files

| file | read it when | keywords |
|---|---|---|
| [funscript-timing.md](funscript-timing.md) | deriving or retiming a curve; an `animsweep` row reads OFF or near | stroke rate vs cycle period, autocorrelation, whole-cycle, drift, frame quantisation, reps |
| [funscript-proxies.md](funscript-proxies.md) | picking what to track in a scene; a polarity flag needs judging | proxy, polarity, inversion, correlation, region vs frame, alpha trim, alignment, jitter floor, a proxy seeing nothing is not nothing happening, onset detection, footfall, minimum gap |
| [funscript-authoring.md](funscript-authoring.md) | writing or editing a curve; judging playability on a device; touching any row of a *ladder*; adding or renaming a device variant | units/s, Handy caps, soft cap vs hard cap, token bucket, 100 ms spacing, range, buzz, slew limiting, variants, handy2pro/handy2/handy1, non-monotonic and backwards timestamps, loop seam, truncation artefact, a package's hand-authored handy1, script provenance, ladders |
| [edi-integration.md](edi-integration.md) | adding a gallery row; a script plays wrongly on the device; switching between rows mid-playback | Definitions.csv, slice semantics, InproveLoopDetection, Loop, Type, variant folders, `?seek=`, ladders, Intensity, amplitude, slew limit, chaser stomp, audio clock, grace, row hold, PauseFillerForMenu, seekOverrideMs, CurrentLoopPhaseMs |
| [game-scenes.md](game-scenes.md) | wiring a new scene; working out what a game object should play | diorama, D-slot, GalleryUnlockTrigger, peek scene, peephole, gallery split, `Gallery_*` clips |
| [asset-inspection.md](asset-inspection.md) | you need a clip, a scene object, a layer name, an IL fact, or something out of Edi's own code | UnityPy, typetree, MonoBehaviour raw parse, PPtr `m_FileID`, ikdasm, monodis, single-file bundle |
| [unity-runtime.md](unity-runtime.md) | an object misbehaves after deactivation; a raycast fails; a force does nothing; UI you hid took something else with it; state is written back by something you cannot grep | SetActive, activeInHierarchy, inactive parent, hiding vanilla art, GetComponentsInChildren, panel stack, coroutines, Camera.main, layer masks, KeyCode, animator Rebind, `m_IsActive`, VideoPlayer codecs, unscaled time vs pause, Unity-object dictionary keys, character controllers that assign velocity, AddForce doing nothing |
| [grab-and-ai-mechanics.md](grab-and-ai-mechanics.md) | touching grab dispatch, enemy keep-alive, AI guards or heat | StartGrab, IsGrabbed, mimic, dragons, coroutine-driven states, heat lock floor, suppressions, grapple family, clinging enemies, canGrab, TransitionToGrabbing, grabCoroutine, StopGrab, AiStateGuard, watchdog recovery loops, package capture through GrabScreen, OwnsGrabScene, grabImage, hasBeenOverheated, CanAttackNow, overheat latch |
| [modding-harmony-bepinex.md](modding-harmony-bepinex.md) | adding a patch or a config setting; a setting seems ignored; splitting code into another plugin; **a patch that shows the player a number** | prefix/postfix/finalizer ordering, `Bind()` section+key, KeyboardShortcut, cfgaudit, patch registration vs runtime gating, display patches gated like writers, predicting a number the game computes, order of operations, armour bonus, pure arithmetic in a testable function, plugin-to-plugin soft dependency, one-way plugin split, InternalsVisibleTo, BepInDependency, CustomEnemyBridge, a seam that falls back silently, one config file per plugin, package assemblies, IPackageModule, ModServices, published behaviours, packageaudit, consent default-off, consent on the on/off switch, permission toggle beside a feature toggle, restart-required setting, stale package DLL, a switch that changed meaning, off means off, LoadManifest early return, IPackageSceneOwner, OwnsSceneVisual, a type test replaced by an interface, NearbyEnemyHider hid the scene |
| [debugging-and-diagnostics.md](debugging-and-diagnostics.md) | **a session reports a problem — open this before the source**; a fix "does not work"; the log is clean but behaviour is wrong | log first, LogOutput.log, ALIAS-GAP, EDI-SKIP, probes, instrumenting, log tags, silent gates, WriteUnityLog, dump-every-gate, harness blind spots, an instrument gated on the wrong window, HEAT-TRACE, OVERHEAT, closest approach, log the quantity the gate compares, what the logs have never seen, Floor1 only, Unity callback ordering, RecordBaseHeat, baseHeat, shop entry, silent clamp |
| [porting-a-new-game-version.md](porting-a-new-game-version.md) | the game updates | patchaudit, AI audit, AIState enums, slug harness, clip-duration diff, ALIAS-GAP, incomplete extraction, UnityPlayer.so, appended enum value, upstream fixes your not-a-defect |
| [working-practice.md](working-practice.md) | before adding a second copy of anything, changing a default, trusting a "do not redo" note, running a sweeping mechanical pass, or taking in code *or documentation* from another tree | generate don't mirror, config defaults, decisions expire, deploy is a step, pinned dependencies, venv, allowlist gitignore, decompile diff, rename pass, porting someone else's code, importing someone else's docs, acting on a drift signal, habits nobody can observe, checkable steps, a measurement is not a bug report, player-facing README, documenting another program's UI, WINEDLLOVERRIDES, Proton, DefaultVariant, a backwards-compatibility default, a hardcoded count in a document, prune_gallery, prune_custom_enemy_docs, a one-way sync, deploy --check says up to date |
| [reference-video.md](reference-video.md) | a scene is not in the assets and a recording is the only source | capture dwell, menu detection, audio vs video phase — *superseded for anything in the assets: `code/refvideo.py` renders it (§88)* |

## The ones that have cost the most time

If you read nothing else, these are the ones this project keeps re-learning:

1. **Read the log from the run that produced the report, before reading the source.** Three
   problems were declared "needs another session" while all three sat in that session's own log,
   already printed by instruments built for exactly them (§92). —
   `debugging-and-diagnostics.md`
2. **Validate an analyser against the build it is known to describe, before believing it about a
   new one.** — `porting-a-new-game-version.md`
3. **A gap must be inert and visible, never silently plausible.** A wrong scene is worse than a
   missing one, because nothing announces it. — `debugging-and-diagnostics.md`
4. **Timing is objective, polarity is not.** A low correlation means *look at this one*, never
   "invert it". — `funscript-proxies.md`
5. **If two copies must agree, do not maintain both — build one from the other.** —
   `working-practice.md`
6. **Ask what the game already does before building the mechanic.** — `grab-and-ai-mechanics.md`
7. **A proxy that sees nothing is not evidence that nothing happens.** A whole-frame number averages
   the thing that moves into the frame that does not; exempting a clip from a whole-clip
   correlation does not exempt each phase from needing a proxy of its own (§97). —
   `funscript-proxies.md`
8. **A diagnostic that has to be re-enabled by hand will one day not be.** Force it where the thing
   is built or deployed (§95). — `debugging-and-diagnostics.md`
9. **A handoff's diagnosis is a claim about the log, not a replacement for it.** Two of §99's four
   prescriptions did not survive re-reading the run they came from, and one of them would have
   changed nothing about the line it was written for (§102). —
   `debugging-and-diagnostics.md`
10. **When a second member joins a family, every `IsFirstMember` test that meant "the current one"
   is now wrong.** They fail silently and one at a time (§102). — `grab-and-ai-mechanics.md`
11. **Ask whether the game still does the thing your workaround works around.** A patch that still
   binds is not a patch that is still needed: 0.3.1 replaced the `Destroy` the grapple keep-alive
   existed for with a release-and-throw, and the mod had been overriding it ever since (§114). —
   `porting-a-new-game-version.md`
12. **Superseding a mechanism is not removing what rode on it.** Ask what the old path *produces*
   and who still consumes it, not whether it is still used: `Patterns` stopped identifying dioramas
   in §65 and went on silently deciding whether they could arm a release until §119. —
   `game-scenes.md`
13. **When you stand a path down, enumerate everything that path provided.** The first prefab ever
   to set `hideInsteadOfDestroyOnGrab` took the mod's 10 s re-grab cooldown down with it, because
   the cooldown lived on the keep-alive path rather than beside it (§119). —
   `grab-and-ai-mechanics.md`
14. **Tabulate a "sometimes" against every axis the log already carries before theorising about
   it.** "Maybe too much stuff going on" became one property of two enemy families the moment the
   warnings were counted per prefab (§119). — `debugging-and-diagnostics.md`

15. **Guard the stage a user can actually reach, not the last stage of the sequence.** §119
   protected the game over panel; the player never got to the panel, because a re-grab took the
   prompt one second earlier every time, and the flag the guard read only latches when a key is
   pressed. Ask which state the report describes and check the log for the one you are guarding
   — `hasShownGameOver=False` on every line was the whole answer (§120). —
   `grab-and-ai-mechanics.md`
16. **A latch is only as strong as the paths allowed to clear it.** The committed-presentation
   latch made every cancel inert, and the grab that stole the game over cleared it first through
   `PlayerStats.Revive` — the release was written for the same event it needed to refuse (§120). —
   `grab-and-ai-mechanics.md`
17. **`Resources.LoadAll` loads; it does not keep.** Nothing else held the returned array, an
   unused-asset unload collected it, and a `_loaded` bool guaranteed it was never fetched again —
   so the Blinded Beast was spawnable exactly once per session (§120). Hold the array and guard on
   "do I have it" rather than "did I once ask". — `game-scenes.md`
18. **A verification that cannot see your change is the right verification, if you know what it
   *can* see.** A decompile diff is blind to local renames (names live in the PDB), so §123's
   1300 of them read as zero — and the 33 lines it did move were three parameter renames and one
   deleted local, each of which needed an account (§123). — `working-practice.md`
19. **Measure against art that is on screen.** `GetComponentsInChildren<Renderer>(true)` also
   returns the inactive grab-screen sprites hanging below a prefab, which lifted the mimic 1.28 m
   into the air while every other enemy needed 0.06 m (§120). — `grab-and-ai-mechanics.md`

20. **Two serialized flags on one component can make a branch unreachable — read both.** The
   Blinded Beast pairs `hideInsteadOfDestroyOnGrab` with `preserveHealthDuringGrab`, and
   `EndGrabHidden` tests the second first, so "killed during its own grab" is dead code for the
   only prefab that reaches it; grab-screen damage never touches the enemy at all (§126). —
   `grab-and-ai-mechanics.md`

21. **An instrument that cannot distinguish the fix working from the defect will be misread — and a
   dwell is only as good as the bound it assumes on the transient.** The `[OVERHEAT]` latch
   predicate is exactly right and still printed `STUCK` for the one-frame transient between vanilla
   failing to clear the latch and our own clear running (§134, §138); §139's fix was a 0.5 s dwell,
   which was itself a fourth misreading once a real run's cum-cooldown drain held the same shape for
   up to 2.5 s (§152). **Gate on the condition the defect is defined by, not on how long the symptom
   has been visible** — `heat <= floor + epsilon` rather than a timer. — `debugging-and-diagnostics.md`
22. **Hiding vanilla UI: disable components, never the object, and print the subtree before
   choosing.** `SetActive(false)` on the object that draws also takes its children — on the gallery
   grab panel those children were the exit button and both arrows — and the art was four
   full-screen images, not one. Two sessions inferred this screen's tree; one logged line settled
   it (§138, §139). Every disable also needs its restore, or the next *vanilla* screen wears it. —
   `unity-runtime.md`

## Adding to this

Put a learning here when it would change what a future session *does*, not merely what it knows.
State it as a rule, then give the case. If it belongs to no file, a new file is fine — add a row
above. Keep the CHANGELOG entry as the narrative; this is the distillation.

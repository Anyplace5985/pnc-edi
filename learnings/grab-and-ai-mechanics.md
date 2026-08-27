# Grab scenes, enemy AI and the heat system

How this game's grab, AI and heat mechanics actually behave, and the failure shapes they produce.

**Read this when:** touching grab dispatch, enemy keep-alive, AI state guards, or anything heat-related

**Keywords:** StartGrab, IsGrabbed, GrabScreen, mimic, dragon, coroutine state, heat lock, suppression, counterpart, fallback, hypnosis, currentHypnotist

---

**Blocking a vanilla `Destroy` leaves one-shot state latched.** Mimics set
`hasTriggeredGrab` and then destroy themselves; `KeepEnemiesAfterGrab` blocks the destroy, so
the chest survives permanently inert (§19). Whenever the mod keeps something alive that
vanilla deletes, ask what that object was never designed to do twice.

**A caller and the thing it calls can disagree about what refuses an action — and vanilla hides
it with the `Destroy`.** `MimicEnemy.TriggerMimicGrab` guards on `IsGrabbed` only;
`GrabScreen.StartGrab` guards on `IsGrabbed` *and* `CanBeGrabbed`. In the gap the mimic burns
its one-shot flag, plays its reveal, and `StartGrab` no-ops — harmless in vanilla because the
chest is destroyed either way, fatal once the destroy is blocked (§44). **When you keep
something alive that vanilla deletes, every early-out in its callees becomes a state leak, not
just the obvious one.** Grep for what else the caller does *before* the call it cannot see the
result of.

**Two timers that were never meant to line up will not, and shortening one can widen the bug.**
The mimic re-arm runs on the enemy-reactivation clock, the refusal on the player's immunity
clock (vanilla's own `GrabScreen.GrabImmunity`, 1 s — which also means our longer
`EndGrabImmunitySeconds` is cut short at T+1 and effectively does nothing above 1). Making the
re-arm instant (§45) is right on its own merits and takes the overlap from ~0.4 s to the full
second. **Before removing a delay because it looks like the cause, check whether it was
accidentally masking something** — here the delay was never even the real gate, since attacking
anything triggered an early reactivation, so the actual rule was "whenever you next swing".

**A state machine with no handler for a state cannot recover from it, and the trap is invisible
in the transition code.** `SpinningEnemyAI.UpdateStateMachine` switches on `currentState` and has
cases only for `Idle` and `Spinning` — `Grabbing`, `Shooting` and `Dead` fall through to `ret`.
Leaving `Grabbing` depends *entirely* on `GrabSequence`'s tail. Meanwhile `TransitionToGrabbing`
sets `currentState = Grabbing` and *then* calls `StartGrab`, which has three early-outs. Any of
them strands the enemy permanently (§46). **When a state's only exit is a coroutine, assigning
that state before the coroutine is known to be running is a latent hang** — and a §17b sweep
will never find it, because nothing is latched: every flag is clean and every gate reads true.

**When one caller of a shared API forgets a check, audit every caller before fixing the one you
found.** `GrabScreen.StartGrab` silently declines while the player is in post-grab immunity. Of
its nine call sites, four check `IsGrabbed` afterwards and handle it; the mimic did not (§44) and
**both dragon classes do not either** — they burn `hasTriggeredDragonGrab`, stop their coroutine
and call `RemoveEnemyAfterGrab()`, so a refused grab deletes the dragon with no scene ever
playing. That one was never reported; it was found only by grepping the call sites after the
mimic bug. Two instances of a pattern means enumerate the rest, and `ikdasm` output makes that a
grep rather than a project (§46).

**A vanilla early-out is often doing work — read it before you skip it.** The first version of
§46's grab gate blocked all eight enemy grab entry points. But vanilla's refused-grab path sets
`hasGrabbedThisAttempt = true; grabInDamagingState = false` *before* checking `IsGrabbed`, and
those two assignments are what make the swing whiff. Gating the method skipped them, so an enemy
would have kept testing every frame and connected the moment immunity lapsed — a hang fix that
quietly made the game harder. **Blocking a method also cancels the parts of it you wanted.** The
gate now covers only the two classes that genuinely misbehave.

**An object's name is not its identity — resolve by what it drives.** Two different characters
use an object called `GloryHoleCamera`: the Shop's is a `HealingCameraSwapTrigger` running the
`Minotaur` controller (Gravy, heals to full), the Jail's is a `TrapCameraSwapTrigger` running
`BJ Animator` (Baphomet, a trap). A `Baphomet Statue` also stands in the Shop as scenery, which
makes the wrong attribution look obvious. `CameraSwapHooks` gets this right by refusing to resolve
names containing `camera`/`gloryhole`/`trigger` and reading the live animator's **clip names**
instead — `minotaur|gravy` tested before `baph` (§47). When a prop name is reused, the asset that
plays is the only thing that identifies the scene.

**Guard the invariant, not the entry path.** The fix for §46 is a watchdog for "in a
coroutine-driven state with no coroutine", not a correction to `TransitionToGrabbing`. There are
four routes into that state and `TransitionToShooting` has the identical shape, so patching the
one observed caller would leave the next route to hang again. Where the broken condition is
expressible in one line and the ways of reaching it are not, watch the condition.

**A lock floor breaks every `heat == 0` test vanilla has.** Twice now: overheat cleared only at
exactly 0 (§11), and the cum cooldown completes only at exactly 0 (§31) — `HandleHeatBuildup`
sets `heatFullyCooled` there, and `OnMaxHeatAnimationComplete` refuses to do anything without
it, so the cum animation repeated for an entire grab. Both were invisible because the symptom
(an animation looping) looks nothing like the cause (an unreachable comparison). **The lock floor
is this mod's zero** — when vanilla tests heat against 0, the mod has to test against the floor.

They have now been counted rather than assumed (§94): `python3 code/patchaudit.py --heat` lists
every heat-vs-0 comparison in the assembly with a verdict for each, and on 0.3.1 there are **ten**
and no third fault. Five of them (`CanAttackNow`, `CanDash`, `CanPerformActions`,
`IsAttackLocked`, `CalculateTotalMovementMultiplier`) are all reached only while
`hasBeenOverheated` is set, which is why fixing that one flag at the source covered five call
sites at once — **find the flag the tests share before patching the tests**. The audit's own table
is the standing answer: a site the next game build adds prints `UNREVIEWED` and fails the run.

**Ask what the game already does before building the mechanic.** Four rounds went into a
raycast answering "is the player looking at this diorama". The game answers it with a
hand-placed `GalleryUnlockTrigger` box per diorama — that is how the gallery entry unlocks —
and the boxes are authored exactly where the player should be standing (§26). Reading the
game's own solution out of `Assembly-CSharp.dll` cost twenty minutes and replaced the entire
problem. Reach for `ikdasm`/`monodis` on the game assembly early.

**A dead gate reads as a working one.** The peephole watch requirement gated on
`SceneEscapeGate.WatchTimeSatisfied`, but `CameraSwapHooks` deliberately never starts that gate
for keyhole triggers — so the property fell through to a stale flag left by the previous grab
scene, and the gate was decided by unrelated history (§28). A boolean that is *always* consulted
but only *sometimes* initialised will look correct in testing about half the time. Check who
calls `BeginScene`, not just who reads the flag.

**Two systems sharing one widget need one writer.** The look meter and the peephole watch bar are
the same gauge. Because `AmbientReleaseGaze.Tick` pushes a value every frame, anything else
writing to it loses immediately — the fix is for that one tick to choose the source, not for the
second system to write too. Its early-outs then matter to both: `Enabled` covers only the diorama
timer, so the peephole check has to sit above it.

**Delete the fallback once the primary path covers everything.** The diorama sight test was
first *fixed* and kept as a fallback, then deleted outright when it turned out nothing could
reach it: peek holes are skipped before that code runs, and all nine ambient patterns have an
unlock box. A fallback nobody exercises is not safety, it is a second implementation that will
drift and get blamed. Check what actually reaches a code path before keeping it "just in case".

**A suppression's counterpart may live in a different class.** `SuppressFullscreenGrabLayer` sits in
`DragonGrabHooks` and looks like it has no undo; the undo is `GrabEndHelper.CleanupGrabPresentation`,
which runs the whole teardown at EndGrab and deliberately sets the overlay alpha to **0**. Grepping
the file the suppression lives in finds nothing and reads as proof, and "restoring" the original
alpha on top of that fights the real cleanup (§54, reverted §55). Before adding a restore, search
for who already tears the thing down — by field name, across the tree, not by file.

**Every suppression needs a counterpart, and the counterpart must key on what it undoes.** The
chaser-boss presentation hid `grabImage`, `grabOverlay` and the overlay's alpha on StartGrab, and
nothing restored any of them; the method that *looks* like the counterpart (`ForceRestorePlayerView`)
only re-enables the camera and controllers. Two of the three were masked because the game's own
`HideGrabUI` hides them too — the alpha was masked by nothing, so a single wendigo grab left every
later grab of any enemy with a transparent overlay (§54). When adding the restore, key it on a flag
set by the suppression itself: `_chaserBossPresentationActive` is cleared from two places, so
gating on it would have made the fix depend on Harmony ordering between unrelated patches.

**When the game grows the mechanic you were faking, defer on its own flag, not on a version
check.** 0.3.1 added `EnemyAI.hideInsteadOfDestroyOnGrab` + `IGrabHideable.EndGrabHidden`, which is
exactly what `GrabEnemyProtection` and `EnemyReactivationHelper` were built to do. The mod now
reads that flag per enemy and stands down where it is set, and keeps its own path where it is not —
so a prefab the game does not convert, and game 0.2.1 entirely, still work with no branch on a
version number anywhere (§73).

**And when you stand down, work out what else was on the path you stood down from.** The Blinded
Beast is the first prefab in the project's history to actually set that flag — six sessions of
`[GRAB-HIDE]` lines all read `vanilla still destroys it` before 2026-08-24. The moment the deferral
fired for real it took `EndGrabEnemyCooldownSeconds` with it, because the mod's 10 s re-grab
cooldown lives on the keep-alive path rather than beside it. Vanilla has no such cooldown, so the
beast landed a grab every ~6 s, which is what turned a presented game over into a loop the player
could not answer (§119). A deferral moves a *set* of behaviours, not the one you were thinking
about: enumerate what the path you are switching off provides before you switch it off, not after a
run finds the gap.

**A flag you deferred to may be paired with another that changes what it means.** The Blinded
Beast sets `hideInsteadOfDestroyOnGrab` *and* `preserveHealthDuringGrab`, both on the same
component, and it is the only prefab in 0.3.1 that sets either — read out of the build with a
type-tree sweep over all 20 AI components, not assumed. `EnemyAI.EndGrabHidden` tests
`preserveHealthDuringGrab` first, so its `remainingHealth <= 0` branch — the one that kills an
enemy that died during its own grab scene — is dead code for the only enemy that can reach the
method. Damage dealt on the grab screen never reaches the enemy anyway:
`GrabScreen.OnPlayerAttackDuringGrab` subtracts from the screen's own `enemyCurrentHealth` float,
and zeroing it calls `EndGrab()`, which restores the enemy at the health it walked in with. The
only real damage on that screen is the thorns trinket's `TakeDamage` at grab start, before
anything is hidden. **So "kill the enemy on the grab screen" is not a mechanic this build has** —
do not write a heat, spawn or game-over rule that assumes it, and re-run the sweep rather than
re-reading the C# if a later build looks like it changed (§126).

**When two implementations of one mechanic exist, log which one ran.** A wrong choice between them
does not look like a wrong choice; it looks like a bug in whichever one you are reading. `[GRAB-HIDE]`
prints one line per prefab the first time it is grabbed, naming the path and the flag behind it.

**A skip that used to be protective can become the damage.** `SkipRemoveEnemyAfterGrab` meant "do
not delete the enemy" for four game versions. On a 0.3.1 prefab the same skip stops the enemy being
hidden *and* stops it being registered as `GrabScreen.hiddenEnemyToRestore`, so nothing calls
`EndGrabHidden` when the scene ends — the mod would owe a teardown it never started. Re-read what a
patch prevents after the patched method changes, not just whether it still binds (§73).

**A new game version can add a whole AI class, and every hand-written list of AI classes is a
place it will fall through silently.** 0.3.1 shipped `BrawlerEnemyAI` (the Black Serpent) as a
seventh class. Six helpers — keep-alive, reactivation, the near-player hider, the inactive autofix,
grab-anim resolution, the vanilla grab-hiding probe — each named the six classes they knew, so the
serpent got vanilla's `RemoveEnemyAfterGrab` (`StopAllCoroutines` + `TransitionToDead`), survived
only because the generic `Object.Destroy` block caught the destroy, and then stood in state `Dead`
with nothing able to leave it for the rest of the run (§76). `EnemyAiTypes` is now the one roster
and the only place a new class has to be added. Corollary when auditing a new class: `Dead` reached
through `TransitionToDead` does **not** set `isDead` — only `Die()` does — so any reset keyed on
`isDead` will skip exactly the enemy that needs it.

**The Black Serpent's hypnosis is an approach, and vanilla hands you its whole geometry (§87).**
`BrawlerEnemyAI.canHypnotise` drags the player's camera onto the serpent (`LateUpdate` ->
`CameraController.RotateTowardPosition` at `hypnosisLookSpeed`) while walking it at the player,
and `HandleHypnotisingState` calls `LandGrab` the moment `distanceToPlayer <= grabRange`. Every
number is a serialized field - 8 m `hypnosisStartRange`, 2 m `grabRange`, 6 s
`maxHypnosisDuration`, 20 s `hypnosisCooldown` on the shipped prefab - so anything keyed on "how
far in is this" should read them off the live component and express itself as a fraction of the
band, not hardcode metres.

Two smaller facts that save work: vanilla keeps **one** hypnotist in a private static
`currentHypnotist` (set in `StartHypnosis` when null, cleared in `StopHypnosis` by its owner), so
there is no scene search to do and no ambiguity with two serpents alive; and the gaze-pull, the
advance and the grab are all gated on `InHypnosisLoop()`, so `Hypnosis Start` is a pure wind-up
telegraph and `Hypnosis End` a wind-down - reacting to the state alone puts you ahead of the
mechanic by a clip.

**And hypnotising is not the same as doing something to the player (§112).** The private bool
`hypnosisInView`, set every tick as `IsPlayerDead || IsInPlayerView()`, gates *both* the camera pull
in `LateUpdate` and the advance (`followerEntity.simulateMovement = flag && hypnosisInView`). A
player who turns their back is still being hypnotised by the state machine and is being neither
pulled nor approached. Read that field rather than recomputing visibility: it is the same answer the
camera acts on, one frame fresh, and a second view test can only disagree with the first.

**A grapple is uniform by construction, and three is vanilla's ceiling, not ours.**
`GrappleScreenobject.StartGrapple` refuses an enemy whose `ChargingEnemyAI.grappleAnimatorController`
differs from the `activeGrappleController` already running, so imps and goonshrooms can never share
a pile — resolving "whose scripts to play" or "what to call in" off the *first* readable clinger is
exact rather than a heuristic (§86). It also returns false at `grappleCount >= maxGrappleCount`,
which is a **serialized** field (3 on the shipped prefab), so read it rather than hardcoding 3 —
and do not try to spawn past it, because the grapple UI animator has no fourth state and the cling
scenes are named `prefix + count`. Any "make it escalate further" ask has to become pacing.

**A game-over prompt vanishing when a grab starts is the death rule, not a lost game over.** At
0 HP the player stays grabbable, the grab that lands plays as the death scene, and the game over is
presented when it ends (§8, §13); `GrappleDeathSequence` even forces `CanBeGrabbed = true` so the
death grab can be offered. §76 read that sequence out of a log as a bug and started refusing the
grab; §77 reverted it. The prompt disappearing and the run continuing are true of both the bug and
the feature, and nothing in the log tells them apart — **before calling a mod behaviour a bug, find
the CHANGELOG entry that put it there.** The one thing the latch legitimately covers is narrow:
teardown belonging to the scene that just ended, cancelling a game over inside
`ShowGameOverSequence`'s one-second delay (§75).

**`ResumeAIBehavior` can put an enemy straight back into `Grabbing` at the end of a grab.** It
re-picks the state by distance, and `distance <= grabRange` is the *normal* condition when a scene
has just ended — the player is standing where it left them. The mod's reactivation therefore ran
`TransitionToGrabbing` (a fresh, live `grabCoroutine`) and then `ApplyGrabEndCooldown`'s `StopGrab`
one line later, which stops the coroutine and nulls the handle without transitioning: state
`Grabbing`, no coroutine, nothing but `AiStateGuard` able to leave it. That 0.5 s recovery was
bug #14's visible hitch (§78). **Never call `StopGrab` on an AI that is still in `Grabbing`** —
letting `GrabSequence` run is safe, it clears its own flags and transitions out, and the grab it
attempts is refused by the player's post-grab immunity.

**The same `Stop*` call is right on one path and wrong on the other, and the difference is whether
the object has been deactivated since.** After a `SetActive(false)` the coroutine is gone but the
handle is not, and `StartGrab`'s `if (grabCoroutine != null) return` then refuses forever — so
`ClearStaleCoroutineHandles` must call it. On a live AI the handle means a running coroutine, and
the same call strands the state machine. Ask which of the two you are on before reusing either
(§78).

**A test about one enemy family is not a test about the session that is running (§102).** The
grapple gate asked `GrappleEnemies.IsImpEnemy(enemy)` and meant "does this enemy belong to
the cling that is already on screen". Those were the same question for as long as imps were the
only grappler, and 0.3.1's goonshroom made them different — so a goonshroom grapple refused the
goonshroom's own grab. When a second member joins a family, grep for the *first* member's name in
the code: every `IsX` that was standing in for "the current one" is now wrong, and each will fail
silently in its own way. `ResolveGrappleFamily` (§66) had already been written for exactly this,
one caller at a time.

**And the name is part of the test.** Two of those imp-only tests were left: the keep-alive
(`AttachImp`, `AttachedImps`, `ReleaseGrapplingImpsNearPlayer`, every one gated on `IsImpEnemy`)
and the grapple death sequence. Both survived two sessions of generalising the family *around*
them, because the method names read like descriptions of what they did rather than claims about
who they applied to (§114).

**The evidence for a bug of this shape is an asymmetry, not an error.** Nothing in the 2026-08-23
log said "failed": it said twelve `[GRAPPLE-ATTACH]`/`[GRAPPLE-RELEASE]` pairs, all imps, none
goonshroom, in a run full of goonshroom grapples. When two members of a family should produce the
same log lines, count them per member — a family that never appears is as informative as a line
that says something went wrong.

**Before generalising a workaround, check the game still needs it (§114).** The grapple keep-alive
existed because 0.2.1's `GrappleScreenobject.RemoveOneGrappler` did `Object.Destroy(gameObject)` on
a shaken-off grappler. **0.3.1 replaced that line with `ReleaseGrappler(enemy, shakeSign)`** -
which repositions the enemy beside the player and calls `ChargingEnemyAI.ThrowAfterGrapple`:
`SetActive(true)`, every child collider and renderer re-enabled, charge flags cleared,
`currentState = AIState.Idle`, and a rigidbody throw. That is the mod's entire release path plus a
throw, for every grappler, since `StartGrapple` reads `grappleAnimatorController` off
`ChargingEnemyAI` and so every clinging enemy is one. The mod was not missing the goonshroom; it
was overriding vanilla for the imp. The whole mechanic was **deleted**, not defaulted off.

**"Vanilla destroys grapplers" is true of three paths and false of the one the keep-alive was
written for.** `EndGrapple` destroys whatever is still clinging when the grapple ends any other
way, the trio-grab overflow destroys the non-representatives, and `DestroyRepresentativeAfterGrab`
destroys the representative when its grab scene ends. All three are left alone. Name the *path*,
not the class, when writing down what the game does to an object.

**Ask the game's own list rather than keeping a parallel one.** The four callers of the old
`GrappleEnemyProtection.IsProtected` all meant "leave a clinging enemy alone" - a clinging enemy is deactivated by
vanilla's `PerformGrabAttack`, so the autofix, the waker and the hider would each rescue one that
is exactly where it belongs. `GrappleEnemies.IsClingingNow` reads `grapplingEnemies` off the live
`GrappleScreenobject`; two lists can disagree and one cannot (§114).

**A reinforcement enemy spawned straight into a grapple is the one that still needs stowing.** It
never charged, so vanilla never deactivated it, and it stands around in the level while its overlay
clings to the player. Nothing needs recording for a restore: whichever way the grapple ends,
vanilla owns the other side (§114).

**"It has only ever been played against X" is a reason to test, not a reason to exclude — ask what
the mechanic compensates for.** `GrappleDeathSequence` was written up as deliberately imp-only
because it arms a game over. That argument does not survive asking why it exists: the clinging
enemies are what *block* the death (a grapple owns the screen, no grab can start while one runs,
and the death needs a grab), so the sequence is about grapplers and never was about imps. The
family that did not have it fell back to the revive-to-1-HP path — being invulnerable while
grappled, the exact behaviour the sequence replaced. The gap was worse than the widening (§114).

**Vanilla's trio overflow is family-neutral, and the prefabs say so.** `TriggerTrioGrabOverflow`
takes `trioGrabAnimatorController`, both camera offsets and `grabScreenAnimations` off whichever
clinger it picks; a UnityPy pass over every `ChargingEnemyAI` in the build shows the goonshroom
carrying `GoonShroom_GrabScreen` exactly as the five imp variants carry `Imp_Grab_Screen`. Read
the prefab before deciding a mechanic is one creature's (§114). Note what that scene then depends
on: it is entered at forced max heat, and `GoonShroom_GrabScreen` is the controller whose
parameter is `Max Heat` rather than `MaxHeat`, so §109's mirror is what lets the death finish.

**Read the family off the session, and remember it — the game's own list empties before the
session ends.** `grapplingEnemies` was already empty 1 ms before `[GRAPPLE-END]` while
`IsGrappling` was still true, which is the window the wrong refusal landed in. Any question
answered by walking that list needs a cached answer for the teardown window, and an unresolvable
answer must decline to act rather than fall back to a default family — falling back to "imp" is
precisely what produced the wrong refusal (§102).

**An empty `grabScreenAnimations` is not the absence of a name.** Imp scene data lives in
`GrappleScreenobject`, not in the AI, so every imp grab arrives with `anims=0` — and the animator
beside it still names `Imp_Grab_Loop`, which slugs to a real row. The readiness gate refused on the
array alone and the device held `imp_3` through a scene that had moved on (§102). `CurrentAnims` is
one source for the step name and `Animator.GetCurrentAnimatorClipInfo` is another; a gate should
refuse only when *every* source is empty.

**A throw inside a Harmony patch lands in the game's call stack, not yours.** Both halves of that
fix needed guarding for this reason alone: the secondary loop over `CurrentAnims` had been safe
only because reaching it implied the array existed, and `GetCurrentAnimatorStateInfo` can throw on
an animator mid-teardown. Relaxing a gate means auditing everything downstream that the gate used
to guarantee (§102).

**Guard the stage a player can reach.** §119 refused game-over cancels once `hasShownGameOver` was
set. That flag latches in `ShowGameOverPanel`, which runs only when the player presses a key at the
prompt — so the guard covered the panel and the report was about never reaching it. In the next run
every cancel still read `hasShownGameOver=False`, four times over, because the Blinded Beast
re-grabbed 1.0 s after its own grab and vanilla waits `delayBeforePrompt` (1 s) before raising the
prompt at all. The stage to protect is the one the evidence names (§120).

**A latch is only as strong as the paths allowed to clear it.** `_gameOverPresentationCommitted`
makes every cancel path inert, and the grab that stole the game over cleared it first — through
`PlayerStats.Revive`, whose release exists for the death-scene handoff (§77) and is called *by that
same grab*. A guard whose release runs on the event it guards against is not a guard. The release
now refuses while the prompt is up: the handoff is for a death not yet presented, and once it is on
screen the answer is the player's (§120).

**The mod's re-grab cooldown needs an enemy, and vanilla's hiding path can hand it null.**
`StabilizeAfterGrabEnd` applies `EndGrabEnemyCooldownSeconds` from an enemy captured in an `EndGrab`
prefix as `IsGrabbed ? GrabbingEnemy : null` — but a prefab with `hideInsteadOfDestroyOnGrab` has
moved to `GrabScreen.hiddenEnemyToRestore` by then. The cooldown was applied to nothing, silently,
on exactly the enemies that need it most. Capture the fallback, and log what was written: whether
the cooldown landed and whether the AI honours it are different questions, and `EnemyAI.TryGrabPlayer`
reaches a grab through `grabInDamagingState` + `hasGrabbedThisAttempt` without ever consulting
`lastGrabTime` (§120). **The log answered it: the write lands and the AI ignores it.** +10.0 s
written, the beast back at 2.28 s, twice (§122).

**Protect what is on screen; do not block what leads to it.** Two answers to one question lived in
this mod at once — the game over let the re-grab happen and made the presentation untouchable,
while everything else tried to stop the re-grab. The second is the weaker of the two and the beast
is why: a block has to be right about *every* route into the thing it blocks, and an AI reaching a
grab through a route that never reads your timer beats it silently, with a reassuring log line
saying otherwise. A latch on the thing that must survive only has to be right about that one thing.
`EndGrabEnemyCooldownSeconds` is 0 by default from §122, vanilla's timing stands, and the rule for
the next mechanic shaped like this is the latch, not the timer.

**A knob can be a no-op and read as policy for months.** `EndGrabImmunitySeconds = 4` looks like a
4 s block on re-grabs. Vanilla's `GrabScreen.GrabImmunity` sets `CanBeGrabbed = true` at T+1
whatever the mod's own coroutine is doing, so anything above 1 has never changed a frame of play
(measured in §44, acted on in §122). Before tuning a number, check that the game is still reading
it at the moment you care about.

**Only art on screen may decide where the floor is.** `GetComponentsInChildren<Renderer>(true)` is
right for a body renderer that spawns briefly disabled and wrong for everything else it returns:
the mimics carry their grab-screen sprites as inactive children hanging below the body, and seating
the instance on the lowest of *those* put it 1.28 m in the air where every other enemy needed
0.06 m. Require `enabled` and `activeInHierarchy` (§120).

**And ask a frame later, because `Instantiate` runs `Awake` and stops.** The filter above changed
nothing on its first run: an enemy that deactivates its own grab-screen art does it in `Start`,
which has not happened when the same frame measures the bounds, so every hidden child is still
`activeInHierarchy` and there is nothing for the filter to reject. One `yield return null` before
measuring is the difference between the prefab as authored and the prefab as the player sees it
(§122). The general shape: **a visibility test on a fresh instance is a test about lifecycle
timing, not about visibility.** Log which renderer decided the answer — the size of a correction
cannot tell a right measurement from a wrong one.

**A downward ray takes the first floor it finds, which is not always the one the player is on.**
`TryGetSpawnTransform` casts 12 m down from 3 m above a point a few metres ahead, and in the sewers
that point is often over the water channel — so a debug-spawned Dragon landed 1.2 m below the
player, invisible from where they stood and indistinguishable from the key not working. Reject a
hit more than a step below the asker (§120).


**A gate that is permanently false turns "commit the state, then call the coroutine" into an
endless loop, not a one-off hang.** `SpinningEnemyAI.TransitionToGrabbing` sets
`currentState = Grabbing` and then calls `StartGrab`, which early-outs on `!canGrab`. A custom
package that holds the vanilla grab shut by setting `canGrab = false` therefore strands the enemy
every time it enters grab range — and `AiStateGuard` recovers it to `Idle` 0.5 s later, still in
range, so it transitions straight back. Twenty recoveries in one run, in unbroken 0.5 s trains,
reading in play as an enemy lunging twice a second (§130). **Where the early-out is decidable
before the commit — `canGrab`, a null `grabScreen` — gate the transition itself**
(`GrabTransitionGate`); the state then stays `Idle` or `Spinning`, which the switch handles.
Watching the invariant is still right for everything not decidable in advance.

**"The object was deactivated, so its handles are stale" is an assumption worth measuring.**
`ClearStaleCoroutineHandles` justified an unguarded `StopGrab` that way for two sessions, and a
handoff blamed it for §130's re-grab loop. One run of instrumentation at that call site — printing
`activeInHierarchy`, `enabled`, the handle and the state — settled it in 49 samples: every call ran
on a *live* object, because `Reactivate` calls `SetActive(true)` unconditionally and the autofix
path reaches enemies that were never hidden; three found a genuinely live coroutine; and **not one
was in `Grabbing`**, so that call has never produced §78's strand and the guard everyone wanted
would have fired zero times. The mechanism was upstream, in the transition (§130).

**A custom package captures the player through vanilla's own `GrabScreen`, and from the core mod's
side that is indistinguishable from an enemy grab.** Both behaviours in the framework call
`GrabScreen.StartGrab(gameObject, null, ...)` with their own GameObject as the "enemy", so every
patch on `StartGrab` fires for a scene the package owns and dispatches entirely itself. Three things
went wrong at once and each is worth knowing separately (§134):

- **The scene name is an accident.** Nobody swaps the grab-screen animator's controller for a
  package, so `ResolveGrabStepName` reads the state of *whichever enemy was grabbed last* — the wall
  trap resolved to `joker_blackserpent_grabscreen`. It is not stable between captures, so the
  `ALIAS-GAP` line asking for an alias is asking for something that cannot exist; adding one would
  only race the package's own row for the channel.
- **`GrabScreenAudioFill` fills over the package's own sound.** An empty `grabScreenAnimations` on a
  package is not vanilla's asset gap (§124) — it is a package that has no vanilla grab animations.
- **The vanilla art draws underneath.** `ShowGrabUI` switches on `grabImage`, the object the
  grab-screen animator renders into, and it shows through any package overlay that is not opaque.

`CustomEnemyBridge.OwnsGrabScene` is the test, and `PackageGrabArt.Hide` deals with the art. **Do not
restore that art at the end**: a capture ends by calling `EndGrab`, whose `HideGrabUI` switches it
off, and the package's teardown runs *after* that — a restore leaves the last enemy's scene on screen
with the player free to walk around behind it. Vanilla owns the field in both directions.

Heat locks are deliberately *not* part of standing down: a capture is an erotic scene, holds heat like
one, and that lock is what keeps the filler off the channel for its length.

**Vanilla disarms the player through one latch, and a lock floor can make it unclearable.**
`PlayerStats.hasBeenOverheated` is set the moment heat crosses `MaxHeat` and cleared only at
*exactly* zero; `CanAttackNow()` is that latch, and `DualWieldingSystem.PerformAttack` gates every
heat-costing weapon on it, so a staff or tome dies while an unarmed swing carries on. A lock floor
makes zero unreachable, which is what `ClearOverheatAtLockFloor` exists for — but it clears through
vanilla's `ClearOverheatIfBelowMax`, which **refuses while heat is above `MaxHeat`**, and at full lock
the floor sits one point under the cap. `[OVERHEAT]` prints the latch, `CanAttackNow()`, heat, floor
and locks on every change; two runs show it flapping at full lock and clearing every time, so the
gap is real in the code and has not been caught happening (§134).

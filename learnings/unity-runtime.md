# Unity runtime traps

Engine-level behaviour that bit this project and would bite any Unity mod.

**Read this when:** an object misbehaves after being deactivated, a raycast fails, or state is written back by something you cannot grep

**Keywords:** SetActive, coroutine, Camera.main, raycast, layer mask, KeyCode, animator, Rebind, m_IsActive, genericBindings

---

**Deactivating a GameObject silently orphans state.** `SetActive(false)` kills the object's
coroutines *and* stops animation events, but unwinds nothing: coroutine handles stay
non-null, and flags set by one event and cleared by a later one stay set. Guards like
`if (spinCoroutine == null) StartCoroutine(...)` then refuse forever, and `isDashing` left
true blocks `FixedUpdate`'s movement branch permanently. `NearbyEnemyHider` deactivates every
enemy for the duration of a scene, so **anything hidden mid-action needs its transient state
reset on the way back**, not just its components re-enabled. Three separate bugs came from
this one behaviour (CHANGELOG §17b).

**Hiding vanilla art: disable components, never the object - and read the subtree first.** Two
sessions in a row got this wrong on one screen, the gallery's grab panel (§138, §139).

- `SetActive(false)` on the object that draws also takes its **children**, and an explicit
  `SetActive(true)` on a child cannot win against an inactive parent - `activeInHierarchy` stays
  false. On this panel the exit button, both arrows and the animation-name text are children of
  `Grabbed Animation Player`, the very object whose `Image` draws the art, so standing it down
  removed the entire navigation and left no way out of the screen.
- The art was **not one component**: the object's own `Image` plus three full-screen `Layer 2/3/4`
  children. Disabling only `GetComponents<Graphic>()` on the object left an opaque white cover.
  `GetComponentsInChildren<Graphic>(true)`, skipping the navigation objects and their descendants,
  is what works - and the navigation is resolved from the UI's own fields, never by name.
- **Every disable needs its restore, in the same state object.** §138 disabled the panel's
  background `Image` on a guess and never re-enabled it, so one visit to a custom entry left every
  later *vanilla* grab view drawing the menu through it. The guess was also wrong, which is the
  cheaper lesson: the overlay's own backdrop is an opaque child and already covered that background.
- Side effects that came free from deactivation have to be said out loud once it is gone.
  `grabAudioSource` rides on that object: with the object merely quiet rather than off, vanilla's
  grab sound has to be stopped and disabled explicitly, or it plays under a package's own audio.

The general rule underneath: **log the subtree before deciding what to hide.** One
`[CustomGallery] panel stack:` line - children two deep with component type, enabled, alpha and
rect size - replaced two sessions of inference and settled it in one run.

**A raycast from the camera hits the player first.** The camera sits inside the player's
collider, so line-of-sight tests must filter hits belonging to the player (`transform.root`)
or they fail everywhere, at 0.5 m, forever. This cost three rounds of chasing the wrong thing
before the log was instrumented (§25).

**`Camera.main` is not reliable here.** The view is driven by
`FirstPersonController.cameraTransform`, which need not carry the `MainCamera` tag and is
swapped during camera-swap scenes. Resolve as: `Camera.main` → the player's child camera →
lowest-depth camera with no `targetTexture`.

**`x == null` on a generic `T` does not use `UnityEngine.Object.op_Equality`.** Operator
resolution on a type parameter falls back to reference comparison, so a destroyed-but-not-null
Unity object compares as alive - and the failure is silent rather than a compile error. Any
helper generic over `T : MonoBehaviour` (`EnemyReactivationHelper.WakeDisabledAiType<T>` is the
one here) must box to the base class before testing, which is also why a
`((Behaviour)(object)val)` cast in such a helper is load-bearing rather than decompiler noise
(§116).

**Unity `KeyCode` has a hole at 128-255.** ASCII runs to `Delete` (127), then it resumes at
`Keypad0` (256). A config value in between can never be produced by `Input.GetKeyDown`, so the
binding is dead and says nothing. `[KEYBIND]` audits for it at startup. (Read the enum out of
`UnityEngine.CoreModule.dll` rather than trusting memory - that is how this was settled.)

**A raycast layer mask of `-5` is not "everything solid".** This game has `Player`, `Floor`,
`Blocker`, `Interactable`, `Effects`, `Pickups` layers, so a naive mask blocks on the player's
own body, the floor slab under a floor-level audio source, and every interaction volume in
between. Layer names live in `globalgamemanagers`' TagManager — parseable statically. And
`QueryTriggerInteraction.Collide` makes every trigger volume a wall. (The diorama raycast was
ultimately deleted rather than fixed — see below — but the mask trap applies to any new one.)

**A property is only rewritable if some clip declares it — read `genericBindings` before hunting
for another caller.** #18's stuck screen was `grabImage` going active during a teardown that had
just hidden it, with *no* C# anywhere in the process able to do that: the mod's seven
`SetActive(true)` calls are all enemies, and vanilla's only `grabImage.SetActive(true)` is in
`ShowGrabUI`, reachable solely from `StartGrab`. The actor was the **animator**.
`m_ClipBindingConstant.genericBindings` lists everything a clip is allowed to write, and a
`typeID: 1` binding with `attribute: CRC32("m_IsActive") = 2086281974` is a GameObject
*activation* curve. Exactly six clips in this game carry one — `WendigoKiss`/`Sex`/`SexIntro` and
`DragonFaceSit`/`SexScene`/`SexSceneIntro`, i.e. the two chaser bosses — all on the same transform
their sprite curve paints to. So `Rebind()` + `Update(0f)` in the teardown re-activated the layer
*after* the line that hid it, and the animator was disabled on the next statement, freezing frame
0 forever (§56). The fix was the statement order. Corollary: an animator writing something back is
invisible to `grep`, and `Rebind()`/`Update(0f)` must come **before** any manual state you want to
survive it. Fixing it by *order* rather than by re-hiding the specific object is what made it hold
in the verifying run: the dragon grab ends bound to `WendigoGrabScreen` (the restore target is
whatever the previous grab left), so the animator was on a curve-carrying controller at `Rebind()`
time and the layer came down anyway.

**Resolve a Unity resource once and a transient null is permanent for the run.** The escape hint
was invisible for a whole 0.3.1 session while the gate behind it worked perfectly — Q released the
grab on schedule, the countdown was never on screen. `EnsureHintOverlay` cached
`Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf")` in a static on first use, and a uGUI
`Text` with a null font draws nothing at all: no exception, no warning. The next run resolved that
same builtin font without trouble, which is what shows the *source* was never the problem and the
**caching** was. Re-ask on use while the value is still null (§74).

**Take a font from something the game already draws with.** `GrabScreen.GrabText.font` is a legacy
`Text` the mod writes into, so it is known to exist and known to render, and it needs no builtin
resource to be present in the player build at all. Keep the builtin names behind it, and log which
source won — an invisible UI element is the one failure mode that produces no evidence.

**Two consecutive calls in one Update are an alibi for each other.** `HandleEscapeKeys` working
proved `Tick` had been running and `ShowHint` had been called every frame, which cut the search to
the few lines between that call and the screen. When a symptom names one subsystem, check what
shares its call site before opening it up.

**A `StopAllCoroutines` teardown landing inside a coroutine's own delay is unrecoverable.** The
game-over prompt lives in `GameOverScreen.ShowGameOverSequence`, which waits `delayBeforePrompt`
(1 s) before it sets `promptPanel` active and `isWaitingForInput` true; `Update` watches only that
flag, and `OnPlayerDied` returns early forever afterwards. The mod's `CancelGameOverPresentation`
stops the screen's coroutines — correct while a scene is protecting the player, fatal one frame
after the mod itself triggered the game over, because a second `EndGrab` (the escape key is one)
runs it during the delay and nothing re-arms the sequence. Where cancel and trigger share a target,
the trigger must latch the target as committed rather than the cancel guessing when it is welcome
(§75). Corollary for diagnosis: **a state a coroutine is about to write is not visible in any
field yet**, so a snapshot taken during the delay looks identical to one taken after the cancel.

**Ask for the object that defines the state, not for the scene's name.** The horny lock readout was
drawn in the main menu because `UpdateDisplay` gated on its config setting alone and `ResetForScene`
calls it on every scene change. The two obvious tests are both lookups a future scene falls off
silently - the scene name against a list, or a `MainMenuManager` in the scene. Every level has a
`PlayerStats` and no menu has one, so `FindAnyObjectByType<PlayerStats>() != null` answers the
question the display is actually asking ("is there a run to show this for") and stays right for a
scene nobody has seen yet (§114). The same lookup was already running every frame, so it cost
nothing; check what the per-frame code already resolves before adding a second test beside it.

**The exception, and it is the ordering case (§148).** The menu filler asks the scene *name*
instead, which is the test this rule warns about, because the question is asked from
`activeSceneChanged` and whether the new scene's `PlayerStats` exists at that instant is exactly
what is not known. A predicate that depends on callback ordering is worse than one that depends on
a naming convention, so the name test stays until a log settles the ordering - `[SCENE] ...
playerStats=yes|no` is the line, added for it. `EndGalleryPlayback` still uses the `PlayerStats`
lookup, because it is asked from a gallery teardown rather than from a scene change. **Two
predicates for one question is a state to leave deliberately, not to discover later:** when the log
answers, they collapse into the object test.

**Unity's `VideoPlayer` has no H.264 decoder on Linux, and fails silently.** It has no codec of its
own for it: on Windows it hands the file to Media Foundation, on macOS to AVFoundation, and the
Linux standalone player has no equivalent to hand it to. `Prepare()` simply never completes — no
exception, no warning — so an H.264 MP4 shows as a black or transparent rectangle that looks like a
design choice rather than a failure. What Unity *does* carry on every platform is libvpx, so **VP8
in a WebM container plays everywhere**; VP9 has moved between versions and platforms and is not the
safe answer. The custom-enemy packages ship H.264, which is why the witch's dream overlays worked on
Windows and were blank on Linux (§127). `PackageVideo` prefers a `.webm` sibling on every platform
so one asset set works on both, `code/webmify.py` writes them, and its `--check` is a gate — the
point being that a silent codec failure has to become a check, because it will never become a log
line on its own.

**`Update` runs at `timeScale` zero, so "unscaled" and "while paused" are not the same question.**
Clocking a scene on `Time.unscaledDeltaTime` is often right - an overlay has to survive whatever the
game does to `timeScale` during a grab - but it does not mean "ignore `timeScale`", it means "ignore
pausing too", and those come apart the moment something pauses the game. §128's wall trap armed,
pulled the player and advanced animation stages behind the pause menu, and each stage POSTed a new
row to the device. Switching to `Time.deltaTime` is usually the wrong repair, because it also
freezes the case the unscaled clock exists for. Keep the unscaled clock and add an explicit "is the
game logically stopped" predicate - here `PauseHooks.SceneClockHeld`, which is the pause menu *plus*
anything else that holds `timeScale` at zero, such as a mod's own settings window.

**A `Dictionary` keyed by a Unity object is a leak.** A destroyed `UnityEngine.Object` compares equal
to null but is still a perfectly good dictionary key with a stable hash, so entries keyed on
destroyed objects are never found by a null check and never removed. Anything static and keyed that
way grows for the life of the process and keeps whatever its values reference alive with it. Key on
an instance id, or prune on scene change.

**A third-party character controller may own the Rigidbody outright, and then no force does
anything.** This game's player is `FirstPersonController : CMF.AdvancedWalkerController` — Character
Movement Fundamentals — whose `FixedUpdate` computes a velocity and calls `Mover.SetVelocity`, which
does `rig.linearVelocity = _velocity + groundAdjust`. That is an assignment, so **anything written
to that Rigidbody between two physics steps is erased at the start of the next one**: `AddForce`,
an impulse, a direct velocity write, all of them. The wall trap pushed the player with
`AddForce(pull, ForceMode.Acceleration)` for a whole release and moved nobody a centimetre, while
logging that it was pulling (§129).

Nothing about that failure is visible from the calling code — it is a correct Rigidbody call — so
the tell is in the log: an effect that engages and disengages at its own boundary with the distance
never changing. The fix is to apply the push **after** the controller's assignment, in a postfix on
the setter it uses; same physics step, so nothing overwrites it, and nothing accumulates either
because the controller recomputes its own half every step. Adding to the controller's own `momentum`
field is the other obvious candidate and was wrong here: momentum is what CMF applies friction to,
and this game's `groundFriction` is 100, so anything put there dies within a frame of touching the
floor.

Generalise it as: **before pushing anything the game also moves, find out what moves it.** A
component that assigns velocity, position or rotation every step is a component that wins, and the
only seam is the frame between its write and the next.

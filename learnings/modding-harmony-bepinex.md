# Harmony and BepInEx

Patching and configuration mechanics: what runs when, and how a config entry goes silently inert.

**Read this when:** adding a patch or a config setting, or a setting appears to be ignored

**Keywords:** Harmony, prefix, postfix, finalizer, BepInEx, Bind, section key, KeyboardShortcut, config default, cfgaudit

---

**BepInEx's `KeyboardShortcut.IsDown()` blocks on ANY other held key.** It is
`GetKeyDown(MainKey) && ModifierKeyTest()`, and `ModifierKeyTest` requires that no supported
KeyCode outside the shortcut's own is currently down. Right for a UI shortcut, wrong for a debug
key: holding `W` kills it. `Hotkeys.IsDown` relaxes that — **but only for non-modifier keys**,
because the config ships `FillerOnKey = Alpha1 + LeftControl` beside `SpawnZombieKey = Alpha1`,
and dropping the rule outright makes `Ctrl+1` fire both.

- **The grapple is a UI overlay, not the world model.** `GrappleScreenobject` animates a
  2D `grappleUI` (`OneImp`/`TwoImps`/`ThreeImps`) while `ChargingEnemyAI.PerformGrabAttack`
  `SetActive(false)`s the actual imp. Anything that keeps a grappled enemy alive must keep
  it *stowed*, or you get a second copy standing in the level. Vanilla's
  `GrappleScreenobject.SilenceForGrab` is the reference pattern for parking an enemy:
  AI off, colliders off, renderers off, `Rigidbody.isKinematic = true`.
- **Disabling an enemy's colliders without pinning its Rigidbody makes it sink.** Nothing
  left to stand on, so gravity integrates forever.
- **Harmony postfixes still run when a prefix returns `false`.** That caused the blocked-
  grab dispatch leak: `ImpGrappleGate` blocked the grab, `GrabHooks`' postfix dispatched
  anyway.
  Loop seams are absorbed automatically — do not "fix" them by trimming, that costs real
  content and desyncs duration.
  the preview device.
  through to plain gallery playback.
- .NET string literals are **UTF-16** in the DLL; an ASCII grep will not find them.
- The decompiled source in `code/` was a week older than the shipped DLL. **Always check
  the binary, not the source**, for questions about what the mod actually does.

**`UnityInput.Current` resolves its backend once, on first access, and caches the result — so
touching it too early can disable every hotkey for the whole run.** BepInEx tries
`LegacyInputSystem`, falls back to `NewInputSystem` when legacy throws, and falls back again to
`NullInputSystem` — which reads false for every key, forever — if that throws too. Under the Input
System package `NewInputSystem`'s constructor resolves a control for every `KeyCode` immediately
and NREs while `UnityEngine.InputSystem.Keyboard.current` is still null, which it is at plugin-load
time. The visible result is a plugin whose keys do nothing and whose log says nothing, because
`KeyboardShortcut.IsDown()` reads that same cached field (§72). **Do not read `UnityInput.Current`
from `Awake`**, and if something already has, re-probe once the keyboard exists and write the
working backend back into the private `UnityInput.current` field — repairing the shared field is
what reaches every `KeyboardShortcut`; a private backend of your own does not.

**The Input System has no keyboard device while the window is unfocused, and the backend probe
depends on one.** In the §72 run the repair landed 11 s after startup — not a slow fix but the
window being alt-tabbed the whole time: `[FOCUS] lost`, then `Resume`, then the repair 0.5 s later.
Re-probe on a timer rather than once at a fixed point, and do not read a startup-time reading of
`Keyboard.current` as "the Input System is not there".

**A patch class does nothing until it is named in `Plugin.cs` — there is no assembly-wide
`PatchAll()`.** Every class is registered on its own line, each with its own Harmony id
(`new Harmony("com.edi.pnc.heatparam").PatchAll(typeof(GrabScreenHeatParam))`), inside the
`CfgEnableGameplayTweaks` block for anything gameplay-shaped. §109's fix was written with the right
attributes, compiled, deployed, and had **no effect for an entire play session** because that line
was missing. The failure is completely silent: the class builds, the attributes are valid, Harmony
never sees the type, and nothing logs. What made it look like a bad diagnosis rather than a
wiring mistake was that one log line *did* appear — from a plain call site in another file, not
from a patch. **If a patch appears not to fire, check the registration list before you re-examine
the patch**, and confirm which call site actually produced any evidence you are reading.

**Two postfixes on the same method have no defined order unless you give one.** §109 clears an
animator bool in a postfix on `OnMaxHeatAnimationComplete`, while `HeatLockSystem`'s postfix on the
same method re-asserts the cum at full lock (`FullLockHoldsCum`). Whichever ran last would decide
whether a full-lock cum held or dropped to the loop — a race that would have shown up as an
occasional wrong scene, not as a crash. `[HarmonyPriority(800)]` on the clearing postfix pins it to
run first and lets the re-assert have the last word. Reach for the priority whenever two of this
project's own patches touch one method and one of them undoes the other.

**A patch that is not installed cannot start working later.** `PluginPatches` used to register the
gameplay patches behind `if (GameplayTweaksEnabled)`, which is correct while that answer can only
change by editing the config and restarting. Gameplay profiles (§127) made it changeable mid-run,
and the gate then meant a session begun on Vanilla could switch to Pressure and Release and get
nothing at all, silently. **Install every patch unconditionally and gate its body**, which is what
each of them already did. The converse matters too: nothing is ever *un*patched on a switch, because
Harmony unpatching a running game is how you get half-patched state. Startup diagnostics can stay
behind a gate — they are one-shot and there is nothing to switch on later.

**A grep for a raw `ConfigEntry` read is not evidence a patch bypasses the profile.** §158's audit
opened suspecting several gameplay patches (`CumDamageGate`, `EnemyGrabGate`, `HeatPotionLocks`,
among others) read their own config with no profile in the path, because that is what a grep for
`Cfg*.Value` shows. Every one of them in fact checked `Plugin.GameplayTweaksEnabled` — itself
`GameplayProfiles.TweaksEnabled` — one call earlier, which the grep's match line does not show. The
only way to answer "does this respect the profile" is to read the call chain up to the gate, not to
count `ConfigEntry` reads and assume the nearest one is unguarded.

**Two plugins that cooperate must not reference each other.** BepInEx loads plugin DLLs
independently and in no guaranteed order, so a hard assembly reference makes the first plugin fail
to load wherever the second is absent or a different version. Use one late-bound read of a public
static: walk `AppDomain.CurrentDomain.GetAssemblies()` for the type, cache the `PropertyInfo`, and
answer a default when it is not there. **Re-scan on a miss rather than latching one** — either
plugin can be constructed first, and latching kills the link for the whole session on exactly the
installs that want it. `ModManagerBridge` is the example (§127).

**An IMGUI window does not stop the game reading the keyboard.** `Update()` keeps running while
`Time.timeScale` is zero, so a mod's hotkeys fire on every keystroke typed into a settings field,
and bare WASD bindings move things. Put the stand-down at whatever single funnel your key reads go
through, and check for a second path around it — `Hotkeys.IsDown` had one branch going to BepInEx's
own `KeyboardShortcut.IsDown()`, which never touches `SafeInput` (§127).

**A plugin split has two directions, and only the one-way half is free.** `PncModManager`
references nothing and is reached by a late-bound property read, which is the rule above.
`PncCustomEnemies` genuinely needs the core mod's registries and Edi channel, so it references
`PncEdi` and declares `[BepInDependency]` on it — which also buys the load order it needs, since
BepInEx runs the dependency's `Awake` first. What must *not* happen is the reverse reference: the
core mod names no type of the plugin, and the handful of questions it has about packages go through
`CustomEnemyBridge`, a set of static delegates the plugin installs in its own `Awake` (§131).

**`[assembly: InternalsVisibleTo]` is what makes such a split cheap.** The alternative was
promoting some fifteen members to public API so the moved code could still reach them, and a public
surface invites binding by anything. Granting `internal` access to one named assembly keeps the
moved code compiling unchanged and keeps the surface closed. Grant it only to assemblies from the
same repo, built by the same command (§131).

**A seam whose fallback is "behave as if the plugin were absent" degrades silently, so it needs its
own audit.** Every `CustomEnemyBridge` delegate answers vanilla when nothing installed it — that is
what lets a player delete the DLL and keep a working mod. The cost is that deleting the *call* in
the core mod compiles, passes every test, and produces exactly the same behaviour as a missing DLL:
nobody learns of it until a play session. `code/bridgeaudit.py` requires each delegate to be
installed by one side and asked by the other, and names the seam that lost an end (§132). The
general rule is the one `patchaudit` learned in §114 — **a graceful fallback is a reason to audit a
seam, not a reason to trust it.**

**Give each plugin its own config file, along the same line as the code.** `PncCustomEnemies` binds
its own `com.edi.pnc.customenemies.cfg`, including each package's on/off switch and spawn weight.
The exception proves the rule: `Tools / EnableDebugEnemySpawn` stays in the core mod's file, because
it is one gate for every debug spawn key in the install and two settings of that name in two files
is how they end up disagreeing (§131).

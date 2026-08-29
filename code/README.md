# PncEdi source and tooling

Build, release and tool reference. **Rules and lessons live in `../learnings/`** (start at its
`README.md` index); `../PROJECT.md` is the map of the whole project. This file is the how-to.

Edi's own source is at <https://github.com/NoGRo/Edi>; its documentation thread is
<https://discuss.eroscripts.com/t/easy-device-integration-for-games-edi-handy-hps-ble-08-2026/108186>
and the integration guide is
<https://discuss.eroscripts.com/t/easy-device-integration-edi-how-to-integrate-your-game-now/118446>.

`edimod/` is the buildable source for `BepInEx/plugins/PncEdi.dll` (v2.6.0, for game 0.3.2).

Recovered 2026-08-15 by decompiling the shipped DLL with ILSpy 11 — the previous
tree was a v1.0.0 snapshot that predated the shipped build by a week and was
missing 7 files (HeatLockSystem, GrabEnemyProtection, 4x EnemyReactivation*Hook,
AssemblyInfo).

## Where the game is

This repo holds the mod and nothing else. The game is outside it, behind two symlinks that
`deploy.py` patches:

    game-windows -> ../PNC 0.3.2 WIN
    game-linux   -> ../PNC 0.3.2 Linux

`../Archive/PNC 0.2.1 Win` is the install this repo used to *be*. Everything the project has
verified was measured against its assets, so it is the right target whenever you need a 0.2.1
number back:

    PNC_GAME_DIR="../Archive/PNC 0.2.1 Win" .venv/bin/python code/animsweep.py     # 63/63 ok
                                                                    # + 30 rows "no clip/script":
                                                                    # the 0.3.1-only scenes
    dotnet build code/edimod/PncEdi.csproj -c Release -p:GameDir="../Archive/PNC 0.2.1 Win/"

## Build and deploy

    dotnet build code/edimod/PncEdi.csproj -c Release

That builds **all three** plugins, by two different mechanisms and for two different reasons.
`PncEdi.csproj` carries a `ProjectReference` to `code/modmanager/PncModManager.csproj` with
`ReferenceOutputAssembly="false"` — "build it, do not link it" — because that plugin references
nothing here. `code/customenemies/PncCustomEnemies.csproj` *does* reference PncEdi, so a
ProjectReference in this direction would be a cycle; a `BuildCustomEnemies` target runs it with an
`<MSBuild>` task after `DeployPlugin` instead, which also means it compiles against the PncEdi.dll
that was just built rather than whatever was there before. One command still produces everything,
and the three DLLs in `BepInEx/plugins/` can never be from different eras.

It deploys all three DLLs to `BepInEx/plugins/` **and** into both game installs — the
`PatchGameInstalls` target runs `deploy.py --dll-only` after the build, so a stale install cannot
be why a fix looks broken. Suppress it with `-p:DeployToGames=false` (which is what `release.py`
does; an archive build must not swap the binary you are testing).

The DLL is only part of an install. Everything else goes through:

    python3 code/deploy.py                 build, then patch both installs in full
    python3 code/deploy.py --no-build      use BepInEx/plugins/PncEdi.dll as it stands
    python3 code/deploy.py --check         is either install stale? (exit 1 if so)
    python3 code/deploy.py --refs-only     extract BepInEx for the build to reference
    python3 code/deploy.py --target DIR    patch some other install instead

**Run it after touching the config or the gallery.** Editing `Edi/Gallery/handy2pro/` or
`com.edi.pnc.cfg` changes nothing a running game can see until it is deployed.

The payload is `release.py`'s — `deploy.py` imports `bepinex_payload()`, `gallery_files()` and
`fetch_edi()` rather than growing a second definition of what an install needs. Three things
differ on purpose, all because a dev install is not a player install:

| | release | deploy |
|---|---|---|
| `com.edi.pnc.cfg` | rewritten through `SHIPPED`, incl. `Debug = false` | your live testing config, byte for byte, but always `[EDI] Debug = true` |
| `Edi/EdiConfig.json` | the scrubbed template | your live one, **only if the target has none** |
| `PncEdi-README.txt` | rendered for a named game version | not deployed |

Deploying the *shipped* config would put `GodMode = false` and `HeatLockAutoHealRate = 1` back
into the install on every build, i.e. undo the testing setup each time you rebuilt to test
something. `Debug` is handled from both ends: `deploy.py` forces it to `true` in both installs
whatever the working tree says, because they are debug installs and every `Plugin.DBG` line is
behind that one setting — a `false` committed by accident costs the *next* investigation a log with
nothing in it — while `release.py` ships it as `false`, so a player gets a quiet log. It is the one
`SHIPPED` entry that is not there because the live value deviates: live and coded default agree at
`true`, and the release differs from both deliberately. `EdiConfig.json` is user state — device keys, the `Variant` choice — so it is written
once and then left alone.

Every write is a byte compare (size-then-hash for the 220 MB `Edi.exe`), so a full re-run when
nothing changed is a sub-second no-op.

To keep the working DLL while iterating, build to a scratch dir instead:

    SB=/tmp/pncedi
    dotnet build code/edimod/PncEdi.csproj -c Release -p:DeployToGames=false \
      -p:PluginDeployDir=$SB/ -p:OutputPath=$SB/bin/
    cp $SB/PncEdi.dll BepInEx/plugins/PncEdi.dll

To confirm a specific change actually reached the binary, grep the strings — .NET
literals are UTF-16, so `-el` is required:

    strings -el BepInEx/plugins/PncEdi.dll | grep "some new log line"

### BepInEx to compile against comes from the pin, not from a game

`$(BepInExDir)` is `code/dist/bepinex/core/`, extracted from the same checksummed pack
`release.py` ships. It used to be `$(GameDir)BepInEx/core/`, which was fine while the runtime
lived in this directory and is a bootstrap loop now that it does not — you would need a deploy
before you could build. If it is missing the build stops with the command to run:

    No BepInEx to compile against at .../code/dist/bepinex/core/. Run: python3 code/deploy.py --refs-only

## Checking your work — `code/check.py` (§121)

    python3 code/check.py            the fast gates (~10 s) - run after any change
    python3 code/check.py --full     + the asset sweeps (~70 s) - run before a release
    python3 code/check.py --deploy   deploy (build + patch both installs) first, then check
    python3 code/check.py --list     the steps, their tier, and how each one reports failure
    python3 code/check.py -k alias   only the steps whose name contains `alias`
    python3 code/check.py -v         print every step's output, not only the failures

One runner over the thirteen checks PROJECT.md lists. It adds no check of its own; what it adds is
knowing **how each tool says no**, which is the part that made a hand-run sweep unreliable:

  * `gate` — the exit code is the verdict: `dotnet test`, `patchaudit`, `cfgaudit`,
    `ladders --check`, `dioramaaudit`, `deploy --check`, `release --check`, `refvideo --verify`.
  * `grep` — the exit code is **always 0** and the verdict is a word in the output. `slugharness`
    prints `UNMAPPED` per unmapped pair; `animsweep` prints `OFF` in its time column. Wrapping
    either one by exit code alone would report green forever, which is worse than not wrapping it.
  * `report` — no verdict exists to compute. `gallerydiff` and `speedcheck` answer a question a
    human reads; they run under `--full`, their summary is printed, and they fail the run only if
    the tool itself crashes.

`handystate.py` and `intensitybench.py` are deliberately absent: both drive or poll your Handy for
as long as you let them, so they are instruments, not checks. `intensitybench.py` plays one row,
steps `POST /Edi/Intensity/{max}`, and after each step reads the device's own `v2/slide` and
`v3/hsp/state` — it is what established that intensity moves the range without restarting playback
(§125), and it needs Edi running and the device connected.

A step whose prerequisites are missing — no `.venv`, no game install, no `dotnet` or `ffmpeg` on
`PATH` — prints `skip` **with the reason and the command that fixes it**, and is counted separately
in the summary. A check that quietly does not run is the failure this file exists to remove, so a
skip is never silent and never counts as a pass.

Steps run cheapest-and-most-fundamental first, so a broken config is reported in the first second
rather than after the 37-second `refvideo --verify`. `--deploy` deploys **before** the checks, not
after: `deploy --check` is one of the steps, and checking a tree you are about to deploy answers a
question nobody asked.

Adding a check is one `Step(...)` in the `STEPS` list — name, argv, the question it answers, its
tier, its kind, and what it needs on the machine.

## Releasing

    python3 code/release.py                # -> dist/PNC0.3.2-PncEdi-2.6.0.zip   (~89 MB)
    python3 code/release.py --check        # validate everything, write nothing
    python3 code/release.py --update-edi   # look up the newest Edi and print the pin to paste

**The bundled Edi is patched, temporarily.** `release.py` normally pins an upstream Edi release by
tag and checksum. It currently ships v1.0.4 **plus NoGRo/Edi PR #15** instead, because stock v1.0.4
stalls the device and drops it out of time whenever a looping gallery is played with a seek - which
is every pause and resume (§104-§106, issue #14).

That build cannot be downloaded, since no release carries the fix yet — PR #15 was merged upstream
on 2026-08-27 (`8406d51` on `master`), but v1.0.4 is still the newest tag. It is built from that
fix's branch and kept beside the upstream cache:

```
cd <your clone of github.com/NoGRo/Edi>
git checkout fix/close-the-rotated-loop-cycle
dotnet publish Edi.Wpf/Edi.Wpf.csproj -c Release -p:EnableWindowsTargeting=true -o /tmp/edi
cp /tmp/edi/Edi.exe code/dist/cache/Edi-v1.0.4-pr15.exe
```

`EDI_PATCH_SHA256` pins it exactly like the upstream one, so a release stays reproducible and a
rebuild that is not bit-identical fails loudly rather than shipping quietly. `release.py` refuses to
fall back to stock on its own - shipping the bug silently is the one outcome worth preventing.

`deploy.py` installs the same build into both dev installs as their `Edi/Edi.exe`, so what you
launch and what ships are the same binary. It pins against `release.py`'s `edi_pin()` rather than
the upstream `EDI_SHA256`, which is the whole trick: with `EDI_PATCH_PR` set those two differ, and
comparing against the upstream pair made a stock `Edi.exe` look current. That is what the
hand-placed `Edi-fixed.exe` beside it was working around; deploy now deletes it on sight
(`STALE_EDI`).

**To revert**, which is the goal: set `EDI_PATCH_PR = None`. Then `--update-edi` re-pins upstream as
usual, and the next `deploy.py` puts stock Edi back into both installs by itself. Do that as soon
as a released Edi carries the fix.

**One archive**, extracted into the game directory, always with Edi in it. It is named for the
game first and the mod second, because `PncEdi-2.1.0.zip` read like a version of the *game*. Both
now exist side by side, which is the case the naming was for:

    PNC0.2.1-PncEdi-2.1.0.zip     the last build for game 0.2.1
    PNC0.3.2-PncEdi-2.6.0.zip      what a build produces today (2.5.2 is the posted archive)
    ^^^^^^^^ the game it is for   ^^^^^ the mod, plain semver

The game identity can only live in the **name**, not in the version number: `BepInPlugin` parses
its version through `SemanticVersioning.Version` and the assembly attributes through
`System.Version`, so both are numeric by construction. `release.py` enforces plain
`MAJOR.MINOR.PATCH` on the mod version for that reason. The rest of the disambiguation is the
display name — the log reads `Loading [Post Nut Calamity EDI Integration 2.6.0]`.

Everything Edi needs sits together so a fresh install configures nothing:

    Edi/Edi.exe          unmodified from its GitHub release
    Edi/EdiConfig.json   GalleryPath = .\Gallery, the folder beside it
    Edi/Gallery/         the funscripts, 101 per variant

`Edi.exe` is 220 MB and compresses to 89 — a .NET single-file host is nearly all stored assemblies.

**Edi is pinned, not "latest".** `--update-edi` queries the GitHub API, downloads the newest
release, hashes it and prints the three constants to paste into `release.py`. It deliberately does
not edit them itself: shipping an Edi nobody here has run, under our name, is a decision, and an
unpinned dependency also makes the archive unreproducible. Note Edi has **no license file** — it
is redistributed unmodified as the community's mods do, and credited in the README.

### The shipped EdiConfig.json is where the secrets would leak

Edi names a connected Handy **`The Handy [<connection key>]`**, so the **device names** are the
credential — not some field called `key`. Two locks:

1. The shipped file is **hand-authored** at `code/dist/EdiConfig.json` and tracked, never scrubbed
   from the live one at build time. A redaction that misses a field fails silently, permanently,
   and only has to be wrong once. It carries the built-in `Preview Device` and nothing else.
2. `release.py` reads **your live `Edi/EdiConfig.json`**, extracts the real secrets from it —
   device names, the bracketed keys inside them, `Handy.Key` — and refuses to build if any of them
   appears in the file about to ship. It also refuses any device but the preview one, any
   `Handy.Key`, and anything merely *shaped* like a key (`[A-Za-z0-9]{6,}` in brackets).

The second is what catches a secret sitting in a field nobody thought to redact, which is the
failure the first cannot see. If you regenerate the template, keep both.

### The same archive serves Windows and Linux

That is possible because BepInEx's `core/` is managed code and **byte-identical** across its
win-x64 and linux-x64 packs — only the loader differs, and the two can share a folder ignoring
each other:

| platform | loads via | how it starts |
|---|---|---|
| Windows, and Windows-under-Proton | `winhttp.dll` + `doorstop_config.ini` | launch the game normally |
| native Linux | `libdoorstop.so` + `run_bepinex.sh` | `./start-pnc-linux.sh` |

`release.py` asserts that byte-identity every run; if a future BepInEx breaks it, the build stops
rather than shipping something that works on one platform only.

`start-pnc-linux.sh` is ours (`code/dist/`) and exists because BepInEx's `run_bepinex.sh` needs to
be told the executable name. It finds the `.x86_64` itself. **Keep it separate from
`run_bepinex.sh`**, which ships verbatim — upgrading BepInEx then stays a straight copy with
nothing of ours to re-apply.

**A Linux dev install runs a slightly longer version of it.** `deploy.py` splices `DEV_ROTATE` in
just before the hand-over to `run_bepinex.sh`, so each launch moves the previous run's
`BepInEx/LogOutput.log` to `BepInEx/logs/LogOutput-<that run's last write>.log` (newest twenty
kept, `PncEdi-missing-definitions.log` under the same stamp) and the session you are about to play
gets a log of its own. The file in `code/dist/` is untouched, so a player's launcher is the plain
one, and only a target holding a `.x86_64` gets the block. BepInEx has no setting for this —
`LogOutput.log` is a constant in `DiskLogListener` — which is why it lives in the launcher rather
than in `BepInEx.cfg`, and why `AppendLog = true` is still forced for the launches that go around
the script.

Nothing binary is tracked here. The BepInEx runtime is **fetched from a pinned build and checked
against its SHA256** (`BEPINEX_PACKS` in `release.py`), cached under `code/dist/cache/`. That is
what makes a release reproducible from a fresh clone, and since §62 it is where the *deployed*
installs and the build's own references come from as well — there is no copy of BepInEx anywhere
in this repo that was not extracted from those two zips. Offline, drop them into the cache
directory by hand.

The zip is byte-reproducible from a given commit: every entry is stamped with HEAD's commit time
and the README's build date comes from the same place.

**What it refuses to do:** ship a game binary, `certificate.pfx`, an `EdiConfig.json` carrying
anything of yours (see above), or a mod config with an undeclared local tweak in it. It also
cross-checks the four places that declare the version, and warns if the local `BepInEx/core` is
not the build being shipped.

### The config it ships, and why that needs a guard

`com.edi.pnc.cfg` is generated from the live one — which is a *testing* config. This has gone
wrong before, so every setting whose live value differs from **its own documented default** must
appear in `SHIPPED` in `release.py`, with the value to ship and the reason. An undeclared
difference aborts the build:

    release: these settings differ from their default and are not declared in SHIPPED ...
      [Gameplay] AmbientReleaseLookSeconds = 0  (default '3')

The check is self-maintaining because BepInEx writes `# Default value:` into the file itself, from
the `Bind()` call — so it compares against the plugin's own default rather than a list kept by
hand. Two long-standing accidents surfaced the first time it ran: `HeatLockAutoHealRate = 120`
(a testing tweak that had been shipping for as long as the old distributable existed) and a
`PeekGalleryMap` that was a stale *subset* of the coded default, missing three aliases.

`BepInEx.cfg` is deliberately **not** shipped — BepInEx writes a stock one on first run, so a local
diagnostic setting like `WriteUnityLog` can never leak into a release. `deploy.py` goes the other
way for the two dev installs and forces `[Logging.Disk] WriteUnityLog = true` / `Enabled = true`
into each target's own copy on every deploy (§95) — edited in place, never replaced, because
BepInEx regenerates that file from its own version's defaults.

## Config files

Every behaviour change gets a config entry with the old behaviour still reachable. After
adding one, write it into `BepInEx/config/com.edi.pnc.cfg` by hand (BepInEx only rewrites the
file on a clean run).

**Put it under the same section the `Bind()` call names, and check it:**

    python3 code/cfgaudit.py

BepInEx resolves a setting by **(section, key)**. A hand-written entry under the wrong section is
never found: the plugin runs on its coded default, the next launch writes a second copy under the
right section, and the entry you edit is read by nobody. It fails silently and in the
safest-looking direction, because the default usually matches what the file already said —
`DebugHotkeysIgnoreHeldKeys` sat inert under `[Gameplay]` instead of `[Tools]` from §47 to §49.
`release.py` runs this audit itself and refuses to build if it fails.

## Adding gallery content — no rebuild needed

`GalleryRegistry.Known` is only a *seed* list. `LoadDefinitions()` reads
`Edi/Gallery/Definitions.csv` at runtime and registers every row name, so new
scenes/characters need only:

  1. a funscript in `Edi/Gallery/handy2pro/`
  2. a row in `Edi/Gallery/Definitions.csv`
  3. animation-state aliases in `BepInEx/config/com.edi.pnc.cfg` (GalleryAliases,
     DioramaGalleryMap, PeekGalleryMap, Patterns)

A rebuild is only required for new *code* (new hooks, new enemy handling).

### Giving the gallery its own script for a scene

The gallery viewer plays its own `Gallery_*` clips, and several are a **different length** from
the in-game clip the row was scripted against — `code/gallerydiff.py` has the table. One funscript
cannot be whole-cycle correct for both, which shows up as "right in gameplay, off in the gallery".

Splitting one needs no rebuild, because in-game lookups check `InGameAliases` first and fall back
to `GalleryAliases`, while gallery lookups read `GalleryAliases` only:

1. add a `<Row>_Gallery` row + funscript, derived from the **gallery** clip;
2. repoint the gallery slug in `GalleryAliases` at the new row;
3. **if the slug is produced by both routes, pin the in-game one in `InGameAliases`** — otherwise
   the override drags gameplay onto the gallery script too, silently.

Whether a slug collides is not guessable: `nun_cum` is emitted by both, but gameplay says
`gooper_grab` where the gallery says `gooper_start`. Run the harness and read the `via` column —
in-game rows should say `InGameAliases`, gallery rows `GalleryAliases`. **Twenty-one** rows are
split this way — twelve as of §53 and nine more for the 0.3.1 enemies (§71) — which is every
mismatch `gallerydiff.py` finds, so it currently reports 0 still sharing. Dioramas and peepholes
need nothing: every diorama clip exists exactly once in the assets, and all eleven peephole gallery
twins match their in-game duration.

Not every new scene needs a split, and the two that do not are worth knowing by name: `Serpent_Cum`
and `BlindedBeast_Start` list the *same sprites at the same rate* in both clips. That is a fact
about this build, checked by `gallerydiff.py` rather than remembered — a future version can change
it.

## Known ceilings needing code changes

- **Three grapplers is vanilla's ceiling, and no code change lifts it usefully.**
  `GrappleScreenobject.maxGrappleCount` is a serialized field (3 on the shipped prefab) and
  `StartGrapple` refuses at it. Above three there is no grapple-UI animator state and no cling
  scene, because those are named `prefix + count`. `GrappleReinforcement` reads the live field
  rather than assuming 3 and takes the lower of it and the configured ceiling, so
  `*/GrappleReinforcementCeiling` can only ever lower the cap (§86).

`DioramaGalleryMap.DefaultDSlotAmbients` used to be listed here. It is gone (§33): the built-in
D-slot fallback is now parsed from `CfgDioramaGalleryMap.DefaultValue`, so it cannot drift from
the shipped default and imposes no slot limit.

## Files added on top of the decompiled v2.0.8

| file | what |
|---|---|
| `GrappleDeathSequence.cs` | dying in a grapple plays out as that creature's trio scene (any clinging family since §114) |
| `CumDamageGate.cs` | suppresses the HP cost of cumming in a scene |
| `HeatPotionLocks.cs` | heat potions remove horny locks instead of flat heat |
| `AmbientReleaseGaze.cs` | diorama look timer for the release (box + facing angle, no raycast) |
| `DioramaUnlockTriggers.cs` | reads the game's own `GalleryUnlockTrigger` boxes (D1–D9) |
| `GameplayProfileRules.cs` | the profile truth table, Unity-free so `code/tests` can check it (§127) |
| `GameplayProfiles.cs` | the live half: which rules are in force, and handing the player between them (§127) |
| `ModManagerBridge.cs` | late-bound "is the settings window open", so hotkeys stand down (§127) |
| `CustomEnemies.cs` | the package loader: manifests, bundles, spawn injection, funscript sync (§127) |
| `CustomGallerySection.cs` | the Custom Enemies gallery tab (§127) |
| `WallPictureTraps.cs` | the wall-picture trap behaviour, driven by `wall-trap.json` (§127) |
| `CharmWitchController.cs` + `WitchAuraCircle.cs` | the charm-circle boss, driven by a manifest's `witch` block (§127) |
| `RuntimeSpriteVisual.cs`, `RuntimeWav.cs`, `BaseEnemyStripper.cs` | PNG sheets, WAV cues, and stripping a cloned enemy back to its AI (§127) |
| `PackageVideo.cs` | prefers a `.webm` sibling — Unity cannot decode H.264 on Linux (§127) |

The release gauge under the "Horny X/Y" readout is shared: `AmbientReleaseGaze.Tick` drives it
every frame, showing the peephole watch timer when one is pending (`HasKeyholeWatchBar`) and the
diorama look timer otherwise. Anything else that wants the bar has to go through there, or the
per-frame push will hide it again.

(`OverheatRules.cs` existed briefly and was deleted — see CHANGELOG §11.)

### The settings-window plugin — `code/modmanager/` (§127)

`PncModManager` is the in-game settings window: F11, or a button cloned onto the main menu. It is
an IMGUI view over BepInEx's own `ConfigFile`, so it configures **every loaded plugin**, not this
one — which is exactly why it is a separate assembly.

**Neither plugin references the other, and that is deliberate.** BepInEx loads plugin DLLs
independently and in no guaranteed order, so a hard reference would make PncEdi fail to load on any
install where the manager is absent or a different version. The one link is late-bound:
`ModManagerBridge` walks the app domain for `PncModManager.Plugin.IsOpen`, caches the
`PropertyInfo`, and answers false when it is not there. It re-scans on a miss rather than latching
one, because PncEdi can easily be constructed before the manager's assembly is loaded.

That flag is not cosmetic. **`Update()` keeps running while the manager holds `Time.timeScale` at
zero**, so without it every keystroke typed into a settings field also fires whatever hotkey shares
that letter, and FreeCam's bare WASD flies the camera while you edit a number. The stand-down lives
in `SafeInput`'s three readers, which is the funnel for every key this mod reads; `Hotkeys.IsDown`
repeats it because one of its branches goes to BepInEx's own `IsDown()` and bypasses `SafeInput`.

The fork this came from also had a live-reload feature. It is not here: it `Assembly.Load`ed a
rebuilt plugin into the running AppDomain and reflection-wrote BepInEx's `PluginInfo`, and Mono
cannot unload an assembly, so what it bought was a way to leave a mod half-destroyed.

### The custom-enemy plugin — `code/customenemies/` (§131)

`PncCustomEnemies` is the custom-enemy framework: package loading, sprite animation, the gallery
section, the two behaviours that ship with it (the charm witch and the wall-picture trap), and the
runtime WAV and video loaders they need. It was part of PncEdi until §131.

**This one depends on PncEdi, and only in that direction.** A package's scenes are Edi content — it
registers gallery rows and aliases, plays rows, takes heat locks — so pretending otherwise would
mean duplicating the registries. What does *not* happen is the reverse: PncEdi names no type of
this assembly. The handful of core decisions that need to know about packages ask
`CustomEnemyBridge`, a set of delegates the plugin installs in its own `Awake`, and every one of
them has a vanilla answer for "nothing installed them" — which is exactly what deleting
`PncCustomEnemies.dll` gives you.

`[assembly: InternalsVisibleTo("PncCustomEnemies")]` in `PncEdi/AssemblyAccess.cs` is what kept the
split cheap: the moved code goes on using the same `internal` members it always did, rather than a
hundred of them becoming public API that anything could bind to.

`[BepInDependency("com.edi.pnc")]` makes BepInEx load PncEdi first and run its `Awake` first, which
is the order the framework needs — packages register into tables the core mod has already loaded.
Its settings live in its own `com.edi.pnc.customenemies.cfg`, including each package's on/off
switch and spawn weight.

**Three gates keep PncEdi from breaking it silently** (§132), which is what makes the two
separable in practice rather than only on paper: the same `dotnet build` compiles all three
plugins, so a rename is a build error; `patchaudit.py` audits both source trees and both
registration lists; and `code/bridgeaudit.py` catches the case neither of those can see - a
`CustomEnemyBridge` delegate that stops being installed, or stops being *asked*. That last one
matters because every delegate falls back to vanilla, so a call deleted during a refactor looks
exactly like a deleted DLL and nothing reports it until someone plays. Treat those calls as
load-bearing.

**A package's capture runs vanilla's own grab screen** (§134). Both shipped behaviours call
`GrabScreen.StartGrab` with their own GameObject as the "enemy", so every PncEdi patch on `StartGrab`
fires for a scene the package owns and dispatches itself. `CustomEnemyBridge.OwnsGrabScene` is how the
core mod tells them apart — it stands down from naming, Edi dispatch and the grab-screen audio fill,
and keeps the heat lock. `PackageGrabArt` switches off vanilla's `grabImage` for the length of a
capture, and deliberately never switches it back on: `HideGrabUI` does that at `EndGrab`, and a
package's teardown runs after it.

`release.py`'s `PLUGINS` maps each plugin to its project and ships all three.

### Custom-enemy packages (§127)

A package is `BepInEx/custom-enemies/<name>/` with an `enemy.json` (or `wall-trap.json`), its art,
and its funscripts. It needs no code change: the manifest declares the enemy's scenes, gallery rows
and aliases, and `CustomEnemyRegistry` registers them at startup.
`BepInEx/custom-enemies/_example/` and the two format references beside it —
`CUSTOM-ENEMIES.md` and `WALL-PICTURE-TRAPS.md`, imported from the fork and checked claim by claim
against this tree in §129 — are the format.

**A package's text is tracked; its media is not, and neither is in the release.** The split is
deliberate and the two halves have different reasons:

- **The media** — sprite sheets, video, audio — is third-party artwork whose `SOURCE.txt` credits
  galleries and artists. It stays out of git because git history is permanent: a clone would carry
  it forever, and a takedown would mean rewriting history rather than deleting a file. It reaches
  players as its own archive instead (below).
- **The text** — the manifest, `SOURCE.txt`, and `funscripts/` — is tracked. The funscripts are
  *ours*, authored and measured the same way `Edi/Gallery/handy2pro/` was, and a blanket ignore
  aimed at the video beside them used to discard them. The manifest is mostly game-side tuning
  (`maxHealth`, `detectionRange`, `captureDistance`, `spawnWeight`), which otherwise lived in the
  changelog and in two game installs and in no tracked file.

`.gitignore`'s rule under `BepInEx/custom-enemies/` is deny-by-default and names the three kinds of
text back in, so a media format nobody has thought of yet is ignored without anyone remembering to
ignore it. **A fresh clone therefore has a package's text with no media beside it, and the package
will not load until the media is restored from its archive.**

`deploy.py` still copies whatever the working tree holds into both installs. The main release still
ships the framework, the templates and the documentation only — a package is a separate download:

    python3 code/release.py --package femboy-witch     -> dist/PncEdi-FemboyWitch-<version>.zip
    python3 code/release.py --package all              every installed package
    python3 code/release.py --package all --check      validate, write nothing

One archive per package, extracted over the game directory like the release itself, with a
generated README carrying the package's own `SOURCE.txt` credits. Keeping them out of the main
archive holds it at ~89 MB instead of ~142 MB, and leaves a player to opt into explicit
third-party content rather than receive it.

Three guards specific to a package, because a player cannot run this repo's checks:

- **no `SOURCE.txt`, no archive.** A package that ships someone's art ships its credits.
- **an MP4 with no WebM beside it fails the build.** Unity has no H.264 decoder outside Windows and
  macOS, so that is a blank overlay on Linux rather than an error (§127) — the same rule
  `webmify.py --check` applies to the working tree.
- **the H.264 masters are not shipped at all.** `PackageVideo.ResolvePath` tries the `.webm`
  sibling *first and unconditionally*, before its own Linux test, so once a WebM exists the MP4
  beside it is never opened on any platform. In the witch's package that was 35 MB of a 51 MB
  download that nothing would ever read; dropping it took that archive to 16.8 MB. The guard above
  is what makes it safe — no MP4 is dropped unless its WebM is there.

The build also **reports** files the manifest never names, rather than dropping them. A package
directory is also a working directory, and superseded sheets are bytes a stranger downloads for
nothing — but absence from a manifest does not prove disuse, since the WebM itself is found by
sibling convention, so a rule that shipped only named files would drop exactly the file Linux
needs. The note is there to be read by a person.

**The gallery has two writers, and only one of them runs here.** A package's funscripts and
`Definitions.csv` rows have to reach Edi's gallery, and there are two ways for that to happen:

- **From this side.** `deploy.py` and `release.py` read each manifest with real JSON
  (`release.custom_enemy_gallery`), resolve the rows, and merge them onto the repo's
  `Definitions.csv` (`release.definitions_with`) as part of the payload. **This is what runs on a
  machine with this repo**, and it is why `deploy.py --check` still means something: the deployed
  gallery is part of what the payload declares, so it can be compared byte for byte.
- **From the mod, at runtime.** `CustomEnemies.SyncFunscripts` does the same thing against the live
  install. That path exists for a player who drops a package into a game directory with no repo
  behind it. Here it should find its rows already correct and write nothing.

**If `deploy --check` reports stale after a launch, those two have drifted apart** — they build the
row string by the same rule and must keep agreeing (§128). They did drift, and §129 is what that
cost: the repo side read `manifest["scenes"]` for every package kind, and a wall trap keeps its
scenes under `animations`, so it emitted no rows at all for one and the two sides undid each other
on every launch.

Both refuse to touch a row the package does not own: ownership is "the row's `FileName` column names
a funscript this package ships", which is the only test that survives a restart, and a collision
with a real gallery row is refused with a warning rather than silently repointing a measured row at
a package's script. The runtime writer keeps a one-time `Definitions.csv.pre-custom-enemies` backup,
replaces the file by temp-and-move because a plain `WriteAllLines` truncates it before it writes,
and preserves the file's byte-order mark — `ReadAllLines` strips one, and writing it back without
changes three bytes that `--check` compares.

**There is one runtime writer, not one per package kind.** `CustomEnemyRegistry.MergeDefinitions`
is it, and `WallPictureTrapRegistry` calls it. The wall-trap registry used to carry its own copy,
and the copy had lost the ownership rule, the safe write and the funscript content guard — three
ways for a package to overwrite something measured. A third package kind must call the same method
rather than grow a fourth copy.

**A custom scene must not keep playing while the game is paused.** The wall trap and the runtime
sprite visual are clocked on `Time.unscaledDeltaTime` on purpose — a grab overlay has to survive
whatever the game does to `timeScale` during a grab — but `Update` still runs at `timeScale` zero,
so behind the pause menu the trap was arming, capturing and POSTing rows to Edi, and the mod
manager's window is a second way in. `PauseHooks.SceneClockHeld` is the predicate for "the game is
logically stopped"; anything clocked unscaled has to consult it (§128).

**Videos need a WebM, or they are blank on Linux.** Unity's `VideoPlayer` has no H.264 decoder of
its own — Media Foundation on Windows, AVFoundation on macOS, and nothing on the Linux standalone
player — while libvpx ships everywhere, so VP8 in WebM plays on all three. `PackageVideo` prefers a
`.webm` sibling on every platform; `code/webmify.py` writes them and `--check` is a gate in
`check.py`. The failure it prevents is a silent one: `Prepare()` never completes, nothing is
logged, and a transparent overlay with nothing in it looks like a design choice.

**The manifest parser is inherited, not written here.** `HydrateNestedManifestFields` and its
hand-rolled `ExtractDelimited` / `ParseStringArray` exist because Unity 6's `JsonUtility` was
leaving nested objects and arrays at their field initialisers for the fork's author. That diagnosis
was taken on trust and the code ported as-is — rewriting a parser you cannot run is worse than
keeping one that demonstrably worked. **If a manifest field silently reads as its default, start
there.**

### Tests (§118)

    dotnet test code/tests/PncEdi.Tests.csproj

112 tests over the naming, alias and config layer, compiling the **real** source files rather
than copies. `code/tests/README.md` has the detail: what is testable and why the rest is not,
the mutation testing the suite was checked with, and how to bring another file under test.

The short version of the boundary: most of the mod is Harmony patches over live game objects and
needs a running game, which is what the audits below and a play session are for. What sits
between the game and the HTTP call is pure logic, and it is where this project's bugs have
actually been — §92, §80, §96 and the substring-guessing fallback in `NAMING-AUDIT.md` are each
a test now.

### `ConfigMap.cs` — the `key=value` format, once (§117)

Nine settings are written `key=value;key=value`, and seven places each had their own copy of the
same fifteen-line parse loop. `ConfigMap.Pairs(raw, separators)` is now the only one:

    foreach (KeyValuePair<string, string> pair in ConfigMap.Pairs(raw))
        into[pair.Key] = pair.Value;

The contract is what every copy already did — `;`-separated (newlines too where the caller asks,
because `GalleryAliases` is hand-edited and wraps), split on the **first** `=`, both sides
trimmed, an entry dropped if either side is empty or there is no `=` at all.

**What is not in it, on purpose:** casing, slugging, number parsing. `EnemyRemap` lowercases both
sides, `PeekClipMap` slugs the key, `ClassHeatMultipliers` wants a clamped float,
`HeatPotionLocks` wants the longest key that is a substring of the item name. Those are four
different intents over one format, and the caller keeps them. `ConfigMap.SortLongestKeyFirst`
did come out with it, because "longest matching key wins" is a promise the config descriptions
make and it had three implementations.

**`code/slugharness/harness.csproj` compiles `ConfigMap.cs`** along with `NameRemap.cs` — the one
piece of real coupling this created. Add a file there if `NameRemap` ever reaches for another.

### Plugin.cs is three files (§115)

`Plugin` is a `partial class` split across three files. Nothing about it is a namespace or a call
site — every `Plugin.CfgX` and `Plugin.SendPlay` in the other 63 files is unchanged — it is only
that one 1846-line file held three unrelated jobs:

| file | what is in it |
|---|---|
| `Plugin.cs` | the runtime: `Awake`, `Update`, `SendPlay`, the filler ladder and its menu variant, the pause/resume markers |
| `PluginConfig.cs` | all 150 `ConfigEntry` fields and `BindConfig()`, the one run of `Bind` calls |
| `PluginPatches.cs` | `ApplyPatches()` — the Harmony registration list, and nothing else |

`Awake` is now thirteen lines and reads as the startup order it is:

    Instance = this; Log = base.Logger;
    BindConfig();  ... Reload();  SceneManager.activeSceneChanged += ...;
    _inMenuScene = ...;  ApplyPatches();  GoFiller();

The menu flag is seeded from the active scene rather than left to the callback: `Awake` runs inside
whatever scene the game booted into and *before* the first `activeSceneChanged`, so without it the
`GoFiller` on the last line reads the boot menu as gameplay (§148).

**Why the patch list is its own file.** Patches are registered per class, not by an assembly-wide
`PatchAll()`, so a new patch class does nothing until it is named there — and the failure is
silent, which cost §109 a whole run. Two things follow from giving it a file:

- The four patches that may legitimately fail on a build that moved their target go through
  `TryPatch`, which is one method rather than four hand-decompiled `try`/`catch` blocks with
  `BepInExWarningLogInterpolatedStringHandler` scaffolding in them (about sixty lines gone). Do
  not reach for `TryPatch` to quieten a patch that ought to bind — a patch that silently declines
  is the failure mode this project keeps paying for.
- **`patchaudit.py` now checks the list.** Every class in the tree with a `[HarmonyPatch]` member
  must appear in `ApplyPatches`, and every registration must have a patch class behind it. It
  runs on every `patchaudit.py` invocation and exits 1 on a gap, so §109's silent failure is now
  a one-second check. It currently reads 32 and 32.

## Device variants

`Edi/Gallery/` holds three variant folders. **Edi selects a script by variant and the variant is
the folder name**, so per-device versions need no mod change and no config setting — set
`"Variant"` on the device in `Edi/EdiConfig.json`:

| variant | for | ceiling | differs from `handy2pro` |
|---|---|---|---|
| `handy2pro` | Handy 2 Pro with the slider overclock up — **the master and the default** | none | — |
| `handy2` | Handy 2, OSR/SR6, or a 2 Pro overclocked part-way or not at all where the loud rows are too much | 600 u/s sustained, 700 peak | 16/102 |
| `handy1` | Handy 1, or any device you are unsure about | 364 u/s (110 mm @ 400 mm/s) | 79/102 |

**The folders were called `detailed` and `handy1` until §149**, and `detailed` is what every
release up to 2.5.2 shipped. It was renamed because it named a quality tier rather than a device,
which is the one thing a variant name has to do — a player picks it off their hardware. A config
still saying `"Variant": "detailed"` finds no folder, so the archive README says so at the point
where it tells you to set it, and the troubleshooting section names the old value.

```json
"The Handy [xxxxxxxx]": { "Variant": "handy1", "Channel": null, "Min": 0, "Max": 100 }
```

**The master is not limited, and that is still the decision.** A max-overclocked Handy 2 Pro does
1200 mm/s = **960 u/s** (its own overclock menu; review articles say 800 and are low). Against
that, `handy2pro` runs p95 901 u/s — *under* the cap — and only a single script (`imp_3`, median
1041) is sustained beyond it; eleven others exceed only on isolated accents. Scripters write those
on purpose — `shared_zombie` has a 1538 u/s (1923 mm/s) jolt no device can literally reach, which
renders as a snap — so clipping them would strip intended punch from the one device fast enough to
enjoy it. `handy2pro` **is** the Handy 2 Pro script.

**`handy2` is generated to a *pair* of caps, which is new (§149).** The eroscripts multi-axis
guide quotes a soft and a hard figure for every device — 600 and 700 units/s for a Handy 2 — and
the two mean different things: soft is what a script should *sustain*, hard is a
wall. A single-cap limiter cannot express that. Set it to 700 and every deliberate accent is
flattened; set it to 800 and almost nothing is limited at all. So `variants.py`'s limiter carries
a **token bucket** between the two: each transition earns `soft × dt` units of credit and spends
what it travels, the balance capped at `budget` (20 units) and never negative, and a transition may
cover up to `min(hard × dt, soft × dt + bucket)`. A script that has been idling can spend a full
bucket on one accent at the hard cap; a script already running flat out has an empty bucket and is
held at the soft cap for every further transition. 20 units is about 0.2 s of accent before the
soft cap takes over — a snap rather than a section. The result satisfies the guide's contract
exactly: `speedcheck --variant handy2` reports **0 rows over 600 by median and 0 transitions over
700**.

**The guide's next row up, "The Handy 2 Overclocked" (700/800), is deliberately not what this
folder uses.** Overclocking is a 2 Pro feature, so that row is most likely describing the same
device the master is authored for — and its author says outright he owns neither device and took
the figures from forum searching. A folder named for a device should carry that device's own row,
and the more conservative of two hearsay figures is the right way to be wrong. A 2 Pro overclocked
part-way sits between this folder and the master; there is no fourth folder for it, because the
choice between 600/700 and unlimited is exactly the choice the slider itself offers.

**The guide has no Handy 2 Pro row**, and the one figure its comments offer for that device — 1200
*units*/s — is higher than the 960 read off the device's own menu, so nothing there argues for
limiting the master. (A stock, un-overclocked 2 Pro is 450 mm/s = **360 u/s**, which is `handy1`'s
territory rather than `handy2`'s — the middle folder is for a device that is genuinely between the
two, not for a 2 Pro with the slider down.) Its Handy 1 pair (400/500 units/s) is likewise above that device's 364 u/s
firmware ceiling. `handy1` therefore stays a single-cap limit: 364 is hardware, not taste, so
there is no softer figure to sustain and nothing to bank.

**The 125 mm figures were always the 2 Pro's; only the key name was wrong.** `speedcheck.py`'s
`DEV` called them `handy2` and `handy2_oc` because early notes recorded the device as a Handy 2,
but the numbers were read off the 2 Pro's own overclock menu and never changed. The keys are now
`handy2pro` and `handy2pro_oc`, so no measurement is invalidated and no profile is missing.
Corrected in §103, which also gave the tool the two summary lines it lacked: how many rows exceed
the 2 Pro's overclock ceiling (5) and how many fall under its 15 mm/s floor (5). Until then only
the Handy 1 tally was summarised, so the per-row `>Proc` column had no total and nobody read it.
The stale `--variant handy2pro` in the docstring is gone; the gallery has `handy2pro/`, `handy2/`
and `handy1/`.

The Handy 1 case is different and does warrant limiting: the median transition across the whole
set is 363 u/s, i.e. half of everything sits at or above that device's cap. That is sustained
excess, not accents, and it mushes.

### Where a curve comes from

Most scripts were measured from the animation and then scaled into whole-cycle alignment by
`retime.py --apply`. The ones that could not be are kept as code, with the frame evidence beside
each curve, so they are reproducible and arguable rather than an unexplained JSON edit:

| module | scenes | why not measured |
|---|---|---|
| `authored.py` | `Baphomet_Start`, `Baphomet_Cum`, `Gravy_Loop2` | written from a feel cue (§40) |
| `impgrab.py` | `imp_grab_loop`, `imp_grab_cum` | two imps doing different things (§35) |
| `rederive.py` | the six `retime.py` refused, `Wendigo_Continued`, and the original twelve `*_Gallery` rows | wrong shape, wrong target, nothing on screen, or the gallery plays a different clip (§48, §51–§53) |
| `scenes031.py` | game 0.3.1's six dioramas and four peek scenes | a whole-frame proxy averages a diorama into mush (§67) |
| `grabs031.py` | game 0.3.1's three new enemies — eleven grab scenes and nine `*_Gallery` twins | scene-specific proxies, and four cum clips that change geometry partway through (§71) |
| `ladders.py` | the seven filler rows, and the serpent's single `Serpent_Hypnosis` row | a set the mod switches *between* mid-playback, so the rows have to agree with each other, not only with a clip (§87). The serpent's row is generated here for its measured shape, not because it is a ladder — §125 replaced its tiers with one row the mod scales through Edi's `Intensity` |

Re-running any of them with `--write` regenerates its scenes and adds rows to `Definitions.csv`
where they do not exist yet. **Then re-run `variants.py --write`.**

`ladders.py --check` answers "is the working tree still a ladder" and exits 1 if not — the
invariant is invisible in any one file, since a hand-edited `filler_cum_50` looks perfectly
reasonable on its own and only steps the device against its neighbours. `--write` is the fix.

`ladders.py` is the odd one out and worth reading before touching any of the seven filler rows.
Everywhere else a curve answers to one animation; a ladder row is *replaced mid-playback* by its
neighbour whenever the signal moves, so the rows are built on one time grid with one anchor and
differ only in amplitude. Edit one by hand and the switch between it and its neighbours steps the
device again. The mod's half of that contract is `SendPlay(..., preservePhase: true)` and the
hysteresis on both ladders' thresholds.

The `*_Gallery` variants read their master's *file* rather than hardcoding it, so editing a master
and re-running `rederive.py --write` (or `grabs031.py --write`) keeps its gallery twin in step
automatically. Both build a twin with `rederive._remap_by_frame`, which maps the two timelines
through the frames they **share by sprite name** — so a viewer clip that inserts or drops a frame
stretches only that segment. Sanity-check any new twin against the invariant: same length means
the remap is the identity, different length means it must move more than the closing point (§71).

The generated variants are rebuilt from *all* of them, so run `variants.py --write` last.

`handy2pro` is the master and `handy2` and `handy1` are **generated from it** — author there, then:

    .venv/bin/python code/variants.py --write     # rewrites handy2/ and handy1/ from handy2pro/

The same command also emits `handy2/` for every custom-enemy package, from that package's own
`funscripts/handy2pro/` masters. A device pointed at a variant a package does not carry plays
nothing for that enemy, which is the parity failure §5567 found for per-axis files. Package
`handy1/` folders are **not** regenerated: those were authored by hand against the Handy 1 rather
than slew-limited, and overwriting them would throw that work away.

Never hand-edit `handy2/` or `handy1/` in the main gallery; the next regeneration discards it. Check playability with
`code/speedcheck.py [--variant <name>]`, which reports point spacing and the speed each transition
demands. See CHANGELOG §36 for why slew limiting rather than scaling, and PROJECT.md for the
scripting conventions the masters follow.

## Reference videos for other scripters

    .venv/bin/python code/refvideo.py            # render what is missing
    .venv/bin/python code/refvideo.py --force    # re-render all 93
    .venv/bin/python code/refvideo.py --check    # what would be rendered; writes nothing
    .venv/bin/python code/refvideo.py --verify   # decode them back, frame by frame

One video per gallery row that answers to an animation, named for its funscript, written to
`Edi/_reference/videos/` (untracked, regenerable) with a `<row>.json`, an `index.csv` and a
`README.md` beside them. They are **rendered from the shipped assets**, not captured, so their
timing is the game's and a curve authored against one needs no retiming (§88).

Three properties are the whole point, and `--verify` is what keeps them true:

- **One video frame per sprite frame**, at the clip's own sample rate (6-10 fps here). Nothing is
  duplicated or dropped. `--multiple=N` gives N video frames per sprite for a player that dislikes
  a 6 fps file, which is still an integer multiple.
- **A file is as long as the scene's funscript** — the animation loop repeated up to the row's
  length and cut on a frame boundary — so a scripter scripts the whole video rather than working out
  how many loops the row wants (§90). `--one-loop` renders a single loop. The loop length is in the
  sidecar as `loop_ms` and in the table, and it is not `frames / fps`: `GooperGrabScreenCum` holds
  its 14th frame for a final 100 ms.
- **Frames are registered by `m_RD.textureRectOffset` inside the sprite's cell**, not stacked
  bottom-left as the measurement tools do. The alpha trim is not symmetric, so a bottom-left stack
  would add several pixels of horizontal jitter the game does not have.

Other options: `--one-loop`, `--scale=N` (nearest-neighbour, default 2), `--out=DIR`.

The folder's own `README.md` is written **for a scripter who has never seen this project**: what the
files are, what to name what they write, and a table of every scene's length, loop and sideways
travel, so nothing has to be opened as JSON or CSV to start. Keep it that way — the project-side
story belongs here and in `learnings/edi-integration.md` (§90).

Rows without a video are named on every run rather than silently absent: the ten ladder rows
(`ladders.py` builds those against each other, not a scene) and `ambient_wendigo_hole`, whose
scene is really `peek_wendigo_ride`.

## Gallery naming conventions

Applied 2026-08-17 to everything under `Edi/Gallery/handy2pro/`.

**One scene, one file, named after its row.** 71 rows, 71 funscripts (59 at the time of this pass;
§52–§53 added twelve `*_Gallery` variants), every `FileName` equal to
its `Name` lowercased, and every slice `0..len`. There is no slice arithmetic in
`Definitions.csv` any more and no file serves two scenes, so editing one scene cannot disturb
another.

Filenames are **lowercase snake_case** and must avoid Edi's magic tokens: a `.` in the stem sets
the *variant* or an *axis*, and `[loop]` / `[nonLoop]` / `[Gallery]` / `[Filler]` / `[Reaction]` set
flags (`Edi.Core/Gallery/Discover.cs`). The variant comes from the **folder** name (`handy2pro/`).

### Multi-axis

A row's extra axes are files beside it — `nun_grab.twist.funscript` next to `nun_grab.funscript`,
in the same variant folder. Edi joins them to the row by name, so **no `Definitions.csv` row and no
mod change**; the row's slice applies to every axis of it. The token is Edi's `Axis` enum
(`Default`, `Surge`, `Sway`, `Twist`, `Roll`, `Pitch`, `Vibrate`, `Valve`, `Suction`, plus the
e-stim `Frequency`/`Volume`/`PulseWidth`), and an axis nothing writes rests centred at 50 rather
than at 0. `learnings/edi-integration.md` has the TCode mapping and the traps.

The tooling handles them: `speedcheck.py` lists each axis and applies the stroke ceilings only to
`Default` and `Surge`, `variants.py` copies them into `handy1/` unchanged (a mm/s cap means nothing
on a rotational axis), and `release.py`/`deploy.py` glob `*.funscript` so they ship without a
change. `refvideo.py`'s sidecars carry a screen-space motion track for deciding whether a scene has
anything on a lateral axis at all.

Renamed in this pass: `imp1/2/3` -> `imp_1/2/3` (rows too, which makes them a direct hit for the
grapple's `imp_` + tier dispatch instead of an alias hop).

### Splitting the multi-scene strips

Six files used to hold several scenes each: `gallery` (20 rows), `peek` (7), and `ambient`,
`imp`, `plantasha`, `zombie` (2 each). They were split into 35 dedicated files.

The split reproduces Edi's slice semantics exactly, which matters — `inproveLoopAccion`
(`Edi.Core/Gallery/Funscript/FunscriptRepository.cs`) does more than filter by time when
`Loop=true`:

- actions where `StartTime <= at <= EndTime`
- if the first action is more than **100 ms** past `StartTime`, insert a point at `StartTime`
  taking its position from **the action before the window** — content outside the slice
- likewise at `EndTime`, from the action after the window
- otherwise snap the first/last action onto the exact bounds
- finally force `last.pos = first.pos`

So a naive "copy the actions in range" split changes playback wherever a slice edge borrowed a
neighbour. Two of the 35 did: `Baphomet_Start` and `Gooper_Cum`. Every extracted file was
verified by running Edi's pipeline over both the old (strip + slice) and new (dedicated file,
`0..len`) forms — **0 differences**.

Originals are archived in `Edi/_reference/source-scripts/`, outside `GalleryPath`. **Do not
clean that directory out.** `ambient.funscript` and `peek.funscript` were briefly lost and
restored by hand; they appear in no distribution zip and exist only there and in the eroscripts
thread. Dupli9d's `new.funscript` is the same.

Source material that is not a playable gallery — Dupli9d's `new.funscript` — lives there too.
The OpenFunscripter `.ofsp` projects stay beside their scripts; Edi only globs `*.funscript`.

When adding content, keep row names unique — Edi throws on duplicates. There is only one gallery
tree now; `release.py` copies it into the zip, so nothing has to be mirrored by hand.

## Inspecting the game itself

Before building a mechanic, check whether the game already has one. No decompiler needed for
a quick look:

    G="game-windows/Post Nut Calamity_Data/Managed"      # or ../Archive/PNC 0.2.1 Win/... for 0.2.1
    monodis --typedef "$G/Assembly-CSharp.dll" | grep -i gallery
    ikdasm  "$G/Assembly-CSharp.dll" \
      | awk '/\.class .* GalleryUnlockTrigger/,/end of class GalleryUnlockTrigger/'

That is how `GalleryUnlockTrigger` was found (§26) — the game's own answer to "has the player
seen this diorama", which replaced four rounds of raycast debugging.

Scene data needs `UnityPy` (venv; the distro Python is externally managed). `numpy` and `pillow` go
in the same venv — every proxy in `proxies.py` uses both, and installing only `UnityPy` gets you as
far as `load_env()` and no further. `spawntables.py` needs `TypeTreeGeneratorAPI` on top, to
generate the MonoBehaviour typetrees the game does not ship.

**The venv lives in the repo, at `.venv/`.** It used to be scratch under `/tmp`, which did not
survive a reboot and made every asset-reading tool a re-install away from working:

    python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt

`code/requirements.txt` is tracked and pins all four, with a line on each saying what needs it.
The pins are not ceremony: `UnityPy` decodes the sprites and `pillow` decodes their textures, so
both decide what pixels `animsweep`, `gallerydiff` and `refvideo --verify` compare against — an
unpinned upgrade could move a measured number without anyone touching a funscript.

`.venv/` is untracked, and needs no `.gitignore` rule to be: `.gitignore` here is an allowlist
(`/*` then `!` for each opted-in path), so a new top-level directory is invisible to git until
someone opts it in. The tools that need the venv are the ones written `.venv/bin/python` above;
everything else runs on the distro `python3`.

### `dioramaaudit.py` — the ambient patterns, against the build (§119)

    .venv/bin/python code/dioramaaudit.py            # gaps only, exit 1 if any
    .venv/bin/python code/dioramaaudit.py --all      # every pattern and every name it sees

`AmbientProximity` picks the diorama the player is at by matching audio: it lowercases the
AudioSource's `clip.name` and its owning GameObject's name and asks whether either CONTAINS an
alias from `Gameplay/Patterns`, longest alias winning and an exact hit scoring +1000. A pattern
that matches nothing cannot fire; a scene loop matching no pattern still plays but can never arm
its look-to-release, because `AmbientReleaseGaze.NoteCandidate` declines a null pattern.

Both halves are static, which is what makes this a tool rather than a walk past six dioramas —
**but they are not in the same place, and that is the thing worth knowing before extending it.**
An AudioSource's `m_audioClip` is null in almost every shipped scene: the clip is assigned at
runtime by script, so following the sources gets you nothing. The clip *names* have to be read
from the AudioClip assets directly, and matched as a set. The tool checks each alias against both
the clip names (239 in 0.3.1) and the names of objects carrying a looping AudioSource (98),
because `MatchPattern` accepts either.

Its boundary, stated in the file too: it proves an alias *can* match something in the build, not
that the source at a given diorama is the one it matches. Only `AMBIENT-SCAN` in a run answers
that. On 0.3.1 all sixteen patterns resolve — fifteen to a clip, and `dragon squat ride` only to
the object name `Dragon Squat ride`, which makes D10 the one with no second route.

**What a gap costs is smaller than it was.** Since `AnchorInBox` (§119), a diorama the box has
already identified anchors its look-to-release on the nearest playing loop inside that box whether
or not a pattern claimed the audio, so a missing entry is a log line rather than a release that
silently never arms. `Patterns` now identifies only a diorama the game does **not** register with a
`GalleryUnlockTrigger`. A dead alias is still worth catching, which is what this is for.

### `grabflags.py` — who owns an enemy across its own grab (§126)

    .venv/bin/python code/grabflags.py

Prints every enemy AI component in the build that sets `hideInsteadOfDestroyOnGrab` or
`preserveHealthDuringGrab`. On 0.3.1 that is one row, and it sets both:

    Blinded Beast   EnemyAI   hide=True preserveHealth=True

The first flag is what `VanillaGrabHiding` reads to stand the mod's keep-alive down (§73), so
which prefabs carry it is not a detail — it decides which of two implementations owns an enemy's
survival. The pairing is why one check was retired rather than deferred: `EnemyAI.EndGrabHidden`
tests `preserveHealthDuringGrab` first, so its `remainingHealth <= 0` death branch cannot run for
the only prefab that reaches the method, and "the enemy died on its own grab screen" is not a state
this build can produce. Grab-screen damage never reaches the enemy anyway — it comes off
`GrabScreen`'s own `enemyCurrentHealth` float and is discarded on restore.

Both flags are prefab data rather than code, so this reads the assets: it is the same type-tree
generation `spawntables.py` uses, over all seven AI classes. An instrument, not a check — it is
deliberately not in `check.py`, and the reason to run it is a new game build, or any change that
would make the death branch matter.

### `pncpaths.py` — where the repo and the game are (§115)

Not a tool; the one module the tools import for a path. It holds `ROOT`, `GALLERY`,
`DEFINITIONS`, `DETAILED`, `ASSET_FILES`, `game_dir()`, `game_data_dir()` and
`definitions_rows()`.

Before it, nine scripts each carried their own
`ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, eight built the path to
`Definitions.csv` by hand, and `PNC_GAME_DIR` was read in two places that **disagreed about what
it means**: `animcheck` took it as a game *install* and globbed `*_Data` under it, while
`spawntables` took it as the `_Data` folder itself and resolved it against the working directory
rather than the repo. PROJECT.md documents the first. `game_data_dir()` accepts either — one
`Managed/` test tells them apart — so both spellings written down in this repo keep working, and
a relative `PNC_GAME_DIR` now means the same thing from any directory.

`animcheck.ROOT`, `animcheck.FILES` and `animcheck.game_data_dir()` are kept as re-exports,
because `refvideo` and the sweeps already reach the assets through `animcheck` and there was no
reason to make them import two modules.

**The `sys.path` lines are gone with it.** Ten scripts opened with
`sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))`, which is a no-op — Python
already puts the running script's own directory at `sys.path[0]`. The one that was not a no-op
was `animsweep.py`'s `sys.path.insert(0, os.path.join(os.getcwd(), "code"))`, and that is
exactly why it only ran from the repo root. Every tool now runs from anywhere.

`GameObject`, `Transform` and `BoxCollider` read via `read_typetree()`. **MonoBehaviour does
not** — script typetrees are not shipped — so parse `get_raw_data()` by hand: `m_GameObject`
PPtr (int32 fileID + int64 pathID), `m_Enabled` byte, 4-byte align, `m_Script` PPtr, `m_Name`,
then the script's own fields. Strings are length-prefixed and padded to 4 bytes.

Layer names are in the install's `*_Data/globalgamemanagers`: find `TransparentFX`, walk back
to layer 0, then read 32 length-prefixed strings. PNC uses 0 Default, 2 Ignore Raycast, 4 Water,
5 UI, 8 Enemy, 9 Blocker, 10 Interactable, 11 Projectile, 12 Effects, 13 Pickups, 14 Floor,
15 Enemy spawner, 16 Player, 17 EnemyProjectile, 18 Breakables, 19 SweeperEnemy, 20 Pitfalls.

## Adding support for a new game version

The animator-state mapping lives in **`edimod/PncEdi/GalleryTable.cs`** (in the DLL). Everything
else lives in `BepInEx/config/com.edi.pnc.cfg`. Config settings named below are plain config;
`GalleryAliases` / `InGameAliases` are override lists layered on top of the code table.

| new content | edit | rebuild? |
|---|---|---|
| enemy animator state -> scene | `GalleryAliases` | no |
| new enemy prefab | `EnemyRemap` (prefab substring -> family key) | no |
| new peephole | `PeekClipMap` (clip-name substring -> `peek_*`) | no |
| new diorama D-slot | `DioramaAmbientMap` (`D10=…`) | no *(since §33)* |
| new ambient audio | `Patterns` — only a *fallback* since §65; the unlock box identifies it | no |
| the funscript itself | `Edi/Gallery/Definitions.csv` + a file in `handy2pro/` | no |
| **a new grappler** | `GrapplePrefixMap` (family -> cling prefix) | no *(since §66)* |
| a new grappler's *reinforcement pacing* | `GrappleReinforcement.TryResolvePlan` — **rebuild** | **yes** |
| **two grab screens with identical state names** | `GrabVariantSuffixes` (controller substring -> suffix) | no *(since §66)* |
| **a new enemy AI class** | `AiStateGuard` + `EnemyGrabGate` — **rebuild** | **yes, see below** |

The last two are worth knowing exist, because both were added for failures that produce a **wrong
scene rather than a missing one** — nothing logs an `[ALIAS-GAP]`, the device just plays somebody
else's script. A new grappler whose family is not in `GrapplePrefixMap` now dispatches nothing and
says so, which is the behaviour to preserve if you extend it.

The pacing row is a rebuild rather than a config line, and it is the one place a new grappler can
still half-work: since §114 the grapple death sequence begins on **any** clinging family, and it
reaches its trio overflow by calling more of that family in. A family with a cling prefix but no
reinforcement plan will therefore start the sequence and never fill the pile — the bail-outs force
the overflow and then force-end the grapple, so the run still ends in a game over rather than a
stall, but the scene it was supposed to reach is skipped.

### New enemy AI, or changed enemy behaviour — the two hand-built tables

**This is the one part of the mod that a game update can break silently.** Everything else either
keeps working (config tables, `GalleryTable`) or announces itself (`[ALIAS-GAP]`). The AI guards
added in §46 encode facts read out of `Assembly-CSharp.dll` by hand, and none of it is
discoverable at runtime:

| what is hardcoded | where | why it cannot be derived |
|---|---|---|
| which AI classes have states their own `UpdateStateMachine` has no `case` for | `AiStateGuard.GetSpec` | needs reading the `switch` in IL |
| which coroutine field drives each of those states | same | same |
| which classes call `GrabScreen.StartGrab` **without** re-testing `IsGrabbed` | `EnemyGrabGate` | needs reading the call site in IL |

As of 2026-08-17 that is `SpinningEnemyAI` (Grabbing→`grabCoroutine`, Shooting→`shootCoroutine`),
`ChargingEnemyAI` (PreparingCharge and Charging→`chargeCoroutine`), and the two dragon classes
plus `MimicEnemy` for the grab gate. The other three AI classes were checked and are fine.
Re-checked against game 0.3.2 in §136 and unchanged: its new `ChargingEnemyAI.Stunned` is
**deliberately not** in the table, and the entry below says why.

**`AiStateGuard` is keyed by the numeric enum value**, so a state *inserted* into an `AIState`
rather than appended repoints the whole table without renaming anything.
`EnemyAiAudit.AuditStateValues` asserts the names still sit at the expected numbers at startup,
which is what makes that checkable. 0.3.2 appended, so 2 and 3 still mean PreparingCharge and
Charging.

**`EnemyAiAudit` runs at startup and reports drift**, so this is not purely a documentation
promise:

```
grep "\[AI-AUDIT\]" game-windows/BepInEx/LogOutput.log     # or game-linux/...
```

- `ok - guard tables match the game assembly` — nothing to do.
- `BROKEN: SpinningEnemyAI.grabCoroutine no longer exists …` — a field was renamed. **The
  watchdog is now silently doing nothing**; that is the failure this check exists for.
- `GAP: <Type> can start a grab and was not in the §46 audit` — a new class declares a
  `GrabScreen` field. Read its `StartGrab` call site: if it does not do
  `if (!grabScreen.IsGrabbed) return;` straight after, it needs an `EnemyGrabGate` prefix or it
  will commit state to grabs the game refuses during post-grab immunity.
- `GAP: <Type> runs its own state machine and was not in the §46 audit` — a new class has a
  `currentState` enum field. Read its `UpdateStateMachine`: any non-`Dead` state with no `case`
  can only be left by a coroutine, so it needs an `AiStateGuard` entry.

**Read the `switch` before adding an entry; `patchaudit --ai` over-reports here.** Its "unhandled"
line counts a branch as handled only when it calls `Handle*`, so a state whose branch does its own
work is listed as needing a guard when it does not. Game 0.3.2's `ChargingEnemyAI.Stunned` is the
worked example (§136): it has a `case`, it leaves on a plain `Time.time >= stunEndTime`, and
guarding it would cut short three seconds of helplessness the game grants on purpose. The same line
has always over-reported `PreparingCharge` for the same reason — which is why the port procedure
runs the audit against the *old* build first, where the over-reports are already known.

Re-doing the audit is one command, and it covers both tables at once:

```
python3 code/patchaudit.py --ai
```

```
state machines - which states have no `case` in UpdateStateMachine
  ChargingEnemyAI          unhandled: PreparingCharge, Charging, Dead   <-- needs an AiStateGuard entry
  SpinningEnemyAI          unhandled: Grabbing, Shooting, Dead          <-- needs an AiStateGuard entry
  BrawlerEnemyAI           unhandled: Dead

GrabScreen.StartGrab callers - does each re-test IsGrabbed afterwards?
  GAP  MimicEnemy::TriggerMimicGrab
  GAP  DragonEnemyAI::HandleGrabHit
```

### The heat-vs-zero audit

```
python3 code/patchaudit.py --heat
```

A horny lock puts a **floor** under heat, so every vanilla test written against `heat == 0`
changes meaning — twice found the hard way, by an animation that looped forever (§11, §31). This
lists all ten sites in `Assembly-CSharp` at once and prints the verdict for each: patched, covered
by `ClearOverheatAtFloor`, benign, or editor-only. The table is `HEAT_ZERO_REVIEWED` in
`patchaudit.py`; a site that is not in it prints `NEW ... UNREVIEWED` and fails the run, and a
reviewed site the build no longer has prints `gone`. Both are the answer to "assume there are
more" — after §94 there are not, and a game update says so by itself.

Those two lists **are** the two hand-built tables: anything flagged `needs an AiStateGuard entry`
must be in `AiStateGuard.GetSpec`, and every `GAP` that is a real enemy must be in
`EnemyGrabGate`. Run it against 0.2.1 as well - it reproduces §46 exactly, which is what says the
analysis is sound before you believe it about a new build.

The audit also checks the **enum values**, which is the nastiest drift of the lot: `AiStateGuard`
keys on the raw `int` (`Grabbing = 2`), so inserting a state into the middle of an `AIState` enum
repoints the whole table while every name still resolves. It reports
`BROKEN: … AIState value 2 is now 'X', expected 'Grabbing'`.

What the audit **cannot** see is a state that gains or loses a `case` in `UpdateStateMachine`
without anything being renamed — that is IL, not reflection. If enemy behaviour changed in a
release, run the first `awk` above regardless of what the audit says.

### Finding what changed, without launching the game

**Start here: `python3 code/patchaudit.py --compare "../Archive/PNC 0.2.1 Win" --ai`.** One command
answers most of "is anything we wrote down still true": every Harmony patch target and reflected
member checked against the new assembly, a member-level diff of every type the mod names, and the
§46 AI audit. "Reflected member" means all three routes the mod uses - `AccessTools.*`,
`Traverse`, and bare `typeof(T).GetField/GetMethod/GetProperty`. The third was added in §114;
before that, ten reflections across four files were audited by nothing at all. Run it against the *old* build first - it should come back clean and reproduce §46,
and if it does not, the tool is wrong rather than the game (§63 lost three rounds to exactly that).

Then:

1. **Dump the animator states** — every state the game can produce
   (snippet in `NAMING-AUDIT.md`). Diff against the previous dump.
2. **Dump the clip durations** — for retiming (`TIMING-AUDIT.md`).
3. **Run the slug harness** — this is the coverage check:

   ```
   dotnet run --project code/slugharness -- "BepInEx/config/com.edi.pnc.cfg"
   ```

   It prints `source, name, key, state, slug, resolved, via` for every pair. **Any row with
   `UNMAPPED` is a gap.** Add the states of new enemies to the `States` / `GalleryStates` tables
   at the top of its `Program.cs` first, and key them on **the name the game hands the hook** —
   for the gallery route that is the enemy's display name, `Goon Shroom` rather than
   `goonshroom`, which is the distinction that hid a five-row gap for four days (§92). Rebuild
   the harness whenever `NameRemap.cs` changes — it compiles the real file, so it cannot drift
   from the mod's actual behaviour.
4. **Play once and grep** for anything the static pass missed:

   ```
   grep -E "\[ALIAS-GAP\]|\[GRAB-START\]" game-windows/BepInEx/LogOutput.log
   ```

   `[ALIAS-GAP] no mapping for 'x'` names an uncovered slug. There is deliberately no
   fallback guessing a scene from the enemy name any more, so a gap plays nothing and says so.

### Ownership: the table is in the DLL, the config only overrides

`GalleryTable.cs` holds the 326-entry shared table and the 40-entry in-game table. It ships in
the DLL and updates with it. `GalleryAliases` / `InGameAliases` in the config are **empty by
default** and applied *on top*, so:

- shipping a new version reaches everyone, whatever config they already have
- a user's tweak survives that update, because it lives in a separate additive list

This inverts what used to happen. BepInEx writes a setting's default **only when the key is
absent**, so the old arrangement — table as the config default — froze whatever the table looked
like the day a user first ran the mod. The distributed config sat four versions behind the code
for months and ~90% of gameplay ran on a substring-guessing fallback instead. That failure mode
is now structurally impossible.

Entries are one per line in `GalleryTable.cs` so diffs are readable; the parser accepts both
newlines and semicolons, so config overrides keep the old one-line syntax.

**One caveat for existing users:** a config carrying the old 130-entry list will overlay it on
the base table. Those keys are pre-normalisation forms that no longer collide, so they are inert
— except `Imp_Imp2=Imp1` / `Imp_Imp3=Imp1`, which would still override the correct values. Tell
upgraders to clear `GalleryAliases` unless they have deliberate tweaks in it.

## Writing new code in this tree

**Write normal C#.** The tree was ILSpy output and read like it; §116 took the artefacts out,
§123 the last of the placeholder locals, and the old **"match the decompiler idiom" rule is
retired**, at the user's direction — there will be no re-decompile of this mod, so nothing is
served by keeping the tree looking like one. The re-apply list that rule existed for is gone with
it. Name a local after what its expression means; `text`, `num`, `flag` and `array` are not names.

Things that are still real and are not artefacts: `Traverse` and `AccessTools` for private
members (audited by `patchaudit.py`), and `Object`/`Random` aliases where a file also uses
`System`.

- `((RaycastHit)(ref hit)).point` — just write `hit.point`
- `Physics.Raycast(..., ref hit, ...)` — it is `out hit`
- adding `using System;` to a file makes bare `Object` ambiguous; add
  `using Object = UnityEngine.Object;` alongside it (several files already have it)

Harmony notes worth keeping in mind: postfixes still run when a prefix returns `false`, and a
postfix is **skipped** when the original throws — use `[HarmonyFinalizer]` to reset a flag
that must always be cleared.

### What §116 and §123 removed, and how it was proved safe

§116 took out the decompiler's *idiom* by transform; §123 finished the job by hand, naming the
~1300 locals a transform could not (`string`, `int` and `bool` carry nothing to name a variable
from — see the note below the harness). Nothing in the tree reads as decompiler output now.

| | |
|---|---|
| `//IL_0033: Unknown result type...` comments | 371 |
| `(Object)(object)x == (Object)null` -> `x == null` | 619 |
| `((Object)x).name`, `((Component)x).transform`, `((Behaviour)x).enabled`, `((MonoBehaviour)x)` | 322 |
| `BepInEx*LogInterpolatedStringHandler` blocks -> `Log?.LogWarning($"...")` | 12 blocks, ~130 lines |
| blank line between every field declaration | 381 |
| `val` / `component3` / `instance2` locals renamed after their type | 258 |
| `text` / `num` / `array` locals renamed after their initialiser | 51 |

**Three casts were load-bearing and stayed**, and they are the shape to watch for: a cast whose
operand is itself `(object)` is a *generic type parameter* being boxed
(`((Behaviour)(object)val).enabled` where `val` is a `T : MonoBehaviour`), and one in
`EnemyGrabGate` is a real downcast from a local declared `object`. Removing either does not
compile, which is how they were found.

**The proof is an IL diff, not a reading.** Decompile the DLL before the change, decompile it
after, put both through a filter that removes the `//IL_` comments and the `(Object)(object)`
spelling, and diff. The whole pass moved that diff by **58 lines**, every one of them accounted
for: `bool flag = false` printed as `default(bool)`, one parenthesisation of `val?.enemyPrefab`,
and one deliberate `AppendLiteral(message)` -> `AppendFormatted<string>(message)` in
`GalleryHooks.LogGalleryWarning` (identical output; `AppendLiteral` cannot take a variable in
real C#). The opcode histogram says the same thing: 619 `castclass` gone, branch totals
unchanged, no opcode appearing or disappearing — in particular **no `ceq`**, which is what a
`==` that had stopped resolving to `Object.op_Equality` would have produced.

That harness is the reason a change this size was worth making at all. Repeat it for any further
mechanical pass:

    ~/.dotnet/tools/ilspycmd BepInEx/plugins/PncEdi.dll > before.cs     # before touching anything
    # ...edit, rebuild...
    ~/.dotnet/tools/ilspycmd BepInEx/plugins/PncEdi.dll > after.cs
    # strip `//IL_` lines and `(Object)(object)` from both, then diff

**No locals are ILSpy-named any more** (§123). The ~1300 `text` / `num` / `flag` / `array`
locals §116 left behind were named by hand, file by file, because `string`, `int` and `bool`
carry nothing to name a variable from — each one is a judgement about what its expression means.
Two sub-rules were mechanical and are worth reusing: a local read straight out of
`Traverse.Field("x")` takes `x`'s own name, and one read from `Plugin.CfgFoo.Value` takes `foo`.
A rename changes no IL at all, so the diff above stays the check — and note what that means, that
a rename-only pass reads as a *zero* diff, since local names live in the PDB. Parameter names do
not: renaming one shows up in a decompile. §123's 33 diff lines are exactly that, three parameter
renames (`MatchesSpawnHint`, `MatchesHint`, `AppendHeatModLine`) plus one genuine `string a = b;`
copy that was deleted; the six `array2 = array` foreach caches deleted with it are compiler-made
and cost nothing.

**If you script the two sub-rules, scope by real brace depth from the declaration to the end of
its enclosing block.** Counting braces forward and stopping at the first zero looks right and is
not — it stops at the declaration's own line — and it silently rewrote three files past their
method boundaries before the compiler caught it.

The old v1.0.0 source tree (`PncEdi-source-stale-2026-05-30/`) and the untouched shipped binary
(`PncEdi-v2.0.8-original.dll`) were kept beside this file as a reference and a revert target until
§140 deleted them before publication, and §143's squash means they are in no commit of this
repository — the DLL is another author's binary and is not ours to keep redistributing.

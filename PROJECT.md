# PNC + Edi

The Edi device-integration mod for **Post Nut Calamity**: a BepInEx plugin (`PncEdi` v2.6.0, for
game 0.3.2) that watches the game's animations and tells the Edi service which funscript to play,
plus the funscript gallery itself.

It ships as **three plugins**, built by one command and each owning one job:

| plugin | owns | references |
|---|---|---|
| `PncEdi` | the device integration and the gameplay rules — the Edi channel, the gallery registry and aliases, heat and locks, and every patch that shapes vanilla combat | neither of the others |
| `PncCustomEnemies` | the custom-enemy framework (§131): package loading, sprite animation, the custom gallery section, and — since §165 — the public API a package's own behaviour assembly compiles against. It carries no enemy of its own | `PncEdi`, because a package's scenes are Edi content |
| `PncModManager` | the in-game settings window on F11 (§127) — it edits whatever plugins are loaded | nothing, and nothing references it |

The dependency runs one way only, and `code/README.md` has the three checks that keep it that
way. Deleting `PncCustomEnemies.dll` leaves a working mod that behaves as though packages never
existed.

The mod's whole contract with Edi is a row name over HTTP. Everything hard about this project is
on our side of that line: knowing *which* scene is playing, and having a curve for it that matches
what is on screen.

**The mod's own release thread** is
<https://discuss.eroscripts.com/t/game-integration-post-nut-calamity-0-1-0-edi/315695> — where this
mod is posted, where everything it was built on was posted first, and where the custom-enemy
packages go. `CREDITS.md` is what that thread establishes about who made what.

**Edi is open source even though the game is not — read it rather than reverse-engineering it.**

| | |
|---|---|
| source | <https://github.com/NoGRo/Edi> |
| documentation / release thread | <https://discuss.eroscripts.com/t/easy-device-integration-for-games-edi-handy-hps-ble-08-2026/108186> |
| how to integrate a game | <https://discuss.eroscripts.com/t/easy-device-integration-edi-how-to-integrate-your-game-now/118446> |
| **local clone** | keep one beside this repo and **read it rather than re-downloading**; `code/README.md` has the two build flags it needs |

`learnings/edi-integration.md` is where what has been read out of that source is written down —
the slice semantics, `?seek=`, and the multi-axis file naming.

**Building and testing that clone** needs two flags this distro makes necessary. `Edi.Core` targets
`net8.0-windows`, so every command wants `-p:EnableWindowsTargeting=true`, and the test host needs
the `aspnet-runtime-8.0` package (the `dotnet-runtime-8.0` you already have is not enough):

```
dotnet test Edi.Core.Tests/Edi.Core.Tests.csproj -p:EnableWindowsTargeting=true
dotnet publish Edi.Wpf/Edi.Wpf.csproj -c Release -p:EnableWindowsTargeting=true -o <dir>
```

**15 of its 174 tests fail on a clean master** (`DefinitionRepository`, `DevicePlayerConcurrency`,
`PlayerGalleryFlow`). That is the baseline, not something you broke — diff the failure set against
a `git worktree` of master before believing otherwise.

---

## Where to look for what

This file is the map. It covers what the project is, how it is laid out, and how to build, deploy
and release it. Everything else lives in one of six places:

| | what it is | when to open it |
|---|---|---|
| **[README.md](README.md)** | The public front door: what this is, requirements, setup, build, deploy, check, release. Written for someone who has just cloned it and owns none of this context. | When it drifts. It is the one document strangers read, and the only one that has to stand on its own. |
| **[learnings/README.md](learnings/README.md)** | Everything learned the hard way, split by topic with an index. | Before doing anything non-obvious. The index alone tells you which file you need, so you do not have to load them all. |
| **`TODO.md`** — check whether the working tree has one; it is untracked and a clone does not carry it | Private working notes: only what is still **open** — pending work, open questions, known-unfinished things. | Start of a session, if it is there, to pick up work. Nothing resolved lives in it; that moves to the CHANGELOG, which is also where to look when there is no `TODO.md`. |
| **[CHANGELOG.md](CHANGELOG.md)** | The narrative record, numbered `§1` upward. Every change, why it was made, what was tried and rejected. | You need the full story behind a rule, or want to know whether something was already tried. The learnings files cite `§n` back into it. |
| **[code/README.md](code/README.md)** | Build, release and tool reference for the `code/` tree. | Working on the plugin source or the Python tooling. |
| **[CREDITS.md](CREDITS.md)** | Who made the game, Edi, the mod this one continues, the fork the custom-enemy framework came from, and the funscripts the gallery started as. | Before publishing anything, or when you need to know whose work a part of this is. Shipped in the release as `PncEdi-CREDITS.txt`. |

Two audit notes live beside the tools they describe: `code/NAMING-AUDIT.md` (how animator states
resolve to scripts) and `code/TIMING-AUDIT.md` (clip durations).

## Layout

**This repo is the mod, and only the mod.** The game lives outside it and is reached through two
symlinks, which `code/deploy.py` patches (§62). It used to be the other way round — the repo *was*
a 0.2.1 install with the mod inside it — and a lot of the older notes below are written from
inside that game directory.

```
pnc-edi/                                  the repo: nothing here belongs to the game
├── BepInEx/
│   ├── plugins/                          build output, untracked: one `dotnet build` writes all
│   │                                      three DLLs here and into both game installs
│   ├── plugins/PncEdi.dll                the mod (v2.6.0, rebuilt from recovered source)
│   ├── plugins/PncModManager.dll         the in-game settings window - F11 (§127)
│   ├── plugins/PncCustomEnemies.dll      the custom-enemy framework (§131) - delete it and the
│   │                                      mod behaves as if packages never existed
│   ├── custom-enemies/                   enemy packages: _example/, the *.md format docs and
│   │                                      each package's text (manifest, SOURCE.txt, funscripts)
│   │                                      are tracked; the media is not (§135)
│   ├── config/com.edi.pnc.cfg            alias maps, ambient patterns, gameplay tuning
│   └── config/com.edi.pnc.customenemies.cfg
│                                          the custom-enemy plugin's own settings: spawn hotkeys,
│                                          each package's on/off switch and spawn weight (§131)
├── Edi/
│   ├── EdiConfig.json                    devices + variants (per-user; has your hardware IDs)
│   ├── Gallery/
│   │   ├── Definitions.csv               gallery name -> funscript file + time slice
│   │   └── handy2pro/, handy2/, handy1/  the funscripts (variant = folder name). handy2pro is
│   │                                      the master; the other two are generated from it by
│   │                                      code/variants.py (§149)
│   └── _reference/                       capture videos, and videos/ rendered by refvideo.py
│                                          (untracked; not read by Edi)
├── code/
│   ├── edimod/                           buildable plugin source (v2.0.8 + our changes)
│   ├── modmanager/                       the settings window - built by edimod's ProjectReference
│   ├── customenemies/                    the custom-enemy plugin - built by edimod's own target,
│   │                                      and the only one that references PncEdi (§131)
│   ├── packages/                         behaviour assemblies that ship *inside* a package, one
│   │                                      project each (charm-witch/ builds femboy-witch's
│   │                                      CharmWitch.dll). Same build command; they see only
│   │                                      PncCustomEnemies' public API, never PncEdi (§165)
│   ├── tests/                            dotnet test - the naming/alias/config layer (§118)
│   ├── pncpaths.py                       where the repo and the game are - imported, not run
│   ├── deploy.py                         patches the game installs from the working tree
│   ├── webmify.py                        package videos -> VP8 WebM, or they are blank on Linux
│   ├── release.py                        builds dist/PNC<game>-PncEdi-<version>.zip
│   ├── dist/                             release inputs: README template, Linux launcher
│   ├── requirements.txt                  the four third-party Python packages, pinned
│   └── README.md                         build and release instructions
├── .venv/                                the Python venv the asset tools run on — untracked
├── dist/                                 release output — regenerable, untracked
├── game-windows -> ../PNC 0.3.2 WIN      \\ deployed into; not tracked, not read as a source
└── game-linux   -> ../PNC 0.3.2 Linux    /  of anything except the game's own assemblies
```

Beside the repo, outside it:

```
../PNC 0.3.2 WIN/, ../PNC 0.3.2 Linux/    the game installs the symlinks point at
../Archive/PNC 0.2.1 Win/                 the 0.2.1 install this repo used to be
../game-builds/                           the upstream zips both installs came from
```

**`../Archive/PNC 0.2.1 Win` is not junk.** Every verified number in this project was measured
against its assets — the 63/63 timing sweep, `TIMING-AUDIT.md`, the AI tables read out of its
`Assembly-CSharp.dll`. `PNC_GAME_DIR` points any tool at it, and the sweep still reports 63/63
on the scenes that build has — the other 30 rows are 0.3.1-only and print `no clip/script`,
which is the right answer rather than a regression. Nothing re-derives those figures from a
build they were never measured against.

A deployed install carries `BepInEx/` (runtime, our config, all three plugins, and any custom-enemy
packages), both loaders, `start-pnc-linux.sh`
and `Edi/` (the pinned `Edi.exe`, a config, the gallery) — exactly what a player extracts, which is
the point: what is tested and what ships are assembled by the same code.

There is no second copy of anything *maintained by hand*. `mod/` used to hold a hand-mirrored
distributable and the original zips; it was deleted in §58 once `release.py` could assemble a
release from the working tree plus a pinned upstream BepInEx. §59 added the Edi bundle, also pinned
and checksummed — `--update-edi` prints the new constants rather than writing them, so which Edi
ships stays a decision with a run behind it. §62 extended the same idea to the two game installs:
`deploy.py` imports `release.py`'s payload functions rather than growing its own.

---

---

## How a script gets played

1. **Game animation fires.** A Harmony patch in `PncEdi` sees the enemy + animator state.
2. **`NameRemap`** builds a slug, e.g. `nun_alt` + `GhoulGrabStart` → `nun_grab`.
3. **`GalleryAliases`** (in `com.edi.pnc.cfg`) maps that slug to a gallery name.
   Target `-` means *skip*. A `?seek=<ms>` suffix seeks into the script.
4. **`GalleryRegistry.IsKnown`** gates it. **This reads `Definitions.csv` at runtime**
   (`LoadDefinitions`) and adds every row name, so the hardcoded list is only a seed.
5. **`SendPlay`** POSTs `http://127.0.0.1:5000/Edi/Play/<name>` (§84 — not `localhost`).
6. **Edi** looks the name up in `Definitions.csv`, slices the funscript to
   `[StartTime, EndTime]`, rebases to zero and plays it, looping if `Loop=true`.

**A row name is no longer the only thing the mod sends.** Three things now POST
`http://127.0.0.1:5000/Edi/Intensity/<0-100>`, which scales the device's stroke range in place
while the same row keeps looping (§125): the Black Serpent's approach, the chaser bosses' approach
(§151/§153, `ChaserStomp.cs`), and the player's own `MasterIntensity` / `RowIntensityScale` (§150).
The first two are scene-level and the third is a standing preference, so they compose by
multiplication and the serpent outranks the chaser stomp where both are live. It is global to the
channel rather than a property of a row, so the rule is that any row which is not the lowering
scene's own takes the range back with it. **The chaser stomp is not Intensity-only** (§153): while
a dragon or wendigo is audible and in range it dispatches a real row of its own — `Dragon_Stomp` /
`Wendigo_Stomp`, phase-locked to the creature's own footfall — because Intensity can only ever cap
a row's travel down, never raise it above what the row was authored for, and the request behind
this was for the device to read as *more* than the ordinary filler up close. Intensity still runs
underneath it, capping that row's own travel by distance the same way it capped the filler before
this split. `learnings/edi-integration.md` has what was measured about it, and the two rules that
keep two scene-level owners off each other.

Failures at step 3/4 land in `PncEdi-missing-definitions.log`. Since §96 its message names the
registry rather than the file, and prints which `Definitions.csv` was actually read (or that none
was found) — the registry is the seed list plus that file's rows, and a missing file makes every
non-seed row report as unknown at once.

---

## Building, deploying, releasing

**The repo is the mod; the game is a symlink.** Nothing here is a game install, so every step that
needs a game reaches it through `game-windows` / `game-linux`.

```
dotnet build code/edimod/PncEdi.csproj -c Release
```

Builds **all three** plugins and copies them to `BepInEx/plugins/` **and** into both game installs.
A `ProjectReference` pulls in `code/modmanager/PncModManager.csproj`, the in-game settings window,
which deliberately references nothing of PncEdi (§127); a `BuildCustomEnemies` target then builds
`code/customenemies/PncCustomEnemies.csproj`, which *does* reference PncEdi and therefore cannot be
a ProjectReference here without making a cycle (§131). The `PatchGameInstalls` target runs
`deploy.py --dll-only` after every build, so a stale install cannot be why a fix looks broken.
Suppress with `-p:DeployToGames=false`.

The DLL is only part of an install. Everything else goes through:

```
python3 code/deploy.py                 build, then patch both installs in full
python3 code/deploy.py --no-build      use BepInEx/plugins/PncEdi.dll as it stands
python3 code/deploy.py --check         is either install stale?  (exit 1 if so)
python3 code/deploy.py --refs-only     extract BepInEx for the build to compile against
```

**Run `deploy.py` after touching the config or the gallery.** Editing `Edi/Gallery/` or
`com.edi.pnc.cfg` changes nothing a running game can see until it is deployed. `--check` exiting
non-zero is the answer to "is what I am about to launch actually the working tree".

```
python3 code/release.py                -> dist/PNC0.3.2-PncEdi-2.6.0.zip
python3 code/release.py --check        validate everything, write nothing
```

One archive serves Windows and Linux, with Edi bundled and pinned. **Right now that bundle is a
patched Edi, not a stock one** — v1.0.4 plus NoGRo/Edi PR #15, because stock v1.0.4 stalls and
desyncs the device on every pause and resume (§104-§106). It is built from that fix's branch and
kept in `code/dist/cache/`, checksummed like the upstream pin. **PR #15 is merged upstream**
(`8406d51` on `master`, confirmed 2026-08-27), but no release carries it: v1.0.4 is still the
newest tag, so the patched build still ships. Setting `EDI_PATCH_PR = None` in `release.py` reverts
to stock, which is the intent as soon as a released Edi carries the fix — the thing to watch is a
tag after v1.0.4, not the pull request. `deploy.py` imports
`release.py`'s payload functions, so what you test and what ships are assembled by the same code.
Full detail — the secret-leak guards, the config `SHIPPED` check, the BepInEx pinning — is in
`code/README.md`.

---

## Adding content — usually no rebuild

Because of `LoadDefinitions`, a **new gallery name needs no code change**:

1. drop a funscript in `Edi/Gallery/handy2pro/` — the master; **never author in a generated
   variant**, the next regeneration discards it
2. add a row to `Edi/Gallery/Definitions.csv`
3. add animation-state aliases in `com.edi.pnc.cfg`
4. `.venv/bin/python code/variants.py --write` — rebuilds `handy2/` and `handy1/` from the master,
   and every custom-enemy package's `handy2/` from its own. A device pointed at a variant that has
   no copy of a row plays nothing for it (§149)
5. `python3 code/deploy.py --no-build` — none of the above is in a game until it is deployed

**A behaviour is code, and it belongs to a package** (§165). A manifest selects one by name —
`"behaviour": "charm-witch"` plus a tuning block — and a package that ships an assembly publishes
the behaviours other packages then select. The framework itself contains none: `charm-witch` is
built from `code/packages/charm-witch/` into `BepInEx/custom-enemies/femboy-witch/CharmWitch.dll`.
A package that ships code starts **switched off**, and its one switch — `Custom Enemies / <id>` — is
both the on/off and the permission (§167): BepInEx has no sandbox, so consent is what the framework
owes, and a second toggle beside the first only made both packages look enabled while doing nothing.
`BepInEx/custom-enemies/CUSTOM-ENEMIES.md` is the format and that rule, and `code/packageaudit.py`
is what notices a stale or mismatched assembly.

**A whole new enemy needs no code change either**, since §127: drop a package under
`BepInEx/custom-enemies/<name>/` with an `enemy.json`, its art and its funscripts, and
`deploy.py --no-build`. The manifest declares its own gallery rows, aliases and scenes;
`BepInEx/custom-enemies/_example/` and that directory's `CUSTOM-ENEMIES.md` are the format, and
the plugin that reads them is `PncCustomEnemies` — while `WALL-PICTURE-TRAPS.md` now lives in
`joker-wall/`, because since §165 that manifest kind is read by that package's own assembly
(§131 — `code/README.md` has what it owns and what holds its boundary with the core mod).
**A package's text is tracked; its media is not** (§135). The manifest, `SOURCE.txt` and
`funscripts/` are in git — the funscripts are ours, and the manifest is where a package's tuning
lives. The art, video and audio are third-party and stay out, because git history is permanent. So
a fresh clone has a package's text with no media beside it and will not load it until the media is
restored.

`deploy.py` takes whatever the working tree holds. The release takes only the framework and the
templates: a package is **its own download**, built by `python3 code/release.py --package <name>`
(or `all`) and posted beside the release, which keeps the main archive at ~89 MB and leaves a
player to opt into explicit third-party content. `code/README.md` has the three guards that mode
applies — credits required, no MP4 without a WebM, and the H.264 masters dropped because the mod
never opens them when a WebM is there.

Rebuild is only needed for new *behaviour* (new hooks, new enemy handling).
Build: `dotnet build code/edimod/PncEdi.csproj -c Release`, which builds all three plugins and
deploys them to `BepInEx/plugins/` **and** into both game installs by itself.

**Three variant folders, one master.** `Edi/Gallery/handy2pro/` is authored; `handy2/` (600 u/s
sustained, 700 peak) and `handy1/` (364 u/s) are generated from it by `code/variants.py`, which
also emits each package's `handy2/`. Edi picks one by the `"Variant"` on the device in
`EdiConfig.json` — the variant *is* the folder name, so this needs no mod change and no config
setting. The folders were `detailed`/`handy1` until §149; a config still naming `detailed` finds
nothing, and `deploy.py` warns about a variant folder an install carries that the tree does not
build. `learnings/funscript-authoring.md` has the caps and why each one is what it is.

**One class of row is not hand-editable: a ladder.** The seven filler rows are a set the mod
switches between *mid-playback*, so they are built on one shared time grid with one anchor
position and differ only in amplitude — and the mod carries the playback phase across a switch
with `?seek=` (§87). Editing one of them alone breaks the property the set exists to have. They
are generated by `code/ladders.py --write`; see `code/README.md` and
`learnings/edi-integration.md`. The serpent's `Serpent_Hypnosis` comes out of the same tool but is
no longer a ladder: §125 replaced its tiers with one row whose amplitude the mod moves through
Edi's `Intensity` endpoint, so there is nothing left for it to agree with.

---

The order that keeps a session out of trouble: **look at the scene, then measure, then write.**
`learnings/funscript-proxies.md` is the file for the first two steps and
`learnings/funscript-authoring.md` for the third.

---

## Checking your work

**One command runs all of it:**

```
python3 code/check.py            the fast gates (~10 s) - after any change
python3 code/check.py --full     + the asset sweeps (~70 s) - before a release
python3 code/check.py --deploy   deploy first, then check      (--list, -k NAME, -v)
```

`check.py` is a runner, not a new check: it runs the tools below in dependency order, understands
the three different ways they report failure (exit code, a word in the output like `UNMAPPED` or
`OFF`, or a summary a human reads), skips with a printed reason what this machine cannot run, and
gives one exit code. The table stays because a single tool is still the right thing to run while
working on the thing it checks — and because it is what `check.py` is made of (§121).

| command | tier | what it answers |
|---|---|---|
| `dotnet test code/tests/PncEdi.Tests.csproj` | fast | does the naming, alias and config layer still behave? (114 tests) |
| `python3 code/patchaudit.py` | fast | does the mod still bind to the game, and is every patch class registered? (`--ai` also redoes the AI audit) |
| `python3 code/cfgaudit.py` | fast | is every config entry in the section its `Bind()` names? |
| `python3 code/bridgeaudit.py` | fast | is the custom-enemy seam still wired at both ends? Every `CustomEnemyBridge` delegate falls back to vanilla, so a dropped call is otherwise invisible (§132) |
| `dotnet run --project code/slugharness -- BepInEx/config/com.edi.pnc.cfg` | fast | does every animator state resolve to a script? |
| `.venv/bin/python code/animsweep.py` | full | every scene's timing and polarity against its animation |
| `.venv/bin/python code/gallerydiff.py` | full | does the gallery play a different-length clip than gameplay? |
| `python3 code/speedcheck.py` | full | is each script playable on the target device? (`--variant handy2pro\|handy2\|handy1`) |
| `python3 code/handystate.py` | — | what is the device *actually* holding, while a session plays? (never in `check.py`: it is an instrument, not a check) |
| `python3 code/intensitybench.py` | — | does Edi's `Intensity` endpoint move the device's stroke range without restarting playback? (also an instrument; needs Edi up and the device connected) |
| `.venv/bin/python code/grabflags.py` | — | which prefabs set `hideInsteadOfDestroyOnGrab` / `preserveHealthDuringGrab` - who owns an enemy across its own grab (§126). An instrument, not a check |
| `python3 code/ladders.py --check` | fast | are the filler rows still one ladder, and the serpent row still what the generator makes? |
| `.venv/bin/python code/refvideo.py --verify` | full | is every reference video still the frames of its clip, in order? |
| `.venv/bin/python code/dioramaaudit.py` | full | does every ambient `Patterns` entry still match a clip or a looping source in the build? |
| `python3 code/webmify.py --check` | fast | does every custom-enemy video have a WebM? Unity cannot decode H.264 on Linux, so an MP4-only package is a blank overlay there (§127) |
| `python3 code/packageaudit.py` | fast | does every package that declares an assembly ship a current one, at this API version, and does a manifest's named behaviour exist? Every failure here is silent at runtime by design (§165) |
| `python3 code/deploy.py --check` | fast | are the game installs current? |
| `python3 code/release.py --check` | fast | would a release build succeed? |

The tools that read game assets need a venv, because the distro Python is externally managed.
It lives in the repo at **`.venv/`** — untracked, but no longer scratch, so it survives a reboot
and a `/tmp` sweep:

```
python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt
```

`code/requirements.txt` pins the four direct dependencies and says why each is there. Anything
reading game assets takes `PNC_GAME_DIR` — point it at `../Archive/PNC 0.2.1 Win` to reproduce a
pre-0.3.1 figure. Since §115 that is resolved in one place, `code/pncpaths.py`, so it means the
same thing to every tool, a relative path is read against the repo rather than the working
directory, and the tools run from any directory rather than only from the repo root.

---

## Debug keys

Ten enemies on the ten digits, ordered by what the enemy *is* rather than by what slot was free
(§111, re-cut in §119):

    1 Zombie   2 Plantasha   3 Gargoyle   4 Gooper   5 Nun      ordinary
    6 Black Serpent                                             the hypnotist - neither of the above
    7 Imp      8 GoonShroom                                     the clinging family
    9 Blinded Beast   0 Chaser boss (dragon/wendigo)            miniboss, then boss
    M Mimic                                                     furniture, off the row

    .  random from the shuffle pool        Q / Keypad+  escape grab / end grab
    F1 freecam                             Keypad x / - add / remove heat
    F11 the settings window

The mimic is off the digits because it waits for you rather than walking up; the digit row is
exactly the ten walking enemies in encounter order. Gravy's shopkeeper is deliberately unspawnable
by key. The spawn hotkeys for custom-enemy packages (F9, F10) live in
`BepInEx/config/com.edi.pnc.customenemies.cfg`, not in the main config, and
`Tools / EnableDebugEnemySpawn` gates the row itself.

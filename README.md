# PNC + Edi

Device integration for **Post Nut Calamity**, via [Edi](https://github.com/NoGRo/Edi). Three
BepInEx plugins watch the game's animations and tell Edi which funscript to play, plus the
funscript gallery itself.

- **Mod `3.0.0`**, for game **0.3.2**.
- Release thread:
  <https://discuss.eroscripts.com/t/game-integration-post-nut-calamity-0-1-0-edi/315695>
- Whose work this is built on: **[CREDITS.md](CREDITS.md)**. Read it before publishing anything
  derived from this.

> **Adult content — 18+.** *Post Nut Calamity* is an adult game, and this repo is a device-integration
> mod for it: it drives a sex toy in time with the game's animations. The source, the funscripts and
> the documentation all describe sexual content in plain terms. No imagery or game assets are in this
> repo — a package's art and video reach players as separate archives from the release thread — but do
> not clone this at work, and do not open it if you are under 18.

The mod's whole contract with Edi is a row name sent over HTTP. Everything hard is on this side of
that line: knowing *which* scene is playing, and having a curve for it that matches what is on
screen.

## If you just want to play

**You do not want this repo.** Download the release archive from the thread above and follow the
`PncEdi-README.txt` inside it. The archive carries the built plugins, a pinned BepInEx, a pinned
Edi and the gallery — everything but the game.

This repo is the source. It contains **no built DLLs**: they are build output, and building them
needs a copy of the game to compile against (see below), so a clone is a source tree rather than a
runnable install.

## Requirements

| | |
|---|---|
| **A Post Nut Calamity install** | Your own copy. Nothing of the game is in this repo, and none of it may be redistributed. A **Windows** install is required to build against — see the note under Setup. |
| **.NET SDK 8 or newer** | The plugins target `netstandard2.1`; the tests and the slug harness target `net8.0`. |
| **Python 3.11+** | The tooling: `deploy.py`, `release.py`, `check.py` and the asset tools. |
| **Edi** | Not needed to build. Needed to hear anything: the mod POSTs to `http://127.0.0.1:5000`. The release archive bundles a pinned build. |

## Setup

**1. Point the symlinks at your game installs.** The repo is the mod and only the mod; the game
lives outside it and is reached through two symlinks that the tooling patches:

```sh
ln -s "/path/to/your/PNC 0.3.2 Windows install" game-windows
ln -s "/path/to/your/PNC 0.3.2 Linux install"   game-linux
```

`game-linux` is optional — `deploy.py` skips a target that is missing and says so. **`game-windows`
is not.** The build resolves the game's assemblies through `$(GameDir)Post Nut Calamity_Data\Managed\`,
and that folder name only exists in the Windows build; the Linux build names its data folder after
the version. Both symlinks are ignored by git.

**2. Extract the BepInEx assemblies the build compiles against.** They come from the pinned,
checksummed pack that `release.py` ships, not from a game directory, so building never depends on
a deploy having happened:

```sh
python3 code/deploy.py --refs-only
```

Skip it and the build stops with this exact command in the error.

**3. Create the Python venv**, if you intend to run the asset tools. Distro Pythons are externally
managed, so the tools that read game assets need one; the plain `python3` scripts (`deploy.py`,
`release.py`) do not.

```sh
python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt
```

## Build

```sh
dotnet build code/edimod/PncEdi.csproj -c Release
```

One command produces **all three** plugins — `PncEdi`, `PncModManager`, `PncCustomEnemies` — writes
them to `BepInEx/plugins/`, and patches both game installs (`deploy.py --dll-only`), so a stale
install can never be why a fix looks broken. Suppress the install patching with
`-p:DeployToGames=false`.

Build against a different install with `-p:GameDir="/path/to/that/install/"`.

## Deploy

**A DLL is only part of an install, and editing a file changes nothing a running game can see.**
After touching `Edi/Gallery/`, `BepInEx/config/*.cfg` or `BepInEx/custom-enemies/`:

```sh
python3 code/deploy.py                 # build, then patch both installs in full
python3 code/deploy.py --no-build      # use the DLLs in BepInEx/plugins/ as they stand
python3 code/deploy.py --check         # is either install stale?  (exit 1 if so)
```

`--check` is the answer to "is what I am about to launch actually the working tree".

**One warning if you are deploying from a clone.** `deploy.py` deletes as well as writes: a file an
install has and the working tree does not is removed, which is how a deleted funscript or a moved
document stops living on in an install nobody has reinstalled. A custom-enemy package's *media* is
not in this repo (see the last section), so a clone holds that package's text with no art or video
beside it — and a deploy would read that as "these files were deleted". It does not: a package with
no media in the tree at all is skipped whole and named in a warning, because an empty tree has
nothing to say about it (§184). Restore the package's media from its own archive before deploying
over an install that has it.

## Check

```sh
python3 code/check.py                  # the fast gates (~10 s) - after any change
python3 code/check.py --full           # + the asset sweeps (~25 s) - before a release
```

One runner over every check the project has: the unit tests, the audits that keep the three
plugins' boundaries intact, and the sweeps that compare each funscript against the animation it is
supposed to match. `code/check.py --list` prints the steps and how each one reports failure.

## Release

```sh
python3 code/release.py                # -> dist/PNC0.3.2-PncEdi-3.0.0.zip
python3 code/release.py --check        # validate everything, write nothing
```

**A clone cannot run this until it has the Edi build the release pins.** The pin is currently a
build from an upstream pull request rather than a tagged release, and it is not redistributable
from here — `release.py` prints the three commands that produce it, and offers the alternative of
setting `EDI_PATCH_PR = None` to ship stock Edi instead. This is also why `check.py` reports its
`release` step as failing on a fresh clone; its `deploy` step fails there for the reason under
Deploy above. Neither is a regression.

One archive serves Windows and Linux, with BepInEx and Edi both pinned and checksummed. It refuses
to ship a game binary, a signing certificate, an `EdiConfig.json` carrying your device keys, or a
config with an undeclared local tweak in it. Custom-enemy packages are their own downloads
(`--package <name>`), so the main archive stays free of third-party media.

A package may ship its own code, and one that does arrives **switched off**: its single switch in
the mod manager (**F11**) is also the permission to run that code, it says so beside the switch, and
the game needs a restart after it changes. Switched off it runs nothing — no enemy, no traps, no
gallery entry — though its funscripts and its gallery rows still reach Edi, so turning it on later
does not also mean restarting Edi. A package that ships no code has the same switch without any of
that.

## Branch policy

**`main` takes no direct pushes. Every change arrives as a pull request**, including the owner's
(§185) — the ruleset has no admin bypass, so this is enforced rather than agreed. A pull request
needs no approving review, because a solo repo cannot produce one; what it needs is to be a pull
request, so there is a diff to read and a place for CI to report.

```sh
git switch -c short-branch-name
# work, then: python3 code/check.py
git push -u origin short-branch-name        # then open the PR
```

`.github/workflows/checks.yml` runs the checks a public runner can run — seven of the thirteen in
the fast tier; the rest need the game, the installs or the pinned Edi and stay local, so
**`python3 code/check.py` before opening the PR is still the real gate.** `code/README.md` has the
split and why it is drawn there.

## Where to read next

| | |
|---|---|
| **[PROJECT.md](PROJECT.md)** | The map: what this is, how the repo is laid out, how a funscript actually gets played. Read it first. |
| **[learnings/README.md](learnings/README.md)** | Everything learned the hard way, indexed by topic. Read before doing anything non-obvious — and grep it for a symptom before diagnosing one. |
| **[code/README.md](code/README.md)** | Build, release and tool reference for the `code/` tree. |
| **[CHANGELOG.md](CHANGELOG.md)** | The decision record, numbered `§1` upward: what each change was and why, and what was tried and rejected. |
| **[RELEASES.md](RELEASES.md)** | Player-facing release notes — what changed, and what to do differently. Ships in the archive. |
| **[CREDITS.md](CREDITS.md)** | Whose work this is built on. |

## What is not in this repo

Deliberately, and each for its own reason:

- **The game.** Not ours to redistribute. Reached through the symlinks.
- **The built plugin DLLs.** Build output; see above.
- **BepInEx and Edi.** Fetched from pinned upstream builds and verified against their SHA256,
  cached under `code/dist/cache/`.
- **`Edi/EdiConfig.json`.** Its device names embed per-user Handy connection keys, which are
  effectively credentials for controlling that hardware.
- **`TODO.md`.** Private working notes — one person's handoff to their next session, written with
  no reader in mind. The other documents check whether one exists rather than assuming it does; the
  newest `§n` entry in `CHANGELOG.md` is the public answer to "where is this up to".
- **Custom-enemy package media.** A package's *text* — manifest, funscripts, `SOURCE.txt` — is
  tracked, because the funscripts are ours and the manifest is where a package's tuning lives. The
  art, video and audio are third-party, and git history is permanent. A fresh clone therefore has a
  package's text with no media beside it and will not load it until the media is restored from the
  package's own archive. `BepInEx/custom-enemies/CUSTOM-ENEMIES.md` says so.

#!/usr/bin/env python3
"""Patch the game installs behind `game-windows/` and `game-linux/` with the working tree.

    python3 code/deploy.py                 build the plugin, then patch every target
    python3 code/deploy.py --no-build      use BepInEx/plugins/PncEdi.dll as it stands
    python3 code/deploy.py --dll-only      just the plugin (what the csproj build hook calls)
    python3 code/deploy.py --check         say what would change, write nothing
    python3 code/deploy.py --refs-only     only extract BepInEx for the csproj to compile against
    python3 code/deploy.py --target DIR    patch DIR too (repeatable; skips the defaults if given)

This repo holds the mod and nothing else. The game lives outside it, and the two symlinks are how
it is reached:

    game-windows -> ../PNC 0.3.2 WIN
    game-linux   -> ../PNC 0.3.2 Linux

**The payload is `release.py`'s.** `bepinex_payload()`, `gallery_files()` and `fetch_edi()` are
imported rather than reimplemented, so what you test locally is assembled by the same code that
assembles what ships - ../learnings/working-practice.md's "if two copies must agree, do not
maintain both, build one from the other". Five things deliberately differ, all of them because a dev install is not a
player install:

  * **the config** is your live `com.edi.pnc.cfg`, byte for byte, with `MOD_FORCED` applied:
    `[EDI] Debug = true` and `[Ambient] DiagnosticMode = true`, because these two installs exist
    to be played while a log is read. The release goes the other way - the shipped config is built
    from the working tree, where both keep the quiet value, and `Debug` is pinned to `false` in
    SHIPPED on top of that - so the two ends are set independently and neither is the working
    tree's. `release.py` also rewrites the config through SHIPPED (GodMode off,
    HeatLockAutoHealRate back to 1, ...); deploying that would silently replace the testing config
    with the shipped one every build. It is rewritten from the working tree on every deploy, so an
    edit made inside a game directory is not a place work can accumulate - change it here and
    deploy.
  * **`BepInEx/config/BepInEx.cfg`** is not deployed but is *edited in place*, forcing
    `[Logging.Disk] WriteUnityLog = true`, `Enabled = true` and `AppendLog = true` for the same
    reason `MOD_FORCED` is forced: a game-side throw is invisible without the first two (§56,
    §72), and without the third every launch truncates the previous session's log, which has
    already cost one run's evidence. It cannot be shipped or replaced wholesale - BepInEx
    regenerates this file from the running version's own defaults - so the deploy re-forces
    exactly those three keys each time and leaves the rest of the file alone. `release.py` still
    ships no `BepInEx.cfg` at all, so nothing here can reach a player.
  * **`Edi/EdiConfig.json`** is written only when the target has none. It carries your device keys
    and your `Variant` choice, and it is the one file in a game directory that is user state.
  * **`start-pnc-linux.sh` gets a log-rotation block** in a Linux dev install, and only there -
    see `DEV_ROTATE`. The shipped script in `code/dist/` is untouched, so a player still gets one
    plain launcher.
  * **`PncEdi-README.txt` / `PncEdi-CHANGELOG.txt` are not deployed.** They are rendered for a
    named game version and would sit in a 0.3.1 tree claiming to be built for 0.2.1. Nothing reads
    them at runtime.

Every write is skip-unchanged, so a re-run after a one-line code change copies one DLL.
`--check` exits non-zero when anything is out of date, so it doubles as a "is what I am
about to test actually the working tree" assertion.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import release as R                                                   # noqa: E402

ROOT = R.ROOT
DEFAULT_TARGETS = ["game-windows", "game-linux"]

# Where the csproj finds BepInEx to compile against. The runtime used to live in this directory,
# because this directory used to be a game install; now it does not, and a build must not depend
# on a game having been deployed first. Extracted from the same pinned pack release.py ships.
BUILD_REFS = ROOT / "code" / "dist" / "bepinex" / "core"

EXECUTABLE = R.EXECUTABLE_IN_ZIP        # run_bepinex.sh, start-pnc-linux.sh


def note(msg: str) -> None:
    print(f"  {msg}")


# --------------------------------------------------------------------------------------------
# writing


def write_if_changed(path: Path, data: bytes, check: bool, executable: bool = False) -> bool:
    """True if the file needed writing. Compares bytes, so a re-deploy is nearly free."""
    if path.exists() and path.read_bytes() == data:
        if executable:
            ensure_executable(path, check)
        return False
    if not check:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        if executable:
            ensure_executable(path, check)
    return True


def ensure_executable(path: Path, check: bool) -> None:
    mode = path.stat().st_mode
    if mode & 0o111 == 0o111:
        return
    if not check:
        path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def big_file_matches(path: Path, size: int, sha256: str) -> bool:
    """Size first, hash only if it could match - Edi.exe is 220 MB and this runs every deploy."""
    if not path.exists() or path.stat().st_size != size:
        return False
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest() == sha256


# --------------------------------------------------------------------------------------------
# what goes into a target


def live_config() -> bytes:
    path = ROOT / "BepInEx/config/com.edi.pnc.cfg"
    if not path.exists():
        R.fail(f"{path} is missing")
    return force_debug_settings(path.read_bytes())


# The mod's own config, forced in every target: these two installs exist to be played while a log
# is read, so what they log is a property of being a debug install rather than of what happens to
# be committed. Neither key reaches a player - `release.py` builds the shipped config from the
# working tree, where both stay at the quiet value, and `Debug` is pinned to `false` in its
# SHIPPED table on top of that.
#
# `EDI/Debug` gates every diagnostic in the mod, behind `Plugin.DBG`. A `false` committed by
# accident breaks nothing visibly; it just makes the next investigation start from a log with
# nothing in it, which is the expensive kind of quiet.
#
# `Ambient/DiagnosticMode` dumps every playing AudioSource + SpriteRenderer within
# `DiagnosticRange` every 2 s. It is what identifies a diorama whose audio matches no `Patterns`
# entry - the scene plays, but `AmbientReleaseGaze.NoteCandidate` declines a null `AudioSource`,
# so the look-to-release never arms. It costs a periodic block in `LogOutput.log` and nothing
# else; the greps that start a session (`ALIAS-GAP`, `EDI-SKIP`, `failed:`) do not care how much
# is around them.
#
# `Tools/EnableDebugEnemySpawn` and `Tools/EnableFreecam` are forced for a third reason, added in
# §169: they ship **off**, because a fresh player pressing a digit should not get a zombie, and
# every session here reaches a scene by spawning it. Forcing them keeps the two ends independent
# the same way `Debug` is - the working tree carries the player's value and a dev install carries
# the one a session needs.
MOD_FORCED = [("EDI", "Debug", "true"),
              ("Ambient", "DiagnosticMode", "true"),
              ("Tools", "EnableDebugEnemySpawn", "true"),
              ("Tools", "EnableFreecam", "true")]


def force_debug_settings(raw: bytes) -> bytes:
    """The mod config with `MOD_FORCED` applied, whatever the working tree says."""
    for section, key, value in MOD_FORCED:
        raw = force_setting(raw, section, key, value)
    return raw


def force_setting(raw: bytes, section: str, key: str, value: str) -> bytes:
    """Set `key = value` under `[section]` in an INI-style config, preserving everything else.

    BepInEx configs are rewritten by the game on every shutdown - comments, defaults and key
    order are all regenerated - so these files cannot be replaced wholesale from a template
    without losing whatever the current BepInEx version decided the file should contain. Editing
    one key in place is the only edit that survives that round trip.

    Line endings are preserved per line, because the Windows install's BepInEx.cfg is mixed
    CRLF/LF and rewriting it uniformly would show up as a diff on every deploy.
    """
    text = raw.decode("utf-8")
    out, in_section, done = [], False, False
    pattern = re.compile(rf"{re.escape(key)}\s*=")
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_section and not done:                       # section ended without the key
                out.append(f"{key} = {value}")
                out.append("")
                done = True
            in_section = stripped[1:-1] == section
        elif in_section and not done and pattern.match(stripped):
            line = f"{key} = {value}" + ("\r" if line.endswith("\r") else "")
            done = True
        out.append(line)
    if not done:
        if not in_section:
            out += ["", f"[{section}]"]
        out.append(f"{key} = {value}")
    return "\n".join(out).encode("utf-8")


# BepInEx's own config, forced in every target for the same reason `MOD_FORCED` is: these installs
# are read through their log. `WriteUnityLog` folds the Unity player log into `LogOutput.log`,
# which is where a mod-side marker looking right while the game misbehaves gets explained;
# `Enabled` is what writes the file at all. `AppendLog` keeps the file across launches: it
# defaults to `false`, so every start truncates the previous session, and the 2026-08-22 run's
# log was lost that way to a short launch the same evening - the figures §92 read out of it now
# survive only as quotations in that entry. `DEV_ROTATE` now rotates that file per run in a
# Linux dev install, but `AppendLog` stays forced and stays the thing that protects the evidence:
# rotation only covers launches that go through `start-pnc-linux.sh`, and a run started any other
# way - `run_bepinex.sh` by hand, the Windows install under Proton - still lands in the one growing
# file rather than truncating it.
# All three default to the wrong value for a debug install, and BepInEx regenerates this file
# from defaults whenever it does not exist - so a fresh install, or a BepInEx upgrade that
# rewrites the file, silently goes quiet again unless a deploy re-forces it. `release.py` does
# not ship this file, so nothing here reaches a player.
BEPINEX_CFG = "BepInEx/config/BepInEx.cfg"
BEPINEX_FORCED = [("Logging.Disk", "WriteUnityLog", "true"),
                  ("Logging.Disk", "Enabled", "true"),
                  ("Logging.Disk", "AppendLog", "true")]


def bepinex_cfg_bytes(target: Path) -> bytes:
    """The target's BepInEx.cfg with the debug settings forced, or a seed if it has none.

    The seed is deliberately two keys rather than a copy of a full config: BepInEx binds every
    setting it knows on startup and writes the file back complete, with the current version's
    comments and defaults, keeping the values it finds. A two-key file therefore becomes a
    correct full config on first launch, and cannot pin stale defaults from another version.
    """
    dest = target / BEPINEX_CFG
    if dest.exists():
        raw = dest.read_bytes()
    else:
        raw = b"[Logging.Disk]\n"
    for section, key, value in BEPINEX_FORCED:
        raw = force_setting(raw, section, key, value)
    return raw


# The Linux dev install's launcher gets one job the shipped one does not: move the last run's log
# aside before the game starts, so every session has its own file rather than one that grows until
# somebody greps the wrong run's evidence out of it.
#
# It has to happen before the game starts, because BepInEx cannot name its own log file. There is
# no filename or rotation setting in `[Logging.Disk]` - `LogOutput.log` is a constant inside
# `DiskLogListener`, and the `.1`/`.2` names it does fall back to are for concurrent game
# instances, not for successive runs. So the choice is a launcher doing it beforehand or the mod
# writing a second log of its own, and the launcher is the cheap half: no plugin code, no rebuild,
# nothing new to keep in step with BepInEx.
#
# Its limit is why `AppendLog` above is still forced: this fires only for launches that go through
# this script. A hand-run `run_bepinex.sh`, or the Windows install under Proton, appends to
# `LogOutput.log` as before.
#
# The rotated name carries the *old* log's own last-write time rather than the time of the move -
# that is when the run inside it ended, which is what you are matching against when picking one
# session out of the directory.
DEV_ROTATE = """
# --- dev install only; spliced in by code/deploy.py, not part of the shipped script -----------
# One log per run. BepInEx cannot name its own log file, so the previous run's is moved aside
# here, before the game opens a new one. Rotated logs live in BepInEx/logs/, each named for when
# that run last wrote to it. The newest 20 are kept.
if [ -s ./BepInEx/LogOutput.log ]; then
    stamp=$(date -u -r ./BepInEx/LogOutput.log +%Y%m%d-%H%M%SZ 2>/dev/null || date -u +%Y%m%d-%H%M%SZ)
    mkdir -p ./BepInEx/logs
    # Two runs can share a last-write second, and a mv onto an existing name would destroy the
    # older one - this project has lost a run's log once already, and never wants to again.
    base=$stamp
    n=1
    while [ -e "./BepInEx/logs/LogOutput-$stamp.log" ]; do
        stamp="$base-$n"
        n=$((n + 1))
    done
    mv ./BepInEx/LogOutput.log "./BepInEx/logs/LogOutput-$stamp.log"
    # The mod's own log is the same run's evidence, so it travels with it, under the same stamp.
    if [ -s ./BepInEx/PncEdi-missing-definitions.log ]; then
        mv ./BepInEx/PncEdi-missing-definitions.log "./BepInEx/logs/PncEdi-missing-definitions-$stamp.log"
    fi
    ls -1t ./BepInEx/logs/LogOutput-*.log 2>/dev/null | tail -n +21 | while read -r stale; do
        rm -f "$stale"
    done
    echo "start-pnc-linux.sh: last run kept as BepInEx/logs/LogOutput-$stamp.log"
fi
# --- end dev install only ---------------------------------------------------------------------
"""

LINUX_LAUNCHER = "start-pnc-linux.sh"
# The block goes immediately before the hand-over, so it runs only once every check the script
# makes has passed: a launch that is about to refuse to start rotates nothing.
ROTATE_BEFORE = "exec ./run_bepinex.sh"


def dev_launcher(data: bytes) -> bytes:
    """The shipped Linux launcher with `DEV_ROTATE` spliced in before it hands over to BepInEx."""
    text = data.decode("utf-8")
    if DEV_ROTATE in text:
        return data
    if ROTATE_BEFORE not in text:
        R.fail(f"{LINUX_LAUNCHER} no longer contains {ROTATE_BEFORE!r}, "
               "so DEV_ROTATE has nowhere to go")
    return text.replace(ROTATE_BEFORE, DEV_ROTATE + "\n" + ROTATE_BEFORE, 1).encode("utf-8")


def is_linux_install(target: Path) -> bool:
    """Unity ships the Linux player as `<name>.x86_64`; the Windows install has none."""
    return any(target.glob("*.x86_64"))


def plugin_dll(no_build: bool, name: str = "PncEdi") -> Path:
    """One of the shipped plugins - see `R.PLUGINS` for what they are and why."""
    if no_build:
        dll = ROOT / f"BepInEx/plugins/{name}.dll"
        if not dll.exists():
            R.fail(f"{dll} does not exist; drop --no-build or build once")
        return dll
    dll = R.build_plugin(name)
    # The repo's own copy is the one release.py --no-build reads, so keep it in step with what
    # was just deployed rather than letting the two eras diverge. It is untracked build output.
    write_if_changed(ROOT / f"BepInEx/plugins/{name}.dll", dll.read_bytes(), check=False)
    return dll


def plugin_dlls(no_build: bool) -> dict[str, bytes]:
    return {f"BepInEx/plugins/{name}.dll": plugin_dll(no_build, name).read_bytes()
            for name in R.PLUGINS}


def payload(no_build: bool, dll_only: bool) -> dict[str, bytes]:
    """{path relative to the game directory: bytes}."""
    if dll_only:
        return plugin_dlls(no_build)

    files, core_names = R.bepinex_payload()
    note(f"BepInEx {R.BEPINEX_VERSION}: {len(core_names)} core files, both loaders")

    files.update(plugin_dlls(no_build))
    files["BepInEx/config/com.edi.pnc.cfg"] = live_config()
    files["start-pnc-linux.sh"] = (ROOT / "code/dist/start-pnc-linux.sh").read_bytes()

    gallery = R.gallery_files()
    for arcname, src in gallery:
        files[arcname] = src.read_bytes()
    note(f"gallery: {len(gallery) - 1} funscripts across {len(R.GALLERY_VARIANTS)} variants")

    # The mod reads packages out of the *game's* BepInEx/custom-enemies, so a package sitting in
    # the working tree does nothing until it is deployed - the same trap as the gallery and the
    # config, and the same answer.
    packages = R.custom_enemy_files()
    for arcname, src in packages:
        files[arcname] = src.read_bytes()

    # A package's funscripts and gallery rows go in from *this* side, not from the mod at runtime -
    # see R.custom_enemy_gallery for why that distinction is what keeps `--check` honest.
    scripts, rows = R.custom_enemy_gallery(packages)
    for arcname, src in scripts:
        files[arcname] = src.read_bytes()
    if rows:
        files["Edi/Gallery/Definitions.csv"] = R.definitions_with(rows)
    if packages:
        # Count real packages - the ones with a manifest - not every directory under the root,
        # which would count `_example/` and the README as two more.
        installed = {a.split("/")[2] for a, p in packages
                     if p.name in ("enemy.json", "wall-trap.json")}
        note(f"custom enemies: {len(installed)} package(s), {len(scripts)} funscript(s), "
             f"{len(rows)} gallery row(s), {len(packages)} file(s) in all")
    return files


# A patched Edi that only the release archive carries is a patch the dev installs are not
# testing. `Edi-fixed.exe` was the hand-made stand-in for that gap: a second binary beside the
# stock one, launched by hand. It is deleted here rather than left to rot, because a 221 MB
# stale copy of a build nobody launches any more is exactly the thing a later session runs by
# mistake.
STALE_EDI = ["Edi/Edi-fixed.exe"]


def deploy_edi_exe(target: Path, check: bool) -> bool:
    """Whichever Edi the release ships - stock or the patched build - fetched and hashed by
    release.py's own downloader.

    The pin comes from `R.edi_pin()` rather than the upstream constants: with EDI_PATCH_PR set
    those two differ, and comparing against the wrong one silently leaves a stock Edi in place."""
    size, sha256, label = R.edi_pin()
    dest = target / "Edi/Edi.exe"
    if big_file_matches(dest, size, sha256):
        return False
    if check:
        return True
    data = R.fetch_edi()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    note(f"Edi.exe: {label}")
    return True


def remove_stale_edi(target: Path, check: bool) -> int:
    """Drop binaries an earlier workaround left in the target. See STALE_EDI."""
    changed = 0
    for name in STALE_EDI:
        path = target / name
        if not path.exists():
            continue
        changed += 1
        if not check:
            path.unlink()
    return changed


def deploy_edi_config(target: Path, check: bool) -> bool:
    """Your live config, but only into a target that has none - it is user state.

    Falls back to the shipped template if there is no live one, so a fresh target still starts
    configured. `release.py`'s leak checks run over the template either way; they are not repeated
    here because nothing leaves this machine."""
    dest = target / "Edi/EdiConfig.json"
    if dest.exists():
        return False
    live = ROOT / "Edi/EdiConfig.json"
    src = live if live.exists() else ROOT / "code/dist/EdiConfig.json"
    if check:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    return True


# --------------------------------------------------------------------------------------------
# build references


def ensure_build_refs(allow_fetch: bool, check: bool = False) -> int:
    """Extract BepInEx/core to `code/dist/bepinex/core/` for the csproj to reference.

    `allow_fetch` is false on the build-hook path: a post-build step must not start downloading
    because the cache happens to be cold."""
    zips = [R.CACHE / f"BepInEx-Unity.Mono-{n}-{R.BEPINEX_VERSION}.zip" for n in R.BEPINEX_PACKS]
    if not allow_fetch and not any(z.exists() for z in zips):
        return 0
    changed = 0
    with zipfile.ZipFile(R.fetch_pack("win")) as z:
        for i in z.infolist():
            if i.is_dir() or not i.filename.startswith("BepInEx/core/"):
                continue
            changed += write_if_changed(BUILD_REFS / Path(i.filename).name, z.read(i), check)
    return changed


# --------------------------------------------------------------------------------------------
# main


def resolve_targets(explicit: list[str]) -> list[Path]:
    out, missing = [], []
    for name in explicit or DEFAULT_TARGETS:
        p = Path(name)
        if not p.is_absolute():
            p = ROOT / name
        (out if p.is_dir() else missing).append(p)
    for p in missing:
        print(f"deploy: skipping {p} - not a directory "
              f"({'broken symlink' if p.is_symlink() else 'missing'})", file=sys.stderr)
    return out


# A row deleted from the working tree has to be deleted from the installs too. Every write here
# is skip-unchanged, which quietly means "add or replace" and never "remove" - so when §120 cut
# the middle hypnosis rung, both installs kept `serpent_hypnosis_3.funscript` while the working
# tree and `Definitions.csv` no longer had it. Edi plays rows, not files, so nothing could have
# dispatched it; the cost is that "what is in this install" stops being answerable from the repo,
# and the next name reused lands on a file nobody wrote today.
#
# Scoped to the gallery's own script folders and to `.funscript` only. Nothing else in a game
# directory is ours to delete - `EdiConfig.json` is user state and the game's own files outnumber
# ours - and `STALE_EDI` stays the place for a named binary rather than a swept pattern.
# A variant folder that has been RENAMED away is invisible to the loop below, because that loop
# only ever looks inside the variants the tree currently has. §149 renamed `detailed` to
# `handy2pro` and both installs kept a complete `detailed/` afterwards - 102 scripts that still
# resolve, so a device left on the old name plays the old gallery and nothing says a word. That is
# the "silently plausible" failure this project keeps building tools against, so it is reported
# rather than deleted: a variant folder is a lot to remove on a name comparison, and a player may
# have hand-authored one of their own.
def report_unknown_variants(target: Path) -> None:
    gallery = target / "Edi/Gallery"
    if not gallery.is_dir():
        return
    for folder in sorted(p for p in gallery.iterdir() if p.is_dir()):
        if folder.name in R.GALLERY_VARIANTS or not any(folder.glob("*.funscript")):
            continue
        note(f"WARNING {target.name}: Edi/Gallery/{folder.name}/ is not a variant this tree "
             f"builds - a device pointed at it plays scripts nothing here maintains. Delete it, "
             f"and check EdiConfig.json is on one of {', '.join(R.GALLERY_VARIANTS)}")


def prune_gallery(target: Path, files: dict[str, bytes], check: bool) -> int:
    pruned = 0
    report_unknown_variants(target)
    for variant in R.GALLERY_VARIANTS:
        folder = target / "Edi/Gallery" / variant
        if not folder.is_dir():
            continue
        for script in sorted(folder.glob("*.funscript")):
            name = f"Edi/Gallery/{variant}/{script.name}"
            if name in files:
                continue
            pruned += 1
            if not check:
                script.unlink()
                note(f"removed {name} - no longer in the working tree")
    return pruned


def prune_custom_enemy_docs(target: Path, files: dict[str, bytes], check: bool) -> int:
    """Delete the framework's own documentation files an install still has and the tree does not.

    Deliberately **only** this directory's root - the `.md` and `.example` files that are the
    format's documentation - and never a package directory. `deploy.py` takes whatever the tree
    holds, but an install is also allowed to hold a package this tree does not have (someone drops
    one in to try it), and pruning by payload would delete it on the next deploy.

    Without this, §168's two documentation moves left both installs carrying a `README.md` that no
    longer exists and a `WALL-PICTURE-TRAPS.md` at a location it moved out of, while
    `--check` reported both installs up to date - which is the one thing that check exists to say
    truthfully. A file the payload never writes again is a file nothing else will ever correct."""
    pruned = 0
    folder = target / "BepInEx/custom-enemies"
    if not folder.is_dir():
        return 0
    for doc in sorted(folder.iterdir()):
        if not doc.is_file():
            continue
        name = f"BepInEx/custom-enemies/{doc.name}"
        if name in files:
            continue
        pruned += 1
        if not check:
            doc.unlink()
            note(f"removed {name} - no longer in the working tree")
    return pruned


def deploy_one(target: Path, files: dict[str, bytes], full: bool, check: bool) -> int:
    changed = 0
    # A full deploy of a Linux install gets the rotating launcher; every other target, and every
    # --dll-only pass, gets the payload untouched.
    rotate = full and is_linux_install(target)
    for name, data in sorted(files.items()):
        if rotate and name == LINUX_LAUNCHER:
            data = dev_launcher(data)
        if write_if_changed(target / name, data, check, executable=name in EXECUTABLE):
            changed += 1
    if full:
        changed += write_if_changed(target / BEPINEX_CFG, bepinex_cfg_bytes(target), check)
        changed += deploy_edi_exe(target, check)
        changed += remove_stale_edi(target, check)
        changed += deploy_edi_config(target, check)
        changed += prune_gallery(target, files, check)
        changed += prune_custom_enemy_docs(target, files, check)
        # ../learnings/working-practice.md §60: the Linux build ships mode 0666, and BepInEx's
        # run_bepinex.sh needs an
        # executable to hand over to. start-pnc-linux.sh chmods it too; doing it here as well
        # means a target is launchable straight after a deploy, however it is started.
        for exe in target.glob("*.x86_64"):
            ensure_executable(exe, check)
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true",
                    help="use BepInEx/plugins/PncEdi.dll as it stands rather than rebuilding")
    ap.add_argument("--dll-only", action="store_true",
                    help="deploy only the plugin; implies --no-build unless building is asked for")
    ap.add_argument("--check", action="store_true", help="report what would change, write nothing")
    ap.add_argument("--refs-only", action="store_true",
                    help="extract BepInEx for the build to reference, and stop")
    ap.add_argument("--target", action="append", default=[], metavar="DIR",
                    help=f"a game directory to patch (default: {', '.join(DEFAULT_TARGETS)})")
    args = ap.parse_args()

    if args.refs_only:
        n = ensure_build_refs(allow_fetch=True, check=args.check)
        print(f"deploy: BepInEx build references in {BUILD_REFS.relative_to(ROOT)} "
              f"({'would write ' + str(n) if args.check else 'wrote ' + str(n)} file(s))")
        return

    targets = resolve_targets(args.target)
    if not targets:
        # Not an error: the build hook runs this on machines that have no game checked out, and a
        # missing game directory must never be the reason a build fails.
        print("deploy: no targets, nothing to do")
        return

    ensure_build_refs(allow_fetch=not args.dll_only, check=args.check)

    version = R.plugin_version()
    what = "the plugin DLLs" if args.dll_only else "the full overlay"
    print(f"deploy {version}: {what} -> {', '.join(t.name for t in targets)}")

    files = payload(no_build=args.no_build or args.dll_only, dll_only=args.dll_only)

    total = 0
    for t in targets:
        changed = deploy_one(t, files, full=not args.dll_only, check=args.check)
        total += changed
        verb = "would change" if args.check else "wrote"
        note(f"{t.name}: {verb} {changed} file(s)" if changed else f"{t.name}: up to date")
    if args.check and total:
        sys.exit(1)


if __name__ == "__main__":
    main()

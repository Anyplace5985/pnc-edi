#!/usr/bin/env python3
"""Build the distributable zip: the mod, its config and the funscripts, and nothing of the game.

    python3 code/release.py                 build dist/PNC<game>-PncEdi-<mod version>.zip
    python3 code/release.py --no-build      use the already-deployed DLL instead of rebuilding
    python3 code/release.py --check         validate everything, write nothing
    python3 code/release.py --package NAME  build one custom-enemy package archive (or `all`)

One archive serves Windows and Linux. That works because BepInEx's `core/` is managed code and
byte-identical across their two packs - only the loader differs, and both loaders can sit in the
same folder ignoring each other:

    Windows   winhttp.dll + doorstop_config.ini      (Proton included - it is the Windows path)
    Linux     libdoorstop.so + run_bepinex.sh        driven by our start-pnc-linux.sh

Nothing binary is tracked in this repo, so the BepInEx runtime is fetched from the pinned build
below and checked against its SHA256 rather than copied out of the working game directory. That
is what makes this reproducible from a fresh clone. `code/deploy.py` installs the same pinned
payload into the game directories, so what is tested and what ships come from one place.

The config is the part that needs care. `com.edi.pnc.cfg` is generated from the live one, which
is a testing config, and ../learnings/working-practice.md's "the distributable config is
generated from the local one, so local tweaks ship" describes a real accident that has happened. So every setting whose live value
differs from its own documented default has to be listed in SHIPPED below, saying what to ship
and why. An unlisted difference aborts the build. Two were found that way when this was written
and are noted in their entries.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
CACHE = ROOT / "code" / "dist" / "cache"

MOD_NAME = "PncEdi"
GAME_SLUG = "PNC"
GAME_VERSION = "0.3.2"

# `PncEdi-2.1.0.zip` invited exactly one misreading: that the mod version was a version of the
# *game*. The archive leads with the game it is for, so the two numbers can never be mistaken for
# each other - and that matters more now that both exist:
#
#     PNC0.2.1-PncEdi-2.1.0.zip     the last build for game 0.2.1
#     PNC0.3.1-PncEdi-2.2.0.zip     this one
#     ^^^^^^^^ the game             ^^^^^ the mod, plain semver
#
# The game identity can only live here, not in the version number itself: `BepInPlugin` parses its
# version through `SemanticVersioning.Version` and the assembly attributes through
# `System.Version`, so both are numeric by construction. The mod's *display* name carries the rest
# of the disambiguation - the log reads `Loading [Post Nut Calamity EDI Integration 2.2.0]`.
def release_stem(mod_version: str) -> str:
    return f"{GAME_SLUG}{GAME_VERSION}-{MOD_NAME}-{mod_version}"

# BepInEx bleeding-edge build 785, the one this game directory runs. Both packs carry the same
# BepInEx/core; only the loader files differ, which is the whole basis for one cross-platform zip.
BEPINEX_BUILD = "785"
BEPINEX_VERSION = f"6.0.0-be.{BEPINEX_BUILD}"
DOORSTOP_VERSION = "4.5.0"
BEPINEX_PACKS = {
    "win": (
        "https://builds.bepinex.dev/projects/bepinex_be/785/"
        "BepInEx-Unity.Mono-win-x64-6.0.0-be.785%2B6abdba4.zip",
        "db430f14d6661eb38ba96fcc13c07a163e87e553710821d87e5129f915a1b26b",
    ),
    "linux": (
        "https://builds.bepinex.dev/projects/bepinex_be/785/"
        "BepInEx-Unity.Mono-linux-x64-6.0.0-be.785%2B6abdba4.zip",
        "21e3513f9d4bfc517e91cb8d8e65ac03d305a4d687ae4e9163d6c1ea3576c732",
    ),
}
# Taken from each pack, by platform. Everything else in a pack is BepInEx/core, which is shared.
LOADER_FILES = {
    "win": ["winhttp.dll", "doorstop_config.ini", ".doorstop_version"],
    "linux": ["libdoorstop.so", "run_bepinex.sh"],
}
EXECUTABLE_IN_ZIP = {"run_bepinex.sh", "start-pnc-linux.sh"}

DEFAULT = object()   # ship the value the plugin itself defaults to
LIVE = object()      # ship what the live config says

# Every setting whose live value differs from its documented default must appear here.
SHIPPED: dict[tuple[str, str], object] = {
    ("EDI", "Debug"): "false",
    #   Verbose per-frame logging. It is the coded default and the working tree keeps it on -
    #   `deploy.py` even forces it on into the two game installs, which exist to be read - but a
    #   player gets a quiet log. This is the one entry here that does not follow from a deviation:
    #   live and default agree, and the release still differs from both on purpose.
    ("EDI", "ChaserStompRange"): LIVE,
    #   Coded default is 25. §151 shipped the mechanism (then ChaserAura, an Intensity squeeze on
    #   the filler) blind because the honest far edge (the chaser's own AudioSource.maxDistance)
    #   was unmeasured; the 2026-08-29 run measured it at 30 m and found the dragon's whole
    #   approach living between 3.5-13.6 m, an 84-100% band nobody could feel. 12 puts that same
    #   approach across 50-100%. ChaserAura was later folded into ChaserStomp - same band, same
    #   reasoning, now capping the stomp row's own travel instead of the filler's. A second
    #   2026-08-30 play session found the ramp barely readable below its own Far value either -
    #   IntensityNearDistance (new, defaults to 5 m) moves 100% out from "basically touching" to a
    #   few metres out, and Far dropped from 55 to 50 - both are the coded defaults now, so neither
    #   needs its own SHIPPED entry. Ship the measured range.
    ("EDI", "ChaserStompIntensityFar"): "30",
    #   Coded default is 50. The 2026-08-30 session that measured Range=12 also found repeated
    #   short gate losses during real grab attempts (see ChaserStompGrace below) and, separately,
    #   moved Range to 0 (the honest maxDistance, 30 m for these two prefabs) once the 12 m tuning
    #   turned out to sit inside the AI's own ambiguous not-quite-chasing zone. A wider band at the
    #   same Far value would start the stomp row noticeably earlier, while the sound is still
    #   faint - Far dropped to 30 to keep the *near* end of the experience (close, loud, about to
    #   grab) roughly where it was, rather than diluting it across three times the distance.
    #   Unplayed as of this session; revisit if 30 reads as too early once tested against the wider
    #   band it now pairs with.
    ("Gameplay", "GodMode"): "false",
    #   Coded default is true, but EnableHeatLocks replaces god mode with the horny locks and is
    #   itself on by default. Shipping true would hand players both and neuter the mechanic.
    ("Gameplay", "ShowHeatBarDuringGrab"): "false",
    #   Local debugging aid: the only on-screen read of what heat does mid-grab.
    ("Gameplay", "HeatLockAutoHealRate"): "120",
    #   NOT 120 HP/s. `ApplyHeatScaledAutoHeal` multiplies this by a hard-coded 0.01, so the
    #   setting is hundredths of HP/s: 120 is 1.2 HP/s at zero heat, decaying quadratically to
    #   nothing at max heat - about 83 s to refill the 100 HP bar while idle, and near zero in a
    #   hot fight. §32 read the setting's own description ("Auto-heal HP per second at 0 heat",
    #   wrong by 100x) rather than the formula, called 120 "near-invincibility" and reverted to
    #   the coded default of 1. That ships 0.01 HP/s - one HP per 100 seconds, or 2.8 hours for a
    #   full bar - so every release since has shipped the mechanic switched off. 120 is restored
    #   here as a declared value because it is the only rate with play behind it: it is what this
    #   install has run since the mod was inherited. The description is corrected in Plugin.cs so
    #   the next reader is not misled the same way.
    ("Gallery", "PeekGalleryMap"): DEFAULT,
    #   The live copy is a stale *subset*: it predates three imp three-way spellings the coded
    #   default has gained since. This setting replaces the default rather than layering on it,
    #   so shipping the live copy would quietly drop them.
    ("Naming", "EnemyRemap"): LIVE,
    #   Differs from the default in one entry, Hood_Enemy NoTape=nun_alt against =nun. Both
    #   resolve to the same scripts (GalleryTable carries nun_* and nun_alt_* alike), so this is
    #   cosmetic - it is what every verified log shows, so ship it.
    ("Naming", "GalleryAliases"): LIVE,
    ("Naming", "InGameAliases"): LIVE,
    #   The gallery split (CHANGELOG §52-§53). Twelve scenes whose gallery clip is a different
    #   length from the one they are scripted against; these two lists are the entire mechanism
    #   and there is no code path that reproduces them. Losing them silently un-fixes the bug.
}

GALLERY_VARIANTS = ["handy2pro", "handy2", "handy1"]

# Edi itself, bundled the way the eroscripts mods do, so the archive is one download and works
# out of the box. Pinned rather than "whatever is newest": a release has to be reproducible, and
# an Edi nobody here has run is not something to ship silently. `--update-edi` re-pins from the
# GitHub API and prints the new constants to paste in, which is the automatic part.
#
# Edi.exe is a self-contained WPF build, so it is Windows-only and ~220 MB, which compresses to
# ~89 MB in the archive.
EDI_REPO = "NoGRo/Edi"
EDI_TAG = "v1.0.4"
EDI_URL = f"https://github.com/{EDI_REPO}/releases/download/{EDI_TAG}/Edi.exe"
EDI_SHA256 = "2c38262ba9ade05e2b83cc76121ed9fa9fb18c3ea0b4fc1dec70ffa2ec43b1bc"
EDI_SIZE = 220_682_941

# **Temporary: the archive ships a patched Edi, not the pinned upstream one.**
#
# v1.0.4 desyncs and stalls the device whenever a looping gallery is played with a seek, which is
# every pause and resume - NoGRo/Edi issue #14, fixed by PR #15, diagnosed here in §104-§106. The
# fix is four lines of buffer construction and there is no released build carrying it, so until
# one exists a release either ships the bug or ships this.
#
# PR #15 was merged upstream on 2026-08-27 (8406d51 on master) and that changed nothing here: the
# newest tag is still v1.0.4, so there is still no downloadable Edi with the fix. Nor is master the
# thing to build - it carries unrelated commits past the merge that this project has never run,
# while the cached build below is v1.0.4 plus exactly the four lines.
#
# The build is not downloadable: it comes from that fix's branch, built locally, and lives in the
# same cache as the upstream pin under a name that says what it is. It is checksummed exactly like
# the upstream pin, so a release stays reproducible.
#
# **To go back to stock**, which is the goal: set EDI_PATCH_PR = None. `--update-edi` re-pins
# upstream as usual, and once a *release* carries the fix that is the whole revert. Watch for a tag
# after v1.0.4, not for the pull request.
EDI_PATCH_PR = 15
EDI_PATCH_SHA256 = "497ef72c7e12d453d8efa9c723cd28bbcf49cc0120d3ed999cba1440cde40b9e"
EDI_PATCH_SIZE = 220_698_681
EDI_PATCH_SOURCE = "https://github.com/NoGRo/Edi/pull/15"


def fail(msg: str) -> None:
    print(f"release: {msg}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------------------------
# version


def plugin_version() -> str:
    """The version, cross-checked across all four places that declare it.

    They are hand-maintained in two files, so they can drift; a release named after one of them
    while the plugin reports another is worse than no version at all."""
    info = (ROOT / "code/edimod/Properties/AssemblyInfo.cs").read_text(encoding="utf-8")
    plugin = (ROOT / "code/edimod/PncEdi/Plugin.cs").read_text(encoding="utf-8")
    found = {
        "AssemblyVersion": re.search(r'AssemblyVersion\("([\d.]+)"\)', info),
        "AssemblyFileVersion": re.search(r'AssemblyFileVersion\("([\d.]+)"\)', info),
        "AssemblyInformationalVersion": re.search(r'AssemblyInformationalVersion\("([\d.]+)"\)', info),
        "BepInPlugin": re.search(r'\[BepInPlugin\("[^"]+",\s*"[^"]+",\s*"([\d.]+)"\)\]', plugin),
    }
    missing = [k for k, v in found.items() if v is None]
    if missing:
        fail(f"could not read the version from {', '.join(missing)}")
    got = {k: v.group(1) for k, v in found.items()}

    def normalise(v: str) -> str:
        # The assembly attributes carry four components, BepInPlugin three. Compare on three,
        # and only when the fourth is 0 - "2.1.0.4" is a different thing and should not pass.
        parts = v.split(".")
        return ".".join(parts[:3]) if len(parts) == 4 and parts[3] == "0" else v

    normal = {k: normalise(v) for k, v in got.items()}
    if len(set(normal.values())) != 1:
        fail("version strings disagree: " + ", ".join(f"{k}={v}" for k, v in got.items()))
    version = next(iter(normal.values()))
    # Plain MAJOR.MINOR.PATCH. Not decoration: BepInPlugin runs the string through
    # SemanticVersioning.Version and the assembly attributes through System.Version, so anything
    # else either fails to parse or silently lands somewhere nobody reads. The game this build is
    # for is expressed in the archive name instead - see release_stem.
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        fail(f"mod version {version!r} is not MAJOR.MINOR.PATCH; BepInEx parses it as semver")
    return version


def git_commit() -> str:
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "describe", "--always", "--dirty"],
                             capture_output=True, text=True, check=True)
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def git_commit_epoch() -> int:
    """HEAD's commit time, used as every entry's timestamp so the zip is byte-reproducible."""
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%ct"],
                             capture_output=True, text=True, check=True)
        return int(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
        return 1_600_000_000


# --------------------------------------------------------------------------------------------
# config


def parse_config(text: str) -> list[dict]:
    """Sections, keys, live values and the `# Default value:` each setting documents.

    BepInEx writes that comment itself from the Bind() call, so it is the plugin's own default
    rather than anything maintained by hand here - which is what makes the SHIPPED check
    self-maintaining."""
    out, section, default = [], None, None
    for i, line in enumerate(text.split("\n")):
        stripped = line.strip()
        m = re.match(r"\[(.+)\]$", stripped)
        if m:
            section, default = m.group(1), None
            continue
        m = re.match(r"#\s*Default value:\s?(.*)$", stripped)
        if m:
            default = m.group(1).strip()
            continue
        m = re.match(r"([A-Za-z_]\w*)\s*=\s?(.*)$", line)
        if m:
            out.append({"line": i, "section": section, "key": m.group(1),
                        "value": m.group(2).strip(), "default": default})
            default = None
    return out


def build_shipped_config(live_path: Path) -> tuple[str, list[str]]:
    text = live_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    settings = parse_config(text)
    if not settings:
        fail(f"parsed no settings out of {live_path}")

    lines = text.split("\n")
    notes, unlisted = [], []
    for s in settings:
        ident = (s["section"], s["key"])
        deviates = s["default"] is not None and s["value"] != s["default"]
        if ident not in SHIPPED:
            if deviates:
                unlisted.append(f"[{s['section']}] {s['key']} = {s['value'][:60]}"
                                f"  (default {s['default'][:60]!r})")
            continue
        want = SHIPPED[ident]
        if want is LIVE:
            target = s["value"]
        elif want is DEFAULT:
            if s["default"] is None:
                fail(f"[{s['section']}] {s['key']} is marked DEFAULT but documents none")
            target = s["default"]
        else:
            target = str(want)
        if target != s["value"]:
            lines[s["line"]] = f"{s['key']} = {target}"
            notes.append(f"{s['key']}: {s['value'][:40]} -> {target[:40]}")

    if unlisted:
        fail("these settings differ from their default and are not declared in SHIPPED - decide "
             "whether each belongs in the release, then add it:\n  " + "\n  ".join(unlisted))

    return "\n".join(lines).replace("\n", "\r\n"), notes


# --------------------------------------------------------------------------------------------
# BepInEx


def fetch_pack(name: str) -> Path:
    url, want = BEPINEX_PACKS[name]
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"BepInEx-Unity.Mono-{name}-{BEPINEX_VERSION}.zip"
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == want:
        return path
    print(f"  fetching BepInEx {name} pack ({BEPINEX_VERSION})")
    try:
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
    except Exception as e:                                            # noqa: BLE001
        fail(f"could not download {url}\n  {e}\n"
             f"  Offline? Put the file at {path} by hand and re-run.")
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        fail(f"{name} pack checksum mismatch\n  expected {want}\n  got      {got}")
    path.write_bytes(data)
    return path


def bepinex_payload() -> tuple[dict[str, bytes], list[str]]:
    """{archive path: bytes} for BepInEx/core plus both platforms' loader files."""
    files: dict[str, bytes] = {}
    cores: dict[str, dict[str, bytes]] = {}
    for name in BEPINEX_PACKS:
        with zipfile.ZipFile(fetch_pack(name)) as z:
            core = {i.filename: z.read(i) for i in z.infolist()
                    if i.filename.startswith("BepInEx/core/") and not i.is_dir()}
            cores[name] = core
            for want in LOADER_FILES[name]:
                if want not in z.namelist():
                    fail(f"{want} missing from the {name} pack")
                files[want] = z.read(want)
    if cores["win"] != cores["linux"]:
        differing = sorted(set(cores["win"]) ^ set(cores["linux"])) or [
            k for k in cores["win"] if cores["win"][k] != cores["linux"].get(k)]
        fail("the win and linux packs no longer share an identical BepInEx/core, so one archive "
             "can no longer serve both. Differing: " + ", ".join(differing[:5]))
    files.update(cores["win"])
    return files, sorted(cores["win"])


def patched_edi_path() -> Path:
    return CACHE / f"Edi-{EDI_TAG}-pr{EDI_PATCH_PR}.exe"


def fetch_patched_edi() -> bytes:
    """The locally-built Edi carrying PR #15, checksummed like the upstream pin.

    There is nothing to download - the whole point is that no released build has the fix yet - so
    a missing file is a hard failure with the command that rebuilds it rather than a silent
    fallback to a stock Edi that still has the bug."""
    path = patched_edi_path()
    if not path.exists():
        fail(f"patched Edi missing at {path}\n"
             f"  Build it from the PR branch ({EDI_PATCH_SOURCE}):\n"
             f"    cd <Edi clone> && git checkout fix/close-the-rotated-loop-cycle\n"
             f"    dotnet publish Edi.Wpf/Edi.Wpf.csproj -c Release "
             f"-p:EnableWindowsTargeting=true -o <out>\n"
             f"    cp <out>/Edi.exe {path}\n"
             f"  Or set EDI_PATCH_PR = None in release.py to ship stock Edi {EDI_TAG}, "
             f"bug and all.")
    data = path.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != EDI_PATCH_SHA256:
        fail(f"patched Edi checksum mismatch\n  expected {EDI_PATCH_SHA256}\n  got      {got}\n"
             f"  A rebuild is not bit-identical; re-pin EDI_PATCH_SHA256/SIZE if this is "
             f"deliberate.")
    print(f"  Edi {EDI_TAG} + PR #{EDI_PATCH_PR} (patched, {len(data) / 1e6:.0f} MB)")
    return data


def edi_pin() -> tuple[int, str, str]:
    """Size, SHA256 and a human label for whichever Edi actually ships.

    `fetch_edi` already returns the patched build when EDI_PATCH_PR is set, so anything that
    wants to know whether a file on disk *is* that build has to pin against the patched
    constants rather than the upstream ones. `deploy.py` compared against the upstream pair,
    decided a stock Edi.exe was current, and left the two dev installs running the stutter -
    which is why they carried a hand-placed Edi-fixed.exe beside it for a while."""
    if EDI_PATCH_PR:
        return EDI_PATCH_SIZE, EDI_PATCH_SHA256, f"{EDI_TAG} + PR #{EDI_PATCH_PR} (patched)"
    return EDI_SIZE, EDI_SHA256, EDI_TAG


def fetch_edi() -> bytes:
    if EDI_PATCH_PR:
        return fetch_patched_edi()
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"Edi-{EDI_TAG}.exe"
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == EDI_SHA256:
        return path.read_bytes()
    print(f"  fetching Edi {EDI_TAG} ({EDI_SIZE / 1e6:.0f} MB)")
    try:
        with urllib.request.urlopen(EDI_URL, timeout=600) as r:
            data = r.read()
    except Exception as e:                                            # noqa: BLE001
        fail(f"could not download {EDI_URL}\n  {e}\n"
             f"  Offline? Put the file at {path} by hand.")
    got = hashlib.sha256(data).hexdigest()
    if got != EDI_SHA256:
        fail(f"Edi checksum mismatch\n  expected {EDI_SHA256}\n  got      {got}")
    path.write_bytes(data)
    return data


def update_edi() -> None:
    """Print the constants for the newest Edi release, having downloaded and hashed it.

    Deliberately prints rather than edits: bumping the bundled Edi is a decision - the new one
    wants at least one run against the game before it goes out under our name."""
    api = f"https://api.github.com/repos/{EDI_REPO}/releases/latest"
    try:
        with urllib.request.urlopen(api, timeout=60) as r:
            rel = __import__("json").loads(r.read())
    except Exception as e:                                            # noqa: BLE001
        fail(f"could not reach {api}: {e}")
    assets = [a for a in rel.get("assets", []) if a["name"].lower().endswith(".exe")]
    if not assets:
        fail(f"{rel.get('tag_name')} has no .exe asset")
    a = assets[0]
    print(f"latest is {rel['tag_name']} ({rel.get('published_at')}), {a['name']} "
          f"{a['size'] / 1e6:.0f} MB")
    if rel["tag_name"] == EDI_TAG:
        print("  already pinned, nothing to do")
        return
    print("  downloading to hash it")
    with urllib.request.urlopen(a["browser_download_url"], timeout=600) as r:
        data = r.read()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"Edi-{rel['tag_name']}.exe").write_bytes(data)
    print("\nPaste into release.py, then build and run it once before shipping:\n")
    print(f'EDI_TAG = "{rel["tag_name"]}"')
    print(f'EDI_SHA256 = "{hashlib.sha256(data).hexdigest()}"')
    print(f"EDI_SIZE = {len(data):_}")


def edi_config() -> bytes:
    """The shipped `Edi/EdiConfig.json`, checked against the live one for leaked secrets.

    Edi names a connected Handy `The Handy [<connection key>]`, and that key controls the
    hardware - so the *device names* are the secret, not just some field. The shipped file is
    hand-authored in `code/dist/` rather than scrubbed from the live one, because a redaction that
    misses something fails silently and permanently. This function is the second lock: it reads
    the live config, pulls the actual secrets out of it, and refuses to ship a file containing
    any of them."""
    path = ROOT / "code/dist/EdiConfig.json"
    if not path.exists():
        fail(f"{path} is missing")
    raw = path.read_bytes()
    text = raw.decode("utf-8")

    try:
        shipped = __import__("json").loads(text)
    except ValueError as e:
        fail(f"{path} is not valid JSON: {e}")

    extra = sorted(set((shipped.get("Devices") or {}).get("Devices", {})) - {"Preview Device"})
    if extra:
        fail(f"{path} lists real devices: {extra}. Only 'Preview Device' may ship.")
    if (shipped.get("Handy") or {}).get("Key"):
        fail(f"{path} carries a Handy key")

    # A Handy connection key travels inside the device name, so this shape is the thing to refuse
    # even when it does not match anything in the live config (a teammate's key, a stale copy).
    for m in re.finditer(r"\[[A-Za-z0-9]{6,}\]", text):
        fail(f"{path} contains something shaped like a device key: {m.group(0)}")

    live_path = ROOT / "Edi/EdiConfig.json"
    if live_path.exists():
        live = __import__("json").loads(live_path.read_text(encoding="utf-8"))
        secrets = set((live.get("Devices") or {}).get("Devices", {})) - {"Preview Device"}
        for name in list(secrets):
            secrets.update(re.findall(r"\[([^\]]+)\]", name))
        key = (live.get("Handy") or {}).get("Key")
        if key:
            secrets.add(key)
        leaked = sorted(s for s in secrets if s and s in text)
        if leaked:
            fail(f"{path} contains {len(leaked)} value(s) from your live EdiConfig.json. "
                 "Not printing them; regenerate the template without your devices in it.")
    return raw


def check_local_install_is_stock(core: dict[str, bytes]) -> list[str]:
    """The game installs you test in should be running exactly the BepInEx we ship.

    Not fatal - you can build a release from a machine whose installs have drifted - but if they
    have, every in-game result this release is based on was produced against something else.

    This used to read ROOT, back when this directory *was* a game install. It is now the mod only,
    and the installs are `code/deploy.py`'s targets."""
    problems = []
    targets = [ROOT / t for t in ("game-windows", "game-linux")]
    live = [t for t in targets if t.is_dir()]
    if not live:
        return [f"no game install to check ({', '.join(t.name for t in targets)} not present)"]
    for target in live:
        for name, data in core.items():
            local = target / name
            if not local.exists():
                problems.append(f"{target.name}: {name} missing")
            elif local.read_bytes() != data:
                problems.append(f"{target.name}: {name} differs from the pinned pack")
    return problems


# --------------------------------------------------------------------------------------------
# assembling


# The mod ships as three BepInEx plugins, and all three are built and shipped the same way, so
# this takes the project rather than hardcoding one.
#
#   PncEdi           the mod: the device integration and the gameplay rules.
#   PncModManager    the in-game settings window. It edits whatever plugins happen to be loaded,
#                    so neither assembly references the other (code/edimod/PncEdi/ModManagerBridge.cs).
#   PncCustomEnemies the custom-enemy framework (§131). This one *does* depend on PncEdi - a
#                    package's scenes are Edi content - but only one way: PncEdi asks about
#                    packages through CustomEnemyBridge, which answers vanilla when this DLL is
#                    not there, so a player can delete it and keep a working mod.
#
# Building PncEdi builds the other two by itself; naming them here is for --no-build and for the
# per-plugin scratch builds a release does.
PLUGINS = {
    "PncEdi": "code/edimod/PncEdi.csproj",
    "PncModManager": "code/modmanager/PncModManager.csproj",
    "PncCustomEnemies": "code/customenemies/PncCustomEnemies.csproj",
}


def build_plugin(name: str = "PncEdi") -> Path:
    scratch = ROOT / "code" / "dist" / "build" / name
    if scratch.exists():
        shutil.rmtree(scratch)
    print(f"  building {name}.dll")
    # PncCustomEnemies compiles against PncEdi, and each plugin here is built into its own scratch
    # directory - so it has to be told where the PncEdi of *this* release is, or it would link
    # against whatever the repo's working copy happens to hold. PLUGINS is ordered, PncEdi first,
    # so that DLL exists by the time this runs.
    extra = ([f"-p:PncEdiRefPath={ROOT / 'code' / 'dist' / 'build' / 'PncEdi' / 'PncEdi.dll'}"]
             if name == "PncCustomEnemies" else [])
    r = subprocess.run(
        ["dotnet", "build", str(ROOT / PLUGINS[name]), "-c", "Release",
         f"-p:PluginDeployDir={scratch}{os.sep}", f"-p:OutputPath={scratch / 'bin'}{os.sep}",
         # This build is for the archive, not for playing. `code/deploy.py` is what patches the
         # installs, and a release must not quietly swap the binary you have been testing.
         "-p:DeployToGames=false", *extra],
        capture_output=True, text=True)
    if r.returncode != 0:
        fail("dotnet build failed:\n" + r.stdout[-3000:] + r.stderr[-2000:])
    dll = scratch / f"{name}.dll"
    if not dll.exists():
        fail(f"build reported success but {dll} is not there")
    return dll


def gallery_files() -> list[tuple[str, Path]]:
    """Definitions.csv and the funscripts, per variant. Authoring leftovers stay behind."""
    out = []
    src = ROOT / "Edi/Gallery"
    definitions = src / "Definitions.csv"
    if not definitions.exists():
        fail("Edi/Gallery/Definitions.csv is missing")
    out.append(("Edi/Gallery/Definitions.csv", definitions))
    for variant in GALLERY_VARIANTS:
        d = src / variant
        if not d.is_dir():
            fail(f"Edi/Gallery/{variant} is missing")
        scripts = sorted(d.glob("*.funscript"))
        if not scripts:
            fail(f"Edi/Gallery/{variant} holds no funscripts")
        for f in scripts:
            out.append((f"Edi/Gallery/{variant}/{f.name}", f))
    return out


def custom_enemy_files(packages: bool = True) -> list[tuple[str, Path]]:
    """Custom-enemy package files in the working tree.

    A package is data - a manifest, PNG sheets, funscripts, video - so this copies whatever is
    there rather than knowing anything about what is in one, the same rule the gallery follows.

    `packages=False` restricts it to the `_example/` templates and this directory's own Markdown -
    the README and the two format references - and that is what
    the **release** uses. A real package is third-party artwork: the two that exist carry a
    SOURCE.txt crediting galleries and artists, with no redistribution licence behind them. They
    are fine to have in a local install and are not ours to put in an archive other people
    download, so `deploy.py` takes everything and `release.py` takes only the format's own
    documentation. Anyone can drop a package into their install; that is the whole point of the
    manifest being data.
    """
    root = ROOT / "BepInEx/custom-enemies"
    if not root.is_dir():
        return []
    out = []
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        relative = f.relative_to(root)
        # The format documentation ships; the packages that use it do not. The Markdown rule is
        # deliberately root-level only: since §165 a format can belong to a *package* rather than
        # to the framework - `WALL-PICTURE-TRAPS.md` describes a manifest kind that only
        # `WallPictureTrap.dll` reads - and such a document travels in that package's own archive,
        # beside the code that implements it, rather than in an archive that cannot execute it.
        if not packages and relative.parts[0] != "_example" and (
                f.suffix.lower() != ".md" or len(relative.parts) != 1):
            continue
        out.append((f"BepInEx/custom-enemies/{relative.as_posix()}", f))
    return out


def custom_enemy_gallery(packages: list[tuple[str, Path]]) -> tuple[list[tuple[str, Path]], list[str]]:
    """A package's funscripts and Definitions.csv rows, resolved on this side.

    The mod can do this itself at runtime - `CustomEnemies.SyncFunscripts` copies the scripts into
    `Edi/Gallery/<variant>` and merges the rows - because a player who drops a package into a game
    install has no repo to deploy from. But when there *is* one, having the mod write into a
    deployed tree is how `deploy.py --check` stops meaning anything: the game-side gallery diverges
    from the payload on every launch, `prune_gallery` deletes the package's scripts on the next
    deploy, and the mod puts them straight back. A permanent false "stale" is worse than no check.

    So the same result is assembled here instead, from the same manifests, and lands in the payload
    like everything else. The runtime path then finds its rows already correct and does nothing.
    """
    rows: list[str] = []
    out: list[tuple[str, Path]] = []
    for arcname, path in packages:
        if path.name not in ("enemy.json", "wall-trap.json"):
            continue
        directory = path.parent
        try:
            manifest = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            fail(f"{path.relative_to(ROOT)} is not readable JSON: {exc}")
        for scene in manifest.get("scenes") or []:
            gallery = (scene.get("gallery") or "").strip()
            if not gallery:
                continue
            stem = Path((scene.get("file") or gallery).strip()).stem
            start = int(scene.get("startTime") or 0)
            end = int(scene.get("endTime") or 0) or funscript_end(directory / "funscripts", stem)
            if end <= start:
                end = start + 1000
            loop = "false" if scene.get("oneShot") else "true"
            rows.append(f"{gallery},{stem},{start},{end},gallery,{loop}")
        # A wall trap keeps its scenes under `animations` rather than `scenes`, so reading only the
        # key above produced no rows at all for one and left the runtime writer as the only source
        # of them - a permanent `deploy.py --check` "stale" as the two sides undid each other on
        # every launch (§128 warned this could happen; §129 is it happening). These mirror
        # WallPictureTrapRegistry.SyncFunscripts exactly: no start/end fields, always looping, and
        # a stage with no funscript to measure contributes no row.
        for stage in manifest.get("animations") or []:
            gallery = (stage.get("gallery") or "").strip()
            if not gallery:
                continue
            stem = Path((stage.get("funscript") or gallery).strip()).stem
            end = funscript_end(directory / "funscripts", stem)
            if end <= 0:
                continue
            rows.append(f"{gallery},{stem},0,{end},gallery,true")
    for arcname, path in packages:
        parts = Path(arcname).parts
        # BepInEx/custom-enemies/<package>/funscripts/<variant>/<name>.funscript
        if len(parts) == 6 and parts[3] == "funscripts" and path.suffix == ".funscript":
            out.append((f"Edi/Gallery/{parts[4]}/{path.name}", path))
    return out, rows


def funscript_end(root: Path, stem: str) -> int:
    """The largest `at` in a package's funscript, which is what an `endTime` of 0 means."""
    for path in sorted(root.rglob(f"{stem}.funscript")):
        try:
            actions = json.loads(path.read_text(encoding="utf-8-sig")).get("actions") or []
        except (OSError, ValueError):
            continue
        stamps = [int(a["at"]) for a in actions if isinstance(a, dict) and "at" in a]
        if stamps:
            return max(stamps)
    return 0


def definitions_with(rows: list[str]) -> bytes:
    """The repo's Definitions.csv plus a package's rows, with the repo's rows untouchable.

    A package that names a row the gallery already defines does not get to redirect it - that row
    was measured against a specific game asset, and quietly repointing it at a package's funscript
    would be the worst kind of silent breakage. It is dropped with a warning instead, which is the
    same rule `CustomEnemies.UpsertDefinitions` applies at runtime.
    """
    text = (ROOT / "Edi/Gallery/Definitions.csv").read_text(encoding="utf-8")
    lines = text.splitlines()
    existing = {line.split(",")[0].strip() for line in lines[1:] if line.strip()}
    for row in rows:
        name = row.split(",")[0]
        if name in existing:
            print(f"  WARNING: custom-enemy row {name!r} is already a gallery row - package row dropped")
            continue
        existing.add(name)
        lines.append(row)
    return ("\n".join(lines) + "\n").encode("utf-8")


def variant_diff_count(variant: str) -> int:
    """How many of the master scripts this variant actually changes.

    The README quotes this number, and it was wrong by the time anyone noticed: it said sixteen
    of 102 long after `variants.py` had regenerated the set. Comparing the `actions` arrays
    rather than the files is the whole point - `variants.py` rewrites every file it emits, so a
    byte comparison says "all of them differ" and means nothing."""
    master = ROOT / "Edi/Gallery/handy2pro"
    other = ROOT / "Edi/Gallery" / variant
    changed = 0
    for path in sorted(master.glob("*.funscript")):
        twin = other / path.name
        if not twin.is_file():
            continue
        # BOM: OpenFunscripter writes one, and `json.loads` refuses it.
        left = json.loads(path.read_text(encoding="utf-8-sig")).get("actions")
        right = json.loads(twin.read_text(encoding="utf-8-sig")).get("actions")
        if left != right:
            changed += 1
    return changed


def render_readme(**subs: str) -> bytes:
    text = (ROOT / "code/dist/README.txt.in").read_text(encoding="utf-8")
    for k, v in subs.items():
        text = text.replace(f"@{k}@", v)
    left = re.findall(r"@[A-Z ]+@", text)
    if left:
        fail(f"README template has unfilled placeholders: {sorted(set(left))}")
    return text.replace("\n", "\r\n").encode("utf-8")


# --------------------------------------------------------------------------------------------
# custom-enemy packages, as their own archives
#
# The release ships the framework and the format's templates, never a package (see
# `custom_enemy_files`). A package is mostly third-party artwork, so it reaches players as its own
# download posted beside the release rather than inside it: the main archive stays ~89 MB instead
# of ~142 MB, and a player opts into explicit third-party content instead of receiving it.
#
# Since the media is not in git either, this is also the only reproducible description of what a
# package *is* - it takes whatever the working tree holds, the same rule `deploy.py` follows, so
# what is played here and what is posted are assembled by the same code.


MEDIA_SUFFIXES = {".png", ".jpg", ".gif", ".mp4", ".webm", ".mov", ".wav", ".mp3", ".ogg"}


def package_dirs() -> dict[str, Path]:
    """Installed packages by directory name, ignoring the `_example/` templates.

    A package is a directory holding exactly one manifest, `enemy.json` for an enemy or
    `wall-trap.json` for a wall trap - the same two names `custom_enemy_gallery` keys on."""
    root = ROOT / "BepInEx/custom-enemies"
    if not root.is_dir():
        return {}
    found = {}
    for d in sorted(p for p in root.iterdir() if p.is_dir() and p.name != "_example"):
        if (d / "enemy.json").is_file() or (d / "wall-trap.json").is_file():
            found[d.name] = d
    return found


def package_version(manifest: dict) -> str:
    """A package's version: its own `version` if the manifest names one, else the commit's date.

    The manifests have carried no version so far, and the falling back on the commit date keeps
    the same property the release has - the same commit always produces the same archive name -
    without making every package author invent a scheme."""
    declared = str(manifest.get("version") or "").strip()
    if declared:
        return declared
    return datetime.datetime.fromtimestamp(git_commit_epoch(), datetime.UTC).date().isoformat()


PACKAGE_README = """\
{display} - a content package for {mod} (Post Nut Calamity {game})

Extract this archive over your game directory, the same place {mod} itself was extracted. It
adds one directory:

    BepInEx/custom-enemies/{directory}/

That is all it does. The mod reads the manifest at startup, copies the funscripts into
Edi/Gallery/ and registers the package's gallery rows itself, so there is nothing else to
install and nothing to edit.
{code_note}
Requires {mod} {version_note}, which carries PncCustomEnemies.dll - the plugin that reads
packages. Without that DLL this archive does nothing at all.
{docs_note}
To remove it, delete the directory above.

{sources}
"""


def build_package(directory: Path, out_dir: Path, check: bool) -> None:
    """One package -> one archive, with the guards that a package specifically needs."""
    name = directory.name
    manifest_path = next(p for p in (directory / "enemy.json", directory / "wall-trap.json")
                         if p.is_file())
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        fail(f"{manifest_path.relative_to(ROOT)} is not readable JSON: {exc}")

    display = str(manifest.get("displayName") or name)
    version = package_version(manifest)
    slug = re.sub(r"[^A-Za-z0-9]+", "", display) or name
    stem = f"{MOD_NAME}-{slug}-{version}"
    print(f"{display}  ->  {stem}.zip")

    files = [(a, s) for a, s in custom_enemy_files(packages=True)
             if Path(a).parts[2] == name]
    if not files:
        fail(f"{name}: nothing to package")

    # A package's credits are not optional. Both of the ones that exist carry a SOURCE.txt naming
    # the artists and the posts their media came from, and an archive that drops it on the way out
    # is the one place that attribution actually needed to be.
    source = directory / "SOURCE.txt"
    if not source.is_file():
        fail(f"{name}: no SOURCE.txt - a package that ships someone's art ships its credits")

    # Unity cannot decode H.264 on Linux, so an MP4 with no WebM beside it is a blank overlay
    # there rather than an error (§127). `webmify.py --check` is the same rule for the working
    # tree; this is it for what gets posted, because a player cannot run that check.
    missing = sorted(s.name for a, s in files
                     if s.suffix.lower() == ".mp4" and not s.with_suffix(".webm").is_file())
    if missing:
        fail(f"{name}: no WebM beside {', '.join(missing)} - blank overlays on Linux. "
             f"Run `.venv/bin/python code/webmify.py` first")

    # A package may ship its own code (§165), and two things follow from that. It has to actually
    # be in the archive - a manifest naming a DLL that is not there is a download that silently
    # does nothing - and the person downloading it has to be told, in the README, before they
    # extract it. There is no sandbox: a package assembly runs with the game's full privileges, so
    # what the archive owes is disclosure. The switch it lands behind is default-off.
    assembly = manifest.get("assembly") or {}
    assembly_file = str(assembly.get("file") or "").strip()
    code_note = ""
    if assembly_file:
        if not (directory / assembly_file).is_file():
            fail(f"{name}: the manifest declares {assembly_file} and the package does not have it. "
                 f"Build it first, or drop the \"assembly\" block")
        package_id = str(manifest.get("id") or name)
        code_note = (
            f"\nTHIS PACKAGE SHIPS CODE: {assembly_file}\n\n"
            f"Its behaviour is a program, not just art and funscripts, and it runs like any other\n"
            f"mod - so only turn it on if you trust where you got it.\n\n"
            f"It arrives switched OFF and runs nothing until you turn it on. To do that,\n"
            f"either use the mod manager (F11) in game, or set this line yourself in\n"
            f"BepInEx/config/com.edi.pnc.customenemies.cfg:\n\n"
            f"    Custom Enemies / {package_id} = true\n\n"
            f"Either way, restart the game afterwards. Its funscripts and its gallery rows are\n"
            f"installed either way, so switching it on later does not also mean restarting Edi.\n")

    scripts = [s for a, s in files if s.suffix == ".funscript"]
    if not scripts:
        print(f"  WARNING: {name} carries no funscripts, so it drives no device")

    # What the manifest never names, reported rather than dropped. A package directory is also a
    # working directory - superseded sheets, the MP3 a WAV was converted from - and those are
    # bytes a stranger downloads for nothing, and more of the artist's work than the package
    # actually uses. Reported, not excluded, because absence from the manifest does not prove
    # disuse: a `.webm` is found as a sibling of the MP4 the manifest names (`PackageVideo`), so
    # a rule that shipped only named files would drop exactly the file Linux needs.
    named = set(re.findall(r'"([^"]+\.[A-Za-z0-9]{2,4})"',
                           manifest_path.read_text(encoding="utf-8-sig")))
    unused = sorted(s.name for a, s in files
                    if s.suffix.lower() in MEDIA_SUFFIXES and s.name not in named
                    and s.with_suffix(".mp4").name not in named)
    if unused:
        size = sum(s.stat().st_size for a, s in files if s.name in unused)
        print(f"  note: {len(unused)} file(s) the manifest never names, {size / 1e6:.1f} MB - "
              f"{', '.join(unused)}")

    # The H.264 masters stay in the working tree and out of the archive. `PackageVideo.ResolvePath`
    # tries the `.webm` sibling *first and unconditionally* - before the Linux test below it - so
    # once a WebM exists the MP4 beside it is never opened on any platform, Windows included. In
    # the witch's package that is 35 MB of a 51 MB download that nothing would ever read. The
    # `missing` guard above is what makes this safe: no MP4 is dropped unless its WebM is there.
    dropped = [s for a, s in files if s.suffix.lower() == ".mp4"]
    if dropped:
        saved = sum(s.stat().st_size for s in dropped)
        files = [(a, s) for a, s in files if s.suffix.lower() != ".mp4"]
        print(f"  {len(dropped)} H.264 master(s) not shipped, {saved / 1e6:.0f} MB - the WebM "
              f"beside each is what the mod actually opens")

    # Every media file the manifest names has to survive into the archive, resolved the way the
    # mod resolves it: the file itself, or a `.webm` sibling (`PackageVideo.ResolvePath` prefers
    # one on every platform, which is what lets the H.264 masters be dropped above). §171 is why
    # this is here - not because a file went missing, but because the *rule* is what a package's
    # own code has to agree with, and stating it at build time is the only place it is written
    # down beside the drop that depends on it.
    shipped_names = {Path(a).name for a, _ in files}
    named_media = sorted(n for n in re.findall(r'"([^"]+\.[A-Za-z0-9]{2,4})"',
                                               manifest_path.read_text(encoding="utf-8-sig"))
                         if Path(n).suffix.lower() in MEDIA_SUFFIXES)
    unresolvable = [n for n in named_media
                    if Path(n).name not in shipped_names
                    and Path(n).with_suffix(".webm").name not in shipped_names]
    if unresolvable:
        fail(f"{name}: the manifest names {', '.join(unresolvable)} and the archive would carry "
             f"neither that file nor a .webm beside it - the package would load and then fail")

    entries = {a: s.read_bytes() for a, s in files}
    # A format reference that belongs to a package ships with it (§168), so say it is in there:
    # the file is the only documentation of that manifest kind anywhere in a player's install.
    docs = sorted(s.name for a, s in files if s.suffix.lower() == ".md")
    docs_note = ("\nThis package also carries " + ", ".join(docs)
                 + " - the format reference for the manifest kind its own code reads.\n") if docs else ""

    entries[f"{MOD_NAME}-{slug}-README.txt"] = PACKAGE_README.format(
        display=display, mod=MOD_NAME, game=GAME_VERSION, directory=name, docs_note=docs_note,
        version_note=f"{plugin_version()} or newer",
        code_note=code_note, sources=source.read_text(encoding="utf-8").strip(),
    ).replace("\n", "\r\n").encode("utf-8")

    media = sum(len(v) for a, v in entries.items() if not a.endswith((".funscript", ".json",
                                                                     ".txt")))
    total = sum(len(v) for v in entries.values())
    print(f"  {len(entries)} files, {total / 1e6:.0f} MB uncompressed "
          f"({media / 1e6:.0f} MB media, {len(scripts)} funscript(s))")

    if check:
        print("  --check: nothing written")
        return

    out = out_dir / f"{stem}.zip"
    write_zip(out, entries, git_commit_epoch())
    print(f"\n  {out.relative_to(ROOT)}  {out.stat().st_size / 1e6:.1f} MB"
          f"\n  sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")


def write_zip(path: Path, entries: dict[str, bytes], epoch: int) -> None:
    ts = time.gmtime(epoch)[:6]
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=ts)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if name in EXECUTABLE_IN_ZIP else 0o644
            info.external_attr = (mode << 16) | (0o40000 << 16 if name.endswith("/") else 0)
            info.create_system = 3                       # unix, so the mode above is honoured
            z.writestr(info, entries[name])
    path.write_bytes(buf.getvalue())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true",
                    help="use BepInEx/plugins/PncEdi.dll as it stands rather than rebuilding")
    ap.add_argument("--check", action="store_true", help="validate only, write nothing")
    ap.add_argument("--update-edi", action="store_true",
                    help="look up the newest Edi release and print the constants to pin it")
    ap.add_argument("--out", type=Path, default=DIST, help=f"output directory (default {DIST})")
    ap.add_argument("--package", metavar="NAME",
                    help="build a custom-enemy package archive instead of the release: a "
                         "directory name under BepInEx/custom-enemies/, or `all`")
    args = ap.parse_args()

    if args.update_edi:
        update_edi()
        return

    if args.package:
        found = package_dirs()
        if not found:
            fail("no packages installed under BepInEx/custom-enemies/")
        if args.package == "all":
            wanted = list(found.values())
        elif args.package in found:
            wanted = [found[args.package]]
        else:
            fail(f"no package {args.package!r} - installed: {', '.join(found)}")
        for d in wanted:
            build_package(d, args.out, args.check)
        return

    version = plugin_version()
    print(f"{MOD_NAME} {version} for Post Nut Calamity {GAME_VERSION}"
          f"  ->  {release_stem(version)}.zip")

    r = subprocess.run([sys.executable, str(ROOT / "code/cfgaudit.py")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail("cfgaudit.py is unhappy, fix that first:\n" + r.stdout + r.stderr)
    print("  config sections ok")

    cfg_text, cfg_notes = build_shipped_config(ROOT / "BepInEx/config/com.edi.pnc.cfg")
    for note in cfg_notes:
        print(f"  config: {note}")

    payload, core_names = bepinex_payload()
    print(f"  BepInEx {BEPINEX_VERSION}: {len(core_names)} core files, "
          f"loaders for windows and linux")
    for problem in check_local_install_is_stock({k: payload[k] for k in core_names}):
        print(f"  WARNING: local install {problem}")

    entries: dict[str, bytes] = dict(payload)
    for name in PLUGINS:
        dll = (ROOT / f"BepInEx/plugins/{name}.dll") if args.no_build else build_plugin(name)
        if not dll.exists():
            fail(f"{dll} does not exist")
        entries[f"BepInEx/plugins/{name}.dll"] = dll.read_bytes()
    entries["BepInEx/config/com.edi.pnc.cfg"] = cfg_text.encode("utf-8")
    entries["start-pnc-linux.sh"] = (ROOT / "code/dist/start-pnc-linux.sh").read_bytes()
    entries["PncEdi-CHANGELOG.txt"] = (
        (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
    entries["PncEdi-CREDITS.txt"] = (
        (ROOT / "CREDITS.md").read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))

    gallery = gallery_files()
    for arcname, src in gallery:
        entries[arcname] = src.read_bytes()

    # Templates and README only - see custom_enemy_files: an installed package is third-party
    # artwork and is not ours to redistribute.
    templates = custom_enemy_files(packages=False)
    for arcname, src in templates:
        entries[arcname] = src.read_bytes()
    print(f"  custom enemies: the framework, plus {len(templates)} template file(s); "
          f"installed packages are not redistributed")

    entries["PncEdi-README.txt"] = render_readme(
        VERSION=version, GAME=GAME_VERSION, BEPINEX=BEPINEX_VERSION, DOORSTOP=DOORSTOP_VERSION,
        ROWS=str(sum(1 for _ in (ROOT / "Edi/Gallery/Definitions.csv")
                     .read_text(encoding="utf-8").splitlines()[1:] if _.strip())),
        SCRIPTS=str(len(gallery) // len(GALLERY_VARIANTS)),
        HANDY2DIFF=str(variant_diff_count("handy2")),
        EDITAG=f"{EDI_TAG} (patched, PR #{EDI_PATCH_PR})" if EDI_PATCH_PR else EDI_TAG,
        # The commit's date, not today's, so the same commit always produces the same archive.
        BUILT=datetime.datetime.fromtimestamp(git_commit_epoch(), datetime.UTC).date().isoformat(),
        COMMIT=git_commit())

    # Edi sits next to its own config, which is where it looks for `.\Gallery`.
    entries["Edi/EdiConfig.json"] = edi_config()
    entries["Edi/Edi.exe"] = fetch_edi()
    patched = f" + PR #{EDI_PATCH_PR} (patched)" if EDI_PATCH_PR else ""
    print(f"  Edi {EDI_TAG}{patched} bundled, with a config carrying no devices but the "
          f"preview one")

    for forbidden in ("Post Nut Calamity.exe", "UnityPlayer.dll", "Assembly-CSharp.dll",
                      "certificate.pfx"):
        hits = [n for n in entries if Path(n).name == forbidden]
        if hits:
            fail(f"refusing to ship {forbidden}: {hits}")

    total = sum(len(v) for v in entries.values())
    print(f"  {len(entries)} files, {total / 1e6:.0f} MB uncompressed")

    if args.check:
        print("  --check: nothing written")
        return

    out = args.out / f"{release_stem(version)}.zip"
    write_zip(out, entries, git_commit_epoch())
    size = out.stat().st_size
    print(f"\n  {out.relative_to(ROOT)}  {size / 1e6:.1f} MB"
          f"\n  sha256 {hashlib.sha256(out.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()

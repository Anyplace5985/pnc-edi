#!/usr/bin/env python3
"""Convert a custom-enemy package's videos to WebM, so they play on Linux.

Unity's `VideoPlayer` has no H.264 decoder outside Windows and macOS: there it hands the file to
Media Foundation or AVFoundation, and the Linux standalone player has nothing to hand it to. What
it carries on *every* platform is libvpx, so VP8 in a WebM container plays everywhere.

The custom-enemy packages ship H.264 MP4, which is why the witch's dream-cloud overlays are blank
on Linux. This writes a `.webm` beside each one; `PackageVideo` prefers that sibling on every
platform, so one package then works on both without the manifest changing.

    python3 code/webmify.py                       every package under BepInEx/custom-enemies
    python3 code/webmify.py <dir>...              only these packages or files
    python3 code/webmify.py --check               report what is missing, convert nothing
    python3 code/webmify.py --force               re-encode even where a .webm already exists

VP8 rather than VP9 on purpose: VP9 support in Unity's player has moved between versions and
platforms, VP8 has been there throughout, and these are small overlay clips where the size
difference is not worth the risk. Audio goes to Vorbis for the same reason.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pncpaths import ROOT as _ROOT  # noqa: E402

ROOT = Path(_ROOT)

PACKAGES = ROOT / "BepInEx/custom-enemies"
SOURCE_SUFFIXES = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


def sources(targets: list[str]) -> list[Path]:
    roots = [Path(t) for t in targets] if targets else [PACKAGES]
    found: list[Path] = []
    for root in roots:
        root = root if root.is_absolute() else (ROOT / root)
        if root.is_file():
            found.append(root)
        elif root.is_dir():
            found += [p for p in sorted(root.rglob("*")) if p.suffix.lower() in SOURCE_SUFFIXES]
        else:
            sys.exit(f"webmify: {root} does not exist")
    return [p for p in found if p.suffix.lower() in SOURCE_SUFFIXES]


def convert(src: Path, force: bool) -> str:
    out = src.with_suffix(".webm")
    if out.exists() and not force:
        return "have"
    # -deadline good / -cpu-used 2 is the usual quality-for-time point for libvpx; -crf with
    # -b:v 0 asks for constant quality rather than a bitrate, which suits short looping overlays
    # whose content varies. -row-mt and -threads keep a two-pass-free encode from taking minutes.
    command = [
        "ffmpeg", "-y", "-i", str(src),
        "-c:v", "libvpx", "-crf", "30", "-b:v", "0",
        "-deadline", "good", "-cpu-used", "2", "-row-mt", "1", "-threads", "0",
        "-pix_fmt", "yuv420p",
        "-c:a", "libvorbis", "-b:a", "128k",
        str(out),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        out.unlink(missing_ok=True)
        tail = (result.stderr or "").strip().splitlines()[-3:]
        return "FAILED: " + " / ".join(tail)
    return "wrote"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("targets", nargs="*", metavar="PATH",
                    help=f"package directories or video files (default: {PACKAGES})")
    ap.add_argument("--check", action="store_true",
                    help="report which videos have no .webm and exit 1 if any do not")
    ap.add_argument("--force", action="store_true", help="re-encode even where a .webm exists")
    args = ap.parse_args()

    found = sources(args.targets)
    if not found:
        print("webmify: no source videos found - nothing to do")
        return

    if args.check:
        missing = [p for p in found if not p.with_suffix(".webm").exists()]
        for p in missing:
            print(f"  MISSING  {p.relative_to(ROOT)} has no .webm - blank on Linux")
        print(f"webmify --check: {len(found) - len(missing)}/{len(found)} video(s) have a WebM")
        sys.exit(1 if missing else 0)

    if not shutil.which("ffmpeg"):
        sys.exit("webmify: ffmpeg is not on PATH")

    failed = 0
    for src in found:
        status = convert(src, args.force)
        print(f"  {status:5} {src.relative_to(ROOT)}"
              if status in ("have", "wrote") else f"  {src.relative_to(ROOT)}: {status}")
        failed += status.startswith("FAILED")
    print(f"webmify: {len(found)} video(s), {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

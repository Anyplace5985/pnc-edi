#!/usr/bin/env python3
"""Does every package that declares an assembly actually ship a current one?

    python3 code/packageaudit.py

**A package's code fails silently by design, which is why it needs a check.** §165 let a package
ship a .NET assembly and publish behaviours from it by name. Everything about that path degrades
quietly on purpose: a manifest naming a DLL that is not there loads as a plain reskin, a behaviour
name nothing published leaves the enemy without it, and a package that is switched off runs
no code at all. Each of those is the right runtime behaviour - a player should never get a crash
because a package is half-installed - and each is indistinguishable, from the outside, from "the
behaviour is broken".

So the working tree gets the strict version of the same questions:

  - a manifest declaring `assembly.file` has that file beside it, and it is newer than the sources
    it was built from (a package DLL is the one build output nothing else reads, so a stale one
    survives every other check in this repo);
  - the `api` it declares is the `PackageApi.Version` this framework speaks, since the loader
    refuses a mismatch at runtime and the refusal is a log line nobody reads until something is
    already wrong;
  - a manifest naming a `behaviour` has some installed package publishing that name;
  - and a package that ships no assembly declares none, so the reverse - a stray block left behind
    by a copy-paste - is caught too.

`release.py --package` enforces the first of these for what gets posted. This is it for the tree
you are working in, which is where the fix is cheap.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGES = ROOT / "BepInEx/custom-enemies"
API_FILE = ROOT / "code/customenemies/PncCustomEnemies/PackageApi.cs"
PACKAGE_SOURCES = ROOT / "code/packages"


def api_version() -> int:
    """The API version the framework speaks, read out of the source rather than duplicated here."""
    text = API_FILE.read_text(encoding="utf-8")
    match = re.search(r"public const int Version = (\d+);", text)
    if not match:
        sys.exit(f"packageaudit: no `public const int Version` in {API_FILE.relative_to(ROOT)}")
    return int(match.group(1))


def manifests() -> list[Path]:
    out: list[Path] = []
    for directory in sorted(p for p in PACKAGES.iterdir() if p.is_dir() and p.name != "_example"):
        out.extend(sorted(directory.glob("*.json")))
    return out


def published_behaviours() -> dict[str, str]:
    """Behaviour names published by the package sources in this repo, and who publishes each.

    Read out of the source with a regex rather than by loading the assemblies: this has to work on
    a machine with no game and no build, and `RegisterBehaviour("name", ...)` is a literal at every
    call site by construction - a name built at runtime could not be documented either.
    """
    found: dict[str, str] = {}
    if not PACKAGE_SOURCES.is_dir():
        return found
    for source in PACKAGE_SOURCES.rglob("*.cs"):
        text = source.read_text(encoding="utf-8")
        for name in re.findall(r'RegisterBehaviour\(\s*"([^"]+)"', text):
            found[name] = source.parent.name
        # The name is usually a constant rather than a literal at the call site, which is the
        # shape the example package uses and the one worth encouraging: one place to change.
        if "RegisterBehaviour(" not in text:
            continue
        for const_name, value in re.findall(r'const string (\w+)\s*=\s*"([^"]+)"', text):
            if re.search(rf'RegisterBehaviour\(\s*{const_name}\b', text):
                found[value] = source.parent.name
    return found


def newest_source(package_dir: Path) -> float:
    """The newest source timestamp of the project that builds into this package, or 0."""
    newest = 0.0
    for project in PACKAGE_SOURCES.glob("*/*.csproj"):
        text = project.read_text(encoding="utf-8")
        if f"custom-enemies\\{package_dir.name}\\" not in text and \
           f"custom-enemies/{package_dir.name}/" not in text:
            continue
        for source in list(project.parent.rglob("*.cs")) + [project]:
            if "/obj/" in source.as_posix() or "/bin/" in source.as_posix():
                continue
            newest = max(newest, source.stat().st_mtime)
    return newest


def main() -> int:
    version = api_version()
    behaviours = published_behaviours()
    problems: list[str] = []
    checked = 0

    for manifest_path in manifests():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            problems.append(f"{manifest_path.relative_to(ROOT)}: unreadable JSON ({exc})")
            continue
        checked += 1
        where = manifest_path.relative_to(ROOT)
        package_dir = manifest_path.parent

        assembly = manifest.get("assembly") or {}
        if assembly:
            file = str(assembly.get("file") or "").strip()
            module = str(assembly.get("module") or "").strip()
            declared = assembly.get("api")
            if not file or not module:
                problems.append(f"{where}: an `assembly` block needs both `file` and `module`")
            elif not (package_dir / file).is_file():
                problems.append(f"{where}: declares {file}, which is not in the package - "
                                f"build it (dotnet build code/edimod/PncEdi.csproj -c Release)")
            else:
                built = (package_dir / file).stat().st_mtime
                source = newest_source(package_dir)
                if source and source > built:
                    problems.append(f"{where}: {file} is older than the sources it is built from - "
                                    f"rebuild, or the install runs last build's behaviour")
            if declared != version:
                problems.append(f"{where}: declares api {declared!r}, this framework speaks {version}"
                                f" - the loader refuses a mismatch, so the package would not run")

        behaviour = str(manifest.get("behaviour") or "").strip()
        if behaviour and behaviour not in behaviours:
            problems.append(f"{where}: asks for behaviour {behaviour!r}, which no package in this "
                            f"tree publishes ({', '.join(sorted(behaviours)) or 'none'})")

    if problems:
        print(f"packageaudit: {len(problems)} problem(s) in {checked} manifest(s)")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"packageaudit: {checked} manifest(s) ok, "
          f"{len(behaviours)} behaviour(s) published: {', '.join(sorted(behaviours)) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

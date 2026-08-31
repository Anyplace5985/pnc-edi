#!/usr/bin/env python3
"""Does every place that states the mod's version agree with the source of truth?

    python3 code/versionaudit.py

**Why this exists.** `PncEdi/Plugin.cs` carried two versions that had drifted six minor releases
apart: the `[BepInPlugin]` attribute said `2.6.0` as a string literal, while the `PluginVersion`
constant three lines below said `2.0.8`. BepInEx reads the attribute, so the log and the mod
manager were right and the constant was a lie - harmless only because nothing happened to read it.
The other two plugins had it right all along, passing the constants into the attribute, which is
why nothing ever pointed at the odd one out.

The rule is `learnings/working-practice.md`'s: **where a duplicate must exist, derive it or check
it.** A version cannot be derived across a C# attribute, a `.csproj`-free `AssemblyInfo` and four
Markdown documents, so it gets checked instead.

Source of truth is `PluginVersion` in `code/edimod/PncEdi/Plugin.cs`. Everything else has to match:

  * every `[BepInPlugin]` in the tree passes constants, never a literal version - the defect above
  * `AssemblyInfo.cs`'s three attributes (the two four-part ones take a trailing `.0`)
  * every document that names the mod version, in any of the shapes below

A wrong version in a posted archive cannot be fixed after the fact - somebody already downloaded
it - so this is a gate, not a report. Exits non-zero if anything disagrees.
"""
import os
import re
import sys

import pncpaths as P

ROOT = P.ROOT

TRUTH = "code/edimod/PncEdi/Plugin.cs"

# The mod version is PncEdi's. PncModManager and PncCustomEnemies version independently -
# they ship on their own cadence - so they are checked for the literal-attribute defect only.
PLUGIN_SOURCES = [
    "code/edimod/PncEdi/Plugin.cs",
    "code/modmanager/Plugin.cs",
    "code/customenemies/PncCustomEnemies/CustomEnemyPlugin.cs",
]

ASSEMBLY_INFO = "code/edimod/Properties/AssemblyInfo.cs"

# Documents state the version in five shapes. Each regex captures the version and nothing else;
# a bare "before 3.0.0" is deliberately not one of them, because that is prose about when a
# behaviour changed and it keeps naming that release forever.
# The archive name is matched only for the *current* game version. `PNC0.2.1-PncEdi-2.1.0.zip`
# is a real past build and code/README.md names it on purpose to explain the naming scheme; an
# archive for the game this tree targets is a claim about what a build produces today.
GAME_VERSION = re.search(r'GAME_VERSION\s*=\s*"([^"]+)"',
                         open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "release.py"), encoding="utf-8").read()).group(1)

DOC_PATTERNS = [
    (re.compile(r"PNC" + re.escape(GAME_VERSION) + r"-PncEdi-(\d+\.\d+\.\d+)\.zip"),
                                                               "archive name"),
    (re.compile(r"`PncEdi`\s+v(\d+\.\d+\.\d+)"),               "`PncEdi` v<n>"),
    (re.compile(r"PncEdi\.dll[^\n]*?\(v(\d+\.\d+\.\d+)"),      "PncEdi.dll (v<n>)"),
    (re.compile(r"Mod\s+`(\d+\.\d+\.\d+)`"),                   "Mod `<n>`"),
    (re.compile(r"EDI Integration (\d+\.\d+\.\d+)"),           "log display name"),
]

# The narrative record names every version this mod has ever had, which is its job.
DOC_SKIP = {"CHANGELOG.md", "HISTORY.md", "TODO.md"}

DOC_EXTS = (".md", ".txt", ".in", ".cfg")

BEPINPLUGIN = re.compile(r"\[BepInPlugin\(([^\]]*)\)\]")
CONST_VERSION = re.compile(r'const\s+string\s+PluginVersion\s*=\s*"([^"]+)"')
LITERAL_VERSION = re.compile(r'"\d+\.\d+\.\d+"')


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def truth_version(problems):
    m = CONST_VERSION.search(read(TRUTH))
    if not m:
        problems.append(f"{TRUTH}: no `const string PluginVersion` to read the version from")
        return None
    return m.group(1)


def check_attributes(problems):
    """Every [BepInPlugin] must pass the constants. A literal version there is the defect that
    started this file: the attribute and the constant become two facts, and only one is read."""
    for rel in PLUGIN_SOURCES:
        src = read(rel)
        for m in BEPINPLUGIN.finditer(src):
            args = m.group(1)
            if LITERAL_VERSION.search(args):
                line = src[:m.start()].count("\n") + 1
                problems.append(
                    f"{rel}:{line}: [BepInPlugin] hard-codes a version literal instead of "
                    f"passing PluginVersion - the constant below it can now drift unnoticed")


def check_assembly_info(version, problems):
    src = read(ASSEMBLY_INFO)
    # AssemblyVersion and AssemblyFileVersion are four-part; AssemblyInformationalVersion is not.
    expected = {
        "AssemblyVersion": version + ".0",
        "AssemblyFileVersion": version + ".0",
        "AssemblyInformationalVersion": version,
    }
    for attr, want in expected.items():
        m = re.search(r'\[assembly:\s*' + attr + r'\("([^"]+)"\)\]', src)
        if not m:
            problems.append(f"{ASSEMBLY_INFO}: no {attr} attribute")
        elif m.group(1) != want:
            line = src[:m.start()].count("\n") + 1
            problems.append(f"{ASSEMBLY_INFO}:{line}: {attr} is {m.group(1)}, "
                            f"expected {want} (from {TRUTH})")


def documents():
    """Tracked documents only - a build artefact under dist/ or a game install reached through a
    symlink legitimately carries whatever version it was built as."""
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs
                   if d not in {".git", ".venv", "dist", "obj", "bin", "node_modules"}
                   and not d.startswith("game-")]
        for name in files:
            if name.endswith(DOC_EXTS) and name not in DOC_SKIP:
                out.append(os.path.relpath(os.path.join(base, name), ROOT))
    return sorted(out)


def check_documents(version, problems):
    for rel in documents():
        try:
            src = read(rel)
        except (UnicodeDecodeError, OSError):
            continue
        for pattern, what in DOC_PATTERNS:
            for m in pattern.finditer(src):
                if m.group(1) != version:
                    line = src[:m.start()].count("\n") + 1
                    problems.append(f"{rel}:{line}: {what} says {m.group(1)}, "
                                    f"expected {version} (from {TRUTH})")


def main():
    problems = []
    version = truth_version(problems)
    if version:
        check_attributes(problems)
        check_assembly_info(version, problems)
        check_documents(version, problems)

    if problems:
        for p in problems:
            print(f"  {p}")
        print(f"\n{len(problems)} version disagreement(s)")
        return 1

    print(f"version {version}: attribute, assembly info and every document agree")
    return 0


if __name__ == "__main__":
    sys.exit(main())

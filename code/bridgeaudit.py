#!/usr/bin/env python3
"""Is the seam between PncEdi and PncCustomEnemies still wired at both ends?

    python3 code/bridgeaudit.py

**This check is what makes the plugin split real.** §131 separated the mod that talks to a device
from the mod that loads other people's enemies so the two could move independently, and that only
holds while a change to one cannot silently break the other. PncEdi is where most development
happens; the framework changes rarely. So the direction worth defending is PncEdi -> framework.

Most ways of breaking it are already loud. The plugin is compiled by the same `dotnet build` that
builds PncEdi, so renaming or deleting anything it uses is a build error in the same command.
`patchaudit.py` reads both trees, so a game-side rename is caught for both.

**One way is silent, and it is the one this file is for.** Every question PncEdi asks about packages
goes through a delegate on `CustomEnemyBridge`, and every delegate answers "vanilla" when nothing
installed it - deliberately, because that is what makes deleting `PncCustomEnemies.dll` safe. So if
a refactor drops the *call* - a rewritten `GoFiller` that no longer consults `EdiChannelHeld`, a
tidied `SceneEscapeGate` that stops asking for a package's own scene length - everything still
compiles, every test passes, and the framework quietly stops working in exactly the way a missing
DLL looks like. Nothing would report it until a run, and the report would be "the custom enemies
are behaving oddly", which is the expensive kind of bug.

So: each member of the bridge must be **installed** by the plugin and **consumed** by PncEdi. A
member that has lost either end is either dead code or a silent regression, and both want a
sentence rather than a surprise. If you are refactoring PncEdi, a `CustomEnemyBridge` call is
load-bearing even where deleting it looks harmless.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BRIDGE = ROOT / "code/edimod/PncEdi/CustomEnemyBridge.cs"
CORE = ROOT / "code/edimod/PncEdi"
PLUGIN = ROOT / "code/customenemies/PncCustomEnemies"

# NameRemap's resolver is the same idea and predates the bridge (§127), so it is audited with it.
EXTRA = [("NameRemap", "CustomEnemyResolver")]


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def read(directory: Path, skip: set[str] = frozenset()) -> str:
    return "\n".join(strip_comments(p.read_text(encoding="utf-8"))
                     for p in sorted(directory.glob("*.cs")) if p.name not in skip)


def main() -> int:
    if not BRIDGE.exists() or not PLUGIN.exists():
        print("bridgeaudit: no bridge or no custom-enemy plugin - nothing to audit")
        return 0

    bridge = strip_comments(BRIDGE.read_text(encoding="utf-8"))
    # The delegate fields are what the plugin installs; the helper accessors beside them are what
    # PncEdi calls. A helper "covers" a field when its body names it, which is how the two spellings
    # are paired without a second list to keep in step - `SpawnWeight(key)` counts as a use of
    # `SpawnWeightResolver` because that is literally what it invokes.
    fields = re.findall(r"public static (?:Func|Action)<.*?>\s+(\w+);", bridge)
    covers: dict[str, set[str]] = {}
    for match in re.finditer(r"public static [\w<>, \[\]]+? (\w+)(?:\([^)]*\))?\s*=>([^\n;]*(?:;|$))", bridge):
        covers[match.group(1)] = {f for f in fields if f in match.group(2)}
    # An accessor with a body counts the same way. Without this, moving one helper from `=>` to a
    # block turns a covered delegate into a "nothing asks it" failure that is purely about how the
    # helper is spelled (§138). The body runs to the first closing brace at method indent.
    for match in re.finditer(r"public static [\w<>, \[\]]+? (\w+)\([^)]*\)\s*\n\t\{(.*?)\n\t\}", bridge, re.S):
        covers.setdefault(match.group(1), set()).update(f for f in fields if f in match.group(2))

    core = read(CORE, skip={BRIDGE.name})
    plugin = read(PLUGIN)

    problems: list[str] = []
    for field in fields:
        # Installed: the plugin assigns the delegate.
        if not re.search(rf"CustomEnemyBridge\.{field}\s*=", plugin):
            problems.append(f"CustomEnemyBridge.{field} is never installed by PncCustomEnemies - "
                            f"PncEdi will always take the vanilla answer")
        # Consumed: PncEdi reads it, by the field name or through its accessor.
        names = [field] + [helper for helper, used in covers.items() if field in used]
        if not any(re.search(rf"CustomEnemyBridge\.{name}\b", core) for name in names):
            problems.append(f"CustomEnemyBridge.{field} is installed but nothing in PncEdi asks it "
                            f"(tried {', '.join(names)}) - either dead, or a call was refactored away")

    for owner, member in EXTRA:
        if not re.search(rf"{owner}\.{member}\s*=", plugin):
            problems.append(f"{owner}.{member} is never installed by PncCustomEnemies")
        if not re.search(rf"{member}\b", core):
            problems.append(f"{owner}.{member} is installed but PncEdi never reads it")

    print(f"custom-enemy bridge: {len(fields)} delegate(s) + {len(EXTRA)} older seam(s)")
    for problem in problems:
        print(f"  {problem}")
    if not problems:
        print("  ok - every seam is installed by the plugin and asked by the mod")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

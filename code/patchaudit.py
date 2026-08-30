#!/usr/bin/env python3
"""Does the mod still bind to the game? Every patch target and reflected member, checked statically.

    python3 code/patchaudit.py                        # against game-windows
    python3 code/patchaudit.py --game "../Archive/PNC 0.2.1 Win"
    python3 code/patchaudit.py --compare "../Archive/PNC 0.2.1 Win"   # what changed between two builds
    python3 code/patchaudit.py -v                     # list every target, not just the failures
    python3 code/patchaudit.py --ai                   # redo the CHANGELOG §46 AI audit statically
    python3 code/patchaudit.py --heat                 # every vanilla `heat == 0` test, with a verdict

The mod reaches into `Assembly-CSharp` three ways, and **two of them fail silently**:

| how | what happens when the target is gone |
|---|---|
| `[HarmonyPatch(typeof(T), "M")]` | throws at patch time - loud, and takes the plugin down |
| `AccessTools.Field(typeof(T), "f")` | returns **null**; the feature quietly does nothing |
| `Traverse.Create(x).Field("f")` | returns an empty Traverse; reads give default(T) |
| `typeof(T).GetField("f")` | returns **null**; the feature quietly does nothing |

`EnemyAiAudit` covers a hand-picked few of the second kind at runtime (CHANGELOG §46) and is the
model for this: **a gap must be inert and visible, never silently plausible.** This is the same
idea applied to every target at once, and statically, so a game update can be assessed before
launching anything.

Bare `typeof(T).GetField/GetMethod/GetProperty` is the same failure as `AccessTools` - a cached
null and a feature that stops - and until 2026-08-24 this only scanned `AccessTools.*` and
`Traverse`, so nine reflected members across four files had never been audited at all. They are
checked as hard targets: several of them (`SerpentHypnosis`'s three) fall back to a wider gate
rather than throwing when the member is gone, and that is exactly why the audit has to say so -
the fallback makes the loss invisible in play, not harmless.

What it cannot see: a `Traverse.Create(expr).Field("x")` whose owning type it could not infer is
checked against the *whole assembly* rather than against one type, so a field that moved from one
class to another reads as present. Those are printed as `any` rather than `ok`.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "code/edimod/PncEdi"
# Since §131 the mod is more than one assembly, and a patch that binds to the game is a patch
# wherever it lives: the custom-enemy plugin has its own source tree and its own registration list,
# so both are audited, and the registry check is run once per (tree, list) pair rather than being
# taught about two lists at once. PncModManager has no game patches at all - it only reads BepInEx
# config - so it is not here.
# §165 added a third kind: a package's own assembly, which patches the game itself with its own
# Harmony id and its own registration call. A patch that binds to the game is a patch wherever it
# lives, and a package's is the *most* likely to rot unnoticed - it is built into a package
# directory that nothing else reads.
SOURCES = [
    (SRC, "PluginPatches.cs"),
    (ROOT / "code/customenemies/PncCustomEnemies", "CustomEnemyPlugin.cs"),
]
for _project in sorted((ROOT / "code/packages").glob("*/")):
    _sources = _project / _project.name.rstrip("/")
    for _tree in sorted(p for p in _project.iterdir() if p.is_dir() and p.name not in ("obj", "bin")):
        _registrations = [f.name for f in sorted(_tree.glob("*Module.cs"))]
        if _registrations:
            SOURCES.append((_tree, _registrations[0]))

# Assemblies the mod patches into. Anything else a typeof() names (UnityEngine, our own types) is
# not the game's and cannot drift with a game release.
ASSEMBLIES = ["Assembly-CSharp.dll", "Assembly-CSharp-firstpass.dll"]


def fail(msg: str) -> None:
    print(f"patchaudit: {msg}", file=sys.stderr)
    sys.exit(2)


# --------------------------------------------------------------------------------------------
# the game side: parse ikdasm output into {type: (methods, fields)}


CLASS_RE = re.compile(r"^(\s*)\.class\s+(.*)$")
# ikdasm annotates every closing brace with what it closes - `} // end of class 'X'`. That is a
# far better anchor than brace/indent matching: a nested type sits at the same indent as its
# parent's own members, and a bare `}` never appears at all.
END_CLASS_RE = re.compile(r"^\s*\}\s*//\s*end of class\b")
FIELD_RE = re.compile(r"^(\s*)\.field\s+(.*)$")
METHOD_RE = re.compile(r"^(\s*)\.method\s")
# `instance void  Foo(int32 x) cil managed` / `void  Bar() cil managed`
SIGNATURE_RE = re.compile(r"([A-Za-z_$<>][\w`<>$.]*)\s*\(")


def _last_identifier(text: str) -> str | None:
    """The declared name at the end of an IL declaration line.

    `.field private class GrabScreen '<>4__this'` -> `<>4__this`
    `.field public static literal valuetype AIState Idle = int32(0)` -> `Idle`
    Names carrying IL-reserved characters are single-quoted, which is stripped here so the name
    matches what the C# source writes."""
    text = text.split("=")[0].strip()
    if not text:
        return None
    token = text.split()[-1]
    return token.strip("'") or None


def parse_il(il: str) -> dict[str, dict[str, set[str]]]:
    """{full type name: {"methods": ..., "fields": ...}}.

    Nesting is tracked by the closing brace, not by the next `.class`: a nested type sits at the
    same indent as its parent's own members, so a stack that only ever pops when another class
    opens attributes every field after the first nested type to that nested type instead. The
    parser then reports the whole assembly as missing, which is how this was caught - it was run
    against 0.2.1 first, where every target is known to resolve. **Validate a static analyser
    against the build it is known to describe before believing it about a new one.**"""
    types: dict[str, dict[str, set[str]]] = {}
    stack: list[tuple[int, str]] = []           # (indent, full name)
    pending_method_indent: int | None = None

    for line in il.split("\n"):
        if END_CLASS_RE.match(line):
            if stack:
                stack.pop()
            pending_method_indent = None
            continue

        m = CLASS_RE.match(line)
        if m:
            indent, rest = len(m.group(1)), m.group(2)
            # `extends` may be on this line or the next; the name is the last token before it.
            name = _last_identifier(rest.split(" extends ")[0])
            if not name:
                continue
            while stack and stack[-1][0] >= indent:
                stack.pop()
            full = f"{stack[-1][1]}/{name}" if stack else name
            stack.append((indent, full))
            types.setdefault(full, {"methods": set(), "fields": set()})
            pending_method_indent = None
            continue

        if not stack:
            continue

        m = FIELD_RE.match(line)
        if m and len(m.group(1)) == stack[-1][0] + 2:
            name = _last_identifier(m.group(2))
            if name:
                types[stack[-1][1]]["fields"].add(name)
            continue

        m = METHOD_RE.match(line)
        if m and len(m.group(1)) == stack[-1][0] + 2:
            # A short declaration carries its own signature - `.method public hidebysig static
            # void  RestartRun() cil managed` - so read this line before deferring to the next
            # ones. Waiting unconditionally made every such method invisible, which reported
            # RunRestartController.RestartRun as missing from a build that has it.
            sig = SIGNATURE_RE.search(line.split(".method", 1)[1])
            if sig:
                types[stack[-1][1]]["methods"].add(sig.group(1))
                pending_method_indent = None
            else:
                pending_method_indent = stack[-1][1]
            continue

        if pending_method_indent is not None:
            # The signature follows the flags line, but a long return type wraps onto a line of
            # its own - `instance [netstandard]System.Collections.IEnumerator` then the name. So
            # keep reading until a `name(` appears rather than assuming the very next line has it.
            # (Found because CameraSwapTrigger.ReturnToFirstPersonCoroutine, which the mod patches
            # and which demonstrably works, was reported missing from 0.2.1.)
            sig = SIGNATURE_RE.search(line)
            if sig:
                types[pending_method_indent]["methods"].add(sig.group(1))
                pending_method_indent = None
            elif line.lstrip().startswith("{") or line.lstrip().startswith(".") :
                pending_method_indent = None
    return types


def load_game(managed: Path) -> dict[str, dict[str, set[str]]]:
    if not shutil.which("ikdasm"):
        fail("ikdasm is not on PATH (package: ikvm / mono-tools)")
    types: dict[str, dict[str, set[str]]] = {}
    for name in ASSEMBLIES:
        dll = managed / name
        if not dll.exists():
            fail(f"{dll} does not exist")
        r = subprocess.run(["ikdasm", str(dll)], capture_output=True, text=True)
        if r.returncode != 0:
            fail(f"ikdasm failed on {dll}:\n{r.stderr[-2000:]}")
        for k, v in parse_il(r.stdout).items():
            if k in types:
                types[k]["methods"] |= v["methods"]
                types[k]["fields"] |= v["fields"]
            else:
                types[k] = v
    return types


# --------------------------------------------------------------------------------------------
# the mod side: what it asks the game for


def read_source() -> dict[str, list[tuple]]:
    """Targets, each as (kind, type-or-None, member, file:line)."""
    harmony: list[tuple] = []
    fields: list[tuple] = []
    reflect: list[tuple] = []
    loose: list[tuple] = []
    optional: set[str] = set()

    for source, _ in SOURCES:
        for path in sorted(source.glob("*.cs")):
            text = path.read_text(encoding="utf-8")
            where = path.name

            for m in re.finditer(r'\[HarmonyPatch\(typeof\(([\w.]+)\)\s*,\s*"([^"]+)"', text):
                harmony.append((m.group(1), m.group(2), f"{where}:{_line(text, m.start())}"))

            for m in re.finditer(r'AccessTools\.(?:Field|Method|PropertyGetter|PropertySetter)'
                                 r'\(typeof\(([\w.]+)\)\s*,\s*"([^"]+)"', text):
                fields.append((m.group(1), m.group(2), f"{where}:{_line(text, m.start())}"))

            # `typeof(T).GetField("f", BindingFlags...)` - System.Reflection rather than Harmony, and
            # every bit as silent: the cached FieldInfo is null and the caller takes its fallback.
            # `obj.GetType().GetField(...)` is deliberately not matched - the type is a runtime value,
            # so there is nothing to check it against.
            for m in re.finditer(r'typeof\(([\w.]+)\)\s*\.\s*Get(?:Field|Method|Property)'
                                 r'\(\s*"([^"]+)"', text):
                reflect.append((m.group(1), m.group(2), f"{where}:{_line(text, m.start())}"))

            # Traverse.Create(<expr>).Field("x") - the owning type is an expression, so the member is
            # only checkable against the assembly as a whole.
            for m in re.finditer(r'Traverse\.Create\([^)]*\)\s*(?:\.\w+\([^)]*\)\s*)*?'
                                 r'\.(Field|Method|Property)\("([^"]+)"', text):
                loose.append((m.group(1), m.group(2), f"{where}:{_line(text, m.start())}"))
            for m in re.finditer(r'\.(Field|Method|Property)\("([^"]+)"\)', text):
                loose.append((m.group(1), m.group(2), f"{where}:{_line(text, m.start())}"))

            # The mod guards some members it knows may not be there - `.Field("x").FieldExists()`.
            # Absent is the expected case for those, not a defect (EnemyReactivationHelper's
            # `simulateMovement` is on a component type that is not in Assembly-CSharp at all).
            for m in re.finditer(r'\.(?:Field|Property)\("([^"]+)"\)\s*\.\w*Exists\(\)', text):
                optional.add(m.group(1))

    return {"harmony": harmony, "fields": fields, "reflect": reflect, "optional": optional,
            "loose": sorted({(k, n) for k, n, _ in loose})}


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


# --------------------------------------------------------------------------------------------
# the registration list

def registry_audit() -> list[str]:
    problems: list[str] = []
    for source, registry in SOURCES:
        problems += registry_audit_one(source, registry)
    return problems


def registry_audit_one(SRC: Path, REGISTRY: str) -> list[str]:
    """Every patch class must be named in `PluginPatches.ApplyPatches`, and vice versa.

    Harmony patches are registered here one class at a time - `Patch("com.edi.pnc.x",
    typeof(X))` - rather than by an assembly-wide `PatchAll()`. That is deliberate (the gated
    block only registers the gameplay patches when `Gameplay/Enabled` is on), but it means a new
    patch class does nothing at all until it is named on that list, and **the failure is
    completely silent**: the attributes are right, the class compiles, and nothing logs. §109's
    fix was written correctly, built, deployed, and had no effect for a whole run because of it.

    This is the check that could have caught that in a second. It is the same shape as the rest
    of this file - a gap must be inert and visible, never silently plausible.
    """
    declared: dict[str, str] = {}
    for path in sorted(SRC.glob("*.cs")):
        if path.name == REGISTRY:
            continue
        text = re.sub(r"//[^\n]*", "", path.read_text(encoding="utf-8"))
        if "[HarmonyPatch" not in text:
            continue
        # Attribute each `[HarmonyPatch` to the top-level class whose body it falls in.
        #
        # This used to take the *first* top-level class in the file, on the reasoning that the tree
        # had one per file. The custom-enemy files broke that: they declare their manifest and
        # package types first and the patch class last, so the audit blamed a plain data class for
        # carrying patches and called the real one an unused registration - two false failures for
        # one correct file. Finding the enclosing class instead makes the check independent of how
        # a file happens to be laid out, which is what it was always trying to say.
        #
        # `PatchAll(Type)` covers a type's nested classes, and the regex is anchored at column zero,
        # so only outermost declarations are considered - a nested patch class still resolves to the
        # top-level type that is actually registered.
        decls = list(re.finditer(
            r"^(?:public |internal |)(?:static |sealed |partial |abstract )*class (\w+)", text, re.M))
        if not decls:
            continue
        # A class-level `[HarmonyPatch(...)]` sits on the lines just above `class X`, so each
        # region starts at the top of that contiguous attribute block rather than at `class`.
        # These have to be computed for every declaration before any region is cut, or the
        # attribute block would fall inside the *previous* class's region as well as its own.
        starts = []
        for decl in decls:
            start = decl.start()
            while True:
                previous = text.rfind("\n", 0, start - 1) + 1
                if previous >= start or not text[previous:start].lstrip().startswith("["):
                    break
                start = previous
            starts.append(start)
        for i, decl in enumerate(decls):
            end = starts[i + 1] if i + 1 < len(decls) else len(text)
            if "[HarmonyPatch" in text[starts[i]:end]:
                declared[decl.group(1)] = path.name

    reg = (SRC / REGISTRY).read_text(encoding="utf-8")
    # Two spellings, because the trees register two ways: the plugins go through their own
    # `Patch("id", typeof(X))` helper, and a package assembly (§165) calls Harmony directly -
    # `new Harmony("id").PatchAll(typeof(X))` - since it has no helper of the framework's to use.
    registered = {m.group(1) for m in
                  re.finditer(r'\b(?:Try)?Patch\(\s*"[^"]+"\s*,\s*typeof\((\w+)\)', reg)}
    registered |= {m.group(1) for m in
                   re.finditer(r'\bPatchAll\(\s*typeof\((\w+)\)', reg)}

    problems = []
    for cls, where in sorted(declared.items()):
        if cls not in registered:
            problems.append(f"{cls} carries [HarmonyPatch] members but is not registered in "
                            f"{REGISTRY} - it is compiled in and does nothing ({where})")
    for cls in sorted(registered - set(declared)):
        problems.append(f"{REGISTRY} registers {cls}, which declares no [HarmonyPatch] member")

    print(f"\npatch registry: {len(registered)} class(es) registered in {REGISTRY}, "
          f"{len(declared)} declaring [HarmonyPatch] members")
    if not problems:
        print("  ok - every patch class is registered, and every registration has a patch class")
    return problems


# --------------------------------------------------------------------------------------------
# checking


def short(name: str) -> str:
    """`PixelCrushers.GridController.DualWieldingSystem` and `DualWieldingSystem` are the same
    type to a `typeof()` with a `using` above it; the IL always carries the full name."""
    return name.rsplit(".", 1)[-1]


def resolve(types: dict, name: str) -> str | None:
    if name in types:
        return name
    hits = [k for k in types if short(k) == short(name)]
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)


def check(types: dict, targets: dict, verbose: bool) -> list[str]:
    problems = []
    all_fields = {f for t in types.values() for f in t["fields"]}
    all_methods = {m for t in types.values() for m in t["methods"]}

    print(f"  {len(types)} types parsed from the game assemblies")

    for kind, key in (("harmony", "methods"), ("fields", None), ("reflect", None)):
        for type_name, member, where in targets[kind]:
            resolved = resolve(types, type_name)
            if resolved is None:
                # Not a game type at all (UnityEngine.Object, our own classes) - not our concern.
                if verbose:
                    print(f"  --   {type_name}.{member}  ({where}) - not a game type, skipped")
                continue
            t = types[resolved]
            ok = member in t["methods"] or member in t["fields"]
            if ok:
                if verbose:
                    print(f"  ok   {resolved}.{member}  ({where})")
            else:
                problems.append(f"{kind.upper()} {resolved}.{member} does not exist  ({where})")

    for kind, member in targets["loose"]:
        pool = all_methods if kind == "Method" else all_fields
        if member in pool:
            if verbose:
                print(f"  any  Traverse .{kind}(\"{member}\") - exists somewhere")
        elif member in targets["optional"]:
            if verbose:
                print(f"  opt  Traverse .{kind}(\"{member}\") - absent, and guarded by *Exists()")
        else:
            problems.append(f"TRAVERSE .{kind}(\"{member}\") exists on no type in the assembly")
    return problems


# --------------------------------------------------------------------------------------------
# the §46 AI audit, statically
#
# `code/README.md` used to describe this as two awk/grep commands to run by hand. Doing it by
# hand is exactly what does not happen under time pressure, and it is the one part of the mod a
# game update can break **silently** - `EnemyAiAudit` catches renamed fields at runtime but
# cannot see a `case` appearing or disappearing, because that is IL.


def ai_audit(il_by_assembly: list[str]) -> None:
    il = "\n".join(il_by_assembly)

    print("\nstate machines - which states have no `case` in UpdateStateMachine")
    print("  (a non-Dead state with no handler can only be left by a coroutine -> AiStateGuard)")
    for cm in re.finditer(r"^\.class [^\n]*?(\w+)\n(?:.*?)^\} // end of class \1$", il,
                          re.S | re.M):
        cls, body = cm.group(1), cm.group(0)
        if "UpdateStateMachine() cil managed" not in body:
            continue
        em = re.search(r"\.class .*? AIState\b(.*?)\} // end of class AIState", body, re.S)
        if not em:
            continue
        names = {int(v, 16): n for n, v in re.findall(
            r"\.field public static literal .*? (\w+) = int32\(0x([0-9a-f]+)\)", em.group(1))}
        um = re.search(r"UpdateStateMachine\(\) cil managed(.*?)end of method", body, re.S)
        sw = re.search(r"switch\s*\(\s*(.*?)\)", um.group(1), re.S)
        if not sw:
            continue
        targets = [x.strip() for x in sw.group(1).replace("\n", " ").split(",")]
        unhandled = []
        for i, tgt in enumerate(targets):
            seg = re.search(re.escape(tgt) + r":(.{0,200})", um.group(1), re.S)
            if not re.search(r"call\s+instance void \w+::Handle\w+", seg.group(1) if seg else ""):
                unhandled.append(names.get(i, f"?{i}"))
        risky = [u for u in unhandled if u != "Dead"]
        flag = "   <-- needs an AiStateGuard entry" if risky else ""
        print(f"  {cls:24} unhandled: {', '.join(unhandled) or 'none':32}{flag}")

    print("\nGrabScreen.StartGrab callers - does each re-test IsGrabbed afterwards?")
    print("  (a caller that does not commits state to grabs the game refuses -> EnemyGrabGate)")
    lines = il.split("\n")
    seen = set()
    for i, line in enumerate(lines):
        if "GrabScreen::StartGrab" not in line or "call" not in line:
            continue
        checks = "get_IsGrabbed" in "\n".join(lines[i:i + 25])
        name = "?"
        for j in range(i, min(i + 400, len(lines))):
            mm = re.search(r"end of method (\S+::\S+)", lines[j])
            if mm:
                name = mm.group(1)
                break
        if name in seen:
            continue
        seen.add(name)
        print(f"  {'ok  ' if checks else 'GAP '} {name}")


# --------------------------------------------------------------------------------------------
# heat vs 0: every place vanilla assumes heat can reach exactly zero

# The horny lock puts a *floor* under heat, so `currentHeat == 0` becomes unreachable and every
# vanilla test written against it changes meaning (CHANGELOG §11, §31; `learnings/
# grab-and-ai-mechanics.md`, "A lock floor breaks every `heat == 0` test vanilla has"). Both known
# cases were found by tripping over the symptom - an animation looping - rather than by looking,
# so this lists them all at once and names the verdict for each. A site that is not in this table
# is one nobody has reviewed, and it prints as UNREVIEWED.
HEAT_ZERO_REVIEWED = {
    "GrabScreen::HandleHeatBuildup":
        "§31 - gates heatFullyCooled; patched, ends the cum at the lock floor",
    "PlayerStats::HandleOverheatingStates":
        "§11 - clears hasBeenOverheated only at 0; ClearOverheatAtFloor does it at the floor",
    "PlayerStats::get_CanPerformActions":
        "reached only while hasBeenOverheated - covered by ClearOverheatAtFloor (§11)",
    "PlayerStats::get_CanDash":
        "reached only while hasBeenOverheated - covered by ClearOverheatAtFloor (§11)",
    "PlayerStats::CanAttackNow":
        "reached only while hasBeenOverheated - covered by ClearOverheatAtFloor (§11)",
    "PlayerStats::IsAttackLocked":
        "reached only while hasBeenOverheated - covered by ClearOverheatAtFloor (§11)",
    "PlayerStats::CalculateTotalMovementMultiplier":
        "reached only while hasBeenOverheated - covered by ClearOverheatAtFloor (§11)",
    "PlayerStats::HandleHeatCooldown":
        "benign - `heat > 0` only gates the cooldown tick, which CoolHeat's clamp re-floors",
    "PlayerStats::UpdateAnimationBools":
        "benign - sets the animator's HasAnyHeat, and at the floor the player does have heat",
    "PlayerStats::OnValidate":
        "editor-only - clamps the inspector value, never runs in a build",
}

# `currentHeat` and `CurrentHeat` both, plus maxHeat: a test against the *cap* is the same
# mistake at the other end (GrappleScreenobject::CheckTrioGrabOverflow fires at exactly MaxHeat,
# which is why GetFullLockHeat parks a full lock one point below it).
HEAT_LOAD = re.compile(r"(?:callvirt|call)\s+instance float32 \S*PlayerStats::get_(?:CurrentHeat|MaxHeat)\(\)"
                       r"|ldfld\s+float32 \S*::(?:currentHeat|maxHeat)\b")
HEAT_ZERO = re.compile(r"ldc\.r4\s+0\.0\b")
HEAT_CMP = re.compile(r"^\s*IL_[0-9a-f]+:\s+(?:ble|bge|blt|bgt|beq|bne\.un|ceq|clt|cgt)")
IL_INSTR = re.compile(r"^\s*IL_[0-9a-f]+:")


def heat_audit(il_by_assembly: list[str]) -> list[str]:
    print("\nheat vs 0 - every vanilla test a lock floor makes unreachable")
    print("  (the floor is this mod's zero; see CHANGELOG §11 and §31)")
    lines = "\n".join(il_by_assembly).split("\n")

    found: dict[str, None] = {}
    start = None
    for i, line in enumerate(lines):
        if re.match(r"^\s*\.method\b", line):
            start = i
        end = re.match(r"^\s*\}\s*//\s*end of method\s+(\S+)", line)
        if not end or start is None:
            continue
        body = [b for b in lines[start:i + 1] if IL_INSTR.match(b)]
        start = None
        for j, instr in enumerate(body):
            nxt = body[j + 1:j + 3]
            if len(nxt) < 2 or not HEAT_CMP.match(nxt[1]):
                continue
            # either order: load the heat then push 0, or push 0 then load the heat
            if (HEAT_LOAD.search(instr) and HEAT_ZERO.search(nxt[0])) or \
               (HEAT_ZERO.search(instr) and HEAT_LOAD.search(nxt[0])):
                found[end.group(1)] = None

    problems = []
    for name in found:
        verdict = HEAT_ZERO_REVIEWED.get(name)
        if verdict:
            print(f"  ok   {name:46} {verdict}")
        else:
            print(f"  NEW  {name:46} UNREVIEWED - does the lock floor change what this means?")
            problems.append(f"{name} tests heat against 0 and is not in HEAT_ZERO_REVIEWED")
    for name in HEAT_ZERO_REVIEWED:
        if name not in found:
            print(f"  gone {name:46} reviewed, but this build no longer has the test")
    return problems


def raw_il(managed: Path) -> list[str]:
    out = []
    for name in ASSEMBLIES:
        r = subprocess.run(["ikdasm", str(managed / name)], capture_output=True, text=True)
        out.append(r.stdout)
    return out


# --------------------------------------------------------------------------------------------


def managed_dir(game: str) -> Path:
    base = Path(game)
    if not base.is_absolute():
        base = ROOT / game
    hits = sorted(d for d in base.glob("*_Data") if d.is_dir())
    if not hits:
        fail(f"no *_Data folder under {base}")
    return hits[0] / "Managed"


def compare(a: dict, b: dict, label_a: str, label_b: str) -> None:
    """Type- and member-level diff, restricted to types the mod actually names."""
    named = set()
    t = read_source()
    for type_name, _, _ in t["harmony"] + t["fields"]:
        named.add(short(type_name))

    print(f"\nmembers gained/lost on the {len(named)} types the mod names "
          f"({label_a} -> {label_b}):")
    by_short_a = {short(k): v for k, v in a.items()}
    by_short_b = {short(k): v for k, v in b.items()}
    quiet = True
    for name in sorted(named):
        ta, tb = by_short_a.get(name), by_short_b.get(name)
        if ta is None and tb is None:
            continue                       # not a game type at all (UnityEngine.Object)
        if ta is None or tb is None:
            print(f"  {name}: {'ADDED' if ta is None else 'REMOVED'}")
            quiet = False
            continue
        for what in ("methods", "fields"):
            gone = sorted(ta[what] - tb[what])
            new = sorted(tb[what] - ta[what])
            gone = [g for g in gone if not g.startswith("<")]
            new = [n for n in new if not n.startswith("<")]
            if gone or new:
                quiet = False
                print(f"  {name} {what}:")
                for g in gone:
                    print(f"      - {g}")
                for n in new:
                    print(f"      + {n}")
    if quiet:
        print("  nothing changed on any type the mod names")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--game", default="game-windows", help="game install to audit")
    ap.add_argument("--compare", metavar="GAME",
                    help="also diff the mod's types against this other install")
    ap.add_argument("-v", "--verbose", action="store_true", help="list every target")
    ap.add_argument("--ai", action="store_true",
                    help="also redo the §46 AI audit: switch coverage and StartGrab callers")
    ap.add_argument("--heat", action="store_true",
                    help="also list every vanilla `heat == 0` test the lock floor makes unreachable")
    args = ap.parse_args()

    targets = read_source()
    print(f"mod targets: {len(targets['harmony'])} Harmony patches, "
          f"{len(targets['fields'])} AccessTools reflections, "
          f"{len(targets['reflect'])} bare typeof() reflections, "
          f"{len(targets['loose'])} untyped Traverse members")

    problems = registry_audit()

    managed = managed_dir(args.game)
    print(f"\nauditing {managed.parent.parent.name}")
    types = load_game(managed)
    problems += check(types, targets, args.verbose)

    if args.ai:
        ai_audit(raw_il(managed))

    if args.heat:
        problems += heat_audit(raw_il(managed))

    if args.compare:
        compare(load_game(managed_dir(args.compare)), types,
                Path(args.compare).name, Path(args.game).name)

    print()
    if problems:
        print(f"BROKEN - {len(problems)} target(s) the game no longer has:")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)
    print("ok - every patch target and reflected member still exists")


if __name__ == "__main__":
    main()

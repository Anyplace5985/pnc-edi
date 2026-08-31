#!/usr/bin/env python3
"""Are the format's own templates still the format?

    python3 code/exampleaudit.py

`BepInEx/custom-enemies/_example/` is the only content the release archive ships that no other
check looks at. Every gate in this project skips it deliberately and for good reasons -
`packageaudit.py` skips it because a template names a DLL that is not there and a behaviour nothing
publishes, `speedcheck.py` because its scripts have no rows, `PackageGalleryImport` and
`PackageAssemblies` because it must never load. The result was a directory that drifted four
framework versions behind the reference beside it while looking exactly as correct as the day it
was written, because nothing about a template is wrong at runtime: it never runs.

So this asks a template's own questions instead of a package's:

  - every `.example` file parses, and every key in it is a field the framework still reads;
  - **every field the framework reads appears in some template** - the check that makes the next
    `_example` gap announce itself rather than waiting to be noticed. A new manifest field is a new
    line here or a new line in a template, and a session has to choose;
  - a template that carries an `assembly` block has `file`, `module` and the current `api`, since a
    block missing any of those loads nothing, publishes nothing, binds no config switch and logs
    nothing - the one failure in this format with no symptom at all;
  - `fields[]` names an AI class the base enemy actually carries. The game's seven AI classes are
    siblings rather than a hierarchy, so a wrong one silently overrides nothing;
  - every funscript variant folder is present and inside its device's ceiling, because a player
    whose device names a missing variant gets nothing for the enemy;
  - and the directory is still inert: everything ends `.example`, and all three discovery paths in
    the plugin still skip it by name.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import speedcheck as S
import variants as V

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "BepInEx/custom-enemies/_example"
ENEMY_MODEL = ROOT / "code/customenemies/PncCustomEnemies/CustomEnemies.cs"
ASSEMBLY_MODEL = ROOT / "code/customenemies/PncCustomEnemies/PackageAssemblies.cs"
TRAP_MODEL = ROOT / "code/packages/wall-picture-trap/WallPictureTrap/WallPictureTraps.cs"
WITCH_MODEL = ROOT / "code/packages/charm-witch/CharmWitch/CharmWitchController.cs"
API_FILE = ROOT / "code/customenemies/PncCustomEnemies/PackageApi.cs"

# The three places that walk package directories. All three must skip `_example`, or a template
# renamed in place becomes a half-loaded package: registered by one path, refused a gallery or a
# config switch by another.
DISCOVERY = [
    ROOT / "code/customenemies/PncCustomEnemies/CustomEnemies.cs",
    ROOT / "code/customenemies/PncCustomEnemies/PackageGalleryImport.cs",
    ROOT / "code/customenemies/PncCustomEnemies/PackageAssemblies.cs",
]

# Which AI class each base-enemy hint's prefab actually carries. The classes are siblings - each
# extends MonoBehaviour and each declares its own `maxHealth` - so `component` has to name the one
# on this prefab and nothing else matches. `zombie` is settled by §138/§144, which established that
# no zombie prefab is a `ChargingEnemyAI` in 0.2.1, 0.3.1 or 0.3.2; `plantasha` by the shipped
# Femboy Witch package, whose SpinningEnemyAI overrides demonstrably take effect in play.
#
# Add a row when a template uses a base enemy this does not know. A hint that is absent is not
# checked rather than guessed at.
BASE_ENEMY_AI = {
    "zombie": "EnemyAI",
    "plantasha": "SpinningEnemyAI",
}

# Fields no template is expected to carry, with the reason. Everything else the framework reads has
# to appear somewhere in `_example/`, or this fails.
NOT_TEMPLATED = {
    # `renderer` is `null` in the one template that has a spriteVisual block, which is the value
    # that means "pick the enemy's own renderer" and is what a package normally wants.
    ("CustomEnemySpriteVisual", "renderer"): "shown as null, its normal value",
}


def csharp_fields(path: Path, cls: str) -> list[str]:
    """The public field names of one `[Serializable]` C# model, read out of the source.

    A regex rather than a parser, on the same reasoning as `packageaudit.py`: this has to work on a
    machine with no game and no build, and every one of these models is a flat list of public
    fields by construction - JsonUtility cannot deserialize anything else.
    """
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"class {re.escape(cls)}\b[^{{]*{{(.*?)\n}}", text, re.S)
    if not match:
        sys.exit(f"exampleaudit: no class {cls} in {path.relative_to(ROOT)}")
    return re.findall(r"^\tpublic [\w<>\[\],. ]+? (\w+)\s*(?:=|;)", match.group(1), re.M)


def api_version() -> int:
    match = re.search(r"public const int Version = (\d+);", API_FILE.read_text(encoding="utf-8"))
    if not match:
        sys.exit(f"exampleaudit: no `public const int Version` in {API_FILE.relative_to(ROOT)}")
    return int(match.group(1))


def load(path: Path, problems: list[str]) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        problems.append(f"{path.relative_to(ROOT)}: unreadable JSON ({exc})")
        return None


def check_keys(where: str, obj: dict, known: list[str], model: str,
               problems: list[str], seen: set[tuple[str, str]]) -> None:
    """Every key in `obj` is a field of `model`, and record which fields a template exercised."""
    for key in obj:
        if key in known:
            seen.add((model, key))
        else:
            problems.append(f"{where}: `{key}` is not a field of {model} - the framework ignores "
                            f"it silently, so a template carrying it teaches a field that does "
                            f"not exist")


def main() -> int:  # noqa: C901 - one audit, one list of questions, read top to bottom
    problems: list[str] = []
    if not EXAMPLE.is_dir():
        sys.exit(f"exampleaudit: no {EXAMPLE.relative_to(ROOT)}")

    models = {
        "CustomEnemyManifest": csharp_fields(ENEMY_MODEL, "CustomEnemyManifest"),
        "CustomEnemyGalleryVideos": csharp_fields(ENEMY_MODEL, "CustomEnemyGalleryVideos"),
        "CustomEnemySpriteVisual": csharp_fields(ENEMY_MODEL, "CustomEnemySpriteVisual"),
        "CustomEnemySpriteAnimation": csharp_fields(ENEMY_MODEL, "CustomEnemySpriteAnimation"),
        "CustomEnemyScene": csharp_fields(ENEMY_MODEL, "CustomEnemyScene"),
        "CustomEnemyField": csharp_fields(ENEMY_MODEL, "CustomEnemyField"),
        "PackageAssemblyDeclaration": csharp_fields(ASSEMBLY_MODEL, "PackageAssemblyDeclaration"),
        "WallPictureTrapManifest": csharp_fields(TRAP_MODEL, "WallPictureTrapManifest"),
        "WallPictureTrapAnimation": csharp_fields(TRAP_MODEL, "WallPictureTrapAnimation"),
    }
    # A behaviour's tuning block is the behaviour's own vocabulary, not the framework's. Only the
    # ones this repo ships can be checked, and only for the template that asks for them by name.
    behaviour_models = {"charm-witch": csharp_fields(WITCH_MODEL, "CharmWitchSettings")}

    seen: set[tuple[str, str]] = set()
    version = api_version()
    manifests = sorted(EXAMPLE.glob("*.json.example"))
    if not manifests:
        problems.append(f"{EXAMPLE.relative_to(ROOT)}: no manifest templates at all")

    for path in manifests:
        manifest = load(path, problems)
        if manifest is None:
            continue
        where = str(path.relative_to(ROOT))
        trap = "animations" in manifest and "scenes" not in manifest
        top = "WallPictureTrapManifest" if trap else "CustomEnemyManifest"
        # `assembly` is read by the loader from any manifest kind, so it is legal on both models
        # and belongs to neither's field list; a behaviour's tuning block is keyed by the
        # behaviour's own name and is checked against that behaviour's settings model below.
        skip = {"assembly", str(manifest.get("behaviour") or "")}
        check_keys(where, {k: v for k, v in manifest.items() if k not in skip},
                   models[top], top, problems, seen)

        for key, model in (("spriteVisual", "CustomEnemySpriteVisual"),
                           ("galleryVideos", "CustomEnemyGalleryVideos")):
            block = manifest.get(key)
            if isinstance(block, dict):
                check_keys(f"{where} {key}", block, models[model], model, problems, seen)
                for animation in (block.get("animations") or []):
                    check_keys(f"{where} {key}.animations", animation,
                               models["CustomEnemySpriteAnimation"],
                               "CustomEnemySpriteAnimation", problems, seen)

        for scene in manifest.get("scenes") or []:
            check_keys(f"{where} scenes", scene, models["CustomEnemyScene"],
                       "CustomEnemyScene", problems, seen)
        for stage in (manifest.get("animations") or []) if trap else []:
            check_keys(f"{where} animations", stage, models["WallPictureTrapAnimation"],
                       "WallPictureTrapAnimation", problems, seen)
        for override in manifest.get("fields") or []:
            check_keys(f"{where} fields", override, models["CustomEnemyField"],
                       "CustomEnemyField", problems, seen)
            component = str(override.get("component") or "")
            expected = BASE_ENEMY_AI.get(str(manifest.get("baseEnemy") or "").lower())
            if expected and component != expected:
                problems.append(
                    f"{where}: overrides {component}.{override.get('field')} on base enemy "
                    f"{manifest.get('baseEnemy')!r}, which carries {expected}. The AI classes are "
                    f"siblings, not a hierarchy, so this matches no component and only logs a "
                    f"warning - the template would teach an override that does nothing")

        behaviour = str(manifest.get("behaviour") or "").strip()
        if behaviour:
            block = manifest.get(behaviour)
            if not isinstance(block, dict):
                problems.append(f"{where}: asks for behaviour {behaviour!r} and has no "
                                f"{behaviour!r} block to tune it")
            elif behaviour in behaviour_models:
                check_keys(f"{where} {behaviour}", block, behaviour_models[behaviour],
                           f"{behaviour} settings", problems, seen)

        assembly = manifest.get("assembly")
        if isinstance(assembly, dict):
            check_keys(f"{where} assembly", assembly, models["PackageAssemblyDeclaration"],
                       "PackageAssemblyDeclaration", problems, seen)
            if not str(assembly.get("file") or "").strip() or \
               not str(assembly.get("module") or "").strip():
                problems.append(f"{where}: an `assembly` block needs both `file` and `module`")
            if assembly.get("api") != version:
                problems.append(f"{where}: declares api {assembly.get('api')!r}, this framework "
                                f"speaks {version} - the loader refuses a mismatch")
        elif trap:
            problems.append(f"{where}: a wall trap is a kind the framework does not know, so it "
                            f"exists only because its own assembly implements it - without an "
                            f"`assembly` block a copy of this template loads nothing, publishes "
                            f"nothing, binds no switch and logs nothing")

    # Coverage: every field the framework reads is shown somewhere.
    for model, fields in models.items():
        for field in fields:
            if (model, field) in seen or (model, field) in NOT_TEMPLATED:
                continue
            problems.append(f"no template uses {model}.{field} - a field the framework reads and "
                            f"`_example/` does not show. Add it to a template, or add it to "
                            f"NOT_TEMPLATED in this file with the reason")

    # Funscripts: every variant, the same stems, inside the ceiling.
    scripts = EXAMPLE / "funscripts"
    wanted = ["handy2pro"] + list(V.VARIANTS)
    stems: dict[str, set[str]] = {}
    for variant in wanted:
        directory = scripts / variant
        if not directory.is_dir():
            problems.append(f"{EXAMPLE.relative_to(ROOT)}/funscripts/{variant}/ is missing - a "
                            f"player whose device names this variant gets nothing for the enemy, "
                            f"so a template that ships one folder teaches the parity failure")
            continue
        stems[variant] = {p.name.split(".")[0] for p in directory.glob("*.funscript.example")}
        cap = V.VARIANTS[variant]["hard"] if variant in V.VARIANTS else S.limit("handy2pro_oc")
        for path in sorted(directory.glob("*.funscript.example")):
            doc = load(path, problems)
            if doc is None:
                continue
            actions = doc.get("actions") or []
            for a, b in zip(actions, actions[1:]):
                gap = b["at"] - a["at"]
                if gap <= 0:
                    problems.append(f"{path.relative_to(ROOT)}: timestamps do not advance at "
                                    f"{a['at']} ms")
                    continue
                speed = abs(b["pos"] - a["pos"]) / gap * 1000.0
                if speed > cap:
                    problems.append(f"{path.relative_to(ROOT)}: {speed:.0f} units/s at {a['at']} "
                                    f"ms is over this variant's {cap:.0f}")
    if len(set(map(frozenset, stems.values()))) > 1:
        problems.append(f"the variant folders under {EXAMPLE.relative_to(ROOT)}/funscripts/ do not "
                        f"hold the same scripts: "
                        f"{ {k: sorted(v) for k, v in stems.items()} }")

    # Still inert, both ways.
    shipped = [p for p in sorted(EXAMPLE.rglob("*")) if p.is_file()]
    for path in shipped:
        if path.suffix != ".example" and path.name != "README.md":
            problems.append(f"{path.relative_to(ROOT)} does not end `.example` - it would be "
                            f"discovered as a real package's file")
    for source in DISCOVERY:
        # The literal, not the substring: `_exampleX` contains `_example` and would skip nothing.
        if not re.search(r'"_example"', source.read_text(encoding="utf-8")):
            problems.append(f"{source.relative_to(ROOT)} walks package directories and no longer "
                            f"skips `_example` - a template renamed in place would half-load")
    # Every file here goes into the mod archive, and `release.py` builds that from the working
    # tree - so a template `.gitignore` excludes ships to players and reaches no clone, and every
    # other check in this repo passes either way. That is not hypothetical: the package rules name
    # back `*.json`, `SOURCE.txt` and `funscripts/**/*.funscript`, and a template matches none of
    # the three, so until §180 the only tracked templates were the ones that predated the rule.
    ignored = subprocess.run(["git", "check-ignore", "--stdin"], cwd=ROOT, text=True,
                             input="\n".join(str(f.relative_to(ROOT)) for f in shipped),
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    # 0 = something is ignored, 1 = nothing is, anything else = no git or no repo, so do not judge.
    if ignored.returncode == 0:
        for line in ignored.stdout.split():
            problems.append(f"{line} is excluded by .gitignore - it ships in the release archive "
                            f"and would reach no clone, and no other check would notice")

    if not (EXAMPLE / "SOURCE.txt.example").is_file():
        problems.append(f"{EXAMPLE.relative_to(ROOT)}/SOURCE.txt.example is missing - every "
                        f"shipped package carries a SOURCE.txt and the template set has to show one")

    if problems:
        print(f"exampleaudit: {len(problems)} problem(s) in {len(manifests)} template(s)")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print(f"exampleaudit: {len(manifests)} template(s) ok, "
          f"{len(seen)} manifest field(s) shown, api {version}, "
          f"variants {', '.join(wanted)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

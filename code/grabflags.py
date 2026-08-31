#!/usr/bin/env python3
"""Which prefabs set the two grab flags that decide who owns an enemy across its own scene.

    .venv/bin/python code/grabflags.py
    PNC_GAME_DIR="/path/to/your/PNC 0.2.1 install" .venv/bin/python code/grabflags.py

Two serialized `EnemyAI` fields decide what happens to an enemy while its grab screen is up, and
the mod's whole stand-down (§73) hangs on the first of them:

    hideInsteadOfDestroyOnGrab   vanilla hides and restores the enemy itself, so `PncEdi` arms
                                 none of its keep-alive for that prefab
    preserveHealthDuringGrab     the enemy comes back at the health it walked in with

They are prefab data, not code, so the only way to know who sets them is to read the assets. On
0.3.1 exactly one component sets either, and it sets both:

    Blinded Beast   EnemyAI   hide=1 preserveHealth=1

That pairing is why one check on the deferred path was retired rather than deferred (§126).
`EnemyAI.EndGrabHidden` tests `preserveHealthDuringGrab` *first*, so its `remainingHealth <= 0`
branch - the one that kills an enemy that died during its own grab - cannot run for the only enemy
that reaches the method. Re-run this rather than re-reading the C# if a later build looks like it
changed: a beast with the second flag cleared, or a new prefab with the first one set, brings that
branch back to life.

On 0.2.1 nothing sets either flag - the mechanic did not exist yet - and the tree generator
prints one `Error generating tree nodes` for `BrawlerEnemyAI`, which that build does not have. Both
are the right answers, not failures.

An instrument, not a check - it is deliberately not in `code/check.py`. Needs UnityPy plus
TypeTreeGeneratorAPI, because MonoBehaviour fields are not in the shipped type trees:

    python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt
"""
import UnityPy, os, sys, struct
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

import pncpaths

D = pncpaths.game_data_dir("grabflags")

# Every AI class the mod knows about - `EnemyAiTypes.All` in the plugin. A class that never
# declared either field simply reads None below, which is the same answer as False for this.
AI_CLASSES = ("EnemyAI", "ChargingEnemyAI", "SpinningEnemyAI", "ProjectileEnemyAI",
              "DragonEnemyAI", "ProximityDragonEnemyAI", "BrawlerEnemyAI")


def to_upy_tree(flat):
    """The generator returns its own flat node objects; UnityPy wants its own nested ones."""
    root, stack = None, []
    for n in flat:
        node = TypeTreeNode(m_Level=n.m_Level, m_Type=n.m_Type, m_Name=n.m_Name,
                            m_ByteSize=-1, m_Version=1, m_MetaFlag=n.m_MetaFlag, m_Children=[])
        if n.m_Level == 0:
            root, stack = node, [node]
            continue
        while len(stack) > n.m_Level:
            stack.pop()
        stack[-1].m_Children.append(node)
        stack.append(node)
    return root


# Generate every tree up front and never ask for a class outside Assembly-CSharp: a miss leaves
# the native generator in a state where the next call segfaults the interpreter.
gen = TypeTreeGenerator("6000.3.11f1")
gen.load_local_dll_folder(os.path.join(D, "Managed"))
TREES = {}
for cls in AI_CLASSES:
    try:
        TREES[cls] = to_upy_tree(gen.get_nodes("Assembly-CSharp.dll", cls))
    except Exception:
        pass  # 0.2.1 has no BrawlerEnemyAI; a class this build lacks is not an error
del gen

FILES = sorted(f for f in os.listdir(D)
               if f.startswith(("level", "sharedassets", "resources.assets", "globalgamemanagers.assets"))
               and not f.endswith((".resS", ".resource")))
env = UnityPy.load(*[os.path.join(D, f) for f in FILES])

script_name = {}
for obj in env.objects:
    if obj.type.name == "MonoScript":
        try:
            script_name[(obj.assets_file.name, obj.path_id)] = obj.read_typetree().get("m_ClassName")
        except Exception:
            continue


def script_pptr(obj):
    """m_GameObject(12) + m_Enabled(1, padded to 4) then m_Script(int32 fileID, int64 pathID)."""
    try:
        return struct.unpack_from("<iq", obj.get_raw_data(), 16)
    except Exception:
        return (0, 0)


def resolve(obj, fid, pid):
    af = obj.assets_file
    if fid == 0:
        return script_name.get((af.name, pid))
    try:
        ext = os.path.basename(af.externals[fid - 1].name)
    except Exception:
        return None
    for (fname, p), v in script_name.items():
        if p == pid and os.path.basename(fname) == ext:
            return v
    return None


rows = {}
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    cls = resolve(obj, *script_pptr(obj))
    if cls not in TREES:
        continue
    try:
        d = obj.read_typetree(TREES[cls])
    except Exception:
        continue
    go = obj.assets_file.objects.get((d.get("m_GameObject") or {}).get("m_PathID", 0))
    try:
        name = go.read_typetree().get("m_Name") if go else "?"
    except Exception:
        name = "?"
    rows[(name, cls)] = (bool(d.get("hideInsteadOfDestroyOnGrab")),
                         bool(d.get("preserveHealthDuringGrab")))

setters = {k: v for k, v in rows.items() if any(v)}
for (name, cls), (hide, keep) in sorted(setters.items()):
    print(f"{name:28} {cls:24} hide={hide} preserveHealth={keep}")
print(f"{len(setters)} of {len(rows)} AI components set either flag; "
      f"the rest are False/False and stay on the mod's own keep-alive path", file=sys.stderr)

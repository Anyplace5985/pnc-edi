#!/usr/bin/env python3
"""Every vanilla spawner in the build, and the enemy table it rolls on.

    .venv/bin/python code/spawntables.py
    PNC_GAME_DIR="../Archive/PNC 0.2.1 Win/PNC_Data" .venv/bin/python code/spawntables.py

**There is no biome enemy list.** `EnemySpawner.GetEnemyPrefab` and `ArenaEnemySpawner`'s twin
pick uniformly from *that spawner's own* serialized `enemyData[]`, then uniformly from the chosen
`EnemyData.prefabVariants[]`. The spawn table is per-spawner scene data - authored per room - so
the only way to see it is to read the assets, which is what this does.

**An arena has a second route, and it overrides the first.** If an `ArenaEnemySpawner` carries any
valid `spawnGroups[]`, `SpawnEnemiesCoroutine` picks one `ArenaSpawnGroup` by weight and spawns
exactly its `entries[]` - one enemy per named `ArenaSpawnPoint` - and the flat `enemyData[]` table
is never rolled at all; it is only the fallback for an arena with no group. All four arenas in
0.3.1 have groups, so all four are authored encounters. This script read groups from the day it
was taught to (2026-08-24); before that it saw flat tables only, and the Blinded Beast - which is
in no flat table and in `floor 2 spawngroups/BlindedBeastMiniBoss` - looked unspawnable. See the
correction to CHANGELOG §100.

Read on 2026-08-23 against game 0.3.1: 67 of 70 spawners carry a table, all but three of them in
`sharedassets1` (Floor1). The tables are deliberately uneven - single-enemy rooms, a pure
goonshroom nest, and long lists that repeat a name to weight it - which is the composition
`Gameplay/EnemySpawnMode = pool` used to throw away and `grappler-bias` now preserves. See
CHANGELOG §99.

Needs UnityPy plus TypeTreeGeneratorAPI: MonoBehaviour fields are not in the shipped type trees,
so the trees are generated from `Managed/` at run time.

    python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt
"""
import UnityPy, os, sys, struct, collections
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

import pncpaths

# This used to read `PNC_GAME_DIR` itself, defaulting to a working-directory-relative
# `game-linux/PNC 0.3.2_Data` - so it wanted the `_Data` folder where every other tool wants the
# install above it, and it only ran from the repo root. `pncpaths.game_data_dir` accepts either
# spelling, so the usage line above and PROJECT.md's both still work.
D = pncpaths.game_data_dir("spawntables")

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
TREES = {c: to_upy_tree(gen.get_nodes("Assembly-CSharp.dll", c))
         for c in ("EnemySpawner", "ArenaEnemySpawner", "EnemyData", "ArenaSpawnGroup")}
del gen

FILES = sorted(f for f in os.listdir(D)
               if f.startswith(("level", "sharedassets", "resources.assets", "globalgamemanagers.assets"))
               and not f.endswith((".resS", ".resource")))
env = UnityPy.load(*[os.path.join(D, f) for f in FILES])

script_name = {}
for obj in env.objects:
    if obj.type.name == "MonoScript":
        try: d = obj.read_typetree()
        except Exception: continue
        script_name[(obj.assets_file.name, obj.path_id)] = d.get("m_ClassName")

def script_pptr(obj):
    """m_GameObject(12) + m_Enabled(1, padded to 4) then m_Script(int32 fileID, int64 pathID)."""
    try:
        raw = obj.get_raw_data()
        return struct.unpack_from("<iq", raw, 16)
    except Exception:
        return (0, 0)

def resolve(obj, fid, pid, table):
    af = obj.assets_file
    if fid == 0:
        return table.get((af.name, pid))
    try: ext = os.path.basename(af.externals[fid - 1].name)
    except Exception: return None
    for (fname, p), v in table.items():
        if p == pid and os.path.basename(fname) == ext:
            return v
    return None

SPAWNERS = {"EnemySpawner", "ArenaEnemySpawner"}
hits, enemydata, groupdata = [], {}, {}
for obj in env.objects:
    if obj.type.name != "MonoBehaviour":
        continue
    fid, pid = script_pptr(obj)
    cls = resolve(obj, fid, pid, script_name)
    if cls in SPAWNERS:
        hits.append((obj, cls))
    elif cls == "EnemyData":
        enemydata[(obj.assets_file.name, obj.path_id)] = obj
    elif cls == "ArenaSpawnGroup":
        groupdata[(obj.assets_file.name, obj.path_id)] = obj

print(f"spawner components: {len(hits)}   EnemyData assets: {len(enemydata)}   "
      f"ArenaSpawnGroup assets: {len(groupdata)}", file=sys.stderr)

ed_cache = {}
def read_enemydata(key):
    if key in ed_cache: return ed_cache[key]
    obj = enemydata[key]
    d = obj.read_typetree(TREES["EnemyData"])
    prefabs = []
    for p in (d.get("prefabVariants") or []):
        po = obj.assets_file.objects.get(p.get("m_PathID"))
        if po is None and p.get("m_FileID"):
            try:
                ext = os.path.basename(obj.assets_file.externals[p["m_FileID"] - 1].name)
                for f in env.files.values():
                    if os.path.basename(getattr(f, "name", "")) == ext:
                        po = f.objects.get(p["m_PathID"]); break
            except Exception: pass
        try: prefabs.append(po.read_typetree().get("m_Name") if po else "?")
        except Exception: prefabs.append("?")
    ed_cache[key] = (d.get("enemyName"), prefabs)
    return ed_cache[key]

edkeys = {k: read_enemydata(k) for k in enemydata}

def pptr_object(obj, p):
    """Follow a PPtr from `obj`'s file, crossing into an external file when m_FileID is set."""
    if not p or not p.get("m_PathID"):
        return None
    if not p.get("m_FileID"):
        return obj.assets_file.objects.get(p["m_PathID"])
    try:
        ext = os.path.basename(obj.assets_file.externals[p["m_FileID"] - 1].name)
    except Exception:
        return None
    for f in env.files.values():
        if os.path.basename(getattr(f, "name", "")) == ext:
            return f.objects.get(p["m_PathID"])
    return None

# An arena with spawnGroups ignores its own enemyData[] table entirely: SpawnEnemiesCoroutine
# picks one group by weight and SpawnGroupCoroutine spawns exactly that group's entries, one per
# named ArenaSpawnPoint. So a group is the only way some enemies reach the game at all - the
# Blinded Beast is in no flat spawner table but is in `floor 2 spawngroups/BlindedBeastMiniBoss`.
# A pinned prefab need not carry an EnemyData reference at all (`Plant Duo` pins two Plantasha
# variants and leaves `enemy` null). The prefab is still one of some EnemyData's variants, so the
# census can name the enemy by looking the prefab up in the variant lists rather than inventing a
# species out of the prefab name.
variant_owner = {v: n for n, pf in edkeys.values() for v in pf if n}

grp_cache = {}
def read_group(key):
    if key in grp_cache: return grp_cache[key]
    obj = groupdata[key]
    d = obj.read_typetree(TREES["ArenaSpawnGroup"])
    name = (d.get("groupName") or "").strip()
    if not name:
        name = d.get("m_Name") or "?"
    entries = []
    for e in (d.get("entries") or []):
        v = resolve(obj, (e.get("enemy") or {}).get("m_FileID", 0),
                    (e.get("enemy") or {}).get("m_PathID", 0), edkeys)
        ov = pptr_object(obj, e.get("prefabOverride"))
        pinned = None
        if ov is not None:
            try: pinned = ov.read_typetree().get("m_Name", "?")
            except Exception: pinned = "?"
        # The census counts the *enemy*, not the prefab: a pinned variant is still that enemy, and
        # keying it by prefab name would invent a species (`Plantasha_Enemy ALT1`) that appears in
        # no table and so reads as group-only. ResolvePrefab prefers the override; an entry with a
        # pin and no EnemyData is the only case where the prefab name is all there is.
        key = v[0] if v else variant_owner.get(pinned, pinned or "<empty>")
        who = key if pinned is None else f"{key} (pinned {pinned})"
        entries.append((who, key, e.get("spawnPointId") or ""))
    grp_cache[key] = (name, entries)
    return grp_cache[key]

grpkeys = {k: read_group(k) for k in groupdata}
print("\n=== ArenaSpawnGroup assets in the build ===")
for k, (n, entries) in sorted(grpkeys.items(), key=lambda kv: str(kv[1][0])):
    body = ", ".join(f"{who}@{pt}" for who, _, pt in entries) if entries else "(no entries)"
    print(f"  {n:<28} {len(entries):2d} entries: {body}")
print("\n=== EnemyData assets in the build ===")
for k, (n, pf) in sorted(edkeys.items(), key=lambda kv: str(kv[1][0])):
    print(f"  {n:<22} variants: {', '.join(pf) if pf else '(none)'}")

rows = []
for obj, cls in hits:
    d = obj.read_typetree(TREES[cls])
    owner = "?"
    try:
        go = obj.assets_file.objects.get((d.get("m_GameObject") or {}).get("m_PathID"))
        if go: owner = go.read_typetree().get("m_Name", "?")
    except Exception: pass
    table = []
    for p in (d.get("enemyData") or []):
        v = resolve(obj, p.get("m_FileID", 0), p.get("m_PathID", 0), edkeys)
        table.append(v[0] if v else "?")
    groups = []
    for g in (d.get("spawnGroups") or []):
        v = resolve(obj, (g.get("group") or {}).get("m_FileID", 0),
                    (g.get("group") or {}).get("m_PathID", 0), grpkeys)
        groups.append((v[0] if v else "?", v[1] if v else [],
                       g.get("weight", 0.0), bool(g.get("enabled"))))
    rows.append((obj.assets_file.name, cls, owner, table,
                 d.get("enemiesToSpawn"), len(d.get("spawnPositions") or []), groups))

print("\n=== every spawner and the table it rolls on ===")
for f, cls, owner, table, n, pts, groups in sorted(rows, key=lambda r: (r[0], str(r[2]))):
    print(f"  [{f:<22}] {cls:<18} {str(owner):<28} spawns {str(n):>3} of {pts:>3} pts -> {', '.join(table) if table else '(empty)'}")
    for gname, gentries, w, en in groups:
        who = ", ".join(e[0] for e in gentries) if gentries else "(no entries)"
        print(f"      {'group' if en else 'group (disabled)':<18} {gname:<28} weight {w:g} -> {who}")

print("\n=== how often each enemy appears in a spawner table ===")
c = collections.Counter(e for r in rows for e in r[3])
for e, n in c.most_common():
    print(f"  {n:4d}  {e}")
print(f"\n  spawners with a table: {sum(1 for r in rows if r[3])} / {len(rows)}")

print("\n=== how often each enemy appears in an arena spawn group ===")
gc = collections.Counter(e[1] for r in rows for gname, gentries, w, en in r[6] if en
                         for e in gentries)
for e, n in gc.most_common():
    print(f"  {n:4d}  {e}")
print(f"  arenas with at least one enabled group: "
      f"{sum(1 for r in rows if any(g[3] for g in r[6]))} / "
      f"{sum(1 for r in rows if r[1] == 'ArenaEnemySpawner')} arena spawner(s)")

# The census is only honest if it counts both routes. An enemy reachable only through a group is
# invisible to the flat-table count, which is what made "the Blinded Beast can never spawn" look
# true (see TODO, and the correction to CHANGELOG §100).
only_group = sorted(set(gc) - set(c))
only_table = sorted(set(c) - set(gc))
print("\n=== reachable by one route only ===")
print(f"  group only: {', '.join(only_group) if only_group else '(none)'}")
print(f"  table only: {', '.join(only_table) if only_table else '(none)'}")
unused = sorted({n for n, _ in edkeys.values() if n} - set(c) - set(gc))
print(f"  in no spawner table and no group: {', '.join(unused) if unused else '(none)'}")

# SpawnEnemiesCoroutine does `int spawnCount = availablePositions.Count`, so the enemy count is
# one per spawn point that survives the proximity / line-of-sight / occupancy filters.
# `enemiesToSpawn` gates nothing: ValidateSetup only clamps it against itself. So the number that
# matters is len(spawnPositions), and enemiesToSpawn is a red herring left in the inspector.
live = [r for r in rows if r[3]]
pts = collections.Counter(r[5] for r in live)
print("\n=== vanilla spawn POINTS per spawner (= enemies, one each) ===")
for n in sorted(pts):
    print(f"  {n:2d} points: {pts[n]:3d} spawner(s)")
tot = sum(r[5] for r in live)
print(f"  mean {tot / len(live):.2f} per spawner over {len(live)} spawners; {tot} total before filtering")
# A group arena's count is not len(spawnPositions) at all - it is the number of valid entries in
# whichever group was picked, so it is a range across that arena's groups rather than one number.
garenas = [r for r in rows if any(g[3] for g in r[6])]
if garenas:
    print("\n=== arena spawn GROUPS: enemies per encounter ===")
    for r in sorted(garenas, key=lambda r: (r[0], str(r[2]))):
        sizes = {g[0]: len(g[1]) for g in r[6] if g[3]}
        body = ", ".join(f"{n} ({k})" for k, n in sizes.items())
        print(f"  [{r[0]:<22}] {str(r[2]):<28} {min(sizes.values())}-{max(sizes.values())} "
              f"enemies: {body}")

ets = collections.Counter(r[4] for r in live)
print("\n  (enemiesToSpawn, unused by the spawn loop: " +
      ", ".join(f"{k}x{v}" for k, v in sorted(ets.items(), key=lambda kv: (kv[0] is None, kv[0]))) + ")")

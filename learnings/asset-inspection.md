# Reading the game's assets and assemblies

Getting facts out of the shipped files without launching the game.

**Read this when:** you need a clip, a scene object, a layer name or an IL fact

**Keywords:** UnityPy, typetree, MonoBehaviour, PPtr, m_FileID, AnimationClip, ikdasm, monodis, sharedassets, globalgamemanagers, single-file bundle, Edi.Core

---

**A clip can be longer than its own frames, and a clip can animate more than one thing.** Two of
the 51 (`GooperGrabScreen`, `GooperGrabScreenCum`) carry a second PPtr curve — a `Goop_overlay`
drip layer. `m_StopTime` is set by the *longest* curve, so the cum clip is 1500 ms while its body
runs 14 frames = 1400 and then holds. Frame *k* is on screen at `k/fps`, **never** at `k*dur/n`;
those agree for the other 49 clips, which is precisely why assuming the second form went unnoticed
until a scene refused to correlate. Splitting curves cannot be done by sprite name — a single
curve happily spans two atlas pages (`…Sheet_1_0..21` then `…Sheet_3_0..10`, restarting at `_0`) —
but a real sequence never counts backwards, which is the cut `_first_pptr_curve` makes (§48).

**A sprite's on-screen position is in `m_RD.textureRectOffset`, not in where its pixels start.**
The pixels UnityPy hands back are the alpha-trimmed sub-rect; the sprite's actual extent is its
full `m_Rect` cell, anchored at `m_Pivot`, and `textureRectOffset` is where the trimmed pixels sit
inside that cell. **The trim is not symmetric**, so stacking the images themselves registers them
wrongly: `GhoulGrabStart`'s six frames lose 9-16 px off the left edge and `PlantashaGrab`'s vary by
10 px, while every one of them is drawn in the same place in game. The measurement tools stack
against a shared bottom-left corner and get away with it — across the scenes with a registered
proxy the *vertical* offset range is 0 px everywhere, which is why that convention has held — but
anything that produces a **picture** has to use the offsets or it shows a jitter the game does not
have. `refvideo.sprite_layout` works in pivot-relative coordinates, so it is also right for a clip
whose frames come from cells of different sizes (§88).

**A PPtr's `m_FileID` is part of its identity.** Keying a lookup on `path_id` alone across several
loaded assets files silently resolves pointers to objects in the wrong file. In `animcheck` this
happened to *help* — the overlay sprites came back as `Texture2D` and were filtered out, so the
body frames survived by accident — which is worse than failing, because it produced right answers
for a year with no reason to look. Resolve `m_FileID == 0` against the owning file and `n` against
`externals[n-1]`. **Fixed in §69, when it stopped helping**: game 0.3.1's
`BlackSerpent GrabScreen` lives in `resources.assets`, so all seven of its pointers resolved into
`sharedassets0` and the clip read as *zero frames*. Two lessons came with the fix — a guard written
for a case that cannot occur (`_first_pptr_curve` defending against a clip that never reaches it)
cost the case that does, and **every count taken through a lookup known to drop things silently is
a lower bound**: "the two Gooper clips and nothing else" was really thirteen.

**Static asset inspection beats another test round.** `UnityPy` in the repo's `.venv/` (built
from `code/requirements.txt`) reads
`sharedassets1.assets`: MonoBehaviour typetrees are unavailable without the script metadata,
but the raw field bytes parse by hand (PPtr, align, length-prefixed strings), and
`GameObject`/`Transform`/`BoxCollider` read normally. That is how the D1–D9 table — trigger
names, rooms and box sizes — was produced without launching the game.


**A guard written for a case that cannot occur costs the case that does.** `_first_pptr_curve`
cuts a multi-curve clip down to its first curve. It was distinguishing "a second object" from
"page 2 of the same atlas" by sheet name, to protect `GhoulGrabCum`, which restarts its frame
numbering partway through. But `GhoulGrabCum` declares **one** PPtr curve and the function is only
called when there is more than one - the counter-example could never reach it, and the cleverness
let one frame of the second curve through. The plain rule (cut at the first frame number that does
not increase) is correct (§69).

**Every count taken through a lookup that drops things silently is a lower bound.** The same file
claimed multi-curve clips were "the two Gooper clips and nothing else". With `m_FileID` honoured
there are **thirteen**; the others' second curves had been resolving into the wrong file and
vanishing.

**A .NET single-file app is a container, and Edi's own assemblies are readable out of it (§87).**
`Edi.exe` is a self-contained WPF build, so "read Edi rather than reverse-engineering it" looked
like it needed the GitHub source. It does not: the bundle appends a manifest, findable by its
32-byte signature, and the entries are stored **uncompressed** by default. Extract `Edi.Core.dll`
and `ikdasm` answers questions about Edi's actual behaviour the same way it answers them about the
game - which is how `Play/{name}`'s `[FromQuery] long seek` and `DeviceBase.CompletePlayback`
passing `elapsed % duration` back through it were settled instead of assumed. Recipe below.

**A MonoBehaviour's fields parse in declaration order, and the IL gives you that order.** The
serpent's hypnosis numbers came out of `resources.assets` with no typetree: dump the class with
`ikdasm`, take the `.field` lines in order (attributes between them are `Header`/`Tooltip` and
serialize nothing), then walk `get_raw_data()` past the standard prefix - `m_GameObject` PPtr,
`m_Enabled` byte, 4-byte align, `m_Script` PPtr, `m_Name` - and read them off. `bool` is one byte
followed by padding to the next 4; strings are length-prefixed and padded the same way. The
tooltips come through as readable ASCII in the IL dump and are often the best documentation the
game has.

## Recipes

```
# animator states: each AnimatorController's m_TOS is a hash -> name table
env = UnityPy.load("sharedassets0.assets", "sharedassets1.assets", "resources.assets")
d = o.read_typetree(); {s.split(".",1)[1] for h,s in d["m_TOS"] if s.startswith("Base Layer.")}

# IL, for anything that is a switch or a call site
ikdasm "game-windows/Post Nut Calamity_Data/Managed/Assembly-CSharp.dll" > /tmp/asm.il
monodis --typedef "$G/Assembly-CSharp.dll" | grep -i gallery

# Edi's own code, out of the single-file bundle: find the manifest, then walk the entries
#   sig = 8b1202b96a612038727b930214d7a03213f5b9e6efae3318ee3b2dce24b36aae
#   int64 at (sig offset - 8) is the bundle header offset
#   header: uint32 major, uint32 minor, int32 fileCount, 7-bit-length string bundleID,
#           then (major >= 2) 4 x int64 for deps/runtimeconfig + uint64 flags
#   entry:  int64 offset, int64 size, byte compressionType (+ int64 size if compressed),
#           7-bit-length string relative path
# Entries are uncompressed by default, so the slice is the DLL. Then ikdasm it.
```

`GameObject`, `Transform`, `BoxCollider`, `AnimationClip` and `AnimatorController` read via
`read_typetree()`. **MonoBehaviour does not** - script typetrees are not shipped - so parse
`get_raw_data()` by hand: `m_GameObject` PPtr (int32 fileID + int64 pathID), `m_Enabled` byte,
4-byte align, `m_Script` PPtr, `m_Name`, then the script's own fields. Strings are length-prefixed
and padded to 4 bytes. That is how the D1-D15 unlock-box table was read.

Layer names live in `*_Data/globalgamemanagers`: find `TransparentFX`, walk back to layer 0, then
read 32 length-prefixed strings.

**When the log points at an animator, read the animator, not the code.** §109's whole bug was a
space: `GoonShroom_GrabScreen` names its parameter `Max Heat` where every other grab screen names
it `MaxHeat`, and `Assembly-CSharp` contains the literal `MaxHeat` exactly once and `Max Heat` not
at all — so vanilla's `SetBool("MaxHeat", true)` was a silent no-op on that one controller and its
cum clip never played. Nothing about that is visible from C#; Unity does not warn about a parameter
that does not exist. An `AnimatorController`'s parameter and state names are in its `m_TOS` map,
which is a list of `(hash, name)` pairs — read it with UnityPy and compare the same controller
family across enemies, because the bug is only obvious as an *odd one out*:

    tos = dict(tuple(x) for x in d.get("m_TOS", []))
    print(sorted(v for v in tos.values() if "." not in v and "->" not in v))

**`Resources.FindObjectsOfTypeAll<T>()` is "everything currently in memory", not "everything in the
build".** An asset that nothing references is never loaded, so it cannot be found by any runtime
search — which is why the Blinded Beast, whose `EnemyData` exists but is listed in no spawner's
flat table, was invisible to a resolver that searched five different ways (§110). Note "flat
table": it *is* in an `ArenaSpawnGroup`, which is how the game itself spawns one (§114). One
`Resources.LoadAll<EnemyData>("")` before the scan fixes it, and costs nine assets. To find out
whether an asset is reachable that way at all, read the `ResourceManager`'s `m_Container` out of
**`globalgamemanagers`** (no `.assets` extension — it is not in `resources.assets`): it maps every
Resources path to a `PPtr`, and paths are stored lowercased.

**A census that reads one route reports everything on the other route as impossible.**
`spawntables.py` read each spawner's flat `enemyData[]` table and concluded the Blinded Beast could
never spawn. An `ArenaEnemySpawner` with any valid `spawnGroups[]` never rolls that table at all -
it picks one `ArenaSpawnGroup` by weight and spawns exactly its entries - and all four arenas in
0.3.1 have groups, so the census was reading the *fallback* path for every arena in the game
(§114). Before believing a "this can never happen" derived from assets, decompile the consumer and
check it has only one way in.

**Resolve a pinned prefab back to its `EnemyData` before counting it.** An `ArenaSpawnEntry` can
pin an exact prefab and leave its `EnemyData` reference null (`Plant Duo` does). Keyed by prefab
name, `Plantasha_Enemy` and `Plantasha_Enemy ALT1` become two species that appear in no table and
read as group-only - an invented finding on top of a real one. Every prefab is some `EnemyData`'s
variant, so a `{variant name: enemy name}` map built from the `EnemyData` assets settles it (§114).

**`ilspycmd` decompiles one vanilla class in about a second, and it is installed.**
`~/.dotnet/tools/ilspycmd -t GrabScreen "game-linux/PNC 0.3.2_Data/Managed/Assembly-CSharp.dll"`
gave the exact cum cycle — `TriggerMaxHeatAnimation` sets three flags then the bool,
`OnMaxHeatAnimationComplete` is gated on `heatFullyCooled` and clears them — which is what turned
§109 from a theory into a mechanism. `-l c` lists every class. Reach for it before reasoning about
what vanilla "probably" does; the answer is thirty seconds away.

**`strings` misses .NET string literals unless you ask for UTF-16.** Metadata names (fields, types)
are UTF-8 and show up under plain `strings`, but user string literals are UTF-16 and need
`strings -el`. A plain `strings | grep -x MaxHeat` on Assembly-CSharp returns nothing and looks
like proof the literal is absent, which is the opposite of the truth.

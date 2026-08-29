# Naming audit — how an animation becomes a funscript

Stage 1 of the resolver cleanup, 2026-08-16. **Analysis only — no behaviour was changed.**

The point of this pass was to replace guesswork with ground truth: every animator state the
game can produce, extracted statically, checked against every row in `Definitions.csv`.

## How the data was obtained

Animator state names live in each `AnimatorController`'s `m_TOS` (hash → name table), which
UnityPy reads without script metadata:

```python
env = UnityPy.load("sharedassets0.assets", "sharedassets1.assets", "resources.assets")
for o in env.objects:
    if o.type.name != "AnimatorController": continue
    d = o.read_typetree()
    states = {s.split(".",1)[1] for h,s in d["m_TOS"] if "->" not in s and s.startswith("Base Layer.")}
```

168 controllers, 72 of them with scene-relevant states.

## The resolution stack

Seven resolvers. Order matters and is not obvious:

| # | stage | match | notes |
|---|---|---|---|
| 1 | `NameRemap.BuildGallerySlug(enemyKey, state)` | — | key normalisation, prefix strip, suffix normalise |
| 2 | `InGameAliases` | exact | live gameplay only; viewer ignores it |
| 3 | `GalleryAliases` | exact | the big table |
| 4 | `GalleryRegistry.IsKnown` | exact | **passes the slug through unchanged** |
| 5 | `TryResolveByEnemy` | **greedy substring** | hardcoded per enemy; catches anything |
| — | `PeekGalleryMap.Resolve` | exact → **calls 2–5** → heuristic | for peek scenes |
| — | `DioramaGalleryMap`, `AmbientProximity`, filler maps | various | separate paths |

Stage 4 means a `Definitions.csv` row name that happens to equal a produced slug wins over the
builtin resolver. Stage 5 means anything containing an enemy name resolves *somewhere*, which
is why gaps in the table are invisible.

## Reachability: 59 of 65 rows

### Dead — nothing can dispatch these

| row | why |
|---|---|
| `Zombie_Start` | `ZombieGrabScreen` has only `ZombieGrabScreen_Cum` / `_Loop`. No Start state exists, in gameplay or the viewer (`Gallery_Zombie_GrabScreen` = Cum, Loop, Alt1Cum, Alt1Loop). |
| `ZombieAlt1_Start` | same |
| `imp_grab_start` | `Imp_Grab_Screen` = `Imp_Grab_Cum`, `Imp_Grab_Loop`. `Gallery_Imp_Grabbed` = Cum, Imp 1/2/3, Loop. No Start, and `Plugin.cs` only ever sends `imp_grab_loop` directly. |
| `gargoyle_grab` | shadowed: config alias `gargoyle_grab=Gargoyle_Grabbed` is checked at stage 3, before stage 4 could match the row. Duplicate of `Gargoyle_Grabbed` anyway — same file, same `28132..30123`. |

### Gallery viewer only, never in gameplay

`ZombieAlt1_Loop`, `ZombieAlt1_Cum`. Both zombie controllers use *identical state names*, and
`NormalizeEnemyKeyForGallery` strips `_alt1` from the key, so in-game the alt zombie produces
the base slug. Log evidence:

```
[GRAB-START] prefab='Zombie_Enemy_ALT1' key=zombie_enemy_alt1
[GRAB-INIT]  zombie_enemy_alt1/ZombieGrabScreen_Loop -> zombie_enemy_zombiegrabscreen_loop
[EDI] Play Zombie_Loop
```

Only the viewer's `Alt1Loop` / `Alt1Cum` states reach the Alt1 rows.

### Reachable only by accident

`Plantasha_Loop` — no Loop state in `Plantasha_GrabScreen` or `Gallery_Plantasha_Grabbed`. It
plays only because the *Plantasha peephole* resolves onto it (see below).

## Defects, ranked

### 1. Peek scenes resolve to grab galleries

`PeekGalleryMap.Resolve` consults `GalleryAliases` (stages 2–5) **before** its own heuristic, so
the greedy enemy matcher wins first. Observed:

```
[EDI] Play Plantasha_Loop  (alias of p3_peephole_plantasha_loop)
```

The peephole played the Plantasha grab script. `Heuristic` would have returned `peek_plant_bj`,
but never ran.

For the Gooper pillory the same trap has three overlapping causes:

- the asset is spelled **`GooperPilloary`**, the config key is `GooperPillory`, and stage 1 of
  the peek map is an *exact* match
- `GooperBJPeepHoleAnimator`'s states are named **`Peephole_Wendigo_Start/Loop/End`** —
  copy-pasted from the Wendigo peephole — so the configured alias
  `gooperpillory_peephole_gooperbj_loop` cannot match either
- stage 5 then sees "gooper" and returns `Gooper_Start`

That is TODO #11 ("Gooper diorama re-uses the normal Gooper script"). `Nun&MimicPeepHoleAnimator`
carries the same `Peephole_Wendigo_*` states, and `mimic` is tested before `nun` and `wendigo`,
so it likely lands on `Mimic_Loop`.

**Fix:** run the peek heuristic before the greedy resolver, or refuse stage 5 when the slug
contains `peep`.

### 2. The alias table and the shipped default have diverged

| | entries |
|---|---|
| `Plugin.cs` default | 265 distinct (275 with 10 duplicate keys) |
| `com.edi.pnc.cfg` in use | **133** |

The config is a strict subset — 132 aliases in the code default have never applied, because
BepInEx does not rewrite an existing key. Both the game tree and `mod/single-mod` ship the 133.

Four keys also disagree, two of them wrong:

```
imp_imp2 = Imp1     (default: imp2)
imp_imp3 = Imp1     (default: imp3)
```

The gallery viewer's `Imp 2` / `Imp 3` states play the Imp 1 script. Gameplay is unaffected —
that path uses `imp_2` / `imp_3`, which are correct.

### 2b. Where the "missing" 185 aliases actually come from

Traced 2026-08-16. They are **the author's own later additions to the code default, which no
user has ever run.**

```
v1.9.7 shipped zip   ->  com.edi.pnc.cfg carrying 130 hand-curated aliases
v2.0.8 shipped zip   ->  the identical 130, byte for byte (only the header line changed)
this install         ->  those 130, plus 3 imp entries added in an earlier session = 133
compiled DLL default ->  315
```

Confirmed against the untouched shipped binary, `code/PncEdi-v2.0.8-original.dll` (deleted in
§140, and in no commit of this repository since §143), so the 315
is not a decompilation artefact. The two lists are not related by truncation — different order
(`imp_1=Imp1` is first in the config, `imp_1=imp1` is fifth in the DLL) and different values —
so BepInEx did not generate the config from the default.

**Mechanism:** BepInEx writes a setting's default only when the key is *absent*, and preserves
the existing value otherwise. The author hand-wrote the 130-entry list into the config at or
before v1.9.7, then kept expanding the *code* default — but every release since has shipped
that same stale config beside the new DLL. The file wins, permanently.

So the compiled default is **dead documentation**: it reads like the authoritative table, it is
the obvious thing to edit, and it has no effect on any existing install. It is also why zombie,
imp and plantasha fall through to the greedy resolver — the aliases that would have handled
them properly live in the 185 nobody runs. The `Imp_Imp1/2/3=Imp1` bug likewise came from the
shipped config, not the source, where it was already correct.

### 2c. How much of the curated list is load-bearing

Simulating `TryResolveByEnemy` + the skip heuristic against all 130 shipped entries:

| | count | |
|---|---|---|
| fallback returns the same answer | **77** | redundant |
| fallback returns a *different* answer | **24** | load-bearing |
| fallback returns nothing | **29** | load-bearing |

The 53 that matter encode knowledge the substring matcher cannot have:

- **Gravy/minotaur "2" variants** (14) — `ResolveStage` detects the second scene by
  `alt`/`riding`/`ride`/`v1`, but these are keyed on a trailing `2`, so the fallback collapses
  `Start2`/`Loop2`/`Cum2`/`End2` onto the first scene's scripts.
- **`minothaur` / `4minothaur`** (16) — the game misspells minotaur in some animator states.
  The fallback tests `minotaur` and `gravy`, neither of which matches.
- **Fade and intro skips** (8) — targets of `-`. Without them the fallback plays a scene script
  over a fade, interrupting the running funscript.
- **`CumContinue` → back to the grab loop** (6) — deliberate: after the cum animation the scene
  returns to the grabbed loop, so these point at `Nun_Grab` / `Gargoyle_Grabbed`. The fallback
  sees "cum" and replays the cum script.
- **`Imp_Imp1/2/3`** (3) — the fallback's imp branch matches only exact `imp_1`/`imp1`.

**Two cleanups pull in opposite directions**, and they are mutually exclusive:

1. *Keep the fallback, drop the 77 redundant entries.* Config shrinks by 59%, but greedy
   substring matching stays in charge of **more** cases, not fewer — and that mechanism is what
   produced the peek hijack (defect 1) and the contradictory alt handling (defect 4).
2. *Delete the fallback, make every mapping explicit.* The table **grows**, but becomes
   verifiable against the extracted animator states, and every gap announces itself instead of
   silently resolving to something plausible.

Option 2 is the recommendation. Option 1 optimises the number that does not matter.

### 3. Most of the alias table cannot match the slugs gameplay produces

The enemy key is `Slug(prefabName)`, so the real prefixes are `zombie_enemy`, `imp_enemy`,
`plantasha_enemy`. **Zero of the 133 config keys use those forms** — they are all keyed on the
bare enemy name:

| leading key | config entries | can match? |
|---|---|---|
| gravy / minotaur | 46 | yes (prefab is bare) |
| gargoyle | 11 | yes |
| nun | 10 | yes |
| gooper | 7 | yes |
| imp | 7 | **no** — real key is `imp_enemy` |
| wendigo | 6 | yes |
| baphomet | 6 | yes |
| dragon | 4 | yes |
| mimic | 3 | yes |
| (other) | 33 | mixed |

So zombie, imp and plantasha work **only** via the greedy stage-5 resolver. The entire zombie
alias block in the config is dead weight.

### 4. Alt handling contradicts itself

`NormalizeEnemyKeyForGallery` strips `_alt1` / `_alt` from the key; `ResolveStage` then decides
base-vs-alt by looking for "alt" in the result it just removed. It also only strips those two
suffixes, so `Imp_Enemy ALT 2` → `imp_enemy_alt_2` keeps its suffix and takes a different path
from `Imp_Enemy ALT 1`.

## Recommended target design

One reviewed table, `(enemy/trigger, state) → gallery`, generated from the extracted controller
data and checked in. Resolution becomes:

1. explicit table
2. peek / diorama / ambient maps
3. skip list (idle, walk, attack, fades)
4. **log `unmapped` and do nothing**

Stage 5's greedy matching is deleted, or demoted to a warning that never dispatches. Two
startup self-checks make the table self-maintaining: every producible state maps to exactly one
gallery, and every `Definitions.csv` row is reachable from at least one state.

## Still missing

Peek trigger GameObject names are not in any asset file under the names the slugs imply
(`p3_peephole_plantasha`), so the peek half of the table cannot be completed statically. One
in-game log line finishes it — walk into each peephole and capture:

```
grep -E "\[INTERACT-START\]|\[PEEK-INGAME\]" BepInEx/LogOutput.log
```

`[INTERACT-START] trigger='...' galleryId='...' key=...` names the exact inputs.

## Funscript inventory

No unused scripts. **30 funscripts on disk, 30 referenced**, none missing, in both the game tree
and `mod/single-mod` — verified identical. No file is orphaned by the four dead rows either;
all four share a file with live rows (`gallery`, `zombie`, `imp`).

Non-funscript files kept deliberately:

- `handy2pro/plantasha.ofsp`, `handy2pro/zombie.ofsp` — OpenFunscripter projects. Edi never reads
  them, but they name their source media, which is how the properly-authored scripts were
  identified in the first place (see ../learnings/funscript-authoring.md provenance).
- `Definitions.csv.bak` — the 3 June original, superseded by §1–§5 but a record of the
  pre-rewrite state.

**Worth noting:** `Plantasha_Start` still points at `new.funscript`, Dupli9d's
"very much work in progress" strip, while the OFS-authored `plantasha.funscript` serves
`Plantasha_Loop` and `Plantasha_Cum`. TODO lists `Plantasha_Start` under "feel / shape —
doesn't match the action". That is consistent with its provenance rather than its timing, and
§3's repointing pass appears to have missed it.


---

# Stage 3 — done

Executed 2026-08-16, same day. **This section corrects §2b/§2c above**, which reached the right
diagnosis and then the wrong recommendation.

## The correction

§2c concluded the compiled default was "dead documentation" and advised against syncing it into
the config. That was backwards. Running the **real `NameRemap.BuildGallerySlug`** over every
`(enemy family, animator state)` pair settled it:

| config's `GalleryAliases` | pairs mapped | unmapped |
|---|---|---|
| the shipped 130-entry curated list | 11 | **120** |
| the compiled 315-entry default | 77 | 54 |
| the new table | **131** | **0** |

The curated list is keyed on *pre-normalisation* slugs — `nun_ghoulgrabstart`,
`gooper_goopergrabscreen` — but the slug builder now normalises those to `nun_grab` and
`gooper_grab`. The author improved the builder, updated the code default to match, and shipped
the old config beside it. So the config was stale relative to the code, not the reverse, and
almost nothing in it was firing. Ninety percent of gameplay was running on the greedy fallback.

## Method

Porting the slug pipeline to Python would have been guesswork — `StripEmbeddedEnemyPrefix`,
`NormalizeGrabStepSuffix`, `NormalizeMimicGrabTokens`, `NormalizeGhoulGrabTokens`,
`StripAltGrabSuffix` and `FinishGallerySlug` interact in ways that are hard to reproduce. So the
real file was compiled into a standalone harness instead:

```
code/slugharness/                 NameRemap.cs verbatim + a 6-line Plugin stub
dotnet run --project code/slugharness -- BepInEx/config/com.edi.pnc.cfg
```

It emits `family, state, slug, resolved, via` for every pair, so coverage is a `wc -l`, not a
judgement call. Rebuild it if the slug rules change.

The `(family, state)` inputs come from the animator controllers extracted in stage 1, so the
enumeration is the game's own, not a guess.

## What shipped

- **`GalleryAliases` is now 326 entries**, and the compiled default and both config files are
  **byte-identical** — the drift that caused all of this cannot recur silently.
- **49 entries added** on top of the 315: 29 explicit `-` skips for idle/walk/attack/spin/fade
  states, and 20 real mappings that only the fallback had been covering — the gallery viewer's
  Baphomet and Gravy stages, `dragon_grabbed`, `zombie_alt1loop/cum`, and
  `mimic_weaponsmimiccum` (the Weapons Mimic variant).
- **`TryResolveByEnemy`, `ResolveStage`, `TryResolveImplicitAlias` and `NormalizeGameplayName`
  are deleted** — about 3.7 KB of source. An unmapped slug is now returned unchanged and logged
  once as `[ALIAS-GAP] no mapping for 'x'`; `SendPlay`'s `IsKnown` gate then drops it without
  touching the running script, so a gap is inert and visible instead of silently plausible.

## What this fixes beyond the cleanup

Anything that was resolving through the fallback is now explicit, which removes the class of bug
behind defects 1 and 4: peek slugs can no longer be claimed by an enemy substring, and alt
variants are decided by an entry rather than by whether the word "alt" survived key
normalisation.

## EnemyRemap: fixed, and now load-bearing

The live config was missing four `EnemyRemap` entries the compiled default has —
`Zombie_Enemy=zombie`, `Zombie=zombie`, `Plantasha_Enemy=plantasha`, `Plantasha=plantasha` —
so those two enemies resolved to keys `zombie_enemy` / `plantasha_enemy` instead of the family
form the table is keyed on.

Harmless before, because the greedy fallback caught them. **With the fallback gone it would have
been a regression**: zombie and plantasha grabs would have produced unmapped slugs and played
nothing. Added to both configs; every enemy prefab in the game now resolves:

| prefab | key |
|---|---|
| `Hood_Enemy` / `Hood_Enemy NoTape` | nun / nun_alt |
| `Mimic`, `Weapons Mimic` | mimic |
| `Gooper`, `Gooper ALT1` | gooper |
| `Gargoyle`, `Gargoyle Alt` | gargoyle |
| `Imp_Enemy`, `Imp_Enemy ALT 1..4` | imp |
| `Zombie_Enemy`, `Zombie_Enemy_ALT1` | zombie |
| `Plantasha_Enemy`, `Plantasha_Enemy ALT1` | plantasha |
| `Dragon`, `Wendigo`, `Gravy`, `Baphomet Statue` | dragon / wendigo / gravy / baphomet |

(The nun enemy is internally `Hood_Enemy` — there is no prefab called Nun or Ghoul, which is
why searching the assets for one turns up only dioramas.)

## First thing to check in game

```
grep -E "\[GRAB-START\]|\[ALIAS-GAP\]" BepInEx/LogOutput.log
```

`key=zombie` is correct. `key=zombie_enemy_alt1` means the remap entry did not take.
Any `[ALIAS-GAP]` line names a slug the table does not cover — add it to `GalleryAliases`,
no rebuild needed.


## Stage 4 — ownership inverted

The table moved out of the config default and into `edimod/PncEdi/GalleryTable.cs`, shipped in
the DLL. `GalleryAliases` / `InGameAliases` are now empty override lists layered on top.

Verified: with **both config lists empty**, the harness still reports 131/131 mapped — the code
table alone is complete. With `nun_grab=Gooper_Start` set as an override, the harness reports
`nun_grab -> Gooper_Start`, confirming overrides win.

This closes the root cause behind every finding in §2b, §2c and §3: a shipped config can no
longer freeze the table, because the config no longer contains it.

# Tests

    dotnet test code/tests/PncEdi.Tests.csproj

114 tests over the mod's naming, alias and config layer. They compile the **real** source files
out of `../edimod/PncEdi/` — never a copy — so they cannot drift from what the mod does. That is
the same rule `../slugharness/` has followed since §71, for the same reason.

## What is testable, and why the rest is not

Most of this mod is Harmony patches over live game objects: a patch fires when the player is
grabbed, reads a `GrabScreen` off the scene, and pushes a row name at Edi. None of that exists
without a running game, and pretending otherwise with mocks would test the mocks.

What *is* pure logic is the part between the game and the HTTP call — steps 2, 3 and 4 of the
pipeline in `PROJECT.md`:

| file | what the tests pin down |
|---|---|
| `ConfigMap.cs` | the `key=value;key=value` format all nine map settings share (§117) |
| `NameRemap.cs` | prefab/display name → enemy key, and (key, animator state) → slug |
| `GalleryRegistry.cs` | `Definitions.csv` loading, `IsKnown`, `LoopMs`, `?seek=` stripping |
| `GalleryAliases.cs` + `GalleryTable.cs` | slug → gallery row, in-game vs shared, gap reporting |
| `DioramaGalleryMap.cs` | `D13` → `ambient_*`, and the three routes to it |
| `PeekGalleryMap.cs` | the four exact keys, in order, then the clip-name fallback |
| `ClassHeatMultipliers.cs` | the one setting parsed as a number, and `ScaleCapacity` — how a class multiplier and an armour heat bonus combine (§162) |

**That is where this project's bugs have actually been.** §92 (the gallery menu passing
`Goon Shroom` with a space), §80 (0.3.1 rewriting every peek display name into a joke), §96 (an
unknown row and a missing file logging the same thing), the whole substring-guessing fallback in
`NAMING-AUDIT.md`. Each of those is a test here now.

## The rules these tests follow

**Expectations are ground truth, not snapshots.** A test that records what the code currently
does is a change detector, not a check. The slug cases are rows out of `slugharness`, the enemy
keys are entries the shipped config actually contains, and the behavioural ones cite the
CHANGELOG section that established them.

**Several read the live `com.edi.pnc.cfg` and `Definitions.csv`** rather than a fixture copied
beside them. The failure this project keeps hitting is a *live* config entry that no longer
matches the code, and a hand-copied fixture is exactly what would still pass.
`EveryTargetInTheShippedConfigIsARealRow` and `EveryDSlotInTheLiveConfigNamesAKnownRow` are the
two that would have caught it.

**Everything under test is `static`**, because the mod is a plugin and its tables are
process-wide. So the suite runs single-threaded
(`[assembly: CollectionBehavior(DisableTestParallelization = true)]` in `Fixtures.cs`) and every
test that touches configuration starts with `Fixtures.Configure(...)`, which clears all of it.
A flaky suite is worse than none.

## What the suite is worth

It was mutation-tested when it was written — the point of a test is that it fails:

| mutation | caught by |
|---|---|
| `SortLongestKeyFirst` reversed | 3 tests, incl. the peek clip map and the enemy remap |
| split on the **last** `=` instead of the first | 3 tests, incl. the live-config target check |
| `StripCloneSuffix` dropped from `ResolveEnemyKey` | **nothing, at first** |
| `ScaleCapacity` as `(vanilla + armour) * multiplier` | `ArmourBonusIsAddedAfterTheMultiplier` (§162) |

The third found a real hole: the clone strip was only tested on the function directly, never
through the fallback path that a runtime-spawned unknown enemy takes. One extra line in
`AnUnmappedEnemyFallsBackToItsOwnSlug` closes it. Mutate something before trusting a new test
here.

## Wiring

`Stubs.cs` stands in for `Plugin`, which is a `BaseUnityPlugin` and cannot exist outside a game.
The naming layer only asks it for a config value and somewhere to log, so `Cfg` mirrors the one
member of `ConfigEntry<string>` the mod reads, plus `DefaultValue` — which
`DioramaGalleryMap` deliberately reads, because the built-in D-slot table is the *coded* default
and has to survive a user blanking their own list.

Two real assemblies are referenced, the same two roots the mod builds against:

- **BepInEx** from the pinned pack in the repo (`code/dist/bepinex/core/`). Run
  `python3 code/deploy.py --refs-only` if it is not there.
- **UnityEngine.CoreModule and Assembly-CSharp** from the game, through `game-windows`. This is
  the only thing here that needs a game checked out; `-p:GameDir=...` points it elsewhere.

`Edi/Gallery/Definitions.csv` is copied into the test output, because
`GalleryRegistry.GetDefinitionPaths`'s last candidate is `AppContext.BaseDirectory/Edi/Gallery/`.
That is how the tests get the real 104-row table with no game running.

NuGet versions (`xunit.v3` 3.2.2, `Microsoft.NET.Test.Sdk` 18.8.1) are the ones already in the
local package cache here, because the Edi clone uses the same ones — so a restore needed no
network. On a fresh machine it will.

## Adding a test

Add the case, then break the code and watch it fail. If it does not, the test is describing the
code rather than checking it.

To bring another mod file under test, add a `<Compile Include>` line to the csproj. It has to be
reachable without a Unity runtime; if it needs a live `GameObject`, it belongs to the audits in
`code/` and to a play session instead.

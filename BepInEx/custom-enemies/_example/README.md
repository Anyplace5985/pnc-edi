# Package templates

Six manifests, a credits file and a set of funscripts, with the fields filled in and no content
behind them. `CUSTOM-ENEMIES.md`, one directory up, is the reference these are the worked shapes
of; `WALL-PICTURE-TRAPS.md`, in the Joker Wall Trap package, is the reference for the last one.

**This directory is inert twice over.** Every file here ends in `.example`, which no discovery glob
matches, and the framework skips a directory named `_example` by name besides. Copy it somewhere
new under `BepInEx/custom-enemies/`, drop the `.example` suffixes from the one manifest you want
and the funscripts, and the package loads on the next launch.

| file | the route it shows |
| --- | --- |
| `enemy.json.example` | clone a vanilla enemy and retune it. The smallest thing that works. |
| `enemy.runtime-sprites.json.example` | the same clone with its artwork replaced by PNG sprite sheets read at runtime. No Unity Editor. |
| `enemy.assetbundle.json.example` | a complete prefab loaded from a Unity AssetBundle, arriving with its own AI. Needs the Editor. |
| `enemy.behaviour.json.example` | **ships no code.** Asks by name for a behaviour some other installed package published, and tunes it in the block named the same way. |
| `enemy.assembly.json.example` | **ships code.** Carries a .NET assembly and publishes a behaviour of its own. Starts switched off until a player turns it on. |
| `wall-trap.json.example` | a package *kind* of its own rather than an enemy: its own manifest, its own placement, its own gallery entries, all inside its own assembly. |
| `SOURCE.txt.example` | where the artwork, video and audio came from. Every shipped package carries one. |

**One package directory, one manifest.** These six are alternatives, not a set to copy together:
every `*.json` in a package directory is read, so leaving two behind registers two packages.

## Looking at what you built

**F9** acts on the package named by `Tools / SpawnCustomEnemyId` in
`com.edi.pnc.customenemies.cfg` — leave it empty while yours is the only package installed. It
needs `Tools / EnableDebugEnemySpawn` in `com.edi.pnc.cfg`, which gates every debug key in the
install, and it wants to be pressed **inside a run**: a package that clones a vanilla enemy has no
prefab until that enemy exists in the level.

There is one such key for every kind of package. An enemy is spawned in front of you by the
framework. A package that invents its own kind implements `IPackageDebugSpawn` and is asked to
place its own thing however that reads — the wall-trap template's kind goes on the wall you are
aiming at. If you are writing a package of a new kind, implement that interface rather than binding
a hotkey of your own; a key per package is how a config file ends up with one section each for
things that all do the same job.

## The three field mistakes that cost the most

**`fields` names a component that has to exist on this base enemy.** The game's seven AI classes -
`EnemyAI`, `ChargingEnemyAI`, `SpinningEnemyAI`, `ProjectileEnemyAI`, `BrawlerEnemyAI`,
`DragonEnemyAI`, `ProximityDragonEnemyAI` - are **siblings, not a hierarchy**: each extends
`MonoBehaviour` directly and each declares its own `maxHealth`. So `EnemyAI` is not a base class you
can name to reach all of them, and naming the wrong one matches nothing, logs one warning and
leaves the enemy at its vanilla numbers. A zombie is a plain `EnemyAI`; plantasha is
`SpinningEnemyAI`. Only *fields* are reachable, never properties - which is why there is no
movement-speed override here: an enemy's speed is a property on its A\* `FollowerEntity`.

**Ship every funscript variant, not just the one you author in.** `funscripts/` here has all three
- `handy2pro/`, `handy2/`, `handy1/` - because a player whose device points at a variant your
package does not carry gets **nothing** for your enemy. Author `handy2pro/`, generate `handy2/`,
and author `handy1/` by hand against its 364 units/s firmware ceiling.

**A package that carries code needs its `assembly` block.** Without it the DLL beside the manifest
is never loaded, no behaviour is published, no config switch is bound, and there is no log line
saying so - the package is simply not there. It applies to `wall-trap.json.example` too: a wall
trap is a kind the framework does not know, so it exists only because its own assembly implements
it.

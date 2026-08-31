# Custom enemy packages

This directory is where packages go. Each one is a directory with a manifest in it:

    BepInEx/custom-enemies/<package>/enemy.json

Packages are discovered at startup. What loaded, what did not, and why goes to
`BepInEx/LogOutput.log` under `[CustomEnemies]` and `[SPAWN]` - read that before reading anything
else when a package misbehaves. Funscripts go in `funscripts/<variant>/` beside the manifest, and
every discovered package gets a switch in the mod manager (**F11**) under **PNC Custom Enemies →
Custom Enemies**.

**A package may ship its own code**, and one that does **arrives switched off**. BepInEx cannot
sandbox a plugin, so that package's single switch is both its on/off and the permission to run its
code, it says so beside itself, and the game needs a restart after it changes (§167). Off, it runs
nothing at all: no enemy, no traps, no gallery entry, no behaviour. A package that ships no code has
the same switch with none of that.

**Its funscripts and its gallery rows are installed either way** (§173, §175), and only those. Edi reads that
folder and `Definitions.csv` once, when *it* starts, so rows that arrive only on the day a package
is switched on would mean restarting Edi as well as the game — and until you did, the package would
be running with a silent device. A funscript is data in a file Edi parses, not something the package
runs, so a switched-off package's scripts sitting in the gallery cost nothing that switch is
protecting. [Shipping a behaviour of your own](#shipping-a-behaviour-of-your-own) is the
format; the short version is that only turn one on if you trust where you got it.

There is a second manifest kind, `wall-trap.json` — a picture that hangs itself on a wall and pulls
the player into a scene. **This framework does not implement it.** Since §165 it belongs to a
package: `WallPictureTrap.dll` reads it, and both that assembly and its documentation
(`WALL-PICTURE-TRAPS.md`) ship inside the Joker Wall Trap package. Without a package that provides
that kind, a `wall-trap.json` is read by nothing at all — no switch, no log line, no error.

**The gallery is the one thing the framework reads out of every manifest, whatever kind it is.** The
funscripts under `funscripts/` and the rows built from `scenes[]` or `animations[]` are installed
before any package code runs, for every package, on or off (§175) — including a manifest kind the
framework does not otherwise implement, such as the wall trap above. Everything else about such a
kind stays none of its business.

## Getting a package

**The mod ships the framework, not the content.** With no package installed, `PncCustomEnemies.dll`
loads and does nothing — which is by design, since a package is mostly artwork and not everyone
wants it in their install.

Two packages are published as their own downloads beside the mod on its [Eroscripts release
thread](https://discuss.eroscripts.com/t/game-integration-post-nut-calamity-0-1-0-edi/315695):
the **Femboy Witch**, a portal-walking boss with a charm circle, and the **Joker Wall Trap**, a
picture that hangs on a wall and pulls the player into it. Each is one archive that extracts over
the game directory and adds a single directory under `BepInEx/custom-enemies/`. There is nothing to
configure — the manifest declares the enemy's scenes, gallery rows and aliases, and the mod
registers them at startup.

They are also the worked examples this document describes. `_example/` beside this file holds
**six manifest templates, one per route through this format** - listed in `_example/README.md`,
with the fields filled in and no content behind them - plus a `SOURCE.txt.example` and a funscript
set in all three device variants. The two real packages are the same formats with real art, real
funscripts and real tuning in them, so reading one is the fastest way to see what a manifest looks
like when it is finished. Every file in `_example/` ends in `.example` and the framework skips a
directory of that name besides, which is what makes it inert twice over: copy it somewhere new,
drop the `.example` suffix from the one manifest you want and from the funscripts, and the package
loads on the next launch. **One package directory, one manifest** - every `*.json` in a package
directory is read, so leaving two of the six behind registers two packages.

**Working from a clone of the source repo rather than a release?** A package's *text* is tracked —
its manifest, its `SOURCE.txt` and its `funscripts/` — but its media is not, because that is
third-party artwork and git history is permanent. So a clone gives you a package directory with a
manifest that names sprite sheets and video which are not there, and it will not load until you
restore the media from that package's own archive.

There are two ways to build an enemy:

- **clone a vanilla enemy** (`baseEnemy`) and replace its artwork, its fields, or its whole
  behaviour. No Unity Editor needed - artwork is PNG sprite sheets read at runtime.
  `_example/enemy.json.example` and `_example/enemy.runtime-sprites.json.example`.
- **load a complete prefab** from a Unity AssetBundle (`assetBundle` + `prefab`). This needs the
  Editor, and the prefab has to arrive with a working AI already on it.
  `_example/enemy.assetbundle.json.example`.

Every discovered package gets a switch in the mod manager (**F11**) under **PNC Custom Enemies →
Custom Enemies**, saved in `BepInEx/config/com.edi.pnc.customenemies.cfg`, which overrides the
manifest's `enabled`. Toggling one updates future random spawns and the custom gallery at once; an
enemy already walking around stays until the scene changes.

## Spawning one to look at it

**F9 is the debug key for every kind of package**, and there is only one of it. It acts on the
package whose `id` matches `Tools / SpawnCustomEnemyId` in `com.edi.pnc.customenemies.cfg`. That
setting **ships empty**, which acts on the only spawnable package when there is exactly one and
otherwise logs the ids to choose from: the framework ships no packages, so no package's id is a
default here. It needs `Tools / EnableDebugEnemySpawn` in `com.edi.pnc.cfg` - that switch stays with
the core mod, because it is one gate for every debug spawn key in the install.

What the key *does* depends on the kind:

- an **enemy** package is spawned `Tools / SpawnEnemyDistance` metres in front of the player. The
  framework built the template, so it knows what spawning one means.
- a package that owns **its own kind** is asked to place its own thing, and decides what that means
  - a wall trap goes on the wall you are aiming at rather than in front of you. It does that by
  implementing `IPackageDebugSpawn` (§181); before that it bound a debug key of its own, which meant
  a new key in a new config section for every package of every invented kind while all the enemy
  packages shared one.

A package that clones a vanilla enemy has no prefab until that base enemy exists in the level, so
**spawn from inside a run, not from the main menu**. A package whose code is switched off cannot
place anything and says so. If nothing appears, `[SPAWN]` in the log says why and lists every id
the key would accept.

## Cloning a vanilla enemy

Copy `_example/enemy.json.example` to a new directory as `enemy.json`, give it a unique `id`, and
set `baseEnemy`. That is the same case-insensitive prefab hint the debug spawner takes - `zombie`,
`gooper`, `hood|nun`, `plantasha`, and so on.

`fields` then overrides component fields on the clone, public or private:

```json
"fields": [
  { "component": "EnemyAI", "field": "maxHealth", "value": "120" },
  { "component": "EnemyAI", "field": "attackCooldown", "value": "1.4" }
]
```

`component` matches a component's short or full type name; the field is found on any component of
that type anywhere in the prefab's hierarchy. Supported types are `string`, `bool`, `int`, `float`,
`double`, enums, `Vector2` and `Vector3`; vectors are written `"x,y,z"`.

**Name the AI class this base enemy actually carries.** The game's seven AI classes - `EnemyAI`,
`ChargingEnemyAI`, `SpinningEnemyAI`, `ProjectileEnemyAI`, `BrawlerEnemyAI`, `DragonEnemyAI` and
`ProximityDragonEnemyAI` - are **siblings, not a hierarchy**: every one of them extends
`MonoBehaviour` directly and every one declares its own `maxHealth`, `attackDamage` and
`detectionRange`. So `EnemyAI` is not a base class you can name to reach the others, and naming the
wrong one matches no component on the prefab, logs one warning, and leaves the enemy at its vanilla
numbers - a package that looks retuned and is not. A zombie is a plain `EnemyAI` (§144);
`plantasha` is a `SpinningEnemyAI`, which is why the Femboy Witch's overrides name that one.

**Only fields are reachable, never properties.** The override goes through `AccessTools.Field`, so
anything a component exposes as a property is out of range. That is why there is no movement-speed
override: an enemy's speed is `maxSpeed` on its A\* `FollowerEntity`, and it is a property.

A component or field that does not exist logs a warning and the rest of the package still loads. A
*value* that cannot be parsed into the field's type, or a field of an unsupported type, is an error
and takes the whole package down with it - so check the log after editing one.

### PNG artwork, without the Editor

A clone can replace the vanilla artwork entirely with sprite sheets. The cloned enemy keeps
supplying its tested AI, attacks, hitboxes and navigation.
`_example/enemy.runtime-sprites.json.example` is a working starting point. `renderer` is normally
`null`, which means "the enemy's own"; `continuous: true` keeps one long sheet running across state
changes rather than restarting it, which is what a package with a single idle animation and a long
loop wants.

```json
"spriteVisual": {
  "renderer": null,
  "pixelsPerUnit": 100,
  "pivot": "0.5,0",
  "offset": "0,0,0",
  "scale": "1,1,1",
  "hideOriginalRenderers": true,
  "continuous": false,
  "defaultAnimation": "idle",
  "animations": [
    { "name": "idle",   "file": "idle.png",   "fps": 8,  "loop": true,  "columns": 6, "rows": 1, "frameCount": 6, "aliases": ["idle"] },
    { "name": "walk",   "file": "walk.png",   "fps": 12, "loop": true,  "columns": 8, "rows": 1, "frameCount": 8, "aliases": ["walk", "run", "move"] },
    { "name": "attack", "file": "attack.png", "fps": 12, "loop": false, "columns": 6, "rows": 1, "frameCount": 6, "aliases": ["attack", "charge", "hit"] }
  ]
}
```

Frames read left to right, then top to bottom, and every cell in one sheet must be the same size.
`columns` and `rows` describe the grid; `frameCount` can be smaller to ignore unused cells at the
end.

Each animation's `name` and `aliases` are matched case-insensitively against the vanilla Animator's
current clip name, which is how one custom walk sheet covers three differently named movement
clips. `defaultAnimation` is used when nothing matches.

`renderer` picks the source `SpriteRenderer` by GameObject name or relative hierarchy path; without
it, the first renderer that has a sprite is used. The replacement takes that renderer's material,
sorting layer, sorting order and horizontal/vertical flip, and is aligned to where its artwork
stood, so `offset`, `scale`, `pivot` and `pixelsPerUnit` are usually enough to line new artwork up
without re-exporting it.

`continuous` is for a package built from a single looping source animation. The base animator keeps
switching clips as the enemy walks, attacks and flinches, and each switch restarts the custom sheet
at frame 0 - a visible stutter when every alias points at the same loop. With `"continuous": true`
the animator is ignored and the one loop plays uninterrupted for the enemy's whole life, and the
original renderers stay hidden even if the base enemy switches them back on.

### Stopping the clone from still being the enemy it copied

Replacing the sprite leaves the rest of the base enemy in place: its meshes, trails, particle
systems, lights, muzzle flash, hit and death effects, and its entire voice - idle loop, hurt,
attack, grab and death sounds. `"stripBaseEnemy": true` removes all of it.

It disables every renderer and light, stops and clears every `AudioSource`, disables emission on
every particle system, and sets to null every `AudioClip` field and every `GameObject` field whose
name contains `effect`, `projectile` or `muzzle` on any component of the prefab. The game
null-checks all of those before use, so nothing has to be patched per AI class and a package built
on a different base enemy strips identically.

Anything the package itself creates is exempt: the check is by ownership, so the runtime sprite
visual and the witch's charm circle survive. Renderers and lights are re-asserted twice a second,
because the base AI's own `Start` and the mod's reactivation helpers can switch them back on.

After a strip the enemy is silent until the package gives it a voice - the witch does that with
`lockSound`.

## Full custom enemy

Build the AssetBundle for Windows with Unity **6000.3.11f1** - the same version the game is built
with, which you can confirm for yourself in the game's own `*_Data/globalgamemanagers`. Loading a bundle
built by a different major version is not supported by Unity and will not be by this mod either.

The prefab must already contain a working AI setup: animator, colliders, hitboxes, physics and
pathfinding components, and any attack or grab references. The practical starting point is an
editor-side copy of a vanilla prefab with its art and controllers replaced.

The manifest takes asset basenames or full bundle asset paths:

```json
{
  "id": "bog_witch",
  "displayName": "Bog Witch",
  "description": "A custom swamp enemy.",
  "enabled": true,
  "alwaysUnlocked": true,
  "includeInRandomSpawns": true,
  "spawnWeight": 1.0,

  "assetBundle": "bog_witch.bundle",
  "prefab": "BogWitchEnemy",
  "galleryPrefab": "BogWitchGalleryModel",
  "grabGalleryPrefab": "BogWitchGrabGalleryModel",
  "galleryController": "BogWitchGalleryController",
  "grabController": "BogWitchGrabController",
  "icon": "BogWitchIcon",
  "nameAliases": ["BogWitchEnemy", "Bog Witch"],
  "galleryAnimations": ["Idle", "Walk", "Attack"],

  "scenes": [
    {
      "animation": "Loop",
      "gallery": "bog_witch_loop",
      "file": "bog_witch_loop",
      "startTime": 0,
      "endTime": 0,
      "oneShot": false,
      "sound": "BogWitchLoopAudio",
      "aliases": ["bog_witch_grab_loop"]
    },
    { "animation": "Cum", "gallery": "bog_witch_cum", "file": "bog_witch_cum", "oneShot": false }
  ]
}
```

`galleryPrefab` and `grabGalleryPrefab` are optional. When present the enemy gallery instantiates
them in place of its standard display models; each should contain an `Animator` and be authored at
the same origin and scale as the standard model. Without them the gallery keeps its standard models
and uses the supplied animator controllers, which is what a sprite-and-controller replacement
wants.

## Behaviours, and where they come from

Everything above is a **reskin**: the manifest borrows a vanilla enemy and replaces what it looks
like, what it plays and what it is called. A *behaviour* is the other half - what the enemy actually
does - and it is code.

**A behaviour is published by name, and any manifest can ask for one:**

```json
"behaviour": "charm-witch",
"charm-witch": { "auraRadius": 8.5, "heatPerSecond": 7 }
```

`_example/enemy.behaviour.json.example` is that manifest written out in full - the one template
here that ships no code at all.

`behaviour` names one; the block named the same way tunes it. **A package that only asks for a
behaviour is still pure data** - no compiler, no Unity Editor, nothing but JSON, art and funscripts.
What it does need is that some *installed* package published that name. If none did, the enemy still
loads as a reskin and the log says which behaviour was wanted and what is published instead.

Behaviours that exist today, both published by the packages that ship them:

| name | published by | what it is |
|---|---|---|
| `charm-witch` | the Femboy Witch package | the portal-walking boss described below |

A package can also be a *kind* of its own rather than a behaviour another manifest attaches: the
Joker Wall Trap package's traps have their own manifest (`wall-trap.json`), their own placement and
their own gallery entries, all inside that package's assembly. `_example/wall-trap.json.example` is
the template; `WALL-PICTURE-TRAPS.md`, in the Joker Wall Trap package, is the reference for what
each field means. A kind the framework does not know exists only because its own assembly
implements it, so that template carries an `assembly` block and cannot work without one.

### Shipping a behaviour of your own

A package may ship a .NET assembly and publish behaviours from it:

```json
"assembly": { "file": "MyBoss.dll", "module": "MyBoss.MyModule", "api": 1 }
```

`_example/enemy.assembly.json.example` is the worked version of this one.

`file` is package-relative, `module` is a type in it with a public parameterless constructor
implementing `PncCustomEnemies.Api.IPackageModule`, and `api` is the framework API version the
assembly was built against - a mismatch is refused with a log line saying which side is behind,
rather than failing halfway through a run. **A manifest that carries a DLL and no `assembly` block
is the one failure in this format with no symptom whatsoever**: nothing loads, nothing is
published, no config switch is bound, and no line is logged, because the loader never learned the
package had code to refuse. Compile against `PncCustomEnemies.dll` and the game's own
assemblies; the whole surface is `PncCustomEnemies.Api`, and `code/packages/charm-witch/` in the
mod's repo is a working example of every part of it.

**A package that ships code is off until you switch it on.** Its code runs like any other mod — the
game cannot sandbox it — so only turn one on if you trust where you got it. There is one switch, and
it is the package's ordinary on/off:

    Custom Enemies / <package id> = true

in `com.edi.pnc.customenemies.cfg`, or - easier - enable the package in the mod manager (**F11**),
where it says that it ships code. **Restart the game afterwards.** Until it is on the package does
nothing — no enemy, no traps, no gallery entry, no behaviour — and the log says so by name at every
launch. Its funscripts are still copied to `Edi/Gallery/`, so switching it on later does not also
mean restarting Edi (§173). A
package that ships no code has the same single switch, starts as its manifest says, takes effect
without a restart, and gets no warning.

## The portal-witch behaviour - `charm-witch`

The behaviour the Femboy Witch package publishes, and available to any manifest that names it. It
borrows the base enemy's health bar, damage model and navigation and replaces everything else with
an animated charm circle, timed heat locks, portal blinks, proximity capture, dream-cloud video
overlays, Edi playback, and alive-only reinforcements.

```json
"charm-witch": {
  "enabled": true,
  "auraRadius": 8.5,
  "heatPerSecond": 7,
  "lockIntervalSeconds": 0,
  "lockSound": "charm-lock.wav",
  "lockSoundVolume": 0.85,
  "videoVolume": 1.0,
  "captureDistance": 1.25,
  "minimumSceneSeconds": 20,
  "movementOnly": true,
  "teleportMinSeconds": 5,
  "teleportMaxSeconds": 10,
  "teleportMinDistance": 4,
  "teleportMaxDistance": 11,
  "teleportChaseChance": 0.55,
  "damageTeleportCooldownSeconds": 5,
  "blinkSeconds": 0.16,
  "reinforcementIntervalSeconds": 14,
  "maxReinforcements": 4,
  "circleBreakDamage": 80,
  "circleBreakSeconds": 10,
  "circleBreakCooldownSeconds": 10,
  "auraGallery": "bog_witch_aura",
  "captureGallery": "bog_witch_capture"
}
```

**The block is named after the behaviour**, because that is how the framework finds it:
`ExtractObject(manifest, behaviourName)`. A block under any other name is not read and the
behaviour runs on its defaults, silently. `charm-witch` also accepts a legacy `"witch"` block,
which is what manifests written before §165 call it; new ones should not use it.

With `movementOnly` (the default) the base enemy contributes nothing but walking: every attack
cooldown clock on its AI is pushed forward each frame, so spins, projectiles and the vanilla grab
never fire and the boss cannot be mistaken for a reskin of whatever it was cloned from. Its offence
is the charm circle and the proximity capture. Set it `false` to keep the base attacks.

**Teleporting is the movement, not a flourish.** Every `teleportMinSeconds`-`teleportMaxSeconds` she
blinks: `teleportChaseChance` of those land on the player, close enough that the circle swallows
them, and the rest scatter `teleportMinDistance`-`teleportMaxDistance` away. A blink is always a
chase blink when the player is beyond 1.35× the aura radius, so distance is never a safe answer.
Taking damage also triggers a scatter blink, at most once per `damageTeleportCooldownSeconds`.
`blinkSeconds` is the fade-out; the fade back in takes 1.4× as long.

**`lockIntervalSeconds: 0` makes the aura heat-only**, and that is what the shipped witch uses. A
heat lock is what the game charges for a scene it has actually shown, so handing one out every few
seconds for standing in a circle spent the run's health budget through something the player never
saw (§130). At zero the aura still generates `heatPerSecond` for as long as they stand in it - which
cools off again when they leave - and the arc that fills as the next lock charges stays empty
because there is no lock coming. Her capture scene still costs a lock like any other grab. Any
positive value restores the old behaviour.

**The charm circle** is two counter-rotating rune discs projected on the floor beneath her, a ring
that sweeps upwards through the aura so its extent reads from any camera angle, and an arc that
fills as the next lock charges. Standing inside speeds the rotation up and turns the whole thing
pink.

It can be broken by fighting back. Once she has taken `circleBreakDamage` points of damage the
circle goes down for `circleBreakSeconds`: the ring disappears and it stops generating heat, locks
and the aura overlay, while teleports, reinforcements and the capture keep running. When it returns
it is unbreakable for `circleBreakCooldownSeconds`. Damage dealt during the outage or that
refractory window does not count, so the next break needs a fresh `circleBreakDamage` after the
circle is armed again. `circleBreakDamage: 0` makes the circle permanent. Damage is read from the
base enemy's health, so every damage source counts.

`lockSound` is an optional package-relative **16-bit PCM WAV** played each time standing in the
circle actually raises the lock counter - not when the counter is already full, and not when the
heat-lock profile is off, because only a real gain triggers it. `lockSoundVolume` (0-1) scales it;
the cue is non-positional, so it sounds the same anywhere inside the circle.

`auraGallery` and `captureGallery` should also appear in `scenes`, so their funscripts are copied
and registered like any other. **Neither has a default**: omit one and that scene sends no row,
rather than falling back to some other package's.

### Gallery videos, and Linux

A package's videos are declared once, at the top level of the manifest rather than inside a
behaviour's block, because they are media rather than behaviour: the framework's own gallery reads
them, so a package with no code at all still gets its video steps, and `charm-witch` falls back to
the same list for its in-game dream clouds rather than making a manifest carry two copies. A
behaviour block may still name its own `dreamVideos`, and that wins where it does.

```json
"galleryVideos": {
  "files":  ["dream-1.webm", "dream-2.webm", "capture.webm"],
  "labels": ["Dream 1", "Dream 2", "Capture"],
  "volume": 1.0,
  "gallery": "my_boss_aura",
  "lastGallery": "my_boss_capture"
}
```

`labels` are what the gallery's step list shows, and what a row is looked up by; `gallery` is the
row every video sends, except the last one when `lastGallery` names another.

`files` are package-relative video files, and **they should be WebM**. Unity has no H.264 decoder
outside Windows and macOS, so an MP4 that plays fine on Windows is a blank rectangle on the native
Linux build; what Unity carries on every platform is libvpx. Name the `.webm` and ship only that -
the shipped packages do, since §171.

An MP4 still works if that is what you have: the mod prefers a `.webm` *sibling* of whatever the
manifest names, on every platform, so a package can name `dream-1.mp4` and be saved by a
`dream-1.webm` beside it. Do not rely on it. That arrangement is how a package ends up valid on one
machine and broken on another - the release drops an H.264 master once a WebM exists, so a manifest
naming the MP4 describes a file its own archive does not contain.

From this repo, `python3 code/webmify.py` converts, and `--check` reports what is missing. If a
video is going to be blank, `[VIDEO]` in the log says so by name before it happens.

`volume` (0-1) scales the dream-cloud and capture overlays; video audio is muted while the game is
paused.

## Funscripts

Put scripts beside the manifest, grouped by Edi device variant:

    bog-witch/
      enemy.json
      SOURCE.txt
      funscripts/
        handy2pro/
          bog_witch_loop.funscript
          bog_witch_cum.funscript
        handy2/
          bog_witch_loop.funscript
          bog_witch_cum.funscript
        handy1/
          bog_witch_loop.funscript
          bog_witch_cum.funscript

At startup these are copied into the matching `Edi/Gallery/<variant>` folders and their rows added
to `Edi/Gallery/Definitions.csv`.

**Author `handy2pro/` and generate the rest.** The variant folders are named after the device they
are for (`handy2pro` was called `detailed` before 3.0.0), and a player whose device points at a
variant your package does not carry gets **nothing** for your enemy — Edi looks up the row in the
folder the device names and finds no file. `.venv/bin/python code/variants.py --write` emits a
package's `handy2/` from its `handy2pro/` masters, held to 600 units/s sustained and 700 peak. A
`handy1/` is not generated for you: 364 units/s is a hard enough limit that the shipped packages'
Handy 1 scripts were authored by hand rather than slew-limited, and the tool leaves them alone.

`_example/funscripts/` carries all three folders for that reason, and its two scripts are chosen to
show the one case that matters: the climax runs at 380 units/s, which is inside a Handy 2's 600 and
over a Handy 1's 364, so the `handy1/` copy shortens the *stroke* and leaves the *timing* alone. It
is always the stroke that gives - the script has to stay in step with the animation on screen.

Restart Edi after adding or changing a package if it was already running.

In a scene, `animation` must exactly match the animator state the game or gallery selects, `gallery`
is the name sent to Edi, and `file` is the funscript basename without `.funscript`. `endTime: 0`
means "the largest `at` timestamp in the funscript", so a scene that plays a whole script needs no
times at all. Optional `aliases` catch extra live-game state names without editing any central
config. Each scene also appears as a selectable grab animation in the enemy gallery.

Two rules protect the project's own gallery, and both refuse rather than overwrite:

- a funscript whose name collides with one already installed, but whose **content differs**, is not
  copied;
- a `gallery` name that collides with a row `Definitions.csv` already defines differently is not
  written.

Both log a warning naming the package. Rename the offending scene or script.

## `SOURCE.txt`

Every package in this format ships one, and both of the published ones do. Nothing in the mod reads
it: it is for the people who install the package, and for whoever has to answer for the content
later. Say, for each asset, who made it, where you got it, on what date, and what you did to it -
the resize, the atlas layout, the WAV conversion. `_example/SOURCE.txt.example` is the shape.

A package posted without one is asking its players to take its provenance on trust, which is not a
thing this format wants to normalise.

## Spawning and gallery behaviour

- Custom `EnemyData` is injected into normal and arena spawners before their own `Awake` runs, so
  the enemy appears in the rooms' authored tables like any other.
- The prefab's `galleryEnemyID` fields are set to the package `id` automatically.
- The package gets an `EnemyGalleryEntry` in the **Custom Enemies** gallery tab and in the progress
  manager. A runtime-PNG package gets a safe, visual-only preview clone; `galleryPrefab` overrides
  the preview for AssetBundle packages.
- `alwaysUnlocked` decides whether it needs unlocking; the mod's `Gallery / UnlockAll` still
  overrides locks either way.
- `id`, `displayName`, `prefab` and every `nameAliases` entry resolve to the same funscript
  namespace.
- `includeInRandomSpawns: false` keeps a package out of spawning entirely - useful for something
  you only ever want to summon with F9.

### `spawnWeight`, and the config knob that overrides it

**1 is one ordinary enemy's share** of a room's spawn table. `0.5` is half as likely as a zombie,
`2` is twice, and both spawn paths now agree on that meaning.

**The spawner injection** (always active) adds the enemy to each spawner's own table, because
`EnemySpawner.GetEnemyPrefab` picks uniformly from it and vanilla weights an enemy by listing it
more than once. A fraction of an entry does not exist, so the whole table is scaled up until it
does - every vanilla entry repeated, the custom one getting its share - and the table is left
exactly as authored when no package asks for a fraction. Until §130 this rounded to a whole number
and clamped to at least 1, so nothing below 1 could reduce an enemy's presence: the witch's
authored `0.2` put a boss in every table on the same footing as a zombie.

**The shuffle pool** uses the same number as a float. That pool only decides spawns when
`Gameplay / EnemySpawnMode` is `pool`, which is not the default: `grappler-bias` leaves each room's
authored table alone and only raises the odds of grapplers within it.

**Every package gets its own config entry, beside its own on/off switch.** Loading a package binds
`<id> spawn weight` in the `[Custom Enemies]` section of `com.edi.pnc.customenemies.cfg` - the
custom-enemy plugin's own config file - defaulting to the manifest's `spawnWeight`:

```
[Custom Enemies]
femboy_witch = true
femboy_witch spawn weight = 0.2
```

So an author ships a sensible default in the manifest and a player retunes it where they already
look, without editing someone else's package. It covers both spawn paths, because both read one
property, and changing it takes effect immediately - the spawn tables are rebuilt from the authored
ones on the spot rather than at the next scene.

Arena rooms that use authored `spawnGroups` rather than the arena's random pool stay under the room
author's control unless `pool` mode is on.

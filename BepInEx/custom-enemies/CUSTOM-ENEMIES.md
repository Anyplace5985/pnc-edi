# Custom enemy packages

A custom enemy is a directory with a manifest in it:

    BepInEx/custom-enemies/<package>/enemy.json

Packages are discovered at startup. What loaded, what did not, and why goes to
`BepInEx/LogOutput.log` under `[CustomEnemies]` and `[SPAWN]` - read that before reading anything
else when a package misbehaves.

For pictures that hang on a wall and pull the player in, see
[WALL-PICTURE-TRAPS.md](WALL-PICTURE-TRAPS.md). That is a different manifest (`wall-trap.json`) and
a different format.

## Getting a package

**The mod ships the framework, not the content.** With no package installed, `PncCustomEnemies.dll`
loads and does nothing — which is by design, since a package is mostly artwork and not everyone
wants it in their install.

Two packages are published as their own downloads beside the mod on its [Eroscripts release
thread](https://discuss.eroscripts.com/t/game-integration-post-nut-calamity-0-1-0-edi/315695):
the **Femboy Witch**, a portal-walking boss with a charm circle, and the **Joker wall trap**, a
picture that hangs on a wall and pulls the player into it. Each is one archive that extracts over
the game directory and adds a single directory under `BepInEx/custom-enemies/`. There is nothing to
configure — the manifest declares the enemy's scenes, gallery rows and aliases, and the mod
registers them at startup.

They are also the worked examples this document describes. `_example/` beside this file is a
template with the fields and no content behind them; the two real packages are the same formats
with real art, real funscripts and real tuning in them, so reading one is the fastest way to see
what a manifest looks like when it is finished.

**Working from a clone of the source repo rather than a release?** A package's *text* is tracked —
its manifest, its `SOURCE.txt` and its `funscripts/` — but its media is not, because that is
third-party artwork and git history is permanent. So a clone gives you a package directory with a
manifest that names sprite sheets and video which are not there, and it will not load until you
restore the media from that package's own archive.

There are two ways to build an enemy:

- **clone a vanilla enemy** (`baseEnemy`) and replace its artwork, its fields, or its whole
  behaviour. No Unity Editor needed - artwork is PNG sprite sheets read at runtime.
- **load a complete prefab** from a Unity AssetBundle (`assetBundle` + `prefab`). This needs the
  Editor, and the prefab has to arrive with a working AI already on it.

Every discovered package gets a switch in the mod manager (**F11**) under **PNC Custom Enemies →
Custom Enemies**, saved in `BepInEx/config/com.edi.pnc.customenemies.cfg`, which overrides the
manifest's `enabled`. Toggling one updates future random spawns and the custom gallery at once; an
enemy already walking around stays until the scene changes.

## Spawning one to look at it

**F9** spawns the package whose `id` matches `Tools / SpawnCustomEnemyId` (default `femboy_witch`)
in `com.edi.pnc.customenemies.cfg`, `Tools / SpawnEnemyDistance` metres in front of the player. It
needs `Tools / EnableDebugEnemySpawn` in `com.edi.pnc.cfg` - that switch stays with the core mod,
because it is one gate for every debug spawn key in the install.

A package that clones a vanilla enemy has no prefab until that base enemy exists in the level, so
**spawn from inside a run, not from the main menu**. If nothing appears, `[SPAWN]` in the log says
why and lists every id that did load.

## Cloning a vanilla enemy

Copy `_example/enemy.json.example` to a new directory as `enemy.json`, give it a unique `id`, and
set `baseEnemy`. That is the same case-insensitive prefab hint the debug spawner takes - `zombie`,
`gooper`, `hood|nun`, `plantasha`, and so on.

`fields` then overrides component fields on the clone, public or private:

```json
"fields": [
  { "component": "EnemyAI", "field": "maxHealth", "value": "120" },
  { "component": "EnemyAI", "field": "moveSpeed", "value": "3.5" }
]
```

`component` matches a component's short or full type name; the field is found on any component of
that type anywhere in the prefab's hierarchy. Supported types are `string`, `bool`, `int`, `float`,
`double`, enums, `Vector2` and `Vector3`; vectors are written `"x,y,z"`.

A component or field that does not exist logs a warning and the rest of the package still loads. A
*value* that cannot be parsed into the field's type, or a field of an unsupported type, is an error
and takes the whole package down with it - so check the log after editing one.

### PNG artwork, without the Editor

A clone can replace the vanilla artwork entirely with sprite sheets. The cloned enemy keeps
supplying its tested AI, attacks, hitboxes and navigation.
`_example/enemy.runtime-sprites.json.example` is a working starting point.

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

## The portal-witch behaviour

A clone manifest may add a `witch` object. It borrows the base enemy's health bar, damage model and
navigation and replaces everything else with an animated charm circle, timed heat locks, portal
blinks, proximity capture, dream-cloud video overlays, Edi playback, and alive-only reinforcements.

```json
"witch": {
  "enabled": true,
  "auraRadius": 8.5,
  "heatPerSecond": 7,
  "lockIntervalSeconds": 0,
  "lockSound": "magical-whoosh.wav",
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
  "auraGallery": "femboy_witch_aura",
  "captureGallery": "femboy_witch_capture",
  "dreamVideos": ["dream-1.mp4", "dream-2.mp4"]
}
```

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
and registered like any other.

### Dream videos, and Linux

`dreamVideos` are package-relative video files. **Unity has no H.264 decoder outside Windows and
macOS**, so an MP4 that plays fine on Windows is a blank rectangle on the native Linux build. What
Unity carries on every platform is libvpx, so the mod prefers a `.webm` sibling of whatever the
manifest names, on every platform - ship both and one package works everywhere.

From this repo, `python3 code/webmify.py` writes those siblings for every installed package
(`--check` reports what is missing without converting). If a video is going to be blank, `[VIDEO]`
in the log says so by name before it happens.

`videoVolume` (0-1) scales the dream-cloud and capture overlays; video audio is muted while the
game is paused.

## Funscripts

Put scripts beside the manifest, grouped by Edi device variant:

    bog-witch/
      enemy.json
      bog_witch.bundle
      funscripts/
        detailed/
          bog_witch_loop.funscript
          bog_witch_cum.funscript
        handy1/
          bog_witch_loop.funscript
          bog_witch_cum.funscript

At startup these are copied into the matching `Edi/Gallery/<variant>` folders and their rows added
to `Edi/Gallery/Definitions.csv`. `endTime: 0` means "the largest `at` timestamp in the funscript".
Restart Edi after adding or changing a package if it was already running.

In a scene, `animation` must exactly match the animator state the game or gallery selects, `gallery`
is the name sent to Edi, and `file` is the funscript basename without `.funscript`. Optional
`aliases` catch extra live-game state names without editing any central config. Each scene also
appears as a selectable grab animation in the enemy gallery.

Two rules protect the project's own gallery, and both refuse rather than overwrite:

- a funscript whose name collides with one already installed, but whose **content differs**, is not
  copied;
- a `gallery` name that collides with a row `Definitions.csv` already defines differently is not
  written.

Both log a warning naming the package. Rename the offending scene or script.

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

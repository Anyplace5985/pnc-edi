# Wall-picture traps

A wall trap is a picture that hangs itself on a wall, waits, and drags the player into a scene of
its own. It needs no Unity Editor and no AssetBundle: one transparent PNG portrait, one or more
transparent PNG sprite sheets, and a manifest.

    BepInEx/custom-enemies/<package>/wall-trap.json

**A wall trap is a package that ships code.** Unlike a custom enemy - which is data, and can borrow
a behaviour another package published - the trap *is* a behaviour, with its own manifest kind, its
own placement rules and its own gallery entries, so it lives in an assembly beside its manifest
(`WallPictureTrap.dll`, §165). That has one consequence worth knowing before anything below makes
sense: **the package starts switched off**, and its one switch is what allows the code:

    Custom Enemies / joker_wall = true

in `com.edi.pnc.customenemies.cfg`, or enable the package in the mod manager (**F11**), where it
carries the warning that it ships code — then restart, because assemblies load once at startup.
That code runs like any other mod and the game cannot sandbox it, so the switch is the place you are
asked. Until it is on, the package does nothing: no trap, no gallery entry. Its funscripts and its
rows in `Definitions.csv` are installed either way, so switching it on later does not also mean
restarting Edi (§175).

Everything here is read at startup. Diagnostics go to `BepInEx/LogOutput.log` under
`[WallPictureTrap]`, and that log is the first thing to read when a trap does not behave.

## Where traps appear

Two placers, and a package can use either or both.

**At scene load.** After `placementDelay` seconds (never less than 0.5), every enabled package with
`autoPlace` places traps until it has `spawnCount` of them in the level. A package with
`spawnCount: 0` places nothing here, which is the normal setting for one that would rather appear
as you explore.

**While exploring.** From four seconds after the scene loads, the placer checks every
`roamingSpawnInterval` seconds; once you have moved `roamingSpawnDistance` metres from where the
last check ran, it places `roamingSpawnBatch` more, up to `maxActiveCount` traps of that package.
Both timings are floored (interval at 3 seconds, distance at 4 metres), and when several packages
are loaded the shortest interval and distance of any of them drives the shared placer.

A wall qualifies if it is vertical (surface normal within about 14° of horizontal), at least 3
metres away, no further than 18, and at least `minimumSpawnSeparation` metres from another trap of
the same package. Among the candidates the placer prefers walls about **9 metres** away, prefers
corners when `preferCorners` is set, and actively prefers walls that are *not* currently on screen -
a trap you watched being hung is not much of an ambush.

## Placing one by hand

**F10** places a trap on the vertical wall you are aiming at, up to 35 metres away, and falls back
to the automatic wall search if you are not aiming at anything suitable. It first destroys **every**
trap of that package already in the scene, so it repositions rather than accumulates. The key is
`Wall Picture Traps / PlaceTrapKey` in `com.edi.pnc.customenemies.cfg` - the package binds it
itself, in its own section, since §165 - and it needs `Tools / EnableDebugEnemySpawn` in
`com.edi.pnc.cfg`, which is one gate for every debug spawn key in the install.

## What it does

The trap arms `armDelay` seconds after it is placed. After that, a player who is inside
`pullRadius`, in front of the picture, and in clear line of sight of it gets pulled towards it.

The pull accelerates at `pullStrength` metres per second squared, scaled by how close the player
already is - gently at the edge of the radius, sharply near the middle - up to a ceiling of
`maxPullSpeed`. That ceiling is the number that decides the feel: the player walks at 7 m/s, so a
cap below that is a trap you escape by noticing it, and a cap above it is a trap that takes you.
It defaults to 5.

At `captureDistance` the trap takes the player through the game's own grab system: movement locks,
the struggle button is disabled, and the package's animation plays full-screen over the live level,
dimmed behind by `captureBackdropAlpha`. Each animation stage runs for its `seconds` and then
advances to the next, cycling back to the first at the end; a stage with `seconds: 0` runs until the
scene ends. Every stage change sends its own row to Edi.

The scene cannot be left before the package's `minimumSceneSeconds` - which overrides the mod's own
`Gameplay / EndGrabDelaySeconds` for this scene - and then ends on the escape key
(`Gameplay / EndGrabKey`, **Q** by default). The trap then waits out `cooldown` before it can pull
again.

## Fighting back

The picture is a normal combat target. Its wall-aligned box collider takes melee and projectile
damage through the game's `IDamageable`, flashing red on each hit, and at `maxHealth` damage it is
destroyed for the rest of the scene. `colliderDepth` is how far that hitbox stands off the wall.

## Manifest

Only `id`, `portrait` and one entry in `animations` are required; everything else has the default
shown.

```json
{
  "id": "example_wall",
  "displayName": "Wall Picture",
  "enabled": true,

  "portrait": "portrait.png",
  "portraitPixelsPerUnit": 300,
  "portraitBrightness": 1.0,
  "portraitScale": "1,1,1",

  "autoPlace": true,
  "spawnCount": 1,
  "maxActiveCount": 8,
  "roamingSpawnBatch": 1,
  "roamingSpawnInterval": 12,
  "roamingSpawnDistance": 12,
  "preferCorners": true,
  "minimumSpawnSeparation": 5,
  "placementDelay": 3,

  "armDelay": 5,
  "pullRadius": 7.5,
  "frontArc": 0.15,
  "pullStrength": 24,
  "maxPullSpeed": 5,
  "captureDistance": 1.15,
  "cooldown": 10,

  "maxHealth": 600,
  "colliderDepth": 0.06,

  "minimumSceneSeconds": 20,
  "captureBackdropAlpha": 0.2,
  "captureSound": "capture.wav",
  "captureSoundVolume": 0.8,
  "captureSoundLoop": true,

  "animations": [
    { "name": "massage", "file": "massage.png", "gallery": "example_wall_massage",
      "funscript": "example_wall_massage", "fps": 7.7, "loop": true,
      "columns": 2, "rows": 2, "frameCount": 4, "seconds": 10 },
    { "name": "cum", "file": "cum.png", "gallery": "example_wall_cum",
      "funscript": "example_wall_cum", "fps": 7.7, "loop": true,
      "columns": 4, "rows": 2, "frameCount": 8, "seconds": 4 }
  ]
}
```

Field notes, for the ones where the name is not the whole story:

| field | what it means |
| --- | --- |
| `portraitBrightness` | 0 is black, 1 is the artwork as authored. Low values are how a picture hides on a dark wall. |
| `portraitPixelsPerUnit`, `portraitScale` | the size of the picture on the wall. Higher pixels-per-unit is smaller. |
| `frontArc` | minimum dot product between the picture's facing and the direction to the player. Higher is a narrower cone; 0 would pull from anywhere in front of the wall. |
| `pullStrength` | an acceleration, not a speed - it decides how fast the pull ramps up, `maxPullSpeed` decides where it stops. |
| `maxHealth` | the default of 600 is a wall you cannot casually remove. Drop it to a few dozen to make the picture a real target. |
| `captureSound` | package-relative **16-bit PCM WAV**. Plays on capture, looping if `captureSoundLoop`. A file saved as `WAVE_FORMAT_EXTENSIBLE` is refused with a message in the log even though it is 16-bit PCM inside; re-export as plain PCM. |
| animation `columns`/`rows`/`frameCount` | the sprite-sheet grid. Frames are read left to right, then top to bottom; `frameCount` may be smaller than the grid to ignore unused cells at the end. |
| animation `gallery`/`funscript` | the Edi row name and the funscript basename. Defaults to `<id>_<name>` and to the gallery name respectively. |

## Funscripts

Same layout as any other package - beside the manifest, grouped by device variant:

    example-wall/
      wall-trap.json
      portrait.png
      massage.png
      cum.png
      funscripts/
        handy2pro/
          example_wall_massage.funscript
          example_wall_cum.funscript
        handy2/
          ...
        handy1/
          ...

Each animation gets a row in `Edi/Gallery/Definitions.csv` whose end time is the largest `at` in
the funscript, and its scripts are copied into `Edi/Gallery/<variant>/`. A stage with no funscript
to measure gets no row and plays nothing. Restart Edi after *adding* a package if it was already
running — it reads that file once at its own startup. Turning a package on or off afterwards does
not need one: the mod installs a package's scripts and rows before it reads any switch (§175).

A package may not redefine a gallery row this project already ships: those were measured against
specific game assets, and a name collision is refused with a warning in the log rather than
silently retargeting the existing row. Rename the stage's `gallery` if you hit it.

## Enabling and disabling

Every trap package gets a switch in the mod manager (**F11**) under **PNC Custom Enemies →
Custom Enemies**, saved in `BepInEx/config/com.edi.pnc.customenemies.cfg`, which overrides the
manifest's `enabled`. **The mod binds that switch itself**, before any package code loads, because
for a package that ships code the switch *is* the permission to run it (§167) — off by default, with
the warning drawn beside it. Disabling removes placed traps of that package at once and stops future
placement; re-enabling places new ones as you explore — but a package that was off at startup ran no
code, so switching it on there needs a restart before any trap exists to place.

# How this game's scenes are organised

Dioramas, peek scenes, grab screens and the gallery viewer - what identifies each, and where the names lie.

**Read this when:** wiring a new scene, or working out which script a game object should play

**Keywords:** diorama, D-slot, GalleryUnlockTrigger, galleryID, peek scene, peephole, gallery split, Gallery_ clip, ambient, PauseHooks, ResetForNewScene, Stage1Shop, shop scene, HeatLockSystem

---

As of game 0.3.1 there are **15 dioramas** (D1–D15) and **11 peek scenes**; on 0.2.1 it was 9 and 7.
Telling them apart from asset names alone is where several wrong mappings came from.

| | diorama | peek scene |
|---|---|---|
| how the player triggers it | walks near — it plays on **proximity** | **interacts** with a peephole |
| mechanism | looping `AudioSource` + a `GalleryUnlockTrigger` box | `CameraSwapTrigger` swapping to a peep camera |
| room name | plain, e.g. `Dungeon 4 way` | **suffixed `_Peek` / `_Peep` / `PEEP`**, e.g. `Dungeon 4 way_Peek` |
| gallery id | `D1`..`D9` | `P1`..`P7` |
| script prefix | `ambient_*` | `peek_*` |

**Identify a diorama by its unlock box, not by its audio.** Every diorama carries a
`GalleryUnlockTrigger` whose `galleryID` is `D1`…`D15`, and `DioramaAmbientMap` turns that into the
script. Since §65 that is what identifies the scene on both routes; the `Patterns` audio-clip list
is only the fallback for things with no box (peek holes, and a gallery entry handed over with no
id). It used to be the other way round, which meant a hand-maintained clip-name fragment outranked
the label the game assigns itself — and every new scene needed a new fragment guessed correctly.
**Where the game already labels a thing, read the label.** (§26 found these boxes and used them for
the release mechanic and the playback gate; it just never moved identification onto them.)

**Superseding a mechanism is not the same as removing what was riding on it — check what else it
was carrying.** §65 moved identification onto the box and left the `Patterns` match in place as a
fallback, which read like a tidy retirement. It was not: `AmbientProximity.Rescan` keeps an
AudioSource only `if (patternMatch.Pattern != null)`, and `AmbientReleaseGaze` needs a *Transform*
rather than an id — an angle to face, an `isPlaying` liveness test, and the position that keys which
instance of a repeated diorama has been spent. So the pattern list was quietly still deciding
whether a diorama could arm its one-time release at all, three sections after it stopped deciding
what the diorama was, and a box with no matching alias played fine and silently never armed. The
question that finds this is not "is the old path still used" but "**what does the old path produce,
and does anything downstream still consume it**". §119 anchors the release on the nearest playing
loop *inside the box* instead, which leaves `Patterns` doing only the job that is genuinely its
own.

**A second case, same shape: `PauseHooks.ResetForNewScene` deliberately sent no Resume on a
quit-to-menu, reasoning that the scene change itself always resolved the device — a menu stopped
Edi, or the filler started, either way "undoing the pause" was someone else's job. §148 changed
which job a menu does (it now *plays the filler* instead of stopping Edi) without anyone asking
whether the old no-Resume reasoning still held once that changed. It did not: a `Play` does not
lift `Pause?untilResume=true`, so the device stayed paused under a filler that looked like it was
running (§152).** The comment beside the code even said why it was safe — and stayed true right up
until the mechanism it was reasoning about changed underneath it. **A comment that names *why a gap
is safe* is a claim about a specific other mechanism, and needs revisiting the moment that mechanism
changes — the same way a superseded path needs its consumers enumerated.**

Note a `galleryID` is **not unique**: 0.3.1 ships two `D2` boxes, one for the secret-room version of
that room. `DioramaUnlockTriggers.Entries` is a flat list and every query iterates it, so this
needed no handling — a dictionary keyed on the id would have kept one box and silently dropped the
other.

**The suffix is the reliable signal, and adjacent rooms share a base name.** `Mansion staircase
room` holds diorama D4; `Mansion staircase room_Peep` holds the imp keyhole. `Dungeon 4 way`
holds D8; `Dungeon 4 way_Peek` holds the nun&mimic peephole. They are different rooms.

**A blanket "reset on every scene change" cannot tell a rest stop from a new stage.**
`HeatLockSystem.ResetForScene` zeroed the horny-lock count on every `activeSceneChanged`, including
`Floor1 -> Stage1Shop` — so §147's exemption (the Gravy service scene pays locks out, armed a few
seconds after the shop loads) always found an empty set by the time its own watchtime finished,
because the *scene transition into the shop* had already cleared what the payout was reaching for
(§152). The shop is not a new stage the way the next floor is; it is a stop inside the current one,
and state meant to survive into it needs a narrower reset than "any scene changed" — here, skipping
the clear when the destination scene name matches `shop`, the same substring convention
`Plugin.IsMenuSceneName` uses for `menu`.

Peek rooms each carry an `AmbientAudioSource*` object too, which is why a peephole can look like
a diorama to a proximity check — `AmbientAudioSourceWendigoPeek`, `AmbientAudioSourceNuns`,
`AmbientAudioSourceGooperPillory`, `AmbientAudioSourceNun&Mimic`, `AmbientAudioSourcePlantasha`.
That is what `AmbientPeekHoleRadius` exists to exclude (§22, §25).

Two consequences found on 2026-08-17:

- **`ambient_wendigo_hole` is not a diorama.** The only "wendigo hole" object in the game is
  `AmbientAudioSourceWendigoPeek`, in `dungeon light pillar room_Peek` — it is the wendigo
  *peephole's* ambient audio, and the scene itself is `peek_wendigo_ride`. `DioramaAmbientMap`
  had `D5=ambient_wendigo_hole`, corrected in §32 — but only in the config default. The parallel
  `DioramaGalleryMap.DefaultDSlotAmbients[4]` kept the old value for a day. §33 deleted that array
  and derives the fallback from the setting's own `DefaultValue` instead, so the two can no
  longer disagree.
- **There are two imp gangbang dioramas with different animations — but only 4% apart, not 2×.**
  D5 (`Dungeon Cross Room`, object `Imp Gangbang`, clip `imp gangbang`) is 10 frames @ 8 fps =
  1250 ms holding **two** strokes → 625 ms. D6 (`Mansion 2 square room`, object `imp gangbang 2`,
  clip `imp gangbang 2`) is 12 frames @ 10 fps = 1200 ms holding **two** strokes → 600 ms.
  Different sprite sheets (`imp gangbang_0..9` vs `Imp Gangbang 2_0..11`). Split into
  `ambient_imp_gangbang` (3125 = 5 × 625) and `ambient_imp_gangbang_2` (3000 = 5 × 600) in §33.

  The "two strokes" in D6 is the part that was missed for a day, and the reason is worth keeping:
  its two halves are the same six frames drawn **1 px further left**, so the height sequence is
  identical (`126,126,126,124,127,125` twice) but every vertical edge in the image is offset.
  `stroke_period` compared frames without alignment, and that 1 px inflated the lag-6 score from
  0.12 to 0.70 — past its 0.5 threshold. It read as one 1200 ms stroke, which made D5 and D6 look
  1.92× apart and justified a from-scratch rebuild that was not needed. `animcheck.stroke_period`
  now compares at the best integer x-offset (±3 px). **Alpha-trimmed sprite sheets are not
  registered to each other; align before differencing.**


## The gallery viewer plays its own clips

Every scene is reachable from two routes - an in-game animator state and the gallery viewer - and
the viewer has its own `Gallery_*` clips. Twelve of them are a **different length** from the
in-game clip, so one funscript cannot be whole-cycle correct for both; that is "right in gameplay,
off in the gallery", and it is a *routing* symptom, not a curve defect. `code/gallerydiff.py` has
the table and is the tool that answers it.

Splitting needs no rebuild: in-game lookups check `InGameAliases` first and fall back to
`GalleryAliases`, gallery lookups read `GalleryAliases` only. Whether a slug collides is not
guessable - run the slug harness and read the `via` column.

**Ask the question of every new scene; the answer is not a rule.** Of the ten added in game 0.3.1,
the six dioramas have no gallery clip at all and the four peek scenes have one of identical length,
so none needed a split - while seven of the three new enemies' nine pairs differ, six of them by
exactly **0.889 = 8/9**, which is a frame *rate* difference (the same frames at 9 fps in the viewer
against 8 in play). Same build, opposite answers for different scene kinds (§68).

**A substring alias key must be checked against the names it must NOT match.** `peek_werewolf_ride`'s
gallery clip is called `Blinded Beast Ride Gallery Loop` - the peephole, its camera and its audio
all say werewolf, the gallery says the miniboss - so both spellings are mapped. The key is
`Blinded Beast Ride` *with the "Ride"*, because a bare `BlindedBeast` is a substring of
`Gallery_BlindedBeast_Grab_Start` and would hand the miniboss's own grab screens to a peephole
script (§68).

**A gallery twin is a *replay* of its master, not a second derivation — decide which by the sprite
lists, not the durations.** §68 predicted eight of the three new enemies' ten rows would need a
twin, from the clip lengths alone. Reading the sprite names confirmed it and corrected the one it
got wrong:

| relationship between the two clips | what it needs |
|---|---|
| same sprite names, same rate, same ms | **no twin.** `Serpent_Cum`, `BlindedBeast_Start` |
| identical sprite list at a different fps | a frame remap, which then *proves* the flat ratio instead of assuming it |
| same sprites plus one inserted frame | a frame remap; only that one segment stretches |
| a **redrawn** sheet (`sex-Sheet 1_n` against `sex-Sheet_n`) | nothing to anchor on — a plain rescale, and the sweep is the only check it has |

`BlindedBeast_Cum` looked like "a different frame count, so derive it again" and is in fact the
same animation with a frame gameplay drops. A fresh derivation would have discarded a curve that
was already right. **A twin that reads its master's file cannot drift from it**; one derived
separately can, and will (§71).

**Every non-H animator state gets an explicit `-`, and deciding which are non-H is evidence work.**
The Black Serpent's three `Hypnosis` clips look like three missing scripts. They are a crowd-control
mechanic — `BrawlerEnemyAI.hypnosisLookSpeed`, `maxHypnosisDuration`, `StopHypnosis` — and the clips
live on the **enemy's own controller** beside Idle and Walk, not on its grab screen; there is no cum
clip and no grab. Where a state lives is the tell. A sexual script over a combat mechanic is a wrong
scene, and a wrong scene is worse than a missing one because nothing announces it (§71).

**Identify a gallery entry by its asset name, not by the name the player is shown.** 0.3.1 rewrote
all eleven peek entries' `enemyName` into flavour titles — "It'll Fit... See!", "Snussy Ray",
"Making Puppies" — and every peek scene stopped playing, because `enemyName` was one of only two
keys the resolver matched on (the other, `enemyID`, is just `P1`..`P11`). The entry's own asset name
(`ImpThreeWayGalleryData`) and the peephole animator controller it plays (`ImpThreeWayGallery`) both
survived the rename untouched, and are what the map keys on now (§80). Display strings are the
first thing a build changes; positional IDs are the most dangerous thing to key on, because a
renumbering maps confidently to the wrong scene rather than to nothing.

**A peek `EnemyGalleryEntry` leaves `animatorController` null and carries its peephole on
`grabAnimatorController`, with an empty `availableAnimations`.** The step's animation name is always
`"Loop"`, so nothing about the clip identifies the scene — the clip route that works for the
in-world peepholes (`PeekClipMap`, whose clips are named `Peephole_*`) cannot resolve a gallery peek
entry at all (§80).

**`Resources.LoadAll` loads an asset; it does not keep it.** §110 made the Blinded Beast spawnable
by loading the `EnemyData` folder, because no spawner references it and
`Resources.FindObjectsOfTypeAll` only sees what is already in memory. The returned array was logged
and discarded, behind a `_loaded` bool — so Unity's next unused-asset unload collected the assets
again and the latch guaranteed nothing ever reloaded them. The beast spawned once at 15:30 and
reported `no prefab found` eight times from 15:36 on, in one session. Hold the array in a static
field and guard on "do I have it" rather than "did I once ask" (§120).


# Edi integration

What the mod's contract with Edi is, and the Edi behaviour that shapes how a funscript must be written.

**Read this when:** adding a gallery row, changing a funscript's length, or a script plays wrongly on the device

**Keywords:** Definitions.csv, StartTime, EndTime, Loop, Type, variant, InproveLoopDetection, GalleryPath, slice, SendPlay, seek, phase, ladder, axis, multi-axis, TCode, OSR, Intensity, amplitude, slew, hysteresis, chaser stomp, animNormalizedTime, animClipSeconds, audio clock, grace, row hold, PauseFillerForMenu, ResumeFillerFromMenu, seekOverrideMs, CurrentLoopPhaseMs, pause menu filler,
IsGalleryPlaybackActive, FillerPlaybackActive, _fillerSavedWasFiller, ChaserStompRamp, ChaserStompGrace, grabAttemptDuration, isAttemptingGrab, GrabSequence, dash speed, stuck state vs fast signal, ilspycmd measurement

**Edi itself:** source at <https://github.com/NoGRo/Edi>. Documentation and release thread:
<https://discuss.eroscripts.com/t/easy-device-integration-for-games-edi-handy-hps-ble-08-2026/108186>;
how to integrate a game: <https://discuss.eroscripts.com/t/easy-device-integration-edi-how-to-integrate-your-game-now/118446>.
Everything below was read out of that source rather than inferred from behaviour, which is the rule
here: **Edi is open source even though the game is not.**

---

## The contract

The mod's whole contract with Edi is **a row name over HTTP**: `SendPlay` POSTs to
`http://127.0.0.1:5000/Edi/Play/<name>`. Edi looks the name up in `Edi/Gallery/Definitions.csv`,
slices the funscript to `[StartTime, EndTime]`, rebases to zero and plays it, looping if
`Loop=true`. What Edi then does with the curve and the hardware is Edi's concern.

`GalleryRegistry.IsKnown` gates the dispatch and **reads `Definitions.csv` at runtime**, so a new
row name needs no code change - the hardcoded list in `GalleryRegistry` is only a seed.

**Use the address, not `localhost` (§84).** Edi binds `127.0.0.1:5000` — IPv4 loopback only. On
Windows `localhost` resolves to `::1` first, so a POST to `http://localhost:5000` is refused and
the mod does nothing at all; Wine returns `127.0.0.1` first, which is why Proton never showed it.
A hostname is two addresses with a per-platform ordering rule attached, and a server bound to one
of them is reachable by name only where the rule happens to agree. Both ends are ours and the
address is fixed, so the `Url` default and the shipped config both say `http://127.0.0.1:5000`.

**Nothing in the mod's log proves a request was sent.** `FireAndForget` never awaits
`Http.PostAsync`, so connection, proxy and timeout failures fault an unobserved `Task` while
`[EDI] Play <name>` is logged regardless. The proof lives on Edi's side — see
`debugging-and-diagnostics.md`.

**`?seek=<ms>` biases the first pass only; a looping row still loops from 0 (§87).** `Play/{name}`
takes a `[FromQuery] long seek`, and `DeviceBase.CompletePlayback` restarts a `Loop=true` gallery
by passing `elapsed % duration` back through that same parameter - so the seek is consumed once
and never becomes the loop point. That is what makes a phase-preserving switch possible: POST the
incoming row with the phase the outgoing one had reached and the device continues the gesture
instead of snapping to the top. It is also why an authored `?seek=` in an alias (`Gravy_Loop?seek=320`)
does not quietly shorten that row's loop.

**`?seek=` on a `Loop=true` row is broken in Edi's Handy v3 path, and the damage lasts the whole
playback (§104).** `SelectLoopPointsFromSeek` in
`Edi.Core/Device/Handy/Devices/HandyV3Device.cs` rotates the point list to start mid-cycle —
beginning at the point before the seek and appending the head shifted `+duration` — but never
appends the closing point that re-joins the cycle. An unseeked loop does not need one, because a
well-formed looping script carries its own closing point at `t == duration`; the rotation drops
exactly that. `Serpent_Loop` at `seek=493` becomes 1625 ms of buffer for a 1750 ms loop.

That is fatal because `HspPlayRequest` carries a `loop` bool and **no period**. The Handy's own
protocol (`Protocol/constants.proto`) says `loop` means "the buffer is looping after the last
point", so the loop period *is* `last_point_time - first_point_time`. A seeked entry runs a short
cycle against the animation, dropping one segment per wrap and drifting one point-gap per cycle,
with only two syncs per playback and no periodic correction to pull it back.

A `seek=0` Play is immune (`SelectLoopPointsFromSeek` returns early), which is why a cum row
followed by an unseeked loop clears it, and why the fault looks like it follows rapid switching:
every mid-flight ladder switch carries a seek, so rapid switching is correlated with the trigger
rather than being it.

**Confirmed on the hardware in §105**, by polling `GET v3/hsp/state` with `code/handystate.py`:
`Serpent_Loop@428ms` produced `first_point_time=375, last_point_time=2000` - 1625 ms of buffer for
a 1750 ms loop - while an unseeked entry produced `0 → 1750` and played correctly. **The fault does
not drift**, which is the diagnostic tell: a short loop repeats the same wrong thing every cycle,
where a clock or latency fault would wander. **A mod-side fix cannot close it** - Edi seeks on its
own on pause/resume, so suppressing every seek the mod sends still leaves the path reachable.

**Do not read `ExpectedTime:` in `Edilog<date>.txt` as a bug when it exceeds a row's duration.**
It is `seek + (wallclock % duration)` in the *rotated* coordinates the buffer uses, and exceeding
`duration` is normal there. §104 chased that as a second defect and it was not one.

**A set of rows the mod switches between mid-playback is a ladder, and the rows have to agree with
each other (§87).** Edi has no crossfade: a new name re-slices a new file and plays it from the
start. So the seven filler/damage/heat rows are generated together by `code/ladders.py` on one time
grid, anchored at 0 at both ends - and the mod switches with `SendPlay(..., preservePhase: true)`
plus hysteresis on the thresholds. Hand-editing one row of a ladder breaks the property the whole
set exists to have.

**But a ladder is not the only way to grade a scene, and it is usually the worse one (§125).**
`POST /Edi/Intensity/{max}` scales `device.Max` between the bounds configured for the device
*without re-dispatching anything*: `DevicePlayer.Intensity` sets the property, `DeviceBase`
debounces it 100 ms (`rangeTimer`) and calls `applyRange()` in place, and on a Handy that is a
`PUT v2/slide`. Measured on a Handy 2 Pro: the range follows exactly and the playback phase stays
within **22 ms** across six changes, one of them across a loop seam. The serpent's hypnosis was
three rows, then two, then one row plus this - and the tiers, their boundaries, their hysteresis
and their minimum dwell all went with them, because there is no crossing left to protect.

**Three things to know before reaching for it.**

- **It only moves `Max`.** `Min` stays at whatever the user configured, so what it scales is
  amplitude anchored at the bottom of the stroke. A set of rows that widens from *both* ends
  cannot be reproduced by it - which is why the filler's cum rows stayed a ladder (§125).
- **It is global to the channel, not a property of a row.** Whatever lowers it owns raising it,
  and the mod's rule is that any row which is not the lowering scene's own takes the range back
  with it - armed on `SendPlay`, counted down in `Plugin.Update`, because the case that needs it
  most is a grab scene, which is exactly when the scene's own per-frame code is not running.
- **Rate-limit it.** The debounce discards anything faster than 100 ms before it reaches the
  hardware, so a per-frame POST is pure waste.
- **A slew answers a fast-*moving* number; it is the wrong tool for a temporarily-*wrong* one, and
  telling those apart matters (§151, corrected §155).** §151's first instinct, on seeing the chaser
  stomp's target jump in one step when a boss became audible, died, left earshot, or a second one
  became the nearest, was the same fix already used for Intensity elsewhere: cap how fast the held
  value may move (`ChaserStompRamp`, 45 %/s), on the theory that a value which cannot step cannot
  flap. That is true, but it was solving the wrong half of the problem. `ChaserStomp`'s gate is
  distance **and** `loop.isPlaying` - a state boolean, not a continuous reading - and the boolean is
  what actually flickers (a footstep loop restarting, or a real grab attempt: decompiling
  `DragonEnemyAI`/`ProximityDragonEnemyAI` with `ilspycmd` found `GrabSequence` holds
  `isAttemptingGrab` for exactly `grabAttemptDuration`, 1.5 s, win or miss - a real, sustained gate
  loss with no motion behind it at all). Distance itself never flickers. A rate cap applied to the
  combined target damps the boolean's flicker, which is real, but it *also* damps a genuine
  fast approach - closing the whole band in under a second, easily done by dashing - which is not
  noise, it is the exact event the mechanism exists to track, and the cap was reporting it late by
  design. Two different failure modes were sharing one knob only because they happened to move the
  same field. The fix (§155) is to answer them separately: assign the target directly off distance
  the instant the gate reads true (no slew at all, the same distance-driven-and-unramped model
  `SerpentHypnosis` already proved safe on real hardware, see above), and hold the last real value -
  not slew toward a fallback, not recompute from a now-stale reading - across a lost gate for a
  grace period, exactly the way a flapping *row* already had to be handled (below). **Before adding
  a slew, ask whether the discontinuity is the signal or a stuck state riding along with it** - a
  slew only ever answers the former.
- **A grace has to clear the longest *legitimate* gate loss with margin, not merely match it
  (§155).** `ChaserStompGrace` shipped at 1.5 s "the same default as `SerpentHypnosisViewGrace`" -
  a borrowed number, never checked against what it actually had to bridge. It turned out to equal
  `grabAttemptDuration` exactly, which means every single real grab attempt was a coin flip on
  whether the hold survived it, decided by frame timing rather than by the mechanism. Once a grace
  is guarding a *measured* duration rather than an assumed "brief flicker," measure the duration
  (decompile the source of the gate, do not guess it) and pick a grace that clears it with room to
  spare - equal-to-the-hazard is not a margin, it is a race.
- **One channel, so two systems driving it need an explicit rank and a shared reading (§151).**
  `SerpentHypnosis` outranks `ChaserStomp`; the loser stands down on the winner's `OwnsIntensity`
  while still tracking its own value, so it resumes to where the world is rather than where it was.
  And **compare against what the channel was last asked for, not against what you last sent** -
  `Plugin.RequestedIntensity` exists for that. A system that trusts its own last figure will sit on
  a number the device stopped holding the moment anything else wrote one.

**There is nothing to slew between two different funscripts, so a flapping *row* needs a hold, not
a ramp (§153) - and by §155 the row's hold turned out to be the right answer for the flapping
*number* too.** §151 shipped `ChaserAura` as an Intensity squeeze on the filler - amplitude only -
before the mechanism grew a real row (`Dragon_Stomp` / `Wendigo_Stomp`, dispatched instead of the
filler so the device can read as *more* than baseline, which Intensity can never do since it only
ever caps a row's travel down). Once the same flickering gate decided *which funscript plays*, a
ramp could not smooth that - a `POST Play/{name}` either happens or it does not, so a boundary
crossed twice in one second is the device restarting the beat twice in one second. The fix is the
one §112 already used for a different flickering boolean (`hypnosisInView`) and §139 relearned the
general shape of for `STUCK` (`debugging-and-diagnostics.md`): hold the last answer for a grace
period after the gate goes false, and only act on a crossing that survives it. `ChaserStompGrace`
(2.0 s, cleared against a measured 1.5 s hazard - see above) is that grace, now guarding the
intensity target the same way it guards the row. The row never got a slew option in the first
place, which is what exposed the intensity ramp as the odd one out once someone asked why the two
halves of one gate were guarded two different ways.

**`Plugin.SendPlay`'s phase machinery (`animNormalizedTime`/`animClipSeconds`) takes any clock, not
just an Animator's (§153).** It exists for one grab screen whose animation is already mid-loop when
the scene starts (the Black Serpent's), and the two parameters are read generically -
`animNormalizedTime` is "how many clip-lengths have elapsed", `animClipSeconds` is how long one
clip-length is, and the seek is `Mathf.Repeat(animNormalizedTime, cycles) * clipMs` where
`cycles = GalleryRegistry.LoopMs(row) / clipMs`. Nothing in that math is Animator-specific. The
chaser stomp needed the same thing against a *sound* instead - neither `DragonEnemyAI` nor
`ProximityDragonEnemyAI` fires a footstep event, so the only available clock is the creature's own
`idleMovingSound` `AudioSource.time` - and reused the parameters unchanged: `animClipSeconds` is
the funscript's own declared length in seconds (so the phase math and the authored beat can never
drift apart, since both read `GalleryRegistry.LoopMs`), `animNormalizedTime` is
`(source.time - firstOnsetOffset) / period`, where the offset corrects for the one thing the source
clip's own loop point does not know: its *audio file* wraps at its own `t=0`, not at a beat.

**Swapping the device to a different row and back needs its own saved phase, not `preservePhase`
(§154).** The pause menu used to just leave whatever filler was already playing running - which
turned out to be two bugs: the menu heard the last ladder rung or chaser stomp instead of a neutral
row, and if nothing had been dispatched yet that frame nothing started at all. The fix
(`Plugin.PauseFillerForMenu`/`ResumeFillerFromMenu`) force-switches to the plain `FillerGallery` row
on open and restores the original on close - but `SendPlay(..., preservePhase: true)` cannot do the
restoring half, because its equality check (`loopMs == _lastSentLoopMs`) compares the incoming row
against whatever is playing *right now* (the base filler), not against the row being restored. The
two rows only coincidentally share a period. `SendPlay` grew a plain `seekOverrideMs` parameter
instead, fed from `CurrentLoopPhaseMs()` read *before* the swap-away call overwrites `_lastSentRow`/
`LastSentTime`. The general shape: `preservePhase` answers "what phase was the device already
showing", which is only meaningful when the outgoing and incoming row are being compared to each
other; restoring a specific row to a specific saved phase is a different question and needs the
phase captured at save time, handed back explicitly.

**A fix scoped to "the filler" by checking `FillerPlaybackActive` silently excludes every other
row that can be playing (§157).** `PauseGame_Postfix` only called `PauseFillerForMenu` when
`FillerPlaybackActive` was true, so a real gallery row (a grab, an interact scene) fell through to
the plain `SendPause` branch instead - Edi's own pause, which freezes the row exactly where it is
rather than swapping to a neutral one. That was deliberate at the time §154 wrote it ("a grab...
still pauses"), but playing it against a real scene showed the frozen row was not the experience
wanted - the swap-to-neutral behaviour was supposed to be universal, not filler-specific. The gate
widened to `FillerPlaybackActive || IsGalleryPlaybackActive`, and the save/restore pair now branch
on which was active (`_lastFillerGallery` vs `_lastSentRow`) with a `_fillerSavedWasFiller` flag
carried through so the restore's `SendPlay` call reports the right kind back - restoring a real row
under `filler: true` would have left `IsGalleryPlaybackActive` false for as long as it kept playing,
which is exactly the kind of silent state-flag lie this project's checks cannot catch, because nothing
audits *runtime* flag correctness the way `cfgaudit`/`bridgeaudit` audit static wiring. **The general
shape: a boolean named after one case (`FillerPlaybackActive`) is not the same question as "is
anything worth saving playing at all" (`IsGalleryPlaybackActive`, or the OR of both) - check which
one a gate actually needs before reusing a narrow flag that happens to be true in the case that got
tested.**

## Definitions.csv

Columns are `Name, FileName, StartTime, EndTime, Type, Loop`.

- **`InproveLoopDetection` rewrites the last action** to match the first when `Loop=true`.
- **Device `Variant: "None"` mutes it outright** (`DevicePlayer.isStopState`), including
- **Type column** accepts only `filler`, `gallery`, `reaction`. `reactive` silently falls
- **There is no playback-rate column.** Edi can slice a file but cannot time-scale it, so two
  routes that play the same scene at different lengths need **two files**, not one file played
  faster. That is the whole reason the twelve `*_Gallery` rows exist (CHANGELOG §52, §68).
- **Row names must be unique** - Edi throws on duplicates.
- **The variant is the folder name.** `Edi/Gallery/handy2pro/` and `handy1/` are variants; a
  device's `"Variant"` in `EdiConfig.json` selects one. Per-device scripts therefore need no mod
  change at all.
- Filenames must avoid Edi's magic tokens: a `.` in the stem sets the variant, and `[loop]`,
  `[nonLoop]`, `[Gallery]`, `[Filler]`, `[Reaction]` set flags (`Edi.Core/Gallery/Discover.cs`).


## Multi-axis: one row, several funscripts

**An axis is a filename token, not a Definitions row.** A row's extra axes are files beside its own
script in the same variant folder:

    Edi/Gallery/handy2pro/nun_grab.funscript          the stroke (Axis.Default)
    Edi/Gallery/handy2pro/nun_grab.twist.funscript    the same row's twist
    Edi/Gallery/handy2pro/nun_grab.roll.funscript     ... and roll

`FunScriptFile.axis` takes the **last dot-separated token of the filename without its extension**
and parses it against the `Axis` enum, case-insensitively; `DiscoverExtension.Discover` strips that
token out of the variant it computed, so the **folder** still names the variant.
`FunscriptRepository.ReadGallery` then files each script into `gallery.AxesCommands[axis]` under the
same row name. So a new axis needs **no Definitions.csv row, no config entry and no mod change** -
`Definitions.csv` keeps one row per scene and its slice applies to every axis of it.

The axes, and where an OSR-style device sends them (`OSRPosition`, TCode channels):

| axis | TCode | axis | TCode |
|---|---|---|---|
| `Default` (the stroke) | L0 | `Pitch` | R2 |
| `Surge` | L1 | `Vibrate` | V0 |
| `Sway` | L2 | `Valve` | A0 |
| `Twist` | R0 | `Suction` | A1 |
| `Roll` | R1 | `Frequency`, `Volume`, `PulseWidth` | e-stim (DG-Lab), not TCode |

Five things worth knowing before writing any:

- **An unwritten axis is not silent, it is centred.** `OSRScript` starts every axis it has no script
  for at **50**, except `Default` and `Vibrate` which start at 0. Script only what moves.
- **Positions stay 0-100 on every axis.** There is no per-axis range or unit; what 0 and 100 mean
  physically is the device's business.
- **An axis file is inert on hardware that has no such axis.** A Handy plays `Default` and nothing
  else, so adding `nun_grab.twist.funscript` cannot break the single-axis case - which is what makes
  multi-axis safe to add incrementally, one scene at a time.
- **A row filename must contain no dot for any other purpose.** A dot is how Edi names a variant
  (`name.variant.axis` for a three-part stem) or an axis (two parts, when the token is a reserved
  one). This is the same rule the naming pass already followed; multi-axis is what makes breaking it
  expensive.
- **Every slice rule above applies per axis file.** `InproveLoopDetection` rewrites each one's last
  action to match its own first, so a loop that closes on the stroke axis and not on the twist axis
  will step the twist at the seam.

What this repo's tooling does with them, all as of §89: `speedcheck.py` lists each axis on its own
line and applies the mm/s ceilings to the **linear** axes only (`Default`, `Surge`) - a cap derived
from a stroke length says nothing about degrees; `variants.py` copies per-axis scripts into `handy1/`
**unchanged** rather than slew-limiting them, and reports any that exist in a variant with no master;
`release.py` and `deploy.py` glob `*.funscript`, so axis files ship and deploy with no change; and
`refvideo.py`'s sidecars carry a screen-space motion track (`motion.travel_x_px`, `centroid_x_px`)
that answers "does anything in this scene move sideways, and when".

## Slice semantics, exactly

`inproveLoopAccion` (`Edi.Core/Gallery/Funscript/FunscriptRepository.cs`) does more than filter by
time when `Loop=true`:

- actions where `StartTime <= at <= EndTime`
- if the first action is more than **100 ms** past `StartTime`, insert a point at `StartTime`
  taking its position from **the action before the window** - content outside the slice
- likewise at `EndTime`, from the action after the window
- otherwise snap the first/last action onto the exact bounds
- finally force `last.pos = first.pos`

So a naive "copy the actions in range" split changes playback wherever a slice edge borrowed a
neighbour. **Edi is open source** (`github.com/NoGRo/Edi`) even though the game is not - read it
rather than reverse-engineering its behaviour.

**Edi reads `Definitions.csv` and the variant folders once, at its own startup, so anything the mod
writes there later is invisible until Edi restarts.** That is why a package's funscripts are copied
and its rows merged for every custom-enemy package whether or not it is switched on (§173). §170 had
made a switched-off code package import nothing, which reads well as a rule and means that the day
someone enables a package they must restart the game *and* Edi — and until they do, the package is
running and the device is silent, with nothing saying why. The switch is meant to cost a game
restart; it must not quietly cost an Edi restart too. **A funscript is inert data in a file Edi
parses, not something a package runs**, so importing one costs nothing the switch is protecting.


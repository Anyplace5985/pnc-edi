# Choosing and trusting a motion proxy

What to measure in a frame, how to know the proxy is watching the right thing, and why polarity is not measurable.

**Read this when:** picking what to track in a new scene, or a polarity flag (INV / ?) needs judging

**Keywords:** proxy, polarity, inversion, correlation, region vs frame, alpha trim, alignment, jitter floor, residual, deep=0, onset detection, footfall, spectral flux, minimum gap

---

**Answer "what moves at all" before choosing anything to measure.** `animcheck.py --motion` draws
per-pixel variance over frame 0. Read it for *where* change is concentrated, not how much: a thin
outline all round a body is that body translating a pixel or two, a bright blob in one place is a
part moving against the rest, and only the second is worth a proxy.

**Choose a region by what varies in it, not by where the interesting thing looks like it is.** The
first band for `dragon squat ride` was picked by eye and its edge clipped the partner's raised
knee, so the proxy sometimes measured the knee. Taking the columns whose top edge travels furthest
put it on the shaft instead. Then **look at the mask itself**, drawn over the frames with the
picked pixel marked - that is what made the mistake obvious, where the output alone looked
plausible.

**A proxy that takes `sprites` must align them itself; nothing upstream does.** Sprites are
alpha-trimmed per frame to different sizes (`dragon squat ride` runs 363x281 down to 355x284), so
a band taken as a fraction of each frame's own `.shape` samples a different absolute column every
frame and reads y against a different origin. That returned a near-flat series for a shaft that
travels 27 px and got a correct curve flagged **INV at -0.84**. Paste onto one canvas against the
shared bottom edge first. §33 said it for differencing; it is true of every measurement.

**A repeat is how you tell a residual proxy from noise.** The peek scenes are full-bleed room art,
so the silhouette proxy is dead - but the room is static, which makes the median frame a background
plate worth subtracting (`proxies.moving_mass`). Where the motion is small relative to the frame
that residual is dominated by whatever else differs: `GargoylePeep_Loop`'s halves are proven
identical to within 1-2% of pixels, and the proxy still returned two different series for them.
**Both cannot be true, and that is the test.** `peek_gravy_bath` ran the same proxy and repeated
exactly, which is what says its signal is real.

**Period is a fact, shape is sometimes a decision - say which.** Three of the six dioramas added in
0.3.1 move at or under the 3%-of-height floor that already counts as jitter. Those are authored on
a *measured* period, and `code/scenes031.py` records per scene which half is which. Reproducing a
5 px wobble would be scripting pixel noise and calling it measurement.

**A proxy that sees nothing is not evidence that nothing happens (§97).** `BlindedBeast_Cum_T`'s
2.5 s seated hold was scripted on whole-frame difference, because the clip changes geometry partway
through and no single proxy measures it end to end. That number reads 1.5-2.3 across the hold's
biggest event, so the hold got one burst and it was on the smallest of three. A mask for the fluid,
over the same fourteen frames, separates them outright (9 -> 315 px, the surge +120 in one frame).
When a clip is exempt from a whole-clip correlation, that exempts the *correlation* - each phase
still needs a proxy chosen for it. The same pass disproved the hypothesis it set out to script: the
shaft that was supposed to shake spans identical columns in all fourteen frames and its top edge
moves 3 px, under the jitter floor. **Measure the thing the play names before scripting it** - a
play locates the phase reliably and names the cause only sometimes.

**Register the proxy rather than exempting the scene.** Marking a scene `AUTHORED` silences the
sweep; registering what it was actually measured against keeps it checked. The alignment bug above
was only visible *because* the curve was being re-measured against a named proxy - an exempt scene
would have shipped it.

The best results came from the user describing what moves on screen:
head size, a locked deepthroat, "down then vibrate then up". Those turned unmeasurable
scenes into the most accurate scripts in the set. When a scene resists measurement, ask
what to track rather than trying harder algorithms.

Sprite animations mean the exact frame sequence, period and motion come out of the shipped
assets — no capture, none of the measurement traps above. But the direction is not inferable.
"Higher on screen" means withdrawn in some scenes and deeper in others, and a feel pass
found the automatic verdict wrong on five of ten flagged scenes. **Timing: trust the tool.
Polarity: use it to rank what to look at, then look.** A contact sheet turns each check into
seconds, which is the real win over capturing video.

**Sleeve and rider are the same measurement with opposite signs, and only the staging tells them
apart.** The rule above generalises into the one decision this work has no numerical check for.

| | where the exposed shaft is | most exposed means |
|---|---|---|
| **sleeve** — the shaft passes *through* the body | on the far side, beyond it | the body has slid to the **base**: deep, pos 0 |
| **rider** — the body sits *on* the shaft | below the body | the body has **lifted**: withdrawn, pos 100 |

The Black Serpent's paizuri is a sleeve (§71), the Blinded Beast and the GoonShroom are riders,
and §67's two squat-ride dioramas are riders. All four proxies are "count the pale pixels near the
middle", all four produce a high-range well-correlated series, and all four are half wrong if you
guess. **Ask what the shaft passes through before normalising anything.**

**A second clip of the same scene is the cheapest polarity check there is.** The Black Serpent's
loop clip invites the wrong reading — nothing shows at the top of its stroke, which reads equally
well as "fully sheathed" or "pulled clear". Its *cum* clip settles it: the middle fourteen frames
are her mouth on it, the cleavage count collapses there, and it collapses because **her head is in
front of the band**. Once the same number is visibly an occlusion measurement in one clip, the
question "what is it measuring in the other" gets asked properly. Where a scene has a loop and a
cum, derive both before committing to either's sign (§71).

**A clip that changes what the camera is looking at needs one proxy per phase, not one per clip.**
Four of the five 0.3.1 cum screens do: a paizuri becomes oral becomes a pull-off; a rider seats
itself and the column it was measured by is occluded for 23 of 33 frames; a pink shaft mask starts
measuring fluid at f23. Every position in those curves still came off the frames — but a
correlation taken across the whole clip compares two different scenes and answers nothing, so they
are registered in `proxies.AUTHORED` with a note saying which. **`AUTHORED` means "no single proxy
applies", not "invented"** — and the alternative is a permanent `INV` that makes every future sweep
re-flag correct work (§71).

**Engulfing the tip and being penetrated through are opposite signs.** Where a mouth or hand works
the tip, exposed shaft means withdrawn. Where the shaft passes *through* a body — the gooper is a
slime with the shaft straight through it — that body is a sleeve riding the shaft, and shaft
showing above it means it has slid down to the **base**, which is deep. Same measurement, opposite
mapping. `ambient_gooper_bed_blowjob` was derived under the wrong one of these (§39) and read
perfectly against its own proxy the whole time.

**An inversion rule is about a *quantity*, not about a scene.** §39's finding — that the gooper is
a sleeve with the shaft passing through it, so visible shaft means *deep* — inverts a
**shaft-exposure** proxy. It does not invert a **body-position** proxy, and the two Gooper grab
screens are measured by the latter (the head's own height). The shaft rises from the player at the
bottom of frame in both geometries, so head-low is deep whether she is on the tip or sleeved on
it. Same creature, same family of scene, rule correctly not applied. Before carrying an inversion
across, ask what it was an inversion *of*.

**Hold a derived artefact to the standard of the set, not to whether anyone noticed.** The
gallery split was first scoped by a ~1.1x perceptibility threshold from a feel pass, leaving
six rows 6-11% off. That is inconsistent: `animsweep` calls anything past 0.5% not-ok and the set
has been whole-cycle exact since §48. Perceptibility is the right bar for *how a curve feels*
(range, buzz density); it is the wrong bar for *whether it is in sync*, which is objective and
already has a tool. All twelve are split as of §53.

**Judge a derived artefact in the units it was derived in.** A gallery script replayed from an
in-game master was held to the master's millisecond point spacing - correct while the gallery clip
was slower, wrong the moment one was faster (9 fps against 8), where it rejected a correct file.
The bar is "no worse than its source, measured in frames".

**A scene has two animations, and `animsweep.MAP` only names one.** The gallery viewer plays its
own `Gallery_*` clips, and 12 of 29 rows differ in length from the in-game clip — `Nun_Cum` is
3300 ms in play and 5500 in the gallery. One funscript cannot be whole-cycle correct for both, so
"right in gameplay, off in the gallery" is a *routing* symptom, not a curve defect, and no amount
of playing fixes it. `code/gallerydiff.py` has the table. Splitting is possible without a
rebuild: in-game lookups check `InGameAliases` first and fall back to `GalleryAliases`, gallery
lookups read `GalleryAliases` only. Reported ratios put the **perceptibility threshold near 1.1** —
1.167× and worse were noticed in play, 1.065× and below were not.

**Clip names are not unique.** `Gallery_Nun_Grab` is two different clips (600 ms @10fps grab
screen, 1625 ms @8fps enemy grab), and `clip_frames` returns whichever the asset walk reaches
first. Any tool that looks a clip up by name has to collect *all* matches and say which it took,
or it will invent a discrepancy — that one reported `Nun_Grab` as 2.7× off when the two grab
screens are identical.

**A mid positive correlation from the wrong proxy is worth nothing.** `Wendigo_Continued` scored
+0.45 — inside "polarity agrees" — while running exactly backwards, because every frame is
full-bleed with no alpha trim, so the fallback proxy tracked the cyan spill rather than either
body. The known rule is "a low correlation only means look at this one"; the corollary is that a
*middling* one means the same. Only +0.9 and up is evidence, and only from a proxy you have
confirmed is watching the thing that moves. Note also that this scene's mover is the **partner**,
not the creature — the convention everywhere else in the set.

**A correlation validates consistency, never orientation.** An inverted script measured against an
inverted proxy scores +1.000. Every `r` in this project answers "does the script follow the proxy",
not "is the proxy pointing the right way" — that second question is a claim about what is
happening on screen, and only looking (or being told) settles it.

**A bad polarity reading is more often a bad proxy than a bad script — and inverting cannot fix
phase.** Of the four scenes reworked in §35–§37, three were flagged INV or ambiguous and *none*
was actually inverted. `ambient_nun_wall_chain_head` was 275 ms out of phase (a third of its
cycle), which reads exactly like an inversion and which flipping the sign makes worse.
`ambient_gooper_bed_blowjob`'s silhouette tracked the slime's own body, peaking a frame before the
act did. The fix in both cases was a scene-specific proxy, and those live in `code/proxies.py` so
the sweep prints `own` and stops re-flagging them. Register a proxy there rather than leaving a
known-good scene permanently accused.

**And a correlation means nothing until the periods match.** The sweep samples a script at the
animation's period, so if the script's own stroke rate differs the phase drifts across cycles and
the sign is noise. `imp_1` read INV −0.63 with its rate 1.56× off; `ambient_imp_gangbang_2` read
+0.900 with its rate 0.96× off. Once the rates agreed they became +1.000 and +0.442 — one flag
was never a polarity problem and the other was never a good match. **Check the rate before
reading the sign.** And note that whole-cycle length says nothing about rate: `imp_1` sat at
exactly 11.000 cycles the whole time it was running 1.56× too slow.

Also: a clip's own length is not necessarily its stroke period — `imp gangbang` is 1250 ms
holding two identical strokes. Check frame self-similarity before retiming anything.

**A cycle count is not a stroke count, and rounding one hides the other.** `retime` targets
`round(script_length / cycle) * cycle`, so `Gooper_Start`'s 2046 ms against an 800 ms animation
became 2.557 → 3 cycles → "stretch to 2400" — for a script that already ran 28% *too slow*. The
script visibly holds two strokes; the right target was 1600. Count the script's own strokes before
believing any target derived from its length, especially when the cycle count lands near .5 (§48).

**Two strokes in one clip need not be equal.** `GooperGrabScreenCum` is 800 ms then 600 ms — its
second stroke reuses frames 0,1,4,5,6,7, skipping the two mid-descent ones. A script with two
equal strokes cannot be fitted to that by any scale, which is exactly what "15.93% off, nearest
target nonsense" was telling us. §33 found the mirror case (two strokes hiding inside one clip);
this is two visible strokes wrongly assumed identical.

**"Bit-identical frames" says the picture didn't change, not that the scene didn't.** `GhoulGrabCum`
has 17 of 33 frames byte-for-byte identical and reads as 2.7 s of nothing. Differencing each frame
against a *fixed* reference pose — the medoid, which is necessarily inside the static stretch —
finds two twitches the neighbour-difference drowns, because the descent and the lift are two
orders of magnitude larger. In `PlantashaCum` those twitches land on precisely the frames where
new cum appears, so the twitch *is* the spurt and it is where a buzz belongs. A frame-to-frame
difference will never show you this; a distance-from-rest will (`proxies.nun_cum_motion`).

**Not every clip is a scene.** A third of `WendigoKiss` is a wipe to black — by its last frame the
whole picture is 129k black pixels. Scripting motion there is scripting to something that is not
on screen. Check what is actually *in* the late frames of any "Start" clip before matching its
full length; these are cinematics that hand over to a loop.

**The scripts were authored against clip duration — 20 of 51 proved it before anything changed.**
Those 20 already sat at exactly N.000 cycles despite coming from five authors across three eras.
A criterion that lands 20 independent scenes on the nose is measuring something real, and that is
what licenses treating the rest as defects instead of doubting the model. Look for this kind of
self-validation before running a bulk change: if the rule doesn't already explain most of the
data, it isn't a rule. (`m_AnimationClipSettings.m_LoopTime` looks like it should answer whether
a clip loops. It is False on all 51, dioramas included, so it answers nothing — looping comes
from the animator state.)

**When two characters are doing different things, measure the region, not the frame.** The 3-imp
grapple is full-screen art with no alpha trim, so the silhouette proxy is dead and signed
displacement averages the imp on the tip, the imp on the balls, tails and background into mush —
which is why both scripts felt arbitrary. A colour mask fixes it: the shaft is tan
(`R>150,G>100,B>80`), the imps are deep red (`G≈54`), so tan pixels in a row band measure how much
of the shaft that band exposes. Tip and balls then come out clean and **in anti-phase**, which is
proof no single whole-frame number could have described the scene.

That also exposed a trap: `stroke_period` reports reps=4 for `Imp_Grab_Cum` and is right about the
pixels — the *balls* imp does repeat its 875 ms bob four times. The tip imp descends, holds deep
for two cycles and releases, i.e. one 3500 ms arc. A repeat count is only as meaningful as the
region it was measured over. See `code/impgrab.py`.

**Length and rate fail independently — check both.** `imp_1` sat at exactly 11.000 cycles of its
animation while stroking 1.56× slower than it, so every length-based check said "ok" while the
device visibly lagged the picture. `retime.py`'s `rate` column exists for this. Its animation-side
figure is proxy-derived and only trustworthy where the cycle plausibly *is* one stroke, so treat
it like polarity: it ranks what to look at.

**A silhouette that barely moves is jitter, not signal.** Sprites are alpha-trimmed per frame, so
a pinned outline still wobbles a few px. Switching proxies only when the range is *exactly* zero
lets 3 px of trim noise masquerade as motion and invent strokes. Test the range as a fraction of
sprite height (3% works here) — `motion_proxy()` in `animcheck.py`.

**Retime by scaling, not trimming, and cap the scale.** Under ~5% is below the just-noticeable
difference for stroke timing, so it removes drift without changing feel — and it stays harmless
whether or not the scene actually loops. Above that you are changing the performance, which is a
feel decision, not a measurement one. `code/retime.py` enforces the split.

**An onset detector's minimum-gap parameter has to match the true event rate, or a swelling
background reads as extra events.** Building the chaser stomp funscripts (§153) needed the real
footfall cadence out of `DragonWalk.wav` and `Wendigo_walk.wav`, and a spectral-flux onset
detector tuned with a 120-150 ms minimum gap between candidates found 150 dragon hits and 22-35
wendigo hits — both wrong, both with high-variance gaps (dragon std 59 ms, wendigo std up to 143
ms) that never settled no matter how the frequency band or threshold were retuned. The wendigo clip
carries a low drone that swells and recedes between real footfalls (heard, not measured — "an
ominous hum" was the description that broke the case), and a fine gate reads its rise as a
transient of its own. Widening the minimum gap to 350 ms - roughly matched to the beat the ear
already suspected - resolved both: dragon settled to 43 onsets at 605 ms mean gap (std 19 ms, and
confirmed against a plain 43-by-ear count), wendigo to 12 onsets at 603 ms (std 37 ms). **A
detector parameter that is supposed to reject noise cannot itself be tuned by the same detector** -
each retry here only proved the gate was still too fine by producing the same shape of wrong
answer (many hits, high variance) at every band and threshold tried; what actually broke the
deadlock was a human ear giving the true count first, which then said which parameter was the
free one. Trust it over the algorithm when they disagree and neither can explain why.

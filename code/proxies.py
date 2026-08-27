#!/usr/bin/env python3
"""Scene-specific motion proxies.

`animcheck.motion_proxy` picks between the silhouette top edge and signed displacement, and that
covers 48 of 51 scenes. It cannot cover the rest, because those have something in frame that a
whole-frame statistic averages away:

  imp_grab_loop / imp_grab_cum   two imps doing different things at once (CHANGELOG 35)
  ambient_nun_wall_chain_head    the outline is pinned - she kneels, the chained figure hangs -
                                 so nothing about the silhouette moves; the motion is the width
                                 of her hood (CHANGELOG 37)
  ambient_gooper_bed_blowjob     the silhouette is the slime's own body, which peaks a frame
                                 before the act does; the motion is where the slime sits along
                                 a shaft that passes through it (CHANGELOG 37, polarity 39)
  Dragon_Cum                     the frame is almost entirely dragon; the act is the ~1300 px of
                                 shaft visible under her at bottom centre (CHANGELOG 38)
  Gravy_Loop2                    she is seated for over half the cycle; the act is the pale shaft
                                 below her, visible in only 3 of 7 frames (CHANGELOG 40)
  Plantasha_Start / _Cum         the bulb's outline barely changes; the act is how much shaft
                                 shows between her lips (CHANGELOG 48)
  Nun_Cum                        she is seated and motionless for 2.7 of 3.3 s; the act is the
                                 distance from that seated pose (CHANGELOG 48)

Without this registry `animsweep` reports these as INV forever and `retime` invents a stroke rate
for them, so every future pass re-flags scenes that were derived from the animation and are
correct. Everything registered here matches its own proxy at r >= +0.90; the sweep's generic
columns simply do not apply.

A proxy returns one value per frame, larger = withdrawn = pos 100, same convention as the
built-ins.
"""
import numpy as np

TAN = dict(TIP=(100, 120), XS=(180, 300))
HOOD = (90, 135)


def imp_tip(sprites):
    """Tan (shaft) pixels exposed at the tip. More = the imp's mouth is off it = withdrawn."""
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGB")).astype(int)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R > 150) & (G > 100) & (B > 80)          # shaft is tan; the imps are deep red
        out.append(float(m[TAN["TIP"][0]:TAN["TIP"][1], TAN["XS"][0]:TAN["XS"][1]].sum()))
    return out


def nun_hood(sprites):
    """Mean width of the black hood. Narrowest = deepest = 0, per the on-screen cue."""
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGBA")).astype(int)
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (R < 45) & (G < 45) & (B < 45)
        rows = [r.sum() for r in m[HOOD[0]:HOOD[1]] if r.any()]
        out.append(float(np.mean(rows)) if rows else 0.0)
    return out


# Scenes whose motion is a single arc, not a repeating cycle. `stroke_period` sees the *other*
# actor repeating and reports reps>1, so folding the script into cycles compares an arc against
# its own average and yields noise. Compare over the whole clip instead.
ONESHOT = {"imp_grab_cum", "imp_grab_cum_Gallery"}

# The mirror of ONESHOT: clips `stroke_period` reports as ONE cycle that demonstrably hold N.
#
# `GravyPeep_Loop` is 12 frames and its halves are the same motion - frames k and k+6 differ in
# 1.2-2.2% of pixels at a mean |diff| under 0.8/255, and the moving-mass centroid repeats to
# within a point. `stroke_period` still calls it reps=1, because a peek scene is full-bleed room
# art where ~95% of every frame is identical *static background*: that swamps the lag score and
# flattens the difference between the right lag and any other. §33 is the same failure from the
# other side, where a 1 px offset inflated a lag score past its threshold.
#
# Without this the sweep measures the script against the clip's 1333 ms rather than the stroke's
# 667 and reports a whole-cycle script as OFF at 2.5 cycles.
SPLIT = {"peek_gravy_bath": 2}

# Scenes whose curve is a deliberate authoring decision rather than a tracked measurement, so a
# correlation against any proxy is meaningless by construction. `Baphomet_Start` is scripted as a
# vibration during the tongue phase *instead of* following her head, on the guide's advice for
# lateral/tongue work; `Baphomet_Cum` is a pulse at the bottom of a clip in which nothing rises.
# `Wendigo_Start` spends its last 1.8 s wiping to black, and is scripted to wind down across that
# rather than to follow a picture that is no longer there (CHANGELOG 48).
# Reported by animsweep as "auth" with no r, so nobody reads the low number as a defect.
AUTHORED = {"Baphomet_Start", "Baphomet_Cum", "Wendigo_Start", "Wendigo_Start_Gallery",
            # Game 0.3.1. Each of these has a *measured period* and a written shape, because the
            # animation's own travel is at or under the 3%-of-height floor `motion_proxy` treats
            # as jitter - see code/scenes031.py for the frame evidence per scene. Correlating a
            # written curve against a proxy that measures noise answers nothing.
            "ambient_goonshroom_gangbang",   # 5 px on a 181 px sprite, whole-sprite shimmer
            "ambient_nun_watersports",       # two poses, one pixel apart; a swell, not a stroke
            "ambient_serpent_wall_blowjob",  # a 4-frame hold and a 17 px pull-off
            "peek_serpent_prison",           # 5 frames, and the diff mask catches the fluid
            "peek_werewolf_ride",            # same
            "peek_gargoyle_fuck_fest",       # halves proven identical, residual centroid was not
            # The 0.3.1 grab screens whose clip changes *geometry* partway through, so that no
            # single proxy is measuring the same thing at both ends. These are not authored in
            # the sense the four above are - every position in them came off the frames - but a
            # correlation over the whole clip compares two different scenes and answers nothing.
            "Serpent_Cum",                   # paizuri, then her mouth on it, then a pull-off
            "BlindedBeast_Cum",              # the column is occluded for 23 of 33 frames
            "BlindedBeast_Cum_Gallery",
            "BlindedBeast_Cum_T",            # measured to f9, then a hold and the cum bursts
            "BlindedBeast_Cum_T_Gallery"}


def gooper_shaft(sprites):
    """Where the slime sits along the shaft. Returns high = withdrawn, per the convention.

    The slime is (134,180,102) and the shaft (100,113,69) - both green, but the slime's G-R is
    ~46 against the shaft's ~12, which separates them cleanly. Frames are bottom-aligned first,
    because this sheet is trimmed per frame and the body height itself changes.

    **The sign is inverted, and that is the whole point of this scene.** The shaft passes THROUGH
    the slime body, so the slime is a sleeve travelling along it rather than a mouth on the tip.
    More shaft showing above the slime means the slime has slid DOWN to the base - which is deep,
    not withdrawn. Frame 0 has the least showing (117 px, slime riding high near the tip = 100)
    and frame 3 the most (383 px, slime at the base = 0). Reading it the other way round, as a
    mouth-on-tip scene, gets the scene exactly backwards."""
    H = max(s.read().image.size[1] for s in sprites)
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGBA")).astype(int)
        pad = np.zeros((H, a.shape[1], 4), int); pad[H - a.shape[0]:] = a
        R, G, B, Al = pad[..., 0], pad[..., 1], pad[..., 2], pad[..., 3]
        m = (Al > 128) & (G - R < 25) & (G > 100) & (G < 140) & (R > 85) & (R < 125) \
            & (B > 55) & (B < 95)
        out.append(-float(m.sum()))       # negated: more exposed = slime at the base = deep
    return out


def dragon_shaft(sprites):
    """Cream shaft visible below the dragon at bottom centre. More showing = withdrawn.

    The dragon fills the frame in deep red (R-B ~64 at R~94), so a cream mask with R>150 and a
    small R-B separates the ~700-1400 px of shaft cleanly. The user's cue for this scene was
    exactly this: follow the penis of the character lying on the ground, not the overall mass."""
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGB")).astype(int)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R > 150) & (G > 120) & (B > 110) & (R - B < 90)
        out.append(float(m[150:250, 190:290].sum()))
    return out


def plantasha_shaft(sprites):
    """Shaft visible between her lips at bottom centre. More showing = withdrawn.

    She is a purple bulb with pink lips and the shaft is mid-brown (129,99,77) with a pale
    highlight (179,161,148); the lips are (217,87,99). Brown and pink are both "reddish", so the
    separator is R-G: the shaft sits at ~30 and the lips at ~130. Restricting to the bottom-centre
    band drops the tan sliver of the player's own body at the frame edge.

    This is a mouth-on-tip scene, not a sleeve like `gooper_shaft` - the shaft ends inside her, so
    more of it showing really does mean withdrawn and the sign needs no flip. Frame 0 shows none of
    it (fully taken) and frame 4 the most."""
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGBA")).astype(int)
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (R > 95) & (R < 215) & (R - G > 12) & (R - G < 50) \
            & (G - B > 8) & (G - B < 40)
        H, W = m.shape
        out.append(float(m[int(H * 0.70):, int(W * 0.33):int(W * 0.67)].sum()))
    return out


def nun_cum_motion(sprites):
    """How far she is from her seated pose. Larger = further off it = withdrawn.

    Her silhouette is pinned (she fills the frame) and signed displacement reads the drips rather
    than her body, so both built-in proxies miss what this clip does. What it does do is sit
    perfectly still: 17 of its 33 frames are bit-identical. So take the medoid frame - which is
    necessarily one of those - as "seated", and measure every frame's distance from it.

    That is a magnitude, and ../learnings/funscript-timing.md warns magnitudes give the
    half-period. It is safe *here*
    only because the pose never crosses the reference: she is seated or above it, never below, so
    distance-from-seated is monotone in withdrawal. Do not reuse this on a scene that strokes
    through its own rest pose - it would fold the two halves together.

    Picking the medoid rather than a hardcoded index matters: it is what makes the 300 ms descent,
    the two cum twitches at 900 and 2100 ms and the 300 ms lift come out as the only four events,
    which is exactly what the frames show."""
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.size[0] for i in ims); H = max(i.size[1] for i in ims)
    st = np.zeros((len(ims), H, W, 4), np.float32)
    for k, im in enumerate(ims):
        a = np.array(im).astype(np.float32)
        st[k, H - a.shape[0]:H, :a.shape[1]] = a          # bottom-aligned, as in game
    lum = st[..., :3].mean(3) * (st[..., 3] / 255.0)
    d = np.abs(lum[:, None] - lum[None, :]).mean((2, 3))  # pairwise frame distance
    base = int(d.sum(1).argmin())                         # medoid = the pose it rests in
    return [float(x) for x in d[base]]


def wendigo_top(sprites):
    """Vertical position of the pale figure on top. Higher on screen = withdrawn.

    Returned negated, because the raw measurement is a y centroid and y grows *downward*: the
    figure being low on screen is him seated, which is deep.

    Every frame of `WendigoSex` is a full 480x270 with no alpha trim, so the silhouette proxy has
    nothing to bite on and `signed_shift` reads the drips rather than either body - it scored
    +0.45 against a curve that was actually inverted, which is exactly the "a low correlation only
    means look at this one" case from ../learnings/funscript-proxies.md.

    **The mover here is the partner on top, not the enemy** - unusual for this set, where the
    convention is to follow the creature. He is the warm mid-tone (193,161,141): R>G>B with R-B
    around 52, which separates him from the wendigo's near-black (27,22,23, R-B=4) and from the
    pale cyan spill (212,211,203, R-B=9). Restricting to the middle 53% of the width drops the
    scenery at the edges."""
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGBA")).astype(int)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        m = (R > 150) & (R < 225) & (R - B > 30) & (R - B < 75) & (R - G > 20) & (R - G < 50)
        H, W = m.shape
        m = m[:, int(W * 0.25):int(W * 0.78)]
        rows = np.arange(m.shape[0])[:, None]
        out.append(-float((rows * m).sum() / max(m.sum(), 1)))
    return out


def gravy_shaft(sprites):
    """Pale shaft visible below Gravy. More showing = withdrawn.

    Near-white against her tan/brown, and present in only 3 of the 7 frames (904, 725, 259 px) -
    she is seated for the rest, which is the long bottom dwell the authored bounce sits in."""
    H = max(s.read().image.size[1] for s in sprites)
    out = []
    for s in sprites:
        a = np.array(s.read().image.convert("RGBA")).astype(int)
        pad = np.zeros((H, a.shape[1], 4), int); pad[H - a.shape[0]:] = a
        R, G, B, Al = pad[..., 0], pad[..., 1], pad[..., 2], pad[..., 3]
        m = (Al > 128) & (R > 195) & (G > 185) & (B > 175)
        out.append(float(m[:, 190:290].sum()))
    return out


def squat_ride_shaft(band):
    """Topmost pale pixel in a narrow band: the shaft tip where the rider's underside crosses it.

    For the two squat-ride dioramas (game 0.3.1). The rider is the whole frame and the partner is
    static, so the generic proxy tracks wings, horns and antlers. The band has to be *narrow* and
    centred on the shaft: widen it and the partner's raised thighs, which are pale, static and
    higher up, pin the reading flat.

    Exposed shaft is *below* the rider here, so more of it showing means the rider has lifted =
    withdrawn. That is not §39's gooper geometry, where the shaft passed through the body and
    showed above it. Returned unflipped, i.e. larger = withdrawn, which is what the sweep wants.

    **Every frame is pasted onto one canvas first, anchored to the shared bottom edge.** Sprites
    are alpha-trimmed per frame and the trim is not the same on each - `dragon squat ride` runs
    363x281 down to 355x284 - so taking the band as a fraction of each frame's *own* `.shape`
    samples a different absolute column every frame and reads the y against a different origin.
    Written that way this proxy returned a near-flat 33, 26, 26, 26, 26, 28 for a scene whose
    shaft demonstrably travels 27 px, and the sweep called the curve inverted at -0.84. §33 said
    it already: alpha-trimmed sheets are not registered to each other, align before differencing.
    A proxy that takes `sprites` has to do that alignment itself; nothing upstream does it."""
    x0f, x1f, y0f = band

    def fn(sprites):
        ims = [s.read().image.convert("RGBA") for s in sprites]
        W = max(i.width for i in ims); H = max(i.height for i in ims)
        out = []
        for im in ims:
            a = np.zeros((H, W, 4), dtype=int)
            a[H - im.height:, :im.width] = np.array(im).astype(int)
            R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
            m = (Al > 128) & (R > 120) & (G > 95) & (B > 80) & (R - G < 60)
            m[:int(H * y0f), :] = False
            rows = np.nonzero(m[:, int(W * x0f):int(W * x1f)].any(axis=1))[0]
            out.append(float(H - rows.min()) if len(rows) else 0.0)
        return out
    return fn


def moving_mass(sprites):
    """Centroid height of whatever differs from the median frame. For the peek scenes.

    A peek scene is full-bleed room art behind a keyhole vignette, so there is no alpha trim and
    the silhouette proxy is dead - ../learnings/funscript-proxies.md's `Wendigo_Continued` problem,
    where the fallback
    tracked the background spill rather than either body. But the *room is static*, which makes the
    median frame a background plate: subtract it and what is left is the bodies.

    Returns height above the frame bottom, so larger = higher on screen = withdrawn, matching the
    sweep's convention."""
    ims = [np.array(s.read().image.convert("RGB")).astype(np.float32) for s in sprites]
    H = max(i.shape[0] for i in ims); W = max(i.shape[1] for i in ims)
    stack = np.zeros((len(ims), H, W, 3), dtype=np.float32)
    for k, im in enumerate(ims):
        stack[k, H - im.shape[0]:, :im.shape[1]] = im
    d = np.abs(stack - np.median(stack, axis=0)).mean(axis=3)
    thr = max(6.0, float(np.percentile(d, 99.0)) * 0.25)
    out = []
    for k in range(len(ims)):
        ys, _ = np.nonzero(d[k] > thr)
        out.append(float(H - ys.mean()) if len(ys) >= 20 else 0.0)
    return out


def _canvas(sprites):
    """Every frame pasted onto one canvas against the shared bottom-left corner.

    Sprite sheets are alpha-trimmed per frame and the trim is not the same on each, so a band
    taken as a fraction of each frame's *own* shape samples a different absolute column every
    frame - the failure `squat_ride_shaft` documents at length. Any proxy that takes `sprites` and
    reads a fixed region has to do this itself; nothing upstream does it."""
    ims = [s.read().image.convert("RGBA") for s in sprites]
    W = max(i.width for i in ims); H = max(i.height for i in ims)
    for im in ims:
        a = np.zeros((H, W, 4), dtype=int)
        a[H - im.height:, :im.width] = np.array(im).astype(int)
        yield a, W, H


def serpent_cleavage(sprites):
    """Player flesh visible in the Black Serpent's cleavage. More = deeper.

    A paizuri, and the sign is the whole point of the scene. It was first written negated, on the
    §39 sleeve reading: the shaft passes *through* her cleavage, so the frame showing the most tip
    above it is the frame with the most of it inside her. **Played on the device, that ran
    backwards** - the scene reads as a mouth-on-tip stroke where the visible flesh is the deep end,
    and the sign was flipped to match what the device did (§81). The sleeve argument is kept here
    because it is the reasoning to re-make for the next scene of this staging, not a mistake to
    hide; what it shows is that the rule decides nothing on its own once a play exists.

    She is greyscale everywhere (R=G=B: 29, 53, 74) and the player is the only warm thing in
    frame, so `R - B > 20` separates them with no threshold to tune."""
    out = []
    for a, W, H in _canvas(sprites):
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (R > 120) & (R - B > 20)
        out.append(float(m[int(H * 0.40):int(H * 0.85), int(W * 0.40):int(W * 0.53)].sum()))
    return out


def beast_column(sprites):
    """Top of the pale shaft column below the Blinded Beast. Higher = risen = withdrawn.

    Rider geometry, not sleeve: the exposed shaft is *below* the body, so more of it showing
    means the beast has lifted off. Her skin is a saturated orange (185,126,97) and the column is
    desaturated near-white (203,189,176), which `R - B < 45` separates."""
    out = []
    for a, W, H in _canvas(sprites):
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (R > 150) & (R - B < 45) & (B > 130)
        m[:int(H * 0.55), :] = False
        rows = np.nonzero(m[:, int(W * 0.455):int(W * 0.545)].any(axis=1))[0]
        out.append(float(H - rows.min()) if len(rows) else 0.0)
    return out


def beast_pink(sprites):
    """Centroid of the transformed Blinded Beast's pink shaft. Returned negated: y grows down.

    The transformed stage redraws the same staging at full 480x270 with a pink shaft on brown fur
    (`R - G > 55` splits 160,66,73 from 56,43,37). Its *area* is flat across the clip - 381 to 459
    px - so this one is a translation, and position is the only thing to measure."""
    out = []
    for a, W, H in _canvas(sprites):
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (R > 140) & (R - G > 55)
        m[:int(H * 0.30), :] = False
        m[:, :int(W * 0.42)] = False
        m[:, int(W * 0.58):] = False
        ys = np.nonzero(m)[0]
        out.append(-float(ys.mean()) if len(ys) else 0.0)
    return out


def goonshroom_tip(sprites):
    """Exposed tip between the squatting GoonShroom's cheeks. More showing = risen = withdrawn.

    Rider geometry again. The tip is a pale yellow-green (109,172,106) and the caps are blue-green
    (68,169,128); R-B tells them apart outright, +3 against -60. The three caps also bob, but by
    3-7 px on a 209 px sprite - at `motion_proxy`'s jitter floor - against a 14x range here."""
    out = []
    for a, W, H in _canvas(sprites):
        R, G, B, Al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
        m = (Al > 128) & (G > 140) & (R - B > -10) & (R > 80)
        out.append(float(m[int(H * 0.25):int(H * 0.75), int(W * 0.44):int(W * 0.56)].sum()))
    return out


def cling_area(sprites):
    """Visible area of a GoonShroom cling overlay. More on screen = higher = withdrawn.

    These are drawn hanging into frame from the screen edge, and the sprite's bottom edge *is*
    that edge - a shroom sinking below it is redrawn smaller rather than moved, so how much of it
    exists is how high it is. Tier 1 is the one where the built-in silhouette proxy also works
    (its sprite height runs 75 down to 28 px) and the two agree to within 2 points; tiers 2 and 3
    fill the canvas, which pins `top_edges` flat."""
    out = []
    for a, W, H in _canvas(sprites):
        out.append(float((a[..., 3] > 128).sum()))
    return out


OVERRIDE = {
    # --- game 0.3.1's three new enemies (see code/grabs031.py) --------------------------------
    "Serpent_Loop": serpent_cleavage,
    "Serpent_Loop_Gallery": serpent_cleavage,
    "BlindedBeast_Start": beast_column,
    "BlindedBeast_Start_T": beast_pink,
    "BlindedBeast_Start_T_Gallery": beast_pink,
    "GoonShroom_Start": goonshroom_tip,
    "GoonShroom_Start_Gallery": goonshroom_tip,
    "GoonShroom_Cum": goonshroom_tip,
    "GoonShroom_Cum_Gallery": goonshroom_tip,
    "goonshroom_1": cling_area,
    "goonshroom_2": cling_area,
    "goonshroom_3": cling_area,
    "goonshroom_1_Gallery": cling_area,
    "goonshroom_2_Gallery": cling_area,
    "goonshroom_3_Gallery": cling_area,
    "Dragon_Cum": dragon_shaft,
    # --- game 0.3.1 -------------------------------------------------------------------------
    "ambient_dragon_squat_ride": squat_ride_shaft((0.38, 0.58, 0.55)),
    "ambient_wendigo_squat_ride": squat_ride_shaft((0.46, 0.54, 0.55)),
    "ambient_plant_gangbang": squat_ride_shaft((0.52, 0.60, 0.35)),
    "peek_gravy_bath": moving_mass,
    "Gravy_Loop2": gravy_shaft,
    "ambient_gooper_bed_blowjob": gooper_shaft,
    "imp_grab_loop": imp_tip,
    "imp_grab_cum": imp_tip,
    "ambient_nun_wall_chain_head": nun_hood,
    "Plantasha_Start": plantasha_shaft,
    "Plantasha_Cum": plantasha_shaft,
    "Nun_Cum": nun_cum_motion,
    "Nun_Cum_Gallery": nun_cum_motion,   # same scene, the gallery's own 55-frame clip
    "Wendigo_Continued": wendigo_top,
    # The gallery variants measure the same thing off the viewer's own clip (CHANGELOG 53).
    "Plantasha_Start_Gallery": plantasha_shaft,
    "Plantasha_Cum_Gallery": plantasha_shaft,
    "imp_grab_loop_Gallery": imp_tip,
    "imp_grab_cum_Gallery": imp_tip,
}


def proxy_for(scene, sprites, fallback):
    """(values, label). `fallback` is animcheck.motion_proxy."""
    fn = OVERRIDE.get(scene)
    if fn:
        return fn(sprites), "own"
    return fallback(sprites)

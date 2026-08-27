#!/usr/bin/env python3
"""Does the gallery play the same animation as gameplay? For several scenes, no.

    .venv/bin/python code/gallerydiff.py

Every row is reached from two places — an in-game animator state and a gallery-viewer one — and
`animsweep.MAP` only ever names the in-game clip. That is fine wherever the viewer replays the
same animation, which is what everyone assumed. It does not, for the grab screens: the gallery has
its own `Gallery_*` clips, several of them **a different length**, so one funscript is being asked
to fit two animations at once.

Reported from play as "the two gooper scenes work well during gameplay, but seem off in the
gallery" and "nun_cum seems not to loop great in the gallery, but works great during gameplay" —
and those are the three worst ratios in the table below, in order.

Both routes resolve to the same row today, but they need not: in-game lookups check `InGameAliases`
first and fall back to `GalleryAliases`, while gallery lookups read `GalleryAliases` only
(`GalleryAliases.cs`). So a scene can be split with **config alone, no rebuild** — pin the in-game
slug to the current row in `InGameAliases`, and repoint the shared entry at a new gallery row.
"""
import os
import sys

import animcheck as A
from animsweep import MAP

# row -> the clip the GALLERY VIEWER plays. Read off the clip list by name; the viewer's naming is
# not consistent enough to derive (`Gallery_Gooper_Grab_Start` vs `Dragon_Gallery_Grabbed` vs
# `GooperPilloaryGallery_Loop`), so it is spelled out and verified against the assets below.
GALLERY = {
    'Nun_Grab': 'Gallery_Nun_Grab', 'Nun_Cum': 'Gallery_Nun_Cum',
    'Gooper_Start': 'Gallery_Gooper_Grab_Start', 'Gooper_Cum': 'Gallery_Gooper_Grab_Cum',
    'Gargoyle_Grabbed': 'Gallery_Gargoyle_Grabbed1', 'Gargoyle_Cum': 'Gallery_Gargoyle_Grabbed2',
    'Mimic_Start': 'Gallery_Mimic_Grabbed_Start', 'Mimic_Loop': 'Gallery_Mimic_Grabbed_Loop',
    'Mimic_Cum': 'Gallery_Mimic_Grabbed_Cum',
    'Zombie_Loop': 'Gallery_Zombie_Grab_Loop', 'Zombie_Cum': 'Gallery_Zombie_Grab_Cum',
    'Plantasha_Start': 'Gallery_PlantashaGrab_Start', 'Plantasha_Cum': 'Gallery_PlantashaGrab_Cum',
    'Dragon_Grabbed': 'Dragon_Gallery_Grabbed', 'Dragon_Cum': 'Dragon_Gallery_Grabbed_Continue',
    'Wendigo_Start': 'Gallery_Grabbed_Wendigo_Start',
    'Wendigo_Continued': 'Gallery_Grabbed_Wendigo_Continued',
    'imp_grab_loop': 'Gallery_Imp_Gangbang_Loop', 'imp_grab_cum': 'Gallery_Imp_Gangbang_Cum',
    'imp_1': 'Gallery_Imp_Grabbed_1', 'imp_2': 'Gallery_Imp_Grabbed_2',
    'imp_3': 'Gallery_Imp_Grabbed_3',
    'peek_imp_three_way': 'ImpThreeWayGallery_Loop', 'peek_nuns_threeway': 'NunsDuoGallery_Loop',
    'peek_nun_mimic': 'Mimic&NunGallery_Loop', 'peek_wendigo_ride': 'WendigoRidingGalleryLoop',
    'peek_gooper_pillory': 'GooperPilloaryGallery_Loop', 'peek_plant_bj': 'PlantBJGallery_Loop',
    'peek_zombie_bj': 'Zombie BJ Gallery Loop',
    # Baphomet and Gravy are glory-hole scenes driven by the gallery controllers in the first
    # place, so MAP already names their gallery clip and there is nothing to compare.

    # --- game 0.3.1 ------------------------------------------------------------------------
    # The four new peek scenes each have their own gallery clip, and all four are the *same*
    # length as the in-game one - so they need no split, exactly as the original seven did not.
    # Checked here rather than remembered: a peek having a same-length twin is a fact about this
    # build, not a rule.
    #
    # Note `peek_werewolf_ride`'s gallery clip is called **Blinded Beast Ride**. The peephole's
    # own clips and its ambient audio say "werewolf"; the gallery says the miniboss. Same scene,
    # two names, which is why PeekGalleryMap carries both spellings (§68).
    'peek_gargoyle_fuck_fest': 'GargoyleFuckFestGallery_Loop',
    'peek_gravy_bath': 'GravyBathingGallery_Loop',
    'peek_serpent_prison': 'Serpent Prison Style Gallery Loop',
    'peek_werewolf_ride': 'Blinded Beast Ride Gallery Loop',

    # The three new enemies' grab screens. Eight of the ten need their own row and two do not;
    # this table is what says which, and `Serpent_Cum` / `BlindedBeast_Start` reading "same" here
    # is the evidence for leaving them sharing one script rather than an assumption (§71).
    'Serpent_Loop': 'Gallery_Serpent_Grab_screen_Loop',
    'Serpent_Cum': 'Gallery_Serpent_Grab_screen_Cum',
    'BlindedBeast_Start': 'Gallery_BlindedBeast_Grab_Start',
    'BlindedBeast_Cum': 'Gallery_BlindedBeast_Grab_Cum',
    'BlindedBeast_Start_T': 'Gallery_BlindedBeast_Grab_Start_T',
    'BlindedBeast_Cum_T': 'Gallery_BlindedBeast_Grab_Cum_T',
    'GoonShroom_Start': 'Gallery_Goonshroom_Gangbang_Loop',
    'GoonShroom_Cum': 'Gallery_Goonshroom_Gangbang_Cum',
    'goonshroom_1': 'Gallery_Goonshroom_Grabbed_1',
    'goonshroom_2': 'Gallery_Goonshroom_Grabbed_2',
    'goonshroom_3': 'Gallery_Goonshroom_Grabbed_3',
}

# Rows that now have a dedicated `*_Gallery` row and script, so the mismatch below is resolved for
# them - the gallery slug is repointed in `GalleryAliases` and the in-game one pinned in
# `InGameAliases` (CHANGELOG 52). Listed rather than derived so this file states the intent.
SPLIT = {"Nun_Cum", "Gooper_Start", "Gooper_Cum", "imp_1", "imp_2", "imp_3",
         "Plantasha_Start", "Plantasha_Cum", "imp_grab_loop", "imp_grab_cum",
         "Wendigo_Start", "Dragon_Grabbed",
         # game 0.3.1's three new enemies (§71). Eight of their ten rows are split; the two
         # missing from this set - Serpent_Cum and BlindedBeast_Start - are absent because the
         # viewer plays the same clip, and they read "same" in the table above.
         "Serpent_Loop", "BlindedBeast_Cum", "BlindedBeast_Start_T", "BlindedBeast_Cum_T",
         "GoonShroom_Start", "GoonShroom_Cum", "goonshroom_1", "goonshroom_2", "goonshroom_3"}


def clip_durations(env, name):
    """Every clip carrying this name, as (ms, fps).

    Clip names are NOT unique: `Gallery_Nun_Grab` exists twice, at 600 ms @10fps (the grab screen)
    and 1625 ms @8fps (the enemy model's own grab). `animcheck.clip_frames` returns whichever the
    asset walk reaches first, which for that name is the wrong one - it reported Nun_Grab as
    2.708x off when the two grab screens are in fact identical. Anywhere a name is ambiguous the
    tool has to say so rather than quietly pick."""
    out = []
    for o in env.objects:
        if o.type.name != "AnimationClip":
            continue
        d = o.read_typetree()
        if d.get("m_Name") == name:
            out.append((float(d["m_MuscleClip"]["m_StopTime"]) * 1000.0, float(d["m_SampleRate"])))
    return out


def main():
    env = A.load_env()
    rows = []
    for name, play_clip in MAP.items():
        gal_clip = GALLERY.get(name)
        if not gal_clip:
            continue
        pd_all = clip_durations(env, play_clip)
        gd_all = clip_durations(env, gal_clip)
        if not pd_all or not gd_all:
            rows.append((name, play_clip, 0, gal_clip, 0, 1.0, "CLIP NOT FOUND"))
            continue
        pdur, pfps = pd_all[0]
        # With several same-named clips, the grab screen is the one whose sample rate matches the
        # in-game grab screen's; state it rather than assuming it.
        note = ""
        if len(gd_all) > 1:
            match = [g for g in gd_all if abs(g[1] - pfps) < 0.01]
            note = (f"  [{len(gd_all)} clips named this; took the {match[0][1]:.0f}fps one]"
                    if match else f"  [{len(gd_all)} clips named this, no fps match — CHECK]")
            gd_all = match or gd_all
        gdur = gd_all[0][0]
        ratio = gdur / pdur if pdur else 1.0
        rows.append((name, play_clip, pdur, gal_clip, gdur, ratio,
                     ("same" if abs(ratio - 1) < 0.005 else f"{ratio:.3f}x") + note))
    rows.sort(key=lambda r: -abs(r[5] - 1))

    print(f"{'row':<24}{'gameplay clip':<26}{'ms':>8}  {'gallery clip':<34}{'ms':>8}  ratio")
    for name, pc, pd, gc, gd, ratio, note in rows:
        print(f"{name:<24}{pc:<26}{pd:>8.0f}  {gc:<34}{gd:>8.0f}  {note}")

    bad = [r for r in rows if abs(r[5] - 1) >= 0.005]
    split = [r for r in bad if r[0] in SPLIT]
    left = [r for r in bad if r[0] not in SPLIT]
    print(f"\n{len(bad)} of {len(rows)} rows play a DIFFERENT-LENGTH animation in the gallery.")
    print(f"  {len(split)} already have their own gallery row: "
          + ", ".join(r[0] for r in split))
    if left:
        print(f"  {len(left)} still share one script across both:")
        for r in left:
            print(f"      {r[0]:<24}{r[6]}")
        print("\nSplit one by giving it a `<Row>_Gallery` row and repointing `GalleryAliases` —")
        print("see code/README.md, 'Giving the gallery its own script for a scene'.")
    else:
        print("  0 still share one script — every mismatch has its own gallery row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

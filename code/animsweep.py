#!/usr/bin/env python3
"""Sweep every scene against its animation: timing and polarity at a glance.

    .venv/bin/python code/animsweep.py

time: ok <0.5%% from a whole number of strokes, near <2%%, OFF above.  Objective.
pol : sign of the correlation with the motion proxy.  NOT objective - the proxy assumes
      'higher on screen = withdrawn = 100', which is right for some scenes and backwards for
      others.  Treat INV as "look at this one", never as a verdict.  Confirm with
      animcheck.py --sheet before changing anything.
proxy: sil = silhouette top edge, sig = signed displacement (outline pinned), own = a scene
      specific proxy from proxies.py, auth = deliberately not tracking any proxy.

Frames are sampled at i/fps, not at i*period/n.  Those are the same number for every clip but
GooperGrabScreenCum, where a second sprite curve makes the animator hold the clip 1500 ms while
its own 14 frames last 1400 - see animcheck.clip_frames.  (Both Gooper clips carry that second
curve; only the cum one is held past its frames, on 0.3.1 and on 0.2.1 alike.)
"""
import sys, os, csv, json
import animcheck as A
import proxies as P

MAP = {
 # gameplay grab screens
 'Nun_Grab':'GhoulGrabStart','Nun_Cum':'GhoulGrabCum',
 'Gooper_Start':'GooperGrabScreen','Gooper_Cum':'GooperGrabScreenCum',
 'Gargoyle_Grabbed':'GargoyleSex','Gargoyle_Cum':'GargoyleCum',
 'Mimic_Start':'MimicGrabInit','Mimic_Loop':'MimicGrabLoop','Mimic_Cum':'MimicCum',
 'Zombie_Loop':'ZombieGrabScreen_Loop','Zombie_Cum':'ZombieGrabScreen_Cum',
 'Plantasha_Start':'PlantashaGrab','Plantasha_Cum':'PlantashaCum',
 'Dragon_Grabbed':'DragonFaceSit','Dragon_Cum':'DragonSexScene',
 'Wendigo_Start':'WendigoKiss','Wendigo_Continued':'WendigoSex',
 'imp_grab_loop':'Imp_Grab_Loop','imp_grab_cum':'Imp_Grab_Cum',
 'imp_1':'Imp_Grab_One','imp_2':'Imp_Grab_Two','imp_3':'Imp_Grab_Three',
 # gallery variants: the viewer plays its own clip for these, at a different length (CHANGELOG 51)
 'Nun_Cum_Gallery':'Gallery_Nun_Cum',
 'Gooper_Start_Gallery':'Gallery_Gooper_Grab_Start','Gooper_Cum_Gallery':'Gallery_Gooper_Grab_Cum',
 'imp_1_Gallery':'Gallery_Imp_Grabbed_1','imp_2_Gallery':'Gallery_Imp_Grabbed_2',
 'imp_3_Gallery':'Gallery_Imp_Grabbed_3',
 'Plantasha_Start_Gallery':'Gallery_PlantashaGrab_Start',
 'Plantasha_Cum_Gallery':'Gallery_PlantashaGrab_Cum',
 'imp_grab_loop_Gallery':'Gallery_Imp_Gangbang_Loop',
 'imp_grab_cum_Gallery':'Gallery_Imp_Gangbang_Cum',
 'Wendigo_Start_Gallery':'Gallery_Grabbed_Wendigo_Start',
 'Dragon_Grabbed_Gallery':'Dragon_Gallery_Grabbed',
 # glory hole / minotaur run through the gallery controllers
 'Baphomet_Start':'Gallery_Baphomet_Grabbed_BJ_Start','Baphomet_Loop':'Gallery_Baphomet_Grabbed_BJ_Loop',
 'Baphomet_Cum':'Gallery_Baphomet_Grabbed_BJ_Cum','Baphomet_Start2':'Gallery_Baphomet_Grabbed_Riding_Start',
 'Baphomet_Loop2':'Gallery_Baphomet_Grabbed_Riding_Loop','Baphomet_Cum2':'Gallery_Baphomet_Grabbed_Riding_Cum',
 'Gravy_Start':'Gallery_Gravy_Grabbed_Start','Gravy_Loop':'Gallery_Gravy_Grabbed_Loop',
 'Gravy_Cum':'Gallery_Gravy_Grabbed_Cum','Gravy_Start2':'Gallery_Gravy_Grabbed_Start2',
 'Gravy_Loop2':'Gallery_Gravy_Grabbed_Loop2','Gravy_Cum2':'Gallery_Gravy_Grabbed_Cum2',
 'Gravy_End2':'Gallery_Gravy_Grabbed_End2',
 # dioramas
 'ambient_nun_chair_fuck':'Nun chair fuck','ambient_gooper_bed_blowjob':'gooper bed blowjob',
 'ambient_zombie_bench_fuck':'zombie bench fuck','ambient_gargoyle_ledge_fuck':'gargoyle ledge fuck',
 'ambient_imp_gangbang':'imp gangbang','ambient_imp_gangbang_2':'imp gangbang 2',
 'ambient_mimic_wall_fuck':'mimic wall fuck',
 'ambient_nun_wall_chain_head':'nun wall chain head','ambient_plantasha_blowjob':'plant bj window',
 # peeks
 'peek_imp_three_way':'Peephole_Imps_Loop','peek_nuns_threeway':'Peephole_Nuns_Loop',
 'peek_nun_mimic':'Peephole_Nun&Mimic_Loop','peek_wendigo_ride':'Peephole_Wendigo_Loop',
 'peek_gooper_pillory':'Peephole_GooperBJ_Loop','peek_plant_bj':'Peephole Plantasha Loop',
 'peek_zombie_bj':'Peephole Zombie Loop',
 # game 0.3.1 (see code/scenes031.py for how each curve was derived)
 'ambient_dragon_squat_ride':'dragon squat ride','ambient_wendigo_squat_ride':'wendigo squat ride',
 'ambient_goonshroom_gangbang':'goonshroom gangbang','ambient_nun_watersports':'nun watersports',
 'ambient_plant_gangbang':'plant gangbang','ambient_serpent_wall_blowjob':'serpent blowjob wall',
 'peek_gargoyle_fuck_fest':'GargoylePeep_Loop','peek_gravy_bath':'GravyPeep_Loop',
 'peek_serpent_prison':'Peephole Serpent Loop','peek_werewolf_ride':'Peephole werewolf Loop',
 # game 0.3.1's three new enemies (see code/grabs031.py for how each curve was derived)
 'Serpent_Loop':'BlackSerpent GrabScreen','Serpent_Cum':'BlackSerpent GrabScreen_Cum',
 'BlindedBeast_Start':'Blinded Beast Grabscreen Start',
 'BlindedBeast_Cum':'Blinded Beast Grabscreen Cum',
 'BlindedBeast_Start_T':'Blinded Beast_T Grabscreen Start',
 'BlindedBeast_Cum_T':'Blinded Beast_T Grabscreen Cum',
 'GoonShroom_Start':'GoonShroom_GrabscreenStart','GoonShroom_Cum':'GoonShroom_GrabscreenCum',
 'goonshroom_1':'GoonShroomGrapple_One','goonshroom_2':'GoonShroomGrapple_Two',
 'goonshroom_3':'GoonShroomGrapple_Three',
 # ... and their gallery twins. Serpent_Cum and BlindedBeast_Start need none: the viewer plays
 # the same sprites at the same rate, so one script is whole-cycle correct for both.
 'Serpent_Loop_Gallery':'Gallery_Serpent_Grab_screen_Loop',
 'BlindedBeast_Cum_Gallery':'Gallery_BlindedBeast_Grab_Cum',
 'BlindedBeast_Start_T_Gallery':'Gallery_BlindedBeast_Grab_Start_T',
 'BlindedBeast_Cum_T_Gallery':'Gallery_BlindedBeast_Grab_Cum_T',
 'GoonShroom_Start_Gallery':'Gallery_Goonshroom_Gangbang_Loop',
 'GoonShroom_Cum_Gallery':'Gallery_Goonshroom_Gangbang_Cum',
 'goonshroom_1_Gallery':'Gallery_Goonshroom_Grabbed_1',
 'goonshroom_2_Gallery':'Gallery_Goonshroom_Grabbed_2',
 'goonshroom_3_Gallery':'Gallery_Goonshroom_Grabbed_3',
}
def cat(cyc,corr):
    terr=abs(cyc-round(cyc))/max(round(cyc),1)
    tim = "ok" if terr<0.005 else ("near" if terr<0.02 else "OFF")
    if corr is None: pol="?"
    elif corr<-0.3: pol="INV"
    elif corr>0.3: pol="ok"
    else: pol="?"
    return tim,pol

def main():
  env=A.load_env()
  rows=[]
  for name,clip in MAP.items():
    sprites,dur,fps=A.clip_frames(env,clip)
    stem=name.lower()
    fp=os.path.join("Edi/Gallery/handy2pro",stem+".funscript")
    if not sprites or not os.path.exists(fp):
        rows.append((name,clip,None,None,None,None,"no clip/script")); continue
    period,reps=A.stroke_period(sprites,dur)
    oneshot = name in P.ONESHOT
    if oneshot: period,reps=dur,1          # a single arc has no cycle to fold into
    if name in P.SPLIT:                    # ... and the mirror: a repeat it could not see
        reps=P.SPLIT[name]; period=dur/reps
    authored = name in P.AUTHORED
    tops,proxy=P.proxy_for(name,sprites,A.motion_proxy)
    if authored: proxy="auth"
    acts=json.load(open(fp,encoding="utf-8-sig"))["actions"]; end=acts[-1]["at"]
    cyc=end/period
    n=len(sprites)//reps if reps>1 else len(sprites)
    lo,hi=min(tops),max(tops)
    corr=None
    if hi-lo>1e-6 and not authored:
        want=[(t-lo)/(hi-lo)*100 for t in tops[:n]]
        k=1 if oneshot else max(1,int(round(end/period)))
        ft=A.frame_times(n,period,fps)   # frame i is at i/fps, which is period/n only when the
        got=[sum(A.sample(acts,c*period+ft[i]) for c in range(k))/k for i in range(n)]
        mg,mw=sum(got)/n,sum(want)/n
        den=(sum((g-mg)**2 for g in got)*sum((w-mw)**2 for w in want))**.5
        corr=(sum((g-mg)*(w-mw) for g,w in zip(got,want))/den) if den>1e-9 else 0.0
    rows.append((name,clip,period,end,cyc,corr,proxy))

  print(f"{'scene':<28}{'period':>8}{'slice':>7}{'cycles':>8}  {'time':<5}{'pol':<5}{'r':>7}  proxy")
  for name,clip,period,end,cyc,corr,proxy in rows:
    if period is None: print(f"{name:<28}  -- {proxy}"); continue
    tim,pol=cat(cyc,corr)
    print(f"{name:<28}{period:>8.1f}{end:>7}{cyc:>8.3f}  {tim:<5}{pol:<5}{(f'{corr:+.2f}' if corr is not None else '   -'):>7}  {proxy}")

# MAP is imported by retime.py; don't run the sweep on import.
if __name__ == "__main__":
    main()

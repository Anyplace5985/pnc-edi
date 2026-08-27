using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace PncEdi
{
    public static class Program
    {
        // family -> animator states that can drive an EDI dispatch for that enemy
        static readonly Dictionary<string, string[]> States = new Dictionary<string, string[]>
        {
            ["nun"] = new[] { "GhoulGrabStart", "GhoulGrabscreen", "GhoulGrabCum", "GhoulGrabCumContinue",
                              "GhoulGrab", "GhoulIdle", "GhoulWalk", "Ghoul Attack" },
            ["nun_alt"] = new[] { "GhoulGrabStart", "GhoulGrabscreen", "GhoulGrabCum", "GhoulGrabCumContinue",
                              "GhoulGrab", "GhoulIdle", "GhoulWalk", "Ghoul Attack" },
            ["zombie"] = new[] { "ZombieGrabScreen_Loop", "ZombieGrabScreen_Cum",
                              "Zombie_Grab", "Zombie_Idle", "Zombie_Walk", "Zombie_Attack" },
            ["gooper"] = new[] { "GooperGrabScreen", "GooperGrabScreenCum",
                              "Grab", "Idle", "Walk", "Attack", "GooperSpitGrabAttack" },
            ["gargoyle"] = new[] { "GargoyleGrabScreen", "GargoyleCumScreen",
                              "Grab", "Idle", "Walk", "Attack", "GargoyleGrabProjectileAnim" },
            ["mimic"] = new[] { "MimicGrabInit", "MimicGrabLoop", "MimicCum",
                              "WeaponsMimicGrabInit", "WeaponsMimicGrabLoop", "WeaponsMimicCum" },
            ["plantasha"] = new[] { "PlanticaGrab", "PlanticaCum",
                              "Plantasha_Grab", "Plantasha_Idle", "Plantasha_Shooting",
                              "Plantasha_Spin", "Plantasha_SpinStart", "Plantasha_SpinEnd" },
            ["dragon"] = new[] { "DragonFaceSit", "DragonSexScene", "DragonSexSceneIntro",
                              "DragonGrab", "DragonIdle", "DragonWalk" },
            ["wendigo"] = new[] { "WendigoKiss", "WendigoSexScene", "WendigoSexSceneIntro",
                              "WendigoGrab", "WendigoIdle", "WendigoWalk" },
            ["baphomet"] = new[] { "Start", "Middle", "Cum", "Fade", "StartSex", "SexMiddle", "SexCum",
                              "Idle", "Laugh" },
            ["imp"] = new[] { "Imp_Grab_Loop", "Imp_Grab_Cum", "Imp 1", "Imp 2", "Imp 3",
                              "Idle", "Walk", "Attack" },
            // --- game 0.3.1 ---------------------------------------------------------------
            // Black Serpent Enemy / BlackSerpent GrabScreen
            ["serpent"] = new[] { "Loop", "Cum",
                              "Attack", "Shoot", "Black_Serpent_Idle", "Black_Serpent_Walk",
                              "Hypnosis Start", "Hypnosis Loop", "Hypnosis End" },
            // BlindedBeastGrabScreen *and* BlindedBeastTransformedGrabScreen - both declare
            // exactly "Loop" and "Cum", so the state name alone cannot say which stage this is.
            // NOTE the harness prints one row for both. It compiles NameRemap + GalleryTable,
            // and the stage is resolved a layer above them by GrabHooks.ApplyControllerVariant
            // off the live controller name (§66) - which is not reachable without a game. So
            // `blinded_beast_loop` here means "and `blinded_beast_loop_t` in the second stage".
            ["blinded_beast"] = new[] { "Loop", "Cum",
                              "BlindedBeast_Idle", "BlindedBeast_Walk", "BlindedBeast_Attack",
                              "BlindedBeast_Idle_Transformed", "BlindedBeast_Attack_Transformed",
                              "BlindedBeast_RangedAttack_Transformed",
                              "BlindedBeast_Transforming_Transformed" },
            // GoonShroom_GrabScreen / GoonShroomGrappleScreen
            ["goonshroom"] = new[] { "GoonShroom_GrabscreenStart", "GoonShroom_GrabscreenCum",
                              "One", "Two", "Three",
                              "Idle", "Walk", "Charging", "Explode" },
        };

        // the gallery viewer drives these through the same slug builder
        static readonly Dictionary<string, string[]> GalleryStates = new Dictionary<string, string[]>
        {
            ["nun"] = new[] { "Grab", "GrabAlt", "Cum", "CumAlt", "CumContinue", "CumContinueAlt" },
            ["zombie"] = new[] { "Loop", "Cum", "Alt1Loop", "Alt1Cum" },
            ["gooper"] = new[] { "Start", "StartAlt", "Cum", "CumAlt" },
            ["gargoyle"] = new[] { "Grabbed", "GrabbedAlt", "Cum", "CumAlt", "CumContinue", "CumContinueAlt" },
            ["mimic"] = new[] { "Start", "StartAlt1", "Loop", "LoopAlt1", "Cum", "CumAlt1" },
            ["plantasha"] = new[] { "Start", "StartAlt1", "Cum", "CumAlt1" },
            ["dragon"] = new[] { "Grabbed", "Cum" },
            ["wendigo"] = new[] { "Start", "Continued" },
            ["baphomet"] = new[] { "Start", "Loop", "Cum", "Start2", "Loop2", "Cum2" },
            ["gravy"] = new[] { "Start", "Loop", "Cum", "Start2", "Loop2", "Cum2", "End2" },
            ["imp"] = new[] { "Loop", "Cum", "Imp 1", "Imp 2", "Imp 3" },
            // --- game 0.3.1 ---------------------------------------------------------------
            ["serpent"] = new[] { "Loop", "Cum" },                       // Gallery_Serpent_Grab_screen
            ["blinded_beast"] = new[] { "Start", "Cum", "Start_T", "Cum_T" },  // Gallery_BlindedBeast_Grabbed
            ["Goon Shroom"] = new[] { "Loop", "Cum",                    // Gallery_Goonshroom_Grabbed
                              "GoonShroom 1", "GoonShroom 2", "GoonShroom 3" },
        };

        // WHY SOME KEYS ABOVE ARE DISPLAY NAMES AND SOME ARE NOT
        //
        // `Emit` runs its key through `NameRemap.ResolveEnemyKey`, exactly as the game does, so a
        // key that is already the resolved form tests everything *except* the remap - and the
        // remap is where the gallery route actually broke. The gallery menu hands the hook the
        // enemy's DISPLAY name, and 0.3.1's goonshroom displays as `Goon Shroom`, with a space,
        // which `GoonShroom=goonshroom` could not match as a substring. Every goonshroom gallery
        // entry therefore slugged to `goon_shroom_goonshroom_1` and played nothing, for four days,
        // while this harness reported the same five rows resolving cleanly - because it was asking
        // the question with the answer already substituted in.
        //
        // Display names confirmed from `[GALLERY-STEP] enemy='...'` lines in a real session:
        // `Goon Shroom`, `Blinded Beast`, `Serpent`, `Plantasha`. The rest of the table above is
        // still keyed on the resolved form and so does not test its own remap. **Replace each one
        // with the display name as you see it in a log** - that is the only way this harness
        // covers the route the gallery actually takes.

        public static void Main(string[] args)
        {
            string cfgPath = args[0];
            string remap = null, aliases = null, ingame = null;
            foreach (var line in File.ReadAllLines(cfgPath))
            {
                if (line.StartsWith("EnemyRemap = ")) remap = line.Substring("EnemyRemap = ".Length).TrimEnd('\r');
                else if (line.StartsWith("GalleryAliases = ")) aliases = line.Substring("GalleryAliases = ".Length).TrimEnd('\r');
                else if (line.StartsWith("InGameAliases = ")) ingame = line.Substring("InGameAliases = ".Length).TrimEnd('\r');
            }
            Plugin.CfgEnemyNameRemap = new Cfg(remap);
            NameRemap.Reload();

            // base table from the DLL source, then the config's overrides on top -
            // exactly what GalleryAliases.Reload does at runtime.
            var shared = Parse(GalleryTable.Shared);
            foreach (var kv in Parse(aliases)) shared[kv.Key] = kv.Value;
            var live = Parse(GalleryTable.InGame);
            foreach (var kv in Parse(ingame)) live[kv.Key] = kv.Value;

            Console.WriteLine("source\tname\tkey\tstate\tslug\tresolved\tvia");
            foreach (var kv in States)
                foreach (var st in kv.Value)
                    Emit("ingame", kv.Key, st, shared, live, true);
            foreach (var kv in GalleryStates)
                foreach (var st in kv.Value)
                    Emit("gallery", kv.Key, st, shared, live, false);
        }

        static Dictionary<string, string> Parse(string raw)
        {
            var d = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var p in (raw ?? "").Split(';', '\n', '\r'))
            {
                int i = p.IndexOf('=');
                if (i > 0) d[p.Substring(0, i).Trim()] = p.Substring(i + 1).Trim();
            }
            return d;
        }

        static void Emit(string src, string key, string state,
                         Dictionary<string, string> shared, Dictionary<string, string> live, bool inGame)
        {
            // Resolve first, exactly as the game does: GalleryHooks and GrabHooks both call
            // ResolveEnemyKey on the name they are handed and pass the *result* to
            // BuildGallerySlug. Calling BuildGallerySlug directly skipped the remap, which is
            // the step the goonshroom gallery was failing at - so the harness could not have
            // caught it however many rows it printed. Resolved keys map to themselves, so this
            // changes nothing for the rows that were already keyed that way.
            string resolved = NameRemap.ResolveEnemyKey(key);
            string slug = NameRemap.BuildGallerySlug(resolved, state);
            string via, res;
            if (inGame && live.TryGetValue(slug, out res)) via = "InGameAliases";
            else if (shared.TryGetValue(slug, out res)) via = "GalleryAliases";
            else { res = ""; via = "UNMAPPED"; }
            Console.WriteLine($"{src}\t{key}\t{resolved}\t{state}\t{slug}\t{res}\t{via}");
        }
    }
}

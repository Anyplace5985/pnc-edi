# slugharness

Coverage check for the animator-state -> gallery mapping. Compiles the mod's **real**
`NameRemap.cs` (referenced from `../edimod/PncEdi/`, not copied) plus a six-line `Plugin` stub,
so it cannot drift from what the mod actually does.

    dotnet run --project code/slugharness -- "BepInEx/config/com.edi.pnc.cfg"

Prints `source, name, key, state, slug, resolved, via` for every (enemy, animator state) pair.
**Any row ending in `UNMAPPED` is a gap in `GalleryAliases`.**

    dotnet run --project code/slugharness -- "BepInEx/config/com.edi.pnc.cfg" \
      | awk -F'\t' 'NR>1 && $7=="UNMAPPED"'

`name` is what the game hands the hook and `key` is what `ResolveEnemyKey` makes of it. The two
columns exist because the gap between them is where this harness once had a blind spot.

## Feed it the name the game is handed, not the key it works out (§92)

`Emit` runs its input through `ResolveEnemyKey` first, exactly as `GalleryHooks` and `GrabHooks` do.
It did not always: it called `BuildGallerySlug(key, state)` directly, and the tables were keyed on
resolved forms like `goonshroom`. That skipped the remap — so when the **gallery menu** turned out
to pass the enemy's *display* name, `Goon Shroom` with a space, which no `EnemyRemap` entry matched,
all five GoonShroom gallery rows played nothing for four days while this harness reported them
resolving cleanly. **A harness that skips a step cannot fail at that step.**

Display names confirmed from `[GALLERY-STEP] enemy='...'` lines in a real session: `Goon Shroom`,
`Blinded Beast`, `Serpent`, `Plantasha`. Only the first is keyed that way in `GalleryStates` so far;
the rest are still keyed on their resolved form and therefore **do not test their own remap**.
Replace each one with its display name as you see it in a log.

When the game updates, add the new enemies' animator states to the `States` (in-game) and
`GalleryStates` (gallery viewer) tables at the top of `Program.cs`. Get the state names with the
UnityPy snippet in `../NAMING-AUDIT.md` — do not type them from memory, the game misspells
several (`Planatasha`, `minothaur`, `GooperPilloary`).

Last full run: 169/169 pairs mapped, 0 unmapped.

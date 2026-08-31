# Release notes

Player-facing notes, newest first. What changed, what you have to do differently, and nothing
about how it was built.

---

## 3.0.0 — for Post Nut Calamity 0.3.2

### Which build are you coming from?

Two different builds have been posted in the release thread, and the upgrade is a little different
depending on which one you have:

- **PncEdi 2.5.2**, the last build posted here. It was for game **0.3.1**.
- **Dupli9d's portable patch**, a separate build based on 2.5.2 with its own additions. Its README
  says 2.5.2, but the mod reports itself as **2.6.0** in the log and in its settings window.

This release is **3.0.0** so that there is no confusion with either. If you are coming from the
portable patch, read "Coming from the portable patch" at the end as well — a few of its settings do
not exist here, and the things they did are done differently.

Either way: **delete your old install first**, then extract this release fresh. Delete
`winhttp.dll`, `doorstop_config.ini`, `.doorstop_version`, `libdoorstop.so`, `run_bepinex.sh`,
`start-pnc-linux.sh`, the `BepInEx` folder and the `Edi` folder. The game itself is untouched —
nothing in the archive overwrites a game file.

### Installing is different now

**This release needs game version 0.3.2.** It will not work on 0.3.1.

**There are now up to three downloads instead of one.**

| download | what it is |
|---|---|
| `PNC0.3.2-PncEdi-3.0.0.zip` | the mod itself, with Edi and every funscript. This is the only one you need. |
| `PncEdi-FemboyWitch-<date>.zip` | optional. Adds the Femboy Witch, a boss who is not in the base game. |
| `PncEdi-JokerWallTrap-<date>.zip` | optional. Adds the Joker Wall Trap — pictures on the wall that grab you as you pass. |

The mod archive installs the way it always did: extract it into your Post Nut Calamity folder,
run `Edi\Edi.exe`, connect your device, pick your variant. The full instructions are in
`PncEdi-README.txt` inside the archive.

**The two optional packages are new, and they install differently.** Each one is a folder you drop
into `BepInEx\custom-enemies\`, and then you restart the game. They are not extracted over the game
folder like the main archive.

**The packages must match the mod version.** Both carry code of their own, so a package from an
older release will not load against this one. Download all three at the same time, or don't
download the packages at all.

**A package that ships code arrives switched off.** That code runs with the same access as any
other mod and nothing here can sandbox it, so turning the package on is your permission for it to
run, not just a content toggle. Open the settings window with **F11**, find the package, switch it
on, and restart the game. Until you do, the package does nothing — but its scenes still appear in
your Edi gallery, so switching it on later never means restarting Edi as well.

### Device variants were renamed

If you were on **2.5.2 or earlier**, the variant called `detailed` is now called **`handy2pro`**,
and your old selection no longer matches anything. Pick again from the "Variant" drop-down in Edi,
in your device's row:

    Handy 2 Pro, fully overclocked        handy2pro     <- what Edi picks by itself
    Handy 2, OSR/SR6, or a 2 Pro
      overclocked only part-way           handy2
    Handy 1, or a 2 Pro with no
      overclock at all                    handy1

**`handy2` is new in this release** — 2.5.2 had only the two, `detailed` and `handy1`, and a
Handy 2 or an OSR/SR6 had to pick between a variant written for a faster device and one written
for a much slower one. `handy1` is unchanged in what it plays.

On the wrong variant nothing breaks or goes silent — it just plays too fast to follow, or
shallower than it was written to.

### What else is new

- **104 scenes, up from 101**, in each of the three variants. The three new ones are the chaser
  bosses' stomps and the serpent's hypnosis.
- **A settings window**, opened with **F11** or from a button on the main menu. Every setting the
  mod has, grouped and explained, changeable without editing a config file. Most take effect
  immediately.
- **Gameplay profiles.** One switch — Vanilla, Pressure and Release, God Mode, or Custom — instead
  of setting a dozen options individually. `Vanilla` really is vanilla: nothing the mod does to
  gameplay is on. Switchable mid-run.
- **The device keeps playing in menus**, on the pause screen and after a run ends, instead of
  falling silent. Losing window focus still pauses it. There is a switch for it.
- **Custom enemies and wall traps** are a documented format, so anyone can build one. The format
  ships in the archive even though the packages do not.
- **The chaser bosses have an aura** that drives the device by how close they are, and the
  serpent's hypnosis now builds in stages with a minimum dwell rather than flickering between them.
- **Distance drives the device** for ambient scenes, rather than a fixed playlist.
- **The class selection screen tells the truth** about your horniness capacity: it counts armour
  once instead of twice, and it shows the numbers your chosen profile will actually run at.
- **Debug spawn keys and the free camera ship switched off.** They were on by default in earlier
  builds, which nobody asked for.
- **A patched Edi is bundled**, as before. It fixes a stutter when a looping scene is resumed or
  seeked. The fix is merged upstream but is not in any released Edi yet, so this archive still
  carries its own copy. When a released Edi has it, the patched copy goes away.
- **Many scene timing and polarity fixes** across the gallery and in play, and several scenes that
  never dispatched to the device at all now do.

### Coming from the portable patch

Three of its settings do not exist here, because this build already solved the same problems a
different way. Nothing is lost — there is just nothing for you to set:

| the portable patch had | here |
|---|---|
| `ClassLockCounts`, a per-class table of lock counts | the lock count is derived from your character's own capacity, so every class is consistent without a table |
| `BaseSpawnMultiplier` / `MaxSpawnBonus` | `SpawnCountMultiplier` and `SpawnCountMultiplierAtFullLock` — the ceiling is a setting you can see rather than something that falls out of the arithmetic |
| `HealthRegenAtFullPressure` | regeneration already falls away as pressure builds; a second setting on top of it counted the same pressure twice |

`MinotaurTeleport` and the AI diagnostic dump are not here either — both were development tools.

Its custom enemies, mod manager and gameplay profiles are all here, rebuilt rather than carried
across, which is why the packages install as separate downloads now.

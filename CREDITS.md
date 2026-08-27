# Credits

This project is a mod, and almost nothing in it starts from nothing. What follows is who made the
things it is built on, as precisely as this tree can state it.

Almost all of it comes from one place: the mod's release thread on Eroscripts,
[*Game Integration - Post Nut Calamity 0.1.0
[EDI]*](https://discuss.eroscripts.com/t/game-integration-post-nut-calamity-0-1-0-edi/315695),
where the original mod, every edit of it, and the funscripts the gallery started as were all
posted. Releases of *this* mod go to the same thread. If you are one of the people below and the
attribution is wrong or incomplete, that thread is the place to say so.

## The game

**Post Nut Calamity**, by **ShoeStrangNBoydy**. It is not open source and no part of it is
redistributed here: this repository holds the mod alone, and the release archive contains no game
file. Everything the project knows about the game was read out of the shipped assets of a copy of
it.

## Edi

**Edi**, by **NoGRo** — <https://github.com/NoGRo/Edi>. Edi is what actually talks to the device;
the mod's whole contract with it is a row name over HTTP. It is open source, and this project's
rule has been to read that source rather than reverse-engineer the behaviour, which is where most
of `learnings/edi-integration.md` comes from.

The release archive bundles an Edi build. Whether that build is a stock release or carries a fix
that has not been released yet is stated in the archive's own README, and in `PROJECT.md`.

## The mod this one continues

**There was no single earlier mod, and no single earlier author.** What this project took up was a
composite: the thread's releases pasted over each other in order, first to last, and the result is
what `code/edimod/` was recovered from by decompiling the shipped binary (§7). In release order,
that is:

| | who | what |
|---|---|---|
| 27 May | **everydayhandyuser** | the original `pnc edi integration` — the mod itself, and the first gallery funscripts |
| 28 May | **edale** | the gallery-unlock registry keys, and the documentation that went with them |
| 31 May | **overkeks** | the edit for game 0.2.1: gameplay changes, shipped with source |
| 1 Jun | **Dupli9d** | a patch making that plugin work in game |
| 4 Jun | **Dupli9d** | the "horny system" build — the ancestor of this mod's heat and lock mechanics |

So the gallery registry, the alias mechanism, the heat and lock systems and the shape of the Edi
channel are theirs between them, and a large part of what is here is repair, measurement and
extension on top of that. The version strings this tree inherited — v1.9.7, v2.0.8, traced across
two releases in `code/NAMING-AUDIT.md` — belong to that composite rather than to any one of them.

## The portable patch

The in-game mod manager, the gameplay profiles and the whole custom-enemy framework came from
**`PncEdi-portable-patch`**, by **Dupli9d**, posted to the same thread on 19 August 2026 (§127).
Its features were adapted onto this tree rather than merged, and two of its documents —
`BepInEx/custom-enemies/CUSTOM-ENEMIES.md` and `WALL-PICTURE-TRAPS.md` — are theirs, checked claim
by claim against this tree in §129. The manifest parser is still substantially their code.

## The funscripts

The gallery began as scripts written by other people, and some rows still descend from them
through retiming rather than having been re-derived from the game's animations. In order:

| what | who |
|---|---|
| the original gallery scripts, in `pnc edi integration` | **everydayhandyuser**, 27 May |
| `zombie` and `plantasha` — scripted to video in OpenFunscripter, and the best in the set | shipped inside that same release; the scripter is not named on the thread |
| `new.funscript` — an explicit work in progress, diced into consecutive slices | **Dupli9d**, 1 Jun |
| `imp1`, `imp2`, `imp3` | **mr_spunky**, early Jun |
| `ambient.funscript`, `peek.funscript` | **AniFS**, 6 Jun |
| the play-through captures AniFS scripted against | **mr_spunky**, 6 Jun |

The originals are kept unmodified in `Edi/_reference/source-scripts/`.

Scripting conventions this project follows — stroke ranges, what to do with a blowjob or a riding
scene, when to exaggerate and when to be true to depth — are from eroscripts'
[getting-started guide](https://discuss.eroscripts.com/t/how-to-get-started-with-scripting/2234).

## Redistributed with the release

- **BepInEx** — LGPL-2.1, redistributed unmodified: <https://github.com/BepInEx/BepInEx>
- **Unity Doorstop** — CC0: <https://github.com/NeighTools/UnityDoorstop>

## Custom-enemy package media

Packages are third-party artwork and are **not** in this repository and **not** in the release —
each is its own download, and each carries a `SOURCE.txt` crediting the artists, galleries and
sound sources it draws on. The manifest and funscripts of a package are tracked here; its media
never is, because git history is permanent and a takedown would mean rewriting it.

## Tools

The measurement work rests on **UnityPy**, **Pillow**, **NumPy** and **TypeTreeGeneratorAPI**
(pinned in `code/requirements.txt`, and pinned because they decide what a sprite's pixels are), on
**ILSpy** / `ilspycmd`, and on `ikdasm` and `monodis` from **Mono**. The funscripts that were
authored to video were made in **OpenFunscripter**.

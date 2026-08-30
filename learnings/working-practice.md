# Working practice

Process rules this project arrived at the hard way - about copies, defaults, decisions and deployment.

**Read this when:** before adding a second copy of anything, changing a default, or trusting a note that says 'do not redo'

**Keywords:** build last then publish the checksum, a document that ships cannot describe its own archive, mirrored copy, generate, config default, decisions expire, deploy, release, permission bit, dedup key, decompile diff, rename pass

---

- **Every behaviour change gets a config with the old behaviour available.** The config file
  is the changelog users read. Defaults encode the intended feel; the escape hatch keeps it
  arguable.
- **Except when the "old behaviour" is a workaround the game has superseded — then delete the
  setting with the code.** `KeepImpsAfterGrappleShake` existed because 0.2.1 destroyed a
  shaken-off grappler; 0.3.1 releases and throws it, so the mod's version had become an override
  of a better mechanic. Keeping it as an off-by-default escape hatch would have preserved a dead
  workaround as a supported option, and shipped a setting nobody can evaluate — the thing it
  restores is not "the old feel", it is the mod fighting the game (§114). The test is whose
  behaviour the flag chooses between: two of ours is a setting, ours versus the game's own
  current one is a decision.
- **BepInEx resolves a setting by (section, key), so a hand-written entry in the wrong section is
  inert.** `Bind()` misses it, the plugin uses its coded default, and the next launch writes a
  second copy under the right section while the hand-placed one survives as an orphan nobody
  reads. It fails in the safest-looking direction — the default usually equals what the file
  already said — so nothing misbehaves until someone changes the value and is ignored
  (`DebugHotkeysIgnoreHeldKeys`, §47→§49). `code/cfgaudit.py` checks every one of them (150 at
  the time of writing); run it before regenerating the distributable. Note the audit must key on the **pair**: `Enabled` is bound
  four times under different sections, and a name-keyed check drowns the real defect in three
  false positives.
- **If the config changes and no tool of yours wrote it, the game did.** BepInEx re-serialises on
  startup, which reorders entries into section order and strips the comment blocks of anything it
  did not bind. That rewrite is diagnostic, not noise — it is what exposed §49.
- **Don't hand-maintain a code fallback that duplicates a config default — derive it.**
  The §32 D5 correction landed in `DioramaAmbientMap`'s default string and missed the parallel
  `DioramaGalleryMap.DefaultDSlotAmbients[4]`. Our own config being patched hides this
  completely: in-game testing here can never reach the fallback. Fixing the copy would only have
  reset the clock, so §33 deleted it and reads `ConfigEntryBase.DefaultValue` instead — the
  fallback is now the shipped default *by construction*. Where a duplicate must exist, grep the
  source for the **old value**, not the setting name.
- **A tool that documents a case it does not handle is worse than one that says nothing**, because
  the documentation is what stops anyone checking. `_remap_by_frame`'s docstring named the exact
  case it was written for — "the gallery Plantasha cum includes a frame gameplay skips" — and it
  had never handled it: `_frame_anchors` numbered each clip's distinct frames 0, 1, 2 … and joined
  the two timelines on that ordinal, which equals joining on frame *identity* only while both
  clips hold the same frames in the same order. One insertion and every later frame mapped to its
  neighbour's slot. It sat there from §53 until §71 put a second clip with the same insertion
  through it. Two things follow: anchor a join on the thing's **identity**, never its position in
  a list (the same rule as the dedup key below); and when a tool is claimed to handle a case,
  either the test exists or the claim does not.
- **A derived artefact has a cheap invariant — write it down and check it.** A frame remap onto a
  clip of the *same* length must be the identity; onto a different length it must move something
  other than the closing point. The broken remap produced a twin identical to its master except
  for the last point, which is exactly what a clip 111 ms longer cannot look like, and no one
  looked because the output had the right shape (§71).
- **A dedup key made of position is a key made of luck.** `SeenSceneSources` guarded "one lock
  per scene source" with `scene|kind|name|x,y,z`, so it actually meant *per square decimetre*: a
  walking enemy got a lock each time it caught you somewhere new, a stationary one got exactly one
  per run, and the same enemy catching you twice in one doorway was refused. Nobody designed that.
  If a guard is meant to identify a *thing*, key it on the thing; if it is meant to identify an
  *occasion*, do not key it at all (§42).
- **The distributable config is generated from the local one, so local tweaks ship.** This is now
  a build-time assertion rather than a habit: `release.py` compares every setting against its own
  documented default and aborts on any difference not declared in `SHIPPED`, with a reason. The
  first run found two that had been shipping for months — `HeatLockAutoHealRate = 120` (120 HP/s
  against a default of 1) and a `PeekGalleryMap` that was a stale *subset* of the coded default.
  **A convention only holds until someone is in a hurry; the same rule as a check holds always.**
  It works because BepInEx writes `# Default value:` into the file itself from the `Bind()` call,
  so the guard reads the plugin's own defaults and cannot go stale (§58).
- **A "tried and reverted, do not redo" note is a decision, and decisions expire.** The
  `ambient_imp_gangbang_2` rejection was correct under an assumption that a later session
  disproved, and then sat in a do-not-redo list telling the next session to leave it alone.
  When a measurement invalidates an old premise, go back and annotate what that premise
  justified — the reverted list is read literally, which is the whole point of it.
- **Deploy used to be a separate step from build, and that cost a full round of "the fix doesn't
  work" testing against the previous binary.** Since §62 the build does it: `PatchGameInstalls`
  runs `deploy.py --dll-only` after every `dotnet build`, so the game installs cannot be a
  version behind the source. Everything *else* — config, gallery, BepInEx — still needs
  `python3 code/deploy.py`, and `--check` exits non-zero when a target is stale, which is the
  question to ask before believing a test result. `release.py` passes `-p:DeployToGames=false`:
  building an archive must not swap the binary you are mid-test on.
  **When a manual step has already cost you a session, hang it off the thing you cannot forget
  to do.**
- **A document that ships inside the archive cannot describe that archive.** `CHANGELOG.md` goes
  into every release as `PncEdi-CHANGELOG.txt`, so §163's habit of writing the zip's sha256 into
  the entry that announces it is a loop: recording the number changes the file, which changes the
  archive, which changes the number. The same trap catches any figure about the build — size, file
  count, a "what is in this release" summary — written into a file the build packs. **Build last,
  and publish the checksum the final `release.py` prints**, keeping it in `TODO.md`, which is
  untracked and never shipped. A stale sha in a changelog is worse than none: it is a number a
  reader can check and be misled by.
- **A mirrored copy is a bug waiting for a deadline; generate it instead.** `mod/single-mod` was a
  hand-kept duplicate of the plugin, the config and both gallery trees, and six tools had to write
  to two paths to keep it true. Every accident it caused was the same shape — one side updated,
  the other not. Deleting it (§58) removed the second write from `variants`, `retime`, `rederive`,
  `authored`, `impgrab` and `cfgaudit` and replaced it with `release.py`, which reads the one live
  tree. **If two copies must agree, do not maintain both — build one from the other, at the moment
  it is needed.**
- Log tags are greppable and worth adding: `[HEAT-LOCK]`, `[AMBIENT]`, `[ENEMY-WAKE]`,
  `[ENEMY-REVIVE]`, `[GRAPPLE-DEATH]`, `[SPAWN]`, `[FILLER]`, `[MIMIC-GATE]`, `[GRAB-GATE]`,
  `[AI-GUARD]`, `[SPIN-AI]`.

**Edi is open source** (`github.com/NoGRo/Edi`) even though the game is not. Cloning it settled in
one grep what `GenerateDefinitionFromChapters` does (writes `Definitions_auto.csv`, and only when
`Definitions.csv` is missing — completely inert), and gave the exact slice semantics
`inproveLoopAccion` applies, which is what made splitting the multi-scene strips verifiable
instead of hopeful. Check for upstream source before reverse-engineering behaviour.

**A permission bit is a fact about how a file arrived, not about the file.** The 0.2.1 Linux build
ships `Post Nut Calamity.x86_64` as mode **0666**, and any trip through a zip, a Windows
filesystem or a naive copy strips it anyway. `start-pnc-linux.sh` selected its candidate with
`[ -x ]` and therefore refused to start on a completely ordinary install (§60); it tests `-f` and
chmods instead. BepInEx's own `run_bepinex.sh` has the same trap, which is why the chmod must
happen before handing over to it. **Test on a fresh unpack, not the working directory** — the bit
had been set by hand here months ago, so nothing local could ever have shown this.

**`TODO.md` regrows unless closing an item means deleting it.** (It is untracked since §146 —
private working notes — so check whether the working tree has one before reaching for it. The rule
below is about the file when it exists.) §70 cut it from 1017 lines to
126; by §136 it was back to 1207, and almost none of that was open work — it was sixty sessions of
*closed* items kept in place with a strikethrough and a "confirmed in play" note, plus a handoff per
session and a standing-guidance section that had become a second copy of `learnings/`. The drift is
one habit: a session finishes something and records the outcome where the work was written down.
The rule that keeps the file its own size is that **the four documents each hold one thing** — open
work in `TODO.md`, the narrative in `CHANGELOG.md`, the rules in `learnings/`, the map and the
commands in `PROJECT.md`, `README.md` and `code/README.md` — so closing an item means deleting it
from `TODO.md` once the `§n` entry exists, and one handoff at a time. A generalised rule written into a CHANGELOG
entry has the same problem in the other direction: it is invisible to the grep that `CLAUDE.md`
asks for, because nobody greps a 9,000-line narrative for a rule. State it in `learnings/` and let
the entry point at it (§137).

**A stale-deploy failure is usually not something you changed.** The *game* rewrites
`game-linux`'s own `com.edi.pnc.cfg` at launch, so `deploy.py --check` reports the install
stale after any played session even when nothing in the working tree moved. `deploy.py
--no-build` puts it back. Do not go looking for an edit you did not make.

**Set a value at both ends rather than letting either inherit the working tree.** `deploy.py`
forces `[EDI] Debug = true` into the two game installs — they exist to be played while a log is
read, and every `Plugin.DBG` line is behind that one setting — and `release.py` ships `Debug =
false` through `SHIPPED`, so a player gets a quiet log. Whatever is committed in between decides
neither. The failure this prevents is not a broken build but a quiet one: a `false` committed by
accident costs the *next* investigation its log and looks like nothing at all (§73).

**`SHIPPED` is a decision list, not a deviation list.** Its check only *demands* an entry when the
live value differs from the coded default, which makes it easy to read the absence of an entry as
"nothing to decide here". `("EDI", "Debug")` is there with live and default both `true`, because
the release wants `false` — the entry exists to record a decision no deviation would have forced.

**A tool's dependencies belong beside the tool, and pinned (§102).** The venv the asset tools need
lived in a scratch directory under `/tmp`, so every tool that reads a sprite was one reboot away
from an `ImportError` and a re-install — and the install line lived in prose, in two docs, at two
different levels of detail. It is now `.venv/` in the repo with `code/requirements.txt` tracked
beside the scripts that import it. The pins are not ceremony: UnityPy decodes the sprites and
Pillow decodes their textures, so both decide what pixels `animsweep`, `gallerydiff` and
`refvideo --verify` compare a funscript against, and an unpinned upgrade could move a measured
number with nobody touching a script. The same reasoning as the pinned BepInEx and Edi bundles
(§59): what a verification runs against is part of the verification.

**A `.gitignore` that is an allowlist makes new directories invisible, which cuts both ways.** No
rule was needed to keep `.venv/` out of git — `/*` then `!` per opted-in path means anything new at
the top level is ignored by default. That is the same property that once hid `learnings/` for as
long as it took to notice. Worth checking `git status` after adding a directory you *do* want
tracked.

**A decompile diff is blind to exactly the change a rename pass makes, and that is what makes it
the right check.** Local variable names live in the PDB, not in the IL, so renaming 1300 of them
moves the §116 diff by zero lines - a clean run is not weak evidence, it is the strongest
available statement that nothing else moved with them. What the diff *does* see is worth knowing
before a pass starts, because each hit needs an account: parameter names (metadata, so a
`text` -> `name` on a private method shows up), and any genuine local the pass deleted rather than
renamed. §123's 33 lines were three parameter renames and one redundant `string a = b;` copy.
Compiler-generated locals - the `array2 = array` cache a `foreach` creates - are re-created on the
next build and cost nothing, so deleting those stays invisible too.

**Compiling is not reading, and a note saying you did not read it is not reading it either.**
§127 ported ~5,000 lines of someone else's mod on compile-correctness alone and wrote in the handoff
that the bodies had never been read. §128 read them and found four defects, none subtle - a
`File.WriteAllLines` straight over `Definitions.csv`, a package able to silently repoint an existing
gallery row, a runtime writer that permanently falsified `deploy.py --check`, and scenes that kept
running and POSTing to Edi behind a paused game. Every one of them was in a file that had already
passed a build, `patchaudit`, and a full `check.py`. **A project's checks cannot see inherited
assumptions**, because they were written to guard the assumptions it already had. Budget the reading
into the port; it is not a follow-up task.

**Inherited code is not wrong, it is differently-assumed.** None of §128's four defects is a mistake
in the fork they came from: in a single-install, no-repo, hand-managed tree, writing into the live
gallery and clocking a scene on unscaled time are both fine. They became defects on contact with
*this* project's shape - a repo that generates the install, and a check that answers "is what I am
about to launch the working tree". The useful question when taking code in is therefore not "is this
correct" but **"what does this assume about where it runs, and is that true here"**.

**Two implementations of one rule are acceptable only when they have different callers and a way to
notice disagreement.** §124's "one rule where there were two" is the default and stays. §128 kept a
deliberate exception: package gallery rows are built both by `release.py` (for anyone with this repo)
and by the mod at runtime (for a player who has only a game directory), because neither caller can
use the other's path. What makes that survivable is that a drift between them shows up immediately
and specifically, as `deploy.py --check` reporting stale after a launch. Without that signal it
would just be two rules.

**A drift signal is only worth having if someone acts on the first one.** The paragraph above was
written in §128, naming `deploy.py --check` reporting stale as the thing that would catch the two
gallery writers disagreeing. It caught it on the very next launch, and the cause was not a subtle
divergence in a shared rule: the repo-side builder read `manifest["scenes"]` for every package kind
while a wall trap keeps its scenes under `animations`, so it emitted **no rows at all** for one kind
and the runtime writer put them back on every launch (§129). The signal worked exactly as designed.
What it also showed is that "two implementations, one rule, watched by a check" had quietly become
*three* divergences, because the second implementation was a private copy that had also lost the
ownership rule, the crash-safe write and the file-content guard. **The check tells you the outputs
disagree; it cannot tell you the two writers are no longer one rule with two callers.** When a check
like that fires, fix the output and then go and read both implementations — the answer is usually
that there should only be one.

**Imported documentation is confident about exactly the parts that changed.** §129 took four
Markdown files from the fork §127 had ported code from, and fourteen of their claims were wrong for
this tree. The pattern was not sloppiness — every one was true where it was written. The worst were
the ones describing *the fork's own deliberate changes*: a per-class lock table §127 had explicitly
declined to import, spawn multipliers this tree had replaced with named settings, and a config
section that does not exist here. A document arrives asserting the tree it grew in, and its author
was most careful in the passages about what they had just changed, which are precisely the passages
you did not take. So: **check an imported document claim by claim against the code it now sits
beside, and treat its confident passages as the suspicious ones.** Also check what it *points at* —
its cross-references (`INSTALL-...cmd`, `scripts/validate-*.ps1`, a diagnostic on F12) are the
cheapest wrong claims to find and the ones a reader trusts most.

**A documentation habit that nobody can observe will not happen.** `CLAUDE.md` asked sessions to
"open the index before anything non-obvious" for eleven sessions, and §130 still re-derived a §46
rule from a source comment instead of reading the file that held it. The wording was advice, and
advice loses to whichever file obviously has the answer in front of you. The fix was not a stronger
adjective but an **observable step**: grep `learnings/` for the symptom or identifier, and *say what
came back, including when nothing did*. A step that appears in the reply can be checked by the
person reading it; one that happens silently is indistinguishable from being skipped, because the
answer looks the same either way - just arrived at the long way round (§133). The same shape as
`bridgeaudit.py` (§132) and the missing-definitions log (§96): if the failure mode is silence, the
fix is to make it say something.

**A measurement is evidence about a mechanism, not permission to change it.** A new `[OVERHEAT]`
instrument measured the player disarmed for 51% of a five-minute run, and that number bought a fix on
the spot: clear the overheat latch outright at full lock, since a floor one point under the cap means
vanilla's "cool all the way down" can never be served. The report from the same run was *"the
overheating mechanic worked fine"* — 51% is what riding the cap looks like, overheat and cool and
overheat again, working as designed. The fix would have deleted a punishment from the game on the
strength of a number nobody had complained about, and it was reverted the same session (§134).

A second reason not to generalise from it, recorded later: **51% was a femboy-witch run.** Her aura
is what held heat at the lock floor for that long, so the figure describes one custom enemy's
pressure, not what ordinary play does to the heat bar. A number carries the conditions it was taken
under, and this one's conditions were not written down beside it for two sessions.

The instrument stays; only the conclusion was wrong. **A number is a description of what the machine
did. Whether that is a defect is a question about what someone wanted**, and on this project that
someone is the person who played it. When a fresh instrument produces a striking figure, say the
figure and ask, rather than treating it as a bug report that arrived from yourself.

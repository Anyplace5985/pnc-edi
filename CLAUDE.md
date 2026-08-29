# PNC + Edi

**Read `PROJECT.md` first, at the start of every session, before doing anything else.** It is the
map: what this project is, how the repo is laid out, how a funscript actually gets played, and the
build / deploy / release commands. Nothing below repeats it.

Then, depending on what you are doing:

- **`learnings/`** — everything learned the hard way. **Two ways in, and they serve different
  questions.**

  **Symptom-first, and this one is a rule: before diagnosing any behaviour, or writing anything
  non-obvious, grep `learnings/` for the symptom or the identifier — and say in your reply what you
  found, or that you found nothing.** Not "consult the learnings when useful": run the grep, report
  the result. Both halves are the rule. Saying it out loud is what makes the step checkable, because
  skipping it is invisible from the outside — the answer looks the same either way, just arrived at
  the long way round.

  **Topic-first: `learnings/README.md`,** which a grep cannot stand in for. Read it when you are
  picking up an area rather than chasing a symptom — "I am about to touch funscript timing" — and
  for its "the ones that have cost the most time" section, which is the answer to what you do not
  yet know to search for. Its keywords column is also written in the vocabulary people grep with,
  so it is a grep target in its own right and often the first hit.

      grep -ril "SetActive" learnings/          # a symptom or an API name
      grep -rn "grabCoroutine" learnings/       # an identifier you are about to touch

  This is written down because it was skipped: §130 re-derived "assigning a coroutine-driven state
  before the coroutine is running is a latent hang" from a source comment, when
  `learnings/grab-and-ai-mechanics.md` had carried that rule since §46. It cost time and it only
  worked at all because this tree happens to be commented unusually well at that exact spot. A rule
  that lives in no single source file — which is most of what `learnings/` holds — has no such
  safety net.
- **`README.md`** — the public front door, and the only document written for someone who owns none
  of this context: requirements, setup, build, deploy, check, release. It is what a stranger reads
  first, so when any of those commands or prerequisites change, it changes too.
- **`TODO.md`, if the working tree has one** — untracked private working notes, so a clone
  does not carry it and a session cannot assume it is there. **Check first**; if it exists it
  holds only what is still open, and it is where to start to pick up work. If it does not,
  `CHANGELOG.md`'s newest `§n` entry is the most recent state of play.

  **And when you finish something, delete it from here.** Not a strikethrough, not a "confirmed in
  play" note under the old text — a deletion, once the `§n` entry exists, because that entry is the
  record. One handoff at a time, replacing the last. This is the one rule in this file that has
  already failed twice: §70 cut this file from 1017 lines to 126 and wrote the boundary into four
  documents, and it was back to 1207 by §136 (§137 cut it to 195). It fails because closing an item
  and recording the outcome feel like the same action, and the file you are editing is the obvious
  place for both. It is not: the outcome goes to `CHANGELOG.md`, the rule it produced goes to
  `learnings/`, and what is left here is what is still open.
- **`CHANGELOG.md`** — the narrative record, `§1`-`§143`. Go here for the reasoning behind a rule, or
  to check whether something was already tried and rejected. **It is narrative, not rules** — a
  generalised rule written into a `§n` entry is invisible to the grep above, because nobody greps a
  9,000-line history for a rule. State it in `learnings/` and have the entry point at it.
- **`code/README.md`** — build, release and tool reference for the `code/` tree.
- **`CREDITS.md`** — whose work this is built on: the game, Edi, the PncEdi mod this one
  continues, the fork the custom-enemy framework came from, and the funscripts the gallery started
  as. Two of those authors are unnamed in this tree, which the file says out loud. It ships in
  every release archive, so anything added to it is public.
- **`code/tests/README.md`** — `dotnet test code/tests/PncEdi.Tests.csproj`. The naming, alias
  and config layer is unit-tested against the real source files; run it before and after
  touching any of them, and mutate the code to check a new test actually fails.
- **`python3 code/check.py`** — every check this project has, in one run (`--full` before a
  release). It wraps the tests above and the audits and sweeps PROJECT.md lists, and knows
  which of them report failure by exit code and which by a word in their output (§121).

## Three things that catch people out

(A fourth, if you are editing `PncEdi`: it is one of **three plugins**, and a call to
`CustomEnemyBridge` is load-bearing even where deleting it looks harmless — `PROJECT.md` has the
table of what each plugin owns, `code/bridgeaudit.py` is what notices.)

**Editing a file changes nothing a running game can see.** The game is reached through the
`game-windows` / `game-linux` symlinks and has its own copy of everything. After touching
`Edi/Gallery/`, `BepInEx/config/*.cfg` or `BepInEx/custom-enemies/`, run
`python3 code/deploy.py --no-build`;
`python3 code/deploy.py --check` answers "is what I am about to launch actually the working tree".

**When a session reports a problem, read that session's log before you read the source.** The mod
instruments itself for exactly this: `game-linux/BepInEx/LogOutput.log` — the newest run only, since the Linux
launcher rotates the previous one into `BepInEx/logs/` (`WriteUnityLog` is forced
into both installs by every deploy, §95) and `BepInEx/PncEdi-missing-definitions.log`, plus Edi's
own `Edilog<date>.txt`. Three greps
first — `ALIAS-GAP`, `EDI-SKIP`, `failed:`. Reading the source first turns diagnosis into a search
over everything the code *could* do; the log says what it *did*, and in §92 it held three answers a
source-first pass had already given up on. `learnings/debugging-and-diagnostics.md` has the rule.

**Measure before you write.** The order that keeps a session out of trouble is *look at the scene,
then measure, then write* — `learnings/funscript-proxies.md` for the first two steps,
`learnings/funscript-authoring.md` for the third. Verified numbers in this project were measured
against specific game assets; do not re-derive one against a build it was never measured on.

#!/usr/bin/env python3
"""Is every ambient `Patterns` entry reachable, and does every scene loop match one?

    .venv/bin/python code/dioramaaudit.py
    .venv/bin/python code/dioramaaudit.py --all      # list every clip and source, not just gaps

**The question, and why it can be answered without a run.** `AmbientProximity` picks the diorama
the player is standing at by matching audio: it lowercases the AudioSource's `clip.name` and its
owning GameObject's name and asks whether either CONTAINS an alias from `Gameplay/Patterns`. The
winner is the LONGEST matching alias, with an exact hit scoring +1000 - so `imp gangbang 2` beats
the shorter `imp gangbang` on the same clip, and the order of the entries does not matter.

A pattern that matches nothing cannot fire. A scene loop that matches no pattern is worse: it still
plays, but `AmbientReleaseGaze.NoteCandidate` declines a box with a null pattern, so the diorama can
never arm its one-time look-to-release. That is the defect this was written for, which reads in a
run as `box D13 -> ambient_nun_watersports (no ambient pattern matched here)`.

**Both halves of the match are static, but not in the same place.** The alias list is in
`com.edi.pnc.cfg`. The other half is split: an AudioSource's `m_audioClip` is null in almost every
shipped scene - the clip is assigned at runtime by script - so the clip NAMES have to be read from
the AudioClip assets themselves rather than followed from the sources that will play them. This
checks each alias against both sets: the 240-odd clip names in the build, and the names of the
GameObjects carrying a looping AudioSource. Either one is enough, because `MatchPattern` accepts
either.

That is also the limit worth knowing: this proves an alias CAN match something in the build, not
that the particular source at a particular diorama is the one it matches. Only a run answers that,
and `AMBIENT-SCAN` in the log is where it is answered.

Needs UnityPy. `PNC_GAME_DIR` selects the build, through `pncpaths`.

    python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt
"""
import UnityPy, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pncpaths

SHOW_ALL = "--all" in sys.argv

D = pncpaths.game_data_dir("dioramaaudit")
CFG = os.path.join(pncpaths.ROOT, "BepInEx", "config", "com.edi.pnc.cfg")


def read_patterns(path):
    """`Patterns` is one line: comma-separated entries, each `canonical|alias|alias`."""
    for line in open(path, encoding="utf-8"):
        if line.startswith("Patterns ="):
            entries = []
            for entry in line.split("=", 1)[1].strip().split(","):
                aliases = [a.strip().lower() for a in entry.split("|") if a.strip()]
                if aliases:
                    entries.append((aliases[0], aliases))
            return entries
    sys.exit(f"dioramaaudit: no `Patterns =` line in {path}")


PATTERNS = read_patterns(CFG)

FILES = sorted(f for f in os.listdir(D)
               if f.startswith(("level", "sharedassets", "resources.assets"))
               and not f.endswith((".resS", ".resource")))
env = UnityPy.load(*[os.path.join(D, f) for f in FILES])

# Two name sets, because MatchPattern will accept either one.
clips, gameobject_names = set(), {}
for obj in env.objects:
    if obj.type.name == "AudioClip":
        try:
            clips.add(obj.read_typetree().get("m_Name") or "")
        except Exception:
            pass
    elif obj.type.name == "GameObject":
        try:
            gameobject_names[(obj.assets_file.name, obj.path_id)] = obj.read_typetree().get("m_Name") or ""
        except Exception:
            pass

sources = set()
for obj in env.objects:
    if obj.type.name != "AudioSource":
        continue
    try:
        d = obj.read_typetree()
    except Exception:
        continue
    if not d.get("Loop"):
        continue
    ptr = d.get("m_GameObject") or {}
    if not ptr.get("m_FileID") and ptr.get("m_PathID"):
        name = gameobject_names.get((obj.assets_file.name, ptr["m_PathID"]))
        if name:
            sources.add(name)

clips.discard("")
haystack = [(c, "clip") for c in sorted(clips)] + [(s, "object") for s in sorted(sources)]


def best(name):
    """MatchPattern's rule, applied to one name: longest alias wins, exact scores +1000."""
    lower = name.lower()
    winner, score = None, -1
    for canonical, aliases in PATTERNS:
        for alias in aliases:
            if alias in lower:
                s = len(alias) + (1000 if lower == alias else 0)
                if s > score:
                    winner, score = (canonical, alias, lower == alias), s
    return winner


print(f"{len(PATTERNS)} pattern(s), {len(clips)} AudioClip name(s), "
      f"{len(sources)} object(s) carrying a looping AudioSource\n")

unreachable = []
for canonical, aliases in PATTERNS:
    hits = [(n, kind, alias) for n, kind in haystack for alias in aliases if alias in n.lower()]
    # Only count a hit this entry would actually win: a longer alias elsewhere takes the name.
    won = [(n, kind) for n, kind, _ in hits if (best(n) or (None,))[0] == canonical]
    if won:
        if SHOW_ALL:
            where = ", ".join(f"{kind} '{n}'" for n, kind in won[:4])
            print(f"  ok       {canonical:<24} <- {where}")
    else:
        unreachable.append((canonical, hits))
        print(f"  DEAD     {canonical:<24} matches no clip and no looping source in this build")

if SHOW_ALL:
    print()
    for name, kind in haystack:
        m = best(name)
        if m:
            print(f"  {kind:<6} '{name}' -> {m[0]} ({'exact' if m[2] else f'contains {m[1]!r}'})")
        else:
            print(f"  {kind:<6} '{name}' -> (no pattern)")

print()
if unreachable:
    print(f"{len(unreachable)} pattern(s) can never fire in this build:")
    for canonical, hits in unreachable:
        stolen = sorted({n for n, _, _ in hits})
        if stolen:
            print(f"  {canonical}: its aliases appear in {stolen[:3]}, but a longer alias wins each one")
        else:
            print(f"  {canonical}: no clip or source name contains any of its aliases")
    sys.exit(1)

print(f"ok - all {len(PATTERNS)} pattern(s) resolve to a clip or a looping source in this build")

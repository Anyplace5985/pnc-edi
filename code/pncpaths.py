#!/usr/bin/env python3
"""The paths every tool in `code/` needs, resolved once.

Not a CLI. Import it:

    import pncpaths as P
    P.ROOT               # the repo root, whatever the working directory is
    P.DEFINITIONS        # Edi/Gallery/Definitions.csv
    P.game_data_dir()    # the `*_Data` folder of a game install

**Why this file exists.** Nine scripts each carried their own
`ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`, eight built the path to
`Definitions.csv` by hand, and `PNC_GAME_DIR` was read in two places that disagreed about what it
means - `animcheck` took it as an *install* directory and globbed `*_Data` under it, while
`spawntables` took it as the `_Data` directory itself and resolved it against the working
directory rather than the repo. PROJECT.md documents the first meaning. `game_data_dir` below
accepts both, so neither invocation that is written down anywhere breaks, and there is now one
answer to "where is the game" for every tool.

Nothing here reads the game or the gallery beyond locating them; the readers stay in the tools
that own them.
"""
import csv
import glob
import os
import sys

# `__file__` is `<repo>/code/pncpaths.py`, so two dirnames up is the repo root. This is
# deliberately not `os.getcwd()`: every tool here is run as `code/<tool>.py` from the repo root by
# convention, but nothing enforces that, and one tool that assumed it (`animsweep`) failed from
# anywhere else.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GALLERY = os.path.join(ROOT, "Edi/Gallery")
DEFINITIONS = os.path.join(GALLERY, "Definitions.csv")
DETAILED = os.path.join(GALLERY, "handy2pro")

# The asset bundles every sprite and clip in the game is packed into.
ASSET_FILES = ["sharedassets0.assets", "sharedassets1.assets", "resources.assets"]


def game_dir():
    """A game install directory. `PNC_GAME_DIR` overrides the `game-windows` symlink.

    The repo is the mod and only the mod (PROJECT.md), so the game is always outside it. The
    default is whatever `game-windows` points at; `PNC_GAME_DIR` is how a figure is reproduced
    against another build - every verified number in this project was measured against
    a 0.2.1 install kept outside the repo.

    A relative `PNC_GAME_DIR` is resolved against the repo root, not the working directory, so it
    means the same thing whichever directory a tool is run from.
    """
    override = os.environ.get("PNC_GAME_DIR")
    if not override:
        return os.path.join(ROOT, "game-windows")
    return override if os.path.isabs(override) else os.path.join(ROOT, override)


def game_data_dir(tool=None):
    """The `*_Data` folder of a game install.

    The folder is not called the same thing across builds - Windows ships
    `Post Nut Calamity_Data`, the Linux build ships `PNC 0.3.2_Data` - so it is globbed
    rather than named.

    `PNC_GAME_DIR` may point at either the install or the `_Data` folder inside it. Both spellings
    are written down in this repo (PROJECT.md uses the first, `spawntables.py`'s own usage line
    the second), and telling them apart costs one `Managed/` test.
    """
    base = game_dir()
    if os.path.isdir(os.path.join(base, "Managed")):
        return base                                   # already a *_Data folder
    hits = sorted(d for d in glob.glob(os.path.join(base, "*_Data")) if os.path.isdir(d))
    if not hits:
        sys.exit(f"{tool or 'pncpaths'}: no *_Data folder under {base}\n"
                 f"  point PNC_GAME_DIR at a game install, or check the game-windows symlink")
    return hits[0]


def definitions_rows(path=None):
    """Every row of `Definitions.csv` as a dict.

    Always `utf-8-sig`: the file carries a BOM, and a reader that forgets it gets a first column
    called `﻿Name` that silently matches nothing.
    """
    with open(path or DEFINITIONS, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))

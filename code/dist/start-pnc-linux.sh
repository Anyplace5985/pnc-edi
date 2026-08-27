#!/bin/sh
# Start Post Nut Calamity with the Edi integration on native Linux.
#
# BepInEx's own run_bepinex.sh needs to be told the game executable, either by editing
# executable_name at the top of it or by passing it as the first argument. This wrapper works
# that out instead, so the mod is drop-in on Linux the same way it is on Windows.
#
# Deliberately a separate file from run_bepinex.sh: that one ships verbatim from BepInEx, so
# upgrading BepInEx stays a straight copy with nothing of ours to re-apply.
#
#   ./start-pnc-linux.sh              launch, auto-detecting the executable
#   ./start-pnc-linux.sh -- -screen-width 1920    pass arguments through to the game
#
# Running the game under Proton instead? Then you want the Windows path: winhttp.dll and
# doorstop_config.ini are already in place and Proton loads them itself. This script is not used.

set -eu

here=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$here"

if [ ! -f ./run_bepinex.sh ]; then
    echo "start-pnc-linux.sh: run_bepinex.sh is not next to me." >&2
    echo "Extract the whole archive into the game directory, keeping its layout." >&2
    exit 1
fi

# Unity ships the Linux player as <name>.x86_64. Prefer one that looks like this game, but accept
# a single unambiguous candidate under any name so a renamed install still works.
#
# Tested for -f, NOT -x: the 0.2.1 Linux build ships mode 0666, and any trip through a zip or a
# Windows filesystem loses the bit anyway. Requiring it here would refuse to start on a completely
# normal install - and BepInEx's own run_bepinex.sh refuses for the same reason, which is why the
# chmod below has to happen before we hand over to it.
exe=""
for candidate in ./*.x86_64; do
    [ -f "$candidate" ] || continue
    case $candidate in
        *[Pp]ost*[Nn]ut*|*PNC*|*pnc*) exe=$candidate; break ;;
    esac
    if [ -z "$exe" ]; then
        exe=$candidate
    else
        exe="AMBIGUOUS"
    fi
done

if [ -z "$exe" ]; then
    echo "start-pnc-linux.sh: no *.x86_64 game executable in $here." >&2
    echo "This script belongs in the game directory, beside the .x86_64 and its _Data folder." >&2
    echo "On the Windows build under Proton you do not need it - winhttp.dll does the job." >&2
    exit 1
fi

if [ "$exe" = "AMBIGUOUS" ]; then
    echo "start-pnc-linux.sh: more than one *.x86_64 here and none of them names the game." >&2
    echo "Run BepInEx's script directly instead:  ./run_bepinex.sh ./<the game>.x86_64" >&2
    exit 1
fi

chmod +x ./run_bepinex.sh "$exe" 2>/dev/null || true

# Drop a leading "--" so `start-pnc-linux.sh -- <game args>` reads naturally.
if [ $# -gt 0 ] && [ "$1" = "--" ]; then
    shift
fi

echo "start-pnc-linux.sh: launching $exe with BepInEx"
exec ./run_bepinex.sh "$exe" "$@"

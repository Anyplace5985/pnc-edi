#!/usr/bin/env python3
"""Watch what the Handy is actually holding, while a session plays.

    python3 code/handystate.py [--hz 2] [--log game-linux/BepInEx/LogOutput.log] [--raw]

**Why this exists.** Edi tells the device what to play and then stops looking. A playback is
synchronised twice, both times inside its first 1.6 s (`PlaybackSyncDelay` 1500 ms plus a
follow-up), and after that neither Edi's log nor ours says anything about the device until the
next Play. A 36-second loop is measured for two seconds and unobserved for thirty-four. Every
theory about what the hardware is doing in that gap has been unfalsifiable - see §104 and TODO
item 5.

The Handy answers for itself. `GET v3/hsp/state` returns the buffer the device is actually
looping:

    points            how many points are in the buffer
    first_point_time  the buffer's low bound, in ms
    last_point_time   the buffer's high bound
    current_time      where in that range the device is right now
    play_state        1 = playing

Because Edi rebases every slice to zero, a row's buffer should read `first=0`,
`last=<its duration>`, `points=<the points in its slice>`. That triple is close to a fingerprint,
so this prints the rows it could be - which answers "is the device even holding the script the
screen is showing" directly, rather than by inference.

**It only reads.** No PUT, no play, no stop. Polling is on you: default 2 Hz against your own
device.

Credentials come from Edi's own `UserConfig.json` (`Handy.Key`, `Handy.ApiKey`) and are never
printed. That file is per-user state and is not in this repo - see `.gitignore`'s allowlist and
the note in `PROJECT.md`.
"""
import argparse, csv, json, os, re, sys, time, urllib.error, urllib.request
from datetime import datetime

import pncpaths as P

ROOT = P.ROOT
BASE = "https://www.handyfeeling.com/api/handy-rest/"
# Edi writes UserConfig.json to the platform's local-app-data. **Edi.exe runs under Wine here**,
# so the config the running instance actually uses is the one inside the prefix, and the two do
# not have to agree - they held different connection keys, which is a whole device apart. Both
# are candidates and the device decides which is real.
CONFIG_PATHS = [
    os.path.expanduser(
        "~/.wine/drive_c/users/"
        + os.environ.get("USER", "")
        + "/AppData/Local/Edi/UserConfig.json"),
    os.path.expanduser("~/.local/share/Edi/UserConfig.json"),
]
# EdiConfig.json names each device the way HandyHttpClient does - "The Handy [<connection key>]" -
# so the gallery config is a third, authoritative source for which device Edi is driving.
EDI_CONFIGS = [
    os.path.join(ROOT, "Edi/EdiConfig.json"),
    os.path.join(ROOT, "game-linux/Edi/EdiConfig.json"),
]
HANDY_NAME = re.compile(r"The Handy \[([^\]]+)\]")
# HspPlayState, from the device's own constants.proto. STARVING is the one to watch for: Edi
# never sets `pause_on_starving`, so a starved device keeps its clock running with nothing to
# play - which would feel like skipped strokes and would last until the next Play.
PLAY_STATE = {0: "uninit", 1: "PLAY", 2: "stop", 3: "pause", 4: "STARVE"}


def now():
    return f"{datetime.now():%H:%M:%S.%f}"[:12]


def mask(value):
    """Never print a connection key: it is the credential for someone's hardware."""
    return value[:2] + "*" * max(0, len(value) - 4) + value[-2:] if len(value) > 4 else "****"


def candidates():
    """[(key, api_key, where)] - every connection key this machine knows about.

    Which one is live is not knowable from a file, so they are probed rather than chosen."""
    found, seen = [], set()
    api_key = None
    for path in CONFIG_PATHS:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig") as fh:
            handy = (json.load(fh) or {}).get("Handy") or {}
        api_key = api_key or handy.get("ApiKey")
        key = handy.get("Key")
        if key and key not in seen:
            seen.add(key)
            found.append([key, handy.get("ApiKey"), path])
    for path in EDI_CONFIGS:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig") as fh:
            devices = ((json.load(fh) or {}).get("Devices") or {}).get("Devices") or {}
        names = devices if isinstance(devices, dict) else {}
        for name in names:
            hit = HANDY_NAME.search(name)
            if hit and hit.group(1) not in seen:
                seen.add(hit.group(1))
                found.append([hit.group(1), api_key, path])
    for entry in found:
        entry[1] = entry[1] or api_key
    if not found:
        sys.exit("No Handy connection key found in any known config.")
    return [(k, a, w) for k, a, w in found if a]


def live_credentials(timeout):
    """Probe every candidate and return the one the cloud says is actually connected."""
    tried = []
    for key, api_key, where in candidates():
        try:
            state(key, api_key, timeout)
            return key, api_key, where
        except DeviceAway:
            tried.append((key, where, "not connected"))
        except Exception as err:  # noqa: BLE001 - report and keep probing
            tried.append((key, where, str(err)))
    print("No connected Handy. Keys tried:")
    for key, where, why in tried:
        print(f"  {mask(key)}  from {where}\n      {why}")
    sys.exit(1)


def fingerprints(variant):
    """{(points, duration_ms): [row names]} for every row in the gallery.

    Edi slices `[StartTime, EndTime]` out of the file and rebases to zero, so what reaches the
    device is that many points spanning that many milliseconds."""
    out = {}
    for row in P.definitions_rows():
            path = os.path.join(P.GALLERY, variant, row["FileName"] + ".funscript")
            if not os.path.exists(path):
                continue
            try:
                start, end = float(row["StartTime"]), float(row["EndTime"])
            except (TypeError, ValueError):
                continue
            with open(path, encoding="utf-8-sig") as script:
                actions = json.load(script).get("actions") or []
            n = sum(1 for a in actions if start <= a["at"] <= end)
            out.setdefault((n, int(end - start)), []).append(row["Name"])
    return out


class DeviceAway(Exception):
    """The API answered, but no device is on the other end of it."""


def state(key, api_key, timeout):
    request = urllib.request.Request(
        BASE + "v3/hsp/state",
        headers={
            "X-Connection-Key": key,
            "authorization": "Bearer " + api_key,
            "accept": "application/json",
        })
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    # The REST layer wraps every HSP reply in `result`, the way HspStateResult expects. A
    # reachable API with an absent device answers 200 with an `error` object instead - the Handy
    # is a cloud-brokered device, so "the request succeeded" and "the hardware is there" are
    # different questions.
    if isinstance(body.get("error"), dict):
        raise DeviceAway(body["error"].get("message") or "device unavailable")
    return body.get("result", body)


def log_lines(path):
    """Yield `[EDI] Play ...` lines appended to our log while this runs, newest work last."""
    if not path or not os.path.exists(path):
        return
    with open(path, encoding="utf-8", errors="replace") as fh:
        fh.seek(0, os.SEEK_END)
        while True:
            line = fh.readline()
            if not line:
                return
            if "[EDI] Play" in line or "[EDI-NOSEEK]" in line:
                yield line.rstrip()


def main():
    parser = argparse.ArgumentParser(
        description="Poll the Handy's HSP buffer state while a session plays.")
    parser.add_argument("--hz", type=float, default=2.0,
                        help="polls per second (default 2)")
    parser.add_argument("--log", default="game-linux/BepInEx/LogOutput.log",
                        help="our log, tailed for Play lines to interleave; '' to skip")
    parser.add_argument("--variant", default="handy2pro",
                        help="gallery folder the device is set to (default handy2pro)")
    parser.add_argument("--raw", action="store_true",
                        help="print the whole state object each poll")
    parser.add_argument("--out", metavar="PATH",
                        help="also append every line to this file, so a run survives the "
                             "terminal it was watched in")
    parser.add_argument("--timeout", type=float, default=4.0)
    args = parser.parse_args()

    sink = open(args.out, "a", encoding="utf-8", buffering=1) if args.out else None

    def emit(line):
        print(line)
        if sink:
            sink.write(line + "\n")

    key, api_key, source = live_credentials(args.timeout)
    prints = fingerprints(args.variant)
    log_path = os.path.join(ROOT, args.log) if args.log else None
    tail = log_lines(log_path)

    emit(f"device {mask(key)} - live, from {source}")
    emit(f"gallery fingerprints: {len(prints)} distinct (points, duration) in '{args.variant}'")
    emit(f"polling {BASE}v3/hsp/state at {args.hz} Hz - Ctrl-C to stop\n")
    emit(f"{'time':<13}{'state':>7}{'pos':>7}{'idx':>5}{'first':>7}{'last':>7}{'pts':>5}"
         "  buffer looks like")

    last_key = None
    while True:
        started = time.monotonic()
        for line in tail or ():
            emit(f"  <- {line.split('] ', 2)[-1]}")
        try:
            snapshot = state(key, api_key, args.timeout)
        except urllib.error.HTTPError as err:
            emit(now() + f"  HTTP {err.code} - {err.reason}")
            snapshot = None
        except DeviceAway as err:
            emit(now() + f"  {err} - is Edi running and the Handy powered on?")
            snapshot = None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            emit(now() + f"  {err}")
            snapshot = None
        if snapshot:
            if args.raw:
                emit(json.dumps(snapshot, sort_keys=True))
            first = snapshot.get("first_point_time", 0)
            last = snapshot.get("last_point_time", 0)
            points = snapshot.get("points", 0)
            span = int(last) - int(first)
            names = prints.get((points, span), [])
            # A buffer that does not start at 0 is a seeked (rotated) entry, which is its own
            # story - §104. Say so rather than reporting it as an unknown shape.
            note = ("rotated: starts at %d, not 0" % first) if first else ""
            shape = ", ".join(names[:4]) if names else "no row with this (points, span)"
            if names and len(names) > 4:
                shape += f" (+{len(names) - 4} more)"
            key_now = (points, first, last)
            marker = "  *" if key_now != last_key else ""
            last_key = key_now
            # `current_time` is the stream clock and free-runs well past the buffer, so the
            # useful figure is where inside the loop that lands.
            clock = snapshot.get("current_time", 0)
            pos = (clock - first) % span if span > 0 else clock
            state_name = PLAY_STATE.get(snapshot.get("play_state"), "?")
            emit(now()
                  + f"{state_name:>7}"
                  + f"{pos:>7}"
                  + f"{snapshot.get('current_point', -1):>5}"
                  + f"{first:>7}{last:>7}{points:>5}  {shape}{note}{marker}")
        time.sleep(max(0.0, 1.0 / args.hz - (time.monotonic() - started)))


if __name__ == "__main__":
    main()

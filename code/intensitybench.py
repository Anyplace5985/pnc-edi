#!/usr/bin/env python3
"""Bench Edi's POST /Edi/Intensity/{max} against what the Handy actually holds.

    python3 code/intensitybench.py [--row Serpent_Hypnosis] [--hold 4]

Needs Edi running on 127.0.0.1:5000 and the Handy connected. Read-only against the device;
the only writes are to Edi (one Play, then Intensity steps, then Intensity back to 100).

The question: does Intensity change the device's stroke range LIVE, without restarting the
playback? Edi's DevicePlayer.Intensity sets device.Max, DeviceBase debounces 100 ms and calls
applyRange(), and HandyV3Device.applyRange sends SetStroke(Min, Max). Nothing in that path
re-dispatches PlayGallery unless the range was in the stop band. That is the claim; this
measures it.

Two readings per step:
  the slide endpoint  the device's own slide min/max - did the range actually move?
  v3/hsp/state        current_time - did playback keep running, or did it reset to 0?

Edi writes the range with `PUT v2/slide` (HandyHttpClient.SetStroke) even on the v3 device, so
the read is v2 as well - `v3/slide` is a 404. The candidates below are probed once at startup
because the Handy API has moved endpoints between versions before and a 404 here is not worth a
failed bench run.
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import handystate as H

EDI = "http://127.0.0.1:5000"


def get(path, key, api_key, timeout=6):
    request = urllib.request.Request(
        H.BASE + path,
        headers={"X-Connection-Key": key,
                 "authorization": "Bearer " + api_key,
                 "accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    if isinstance(body.get("error"), dict):
        raise H.DeviceAway(body["error"].get("message") or "device unavailable")
    return body.get("result", body)


SLIDE_CANDIDATES = ("v2/slide", "v3/slide", "v2/slide/settings", "v3/hsp/settings")


def find_slide_endpoint(key, api_key):
    """The first slide path this device answers, or None."""
    for path in SLIDE_CANDIDATES:
        try:
            get(path, key, api_key)
            return path
        except urllib.error.HTTPError as err:
            if err.code != 404:
                print(f"  {path}: HTTP {err.code}")
        except Exception as err:  # noqa: BLE001 - keep probing
            print(f"  {path}: {err}")
    return None


def edi(path, timeout=6):
    request = urllib.request.Request(EDI + path, data=b"", method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--row", default="Serpent_Hypnosis", help="a looping gallery row to play")
    ap.add_argument("--hold", type=float, default=4.0, help="seconds between intensity steps")
    ap.add_argument("--steps", default="100,70,40,20,40,70,100")
    args = ap.parse_args()

    key, api_key, where = H.live_credentials(6)
    print(f"device key {H.mask(key)} from {where}")

    slide_path = find_slide_endpoint(key, api_key)
    if slide_path is None:
        print("No slide endpoint answered - the range read is unavailable, so this run can only"
              " show whether playback survives an Intensity change.")
    else:
        print(f"slide endpoint: {slide_path}")

    print(f"Play {args.row}")
    edi(f"/Edi/Play/{args.row}")
    time.sleep(2.0)

    try:
        run_steps(args, key, api_key, slide_path)
    finally:
        # Intensity is global to the channel: leaving it at 20 would make everything played
        # afterwards quieter, including a game session, with nothing on screen to say why.
        edi("/Edi/Intensity/100")
        edi("/Edi/Stop")
        print("intensity restored to 100, playback stopped")


def row_duration_ms(name):
    """The slice length Edi will play for this row, from Definitions.csv."""
    for row in H.P.definitions_rows():
        if row["Name"].lower() == name.lower():
            try:
                return int(float(row["EndTime"]) - float(row["StartTime"]))
            except (TypeError, ValueError):
                return None
    return None


def run_steps(args, key, api_key, slide_path):
    """Step the intensity and, at each step, ask the device what it holds.

    **`current_time` alone cannot tell a restart from a loop wrap**, and the first run of this
    bench was read wrongly because of it: `Serpent_Hypnosis` is a 1000 ms looping row, so
    `current_time` is somewhere in [0, 1000) at every sample and a drop means nothing at all.
    What separates the two is the *phase the clock should be at*: predict
    `(previous + elapsed) % duration` from the wall clock between the two reads, and a wrap lands
    on the prediction while a restart lands near zero. Anything else is drift worth seeing.
    """
    duration = row_duration_ms(args.row)
    if duration:
        print(f"row duration {duration} ms" + (
            "  (shorter than the hold - the phase check carries the reading)"
            if duration < args.hold * 1000 else ""))
    last_time = None
    last_read = None
    for step in [int(field) for field in args.steps.split(",")]:
        edi(f"/Edi/Intensity/{step}")
        time.sleep(0.4)                      # 100 ms debounce plus one round trip
        slide = get(slide_path, key, api_key) if slide_path else "(unavailable)"
        read_at = time.monotonic()
        st = get("v3/hsp/state", key, api_key)
        t = st.get("current_time")

        verdict = ""
        if last_time is not None and t is not None and duration:
            elapsed = int((read_at - last_read) * 1000)
            predicted = (last_time + elapsed) % duration
            drift = (t - predicted + duration // 2) % duration - duration // 2
            if abs(drift) <= 250:
                verdict = f"  playback continued (phase {drift:+d} ms off)"
            elif t < 400:
                verdict = "  RESTARTED (clock back near zero)"
            else:
                verdict = f"  phase jumped {drift:+d} ms"
        print(f"  intensity {step:3d} -> slide {slide}   hsp current_time={t}{verdict}")
        last_time, last_read = t, read_at
        time.sleep(max(0.0, args.hold - 0.4))


if __name__ == "__main__":
    main()

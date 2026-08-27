# Funscript timing

How to get a scene's period and cycle count right, and the traps that fake a wrong answer.

**Read this when:** deriving or retiming a funscript, or an `animsweep` row reads OFF / near

**Keywords:** stroke rate, cycle period, autocorrelation, whole-cycle, drift, frame quantisation, reps, stroke_period

---

**Compare stroke rate, not cycle period.** Autocorrelation finds the *repeat* period,
which may contain several strokes. `Gravy_Loop` cycles at 994 ms but contains a fast
double-stroke — it looked "58% wrong" against a 631 ms measurement and was actually
correct. Count peaks per cycle before concluding anything.

**Autocorrelation is meaningless on a slice shorter than ~2 cycles.** `Mimic_Start`
(1750 ms, one peak) reported a phantom 1545 ms period. Its slice *is* one animation cycle.
Always check `slice_duration / measured_period` before trusting a number.

**A measurement window longer than one scene is worthless.** The single biggest error
source. Always verify window length against the block's expected per-scene duration and
reject anything over ~1.5×.

**Frame quantisation fakes ~1% errors.** At 60 fps, autocorrelation snaps to 16.7 ms.
A true 555 ms period reads as 550. Use parabolic interpolation on the AC peak and read
the 2×/3× harmonics divided by their order — that gives sub-frame precision and turned
two phantom "1% errors" into +0.1%.

**Magnitude signals give the half-period.** `|frame diff|` peaks twice per stroke. Use a
signed position proxy (centroid, occlusion area) to get the true period and the phase.

**Drift ≠ wrong period.** A slice whose length isn't a whole number of cycles replays a
partial cycle every loop. `peek_wendigo_ride` had a compressed 600 ms lead-in inside a
667 ms loop → 2% slip, ~one cycle every 33 s. Check integer cycle counts separately from
stroke rate.

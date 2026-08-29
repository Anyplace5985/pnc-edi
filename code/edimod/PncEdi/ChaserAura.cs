using System;
using System.Reflection;
using UnityEngine;

namespace PncEdi;

// The chaser bosses' approach, scripted by how close the thing you can hear is.
//
// Asked for in the release thread (post 113's list): the filler should build as the dragon's or
// the wendigo's approach closes in, rather than playing the same way whether the boss is across
// the floor or behind you. That is the one thing in this mod's vocabulary that had no
// mechanism until §125 gave the serpent one - and it is the same mechanism, so most of what
// follows is `SerpentHypnosis`' reasoning applied to a second signal. Read that file first; only
// the four differences below are new.
//
// WHAT THIS SHARES WITH THE SERPENT
//
//   * **Distance drives amplitude, not which row is playing.** `POST /Edi/Intensity/{max}`
//     scales the device's stroke range in place while the filler keeps looping, so there is no
//     re-dispatch, no seam and no phase to carry. Measured on a Handy 2 Pro in §125.
//   * **One continuous ramp, no tiers.** §120 and §125 between them established that a ladder
//     over a six-metre band is coarse rather than slow, and that adding rungs back is a move
//     already rejected. There are no boundaries here, so there is nothing to flap across and
//     nothing that needs hysteresis or a minimum dwell.
//   * **Whatever lowers the range owns raising it.** Intensity is global to the channel.
//
// FOUR THINGS THAT ARE NOT THE SERPENT'S PROBLEM
//
//   1. **The gate is the sound itself, because that is what the request was about.**
//      `DragonEnemyAI.UpdateIdleMovingSound` plays `idleMovingSound` on `loopingAudioSource`
//      while `!isDead && !frozenByArena && (state is Idle or Chasing) && !isAttemptingGrab`, and
//      stops it otherwise. Reading `loopingAudioSource.isPlaying` is that whole predicate, one
//      frame fresh, and it is the same posture as `SerpentHypnosis.InPlayerView` reading
//      vanilla's `hypnosisInView` rather than recomputing visibility: the device is gated on
//      exactly the answer the player's ears are. It also covers the case §47 found - a wendigo
//      parked in the level with its AI ticking, waiting for its trigger time - correctly rather
//      than by accident, because a parked chaser *is* audible and *is* what the request means.
//
//   2. **There is no scene search and no per-frame `FindObjectsByType`.** Both AI classes keep a
//      public static `ActiveDragons` list, added to in `OnEnable` and removed from in
//      `OnDisable`, so the live set is two list walks of length 0 or 1 in practice. An enemy the
//      mod itself hides or deactivates leaves the list on its own, which is the answer we want.
//
//   3. **The band's far edge is a config number, not the prefab's.** The serpent could use
//      `hypnosisStartRange` because the mechanic defines one. Here the honest far edge would be
//      the looping source's `maxDistance` - but `InitializeComponents` only sets `loop` and
//      `playOnAwake` on it, so its spatial settings come from the prefab, and where the source
//      was added at runtime Unity's default is a *non-spatial* one with `maxDistance` 500. A
//      500 m band would put the whole floor at the far value and make the ramp invisible. So
//      `ChaserAuraRange` is an explicit metre figure, `0` means "trust the source's own
//      `maxDistance`", and the entry log prints both so the first run says which the number
//      should have been. The near edge *is* the prefab's: `grabRange`, where the grab lands and
//      its own scene takes the device over.
//
//   4. **The ramp is slew-limited, and that is what answers the objection this request came
//      with.** Post 113's own reply says driving intensity off distance "tends to read as
//      jerky", and the serpent's ramp is only smooth because its band is entered by a mechanic
//      that starts at the far edge. This band has no such courtesy: a chaser's loop starting, a
//      chaser dying, one walking out of earshot, or two of them where the nearest changes, all
//      move the target in one step. `ChaserAuraRamp` caps how fast the *held* value may move
//      toward the target, in percent per second, so every one of those becomes a ramp instead of
//      a jump and the boundary needs no hysteresis to stop it flapping - a value that cannot
//      step cannot flap. It is the same answer §112 gave with a dwell, in the axis §125 moved
//      this kind of decision into.
//
// **THE SERPENT OUTRANKS THIS.** Both write one channel-wide number and the serpent's is part of
// a scene it is also choosing the row for, so while it holds the range this stands down: it keeps
// slewing its own held value so it has somewhere sane to resume from, and sends nothing.
//
// **AND A REAL SCENE TAKES THE RANGE BACK AT ONCE.** Leaving the band slews, because that is a
// thing happening in the world; a grab starting does not, because §125's second run is what that
// costs - a 15 s grab played at the amplitude the last approach left behind, with nothing on
// screen to say why. `Tick` runs from `Plugin.Update` for exactly that case: it is the one time
// the filler refresh this would otherwise live in is not being asked anything.
internal static class ChaserAura
{
	private static FieldInfo _dragonLoopSource;
	private static FieldInfo _proxDragonLoopSource;

	// The held value, in percent, as a float so the slew can move it by fractions of a percent
	// per frame. 100 is "nothing is lowering the range".
	private static float _held = 100f;
	private static int _lastSent = -1;
	private static float _lastSentAt;
	private static bool _lowered;
	private static string _lastLogged;

	/// <summary>
	/// Re-derive the aura's amplitude and send it if it has moved enough to be worth a POST.
	/// Called every frame from <see cref="Plugin.Update"/>.
	/// </summary>
	internal static void Tick()
	{
		if (!Plugin.CfgEnableChaserAura.Value)
		{
			ReleaseNow();
			return;
		}
		// A real scene owns the device. Snapping rather than slewing is the whole point: the
		// scene is already playing by the time this frame runs, so a ramp would spend its first
		// second at the aura's amplitude.
		if (!Plugin.FillerPlaybackActive || Plugin.PlayerDead)
		{
			ReleaseNow();
			return;
		}
		float target = TargetFor();
		float ramp = Mathf.Max(1f, Plugin.CfgChaserAuraRamp.Value);
		_held = Mathf.MoveTowards(_held, target, ramp * Time.unscaledDeltaTime);
		if (SerpentHypnosis.OwnsIntensity)
		{
			// Stood down, but still tracking, so a serpent that breaks off hands back to a value
			// that belongs to where the chaser actually is rather than to where it was.
			_lastSent = -1;
			_lowered = false;
			return;
		}
		int rounded = Mathf.Clamp(Mathf.RoundToInt(_held), 0, 100);
		if (rounded >= 100)
		{
			// Arriving at the top is the release, and it goes whatever the step and the interval
			// say - a range left at 97 is a range nothing will ever restore.
			ReleaseNow();
			return;
		}
		int step = Mathf.Max(1, Plugin.CfgChaserAuraIntensityStep.Value);
		float interval = Mathf.Max(0f, Plugin.CfgChaserAuraIntensityInterval.Value);
		// `Plugin.RequestedIntensity` rather than our own last figure: anything else that moved
		// the channel - the serpent releasing, a scene restoring it - has to be answered, and
		// comparing against what we *sent* would leave the aura believing a number the device no
		// longer holds.
		bool first = _lastSent < 0;
		if (!first && Mathf.Abs(rounded - Plugin.RequestedIntensity) < step)
		{
			return;
		}
		if (!first && Time.unscaledTime - _lastSentAt < interval)
		{
			return;
		}
		_lastSent = rounded;
		_lastSentAt = Time.unscaledTime;
		_lowered = true;
		// The description is built here and not in TargetFor, which runs every frame: formatting
		// five floats and stripping a clone suffix sixty times a second to throw all but one of
		// them away is exactly the per-frame garbage Update should not be making.
		string why = Describe();
		Plugin.SendIntensity(rounded, why);
		if (!string.Equals(_lastLogged, _who, StringComparison.Ordinal))
		{
			_lastLogged = _who;
			Plugin.DBG("CHASER-AURA", why + " -> " + rounded + "%");
		}
	}

	// The nearest audible chaser's numbers, as of the last Tick. Kept as fields so the ramp can
	// be re-derived every frame without allocating anything.
	private static string _who;
	private static float _whoDistance;
	private static float _whoBand;
	private static float _whoGrabRange;
	private static float _whoSourceMax;

	private static string Describe()
	{
		return $"{NameRemap.StripCloneSuffix(_who)} at {_whoDistance:0.0}m of {_whoBand:0.0}-{_whoGrabRange:0.0} (its loop reaches {_whoSourceMax:0.0}m)";
	}

	// 100 when nothing is closing in; otherwise the ramp's value for the nearest audible chaser.
	private static float TargetFor()
	{
		float nearest = float.MaxValue;
		float band = 0f;
		float grabRange = 0f;
		string who = null;
		float sourceMax = 0f;
		for (int i = 0; i < DragonEnemyAI.ActiveDragons.Count; i++)
		{
			DragonEnemyAI ai = DragonEnemyAI.ActiveDragons[i];
			if (ai == null || !Audible(ai, LoopSource(ai, ref _dragonLoopSource), out float max))
			{
				continue;
			}
			Consider(ai.DistanceToPlayer, ai.grabRange, max, ai.name, ref nearest, ref band, ref grabRange, ref sourceMax, ref who);
		}
		for (int i = 0; i < ProximityDragonEnemyAI.ActiveDragons.Count; i++)
		{
			ProximityDragonEnemyAI ai = ProximityDragonEnemyAI.ActiveDragons[i];
			if (ai == null || !Audible(ai, LoopSource(ai, ref _proxDragonLoopSource), out float max))
			{
				continue;
			}
			Consider(ai.DistanceToPlayer, ai.grabRange, max, ai.name, ref nearest, ref band, ref grabRange, ref sourceMax, ref who);
		}
		_who = who;
		_whoDistance = nearest;
		_whoBand = band;
		_whoGrabRange = grabRange;
		_whoSourceMax = sourceMax;
		if (who == null)
		{
			return 100f;
		}
		int far = Mathf.Clamp(Plugin.CfgChaserAuraIntensityFar.Value, 0, 100);
		int near = Mathf.Clamp(Plugin.CfgChaserAuraIntensityNear.Value, 0, 100);
		// 1 is the far edge of the band, 0 is grabRange - the same orientation as the serpent's,
		// so the two knobs read the same way in the config file.
		float bandFraction = Mathf.Clamp01((nearest - grabRange) / Mathf.Max(0.01f, band - grabRange));
		return Mathf.Lerp(near, far, bandFraction);
	}

	private static void Consider(float distance, float grabRange, float sourceMax, string name,
		ref float nearest, ref float band, ref float nearestGrabRange, ref float nearestSourceMax, ref string who)
	{
		float far = Plugin.CfgChaserAuraRange.Value > 0f ? Plugin.CfgChaserAuraRange.Value : sourceMax;
		// Outside the band it is audible but not close enough to mean anything; inside it, the
		// nearest one wins, because that is the one the ramp is about.
		if (far <= 0f || distance > far || distance >= nearest)
		{
			return;
		}
		nearest = distance;
		band = far;
		nearestGrabRange = Mathf.Max(0f, grabRange);
		nearestSourceMax = sourceMax;
		who = name;
	}

	// Vanilla's own answer to "can the player hear this thing coming", and the source's own idea
	// of how far that reaches. A chaser with no looping source, or one whose loop is stopped, is
	// not part of the aura at all.
	private static bool Audible(MonoBehaviour ai, AudioSource loop, out float maxDistance)
	{
		maxDistance = 0f;
		if (ai == null || loop == null || !loop.isPlaying)
		{
			return false;
		}
		maxDistance = loop.maxDistance;
		return true;
	}

	// `loopingAudioSource` is private and the two AI classes do not share a base, so this is one
	// cached FieldInfo each. A rename upstream turns the aura off rather than throwing per frame,
	// which is the safe way to be wrong: nothing else depends on it.
	private static AudioSource LoopSource(MonoBehaviour ai, ref FieldInfo cached)
	{
		if (cached == null)
		{
			cached = ai.GetType().GetField("loopingAudioSource", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
			if (cached == null)
			{
				return null;
			}
		}
		try
		{
			return cached.GetValue(ai) as AudioSource;
		}
		catch (Exception)
		{
			return null;
		}
	}

	/// <summary>Hand the range back at once and forget the approach. A scene change has nothing to ramp back to.</summary>
	internal static void ResetNow()
	{
		_held = 100f;
		_lastLogged = null;
		ReleaseNow();
	}

	private static void ReleaseNow()
	{
		_held = 100f;
		_lastSent = -1;
		// Never restore over the serpent: it lowered the range for a scene of its own and owns
		// putting it back. The stand-down in Tick already clears `_lowered` for that case, so
		// this is the belt to its braces - `ResetIntensity` is a write to one shared number and
		// a spurious one costs a full-amplitude stroke in the middle of an approach.
		if (_lowered && !SerpentHypnosis.OwnsIntensity)
		{
			_lowered = false;
			_lastLogged = null;
			Plugin.ResetIntensity("the chaser aura gave the device back");
		}
	}
}

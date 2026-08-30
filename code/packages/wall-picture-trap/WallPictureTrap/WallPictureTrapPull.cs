using System.Collections.Generic;
using CMF;
using HarmonyLib;
using PncCustomEnemies.Api;
using UnityEngine;

namespace WallPictureTraps;

/// <summary>
/// The seam a wall trap has to use to move the player, and why an ordinary force does not.
///
/// The player is a <c>FirstPersonController : CMF.AdvancedWalkerController</c> - Character Movement
/// Fundamentals, an asset that does not simulate the player with forces at all. Its FixedUpdate
/// computes <c>velocity = movementVelocity + momentum</c> and hands the result to
/// <c>Mover.SetVelocity</c>, which does a flat <c>rig.linearVelocity = _velocity + groundAdjust</c>.
/// That is an assignment, not an accumulation: anything added to the Rigidbody between two physics
/// steps - <c>AddForce</c>, a velocity written directly, an impulse - is erased at the start of the
/// next one, before it has moved the player anywhere. The trap did exactly that
/// (<c>AddForce(pull, ForceMode.Acceleration)</c>) and the 2026-08-26 log is what it looks like
/// when it silently does nothing: `pulling player into 'joker_wall' from 7.49m` and
/// `player escaped pull range` alternating at the radius boundary, with every capture in the run
/// happening at 1.3m because the player had walked in.
///
/// So the pull is applied on the far side of that assignment instead. A postfix on
/// <c>SetVelocity</c> runs in the same FixedUpdate, immediately after CMF has written its own
/// answer, and adds the trap's contribution on top; the next step recomputes CMF's half and this
/// adds its half again. Nothing accumulates, nothing fights the controller, and the player keeps
/// full control of the rest of their movement - the pull is a summand, so walking away at
/// <c>movementSpeed</c> against a slower pull nets out as being dragged while making headway.
///
/// The alternative - writing into the controller's <c>momentum</c> - does not work here: momentum
/// is what CMF applies friction to, and this game's <c>groundFriction</c> is 100, so anything put
/// there is gone within a frame of touching the floor.
///
/// Nothing about this is trap-specific. If something else ever needs to shove the player, it wants
/// this class rather than a Rigidbody call that will look right and do nothing.
/// </summary>
[HarmonyPatch]
internal static class WallPictureTrapPull
{
	private static readonly List<WallPictureTrap> Pulling = new List<WallPictureTrap>();

	/// <summary>
	/// Has the postfix below actually run? Until it has, a trap cannot know whether the player is
	/// a CMF controller at all, and falls back to moving the transform itself. False for the first
	/// frame or two of a pull even in the normal case, which costs nothing; permanently false on a
	/// build whose player is driven some other way, which is the case worth having a fallback for.
	/// </summary>
	internal static bool Bound { get; private set; }

	internal static void Add(WallPictureTrap trap)
	{
		if (trap != null && !Pulling.Contains(trap)) Pulling.Add(trap);
	}

	internal static void Remove(WallPictureTrap trap)
	{
		Pulling.Remove(trap);
	}

	[HarmonyPatch(typeof(Mover), "SetVelocity")]
	[HarmonyPostfix]
	private static void Mover_SetVelocity_Postfix(Mover __instance)
	{
		Bound = true;
		if (Pulling.Count == 0) return;
		Rigidbody body = __instance.GetComponent<Rigidbody>();
		if (body == null) return;
		Vector3 pull = Vector3.zero;
		// Backwards, because a trap that has been destroyed or has stopped pulling drops out here
		// rather than leaving a dead entry to be skipped on every physics step for the rest of the
		// scene. Traps remove themselves too; this is the seat belt for the ones that cannot.
		for (int i = Pulling.Count - 1; i >= 0; i--)
		{
			WallPictureTrap trap = Pulling[i];
			if (trap == null || !trap.isActiveAndEnabled)
			{
				Pulling.RemoveAt(i);
				continue;
			}
			pull += trap.PullVelocity;
		}
		if (pull != Vector3.zero) body.linearVelocity += pull;
	}
}

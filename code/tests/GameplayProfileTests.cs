namespace PncEdi.Tests;

/// <summary>
/// The profile truth table, row by row.
///
/// This is the part of the profile feature worth testing: `GameplayProfiles` itself reaches for
/// `PlayerStats` and `HeatLockSystem` and cannot leave a running game, but the decision it exists
/// to make - given a profile and the three legacy switches, what is the mod doing to the game -
/// is pure, and lives in <see cref="GameplayProfileRules"/> so it can be checked here.
///
/// The property that matters most for an upgrade is the last group: under the default `Custom`
/// profile every answer has to be exactly what the three booleans said before profiles existed,
/// or installing this version silently retunes somebody's game.
/// </summary>
public class GameplayProfileTests
{
	[Fact]
	public void VanillaIgnoresEverySwitch()
	{
		// Vanilla is the one profile that has to win against a config full of enabled tweaks:
		// "leave the game alone" is not a request that admits exceptions.
		Assert.False(GameplayProfileRules.TweaksEnabled(GameplayProfile.Vanilla, true));
		Assert.False(GameplayProfileRules.GodModeEnabled(GameplayProfile.Vanilla, true, true));
		Assert.False(GameplayProfileRules.ReleaseModeEnabled(GameplayProfile.Vanilla, true, true));
		Assert.False(GameplayProfileRules.UsesClassHeatScaling(GameplayProfile.Vanilla, true, true));
	}

	[Fact]
	public void PressureAndReleaseTurnsLocksOnWithoutAskingTheLegacySwitches()
	{
		// Including with `Enabled = false` in the file: picking a named profile is the request,
		// and a leftover master switch must not be able to veto it.
		Assert.True(GameplayProfileRules.TweaksEnabled(GameplayProfile.PressureAndRelease, false));
		Assert.True(GameplayProfileRules.ReleaseModeEnabled(GameplayProfile.PressureAndRelease, false, false));
		Assert.True(GameplayProfileRules.UsesClassHeatScaling(GameplayProfile.PressureAndRelease, false, false));
		Assert.False(GameplayProfileRules.GodModeEnabled(GameplayProfile.PressureAndRelease, true, true));
	}

	[Fact]
	public void GodModeBlocksDamageAndLeavesLocksOff()
	{
		// The combination the profiles exist to make unreachable: god mode and heat locks at once,
		// where nothing can hurt you and the locks that replace being hurt still accumulate.
		Assert.True(GameplayProfileRules.GodModeEnabled(GameplayProfile.GodMode, false, false));
		Assert.False(GameplayProfileRules.ReleaseModeEnabled(GameplayProfile.GodMode, true, true));
		Assert.False(GameplayProfileRules.UsesClassHeatScaling(GameplayProfile.GodMode, true, true));
		Assert.True(GameplayProfileRules.TweaksEnabled(GameplayProfile.GodMode, false));
	}

	[Theory]
	// tweaks, godMode, heatLocks
	[InlineData(false, false, false)]
	[InlineData(false, true, true)]
	[InlineData(true, false, false)]
	[InlineData(true, true, false)]
	[InlineData(true, false, true)]
	[InlineData(true, true, true)]
	public void CustomIsExactlyWhatTheThreeSwitchesMeantBeforeProfilesExisted(
		bool tweaks, bool godMode, bool heatLocks)
	{
		Assert.Equal(tweaks, GameplayProfileRules.TweaksEnabled(GameplayProfile.Custom, tweaks));
		Assert.Equal(tweaks && godMode,
			GameplayProfileRules.GodModeEnabled(GameplayProfile.Custom, tweaks, godMode));
		Assert.Equal(tweaks && heatLocks,
			GameplayProfileRules.ReleaseModeEnabled(GameplayProfile.Custom, tweaks, heatLocks));
		// Class heat scaling under Custom followed the master switch alone, not the lock switch -
		// ClassHeatMultipliers.ApplyToPlayerHeat was called from a bare `if (tweaks)`.
		Assert.Equal(tweaks,
			GameplayProfileRules.UsesClassHeatScaling(GameplayProfile.Custom, tweaks, heatLocks));
	}
}

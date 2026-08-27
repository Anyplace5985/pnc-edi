namespace PncEdi.Tests;

/// <summary>
/// Dioramas: the game hands over a `galleryID` like `D13`, and the mod has to name an
/// `ambient_*` script. Three routes, in order - the user's map, the coded default, then a
/// keyword guess - because a diorama the game adds is better served by a plausible script than
/// by silence.
/// </summary>
public class DioramaGalleryMapTests
{
	[Fact]
	public void TheUsersMapWins()
	{
		Fixtures.Configure(dioramaMap: "D1=ambient_nun_chair_fuck", dioramaDefault: "D1=ambient_zombie_bench_fuck");
		Assert.Equal("ambient_nun_chair_fuck", DioramaGalleryMap.Resolve("D1"));
	}

	[Fact]
	public void TheCodedDefaultStillAppliesWhenTheUserHasBlankedTheirs()
	{
		// The reason the stub carries `DefaultValue` at all: BepInEx keeps the coded default
		// separately, and the built-in D-slot table is meant to survive a user deleting entries.
		Fixtures.Configure(dioramaMap: "", dioramaDefault: "D5=ambient_imp_gangbang");
		Assert.Equal("ambient_imp_gangbang", DioramaGalleryMap.Resolve("D5"));
	}

	[Theory]
	[InlineData("GargoyleD4", "ambient_gargoyle_ledge_fuck")]
	[InlineData("ZombieBench", "ambient_zombie_bench_fuck")]
	[InlineData("NunChair", "ambient_nun_chair_fuck")]
	[InlineData("PlantBJ", "ambient_plantasha_blowjob")]
	[InlineData("WendigoPeek", "ambient_wendigo_hole")]
	public void FallsBackToAKeywordGuessForAnUnlistedId(string galleryId, string expected)
	{
		Fixtures.Configure(dioramaMap: "", dioramaDefault: "");
		Assert.Equal(expected, DioramaGalleryMap.Resolve(galleryId));
	}

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	[InlineData("D99")]
	public void GivesUpRatherThanGuessingWildly(string galleryId)
	{
		Fixtures.Configure(dioramaMap: "", dioramaDefault: "");
		Assert.Null(DioramaGalleryMap.Resolve(galleryId));
	}

	[Fact]
	public void EveryDSlotInTheLiveConfigNamesAKnownRow()
	{
		Fixtures.ConfigureFromLiveConfig();
		for (int slot = 1; slot <= 15; slot++)
		{
			string row = DioramaGalleryMap.Resolve("D" + slot);
			Assert.True(row != null && GalleryRegistry.IsKnown(row),
				$"diorama D{slot} resolves to '{row ?? "nothing"}', which is in no gallery row");
		}
	}
}

/// <summary>
/// Peek scenes. Four exact keys are tried in a deliberate order before the clip name, and the
/// order is the finding: `enemyName` is a display string that 0.3.1 rewrote into jokes, and
/// `enemyID` is only `P1`..`P11`, so a renumbered peephole would otherwise map to a confidently
/// wrong scene - which is worse than a missing one (§80).
/// </summary>
public class PeekGalleryMapTests
{
	private const string Map =
		"ImpThreeWayGalleryData=peek_imp_three_way;ImpThreeWayGallery=peek_nuns_threeway;" +
		"Snussy Ray=peek_plant_bj;P4=peek_wendigo_ride";

	[Fact]
	public void TheAssetNameIsTriedFirst()
	{
		Fixtures.Configure(peekMap: Map);
		Assert.Equal("peek_imp_three_way", PeekGalleryMap.Resolve(
			enemyId: "P4", enemyName: "Snussy Ray", animationName: "",
			assetName: "ImpThreeWayGalleryData", peepholeController: "ImpThreeWayGallery"));
	}

	[Fact]
	public void ThenTheControllerName()
	{
		Fixtures.Configure(peekMap: Map);
		Assert.Equal("peek_nuns_threeway", PeekGalleryMap.Resolve(
			enemyId: "P4", enemyName: "Snussy Ray", animationName: "",
			assetName: null, peepholeController: "ImpThreeWayGallery"));
	}

	[Fact]
	public void ThenTheDisplayNameAndOnlyThenTheTriggerNumber()
	{
		Fixtures.Configure(peekMap: Map);
		Assert.Equal("peek_plant_bj", PeekGalleryMap.Resolve("P4", "Snussy Ray", ""));
		Assert.Equal("peek_wendigo_ride", PeekGalleryMap.Resolve("P4", "not in the map", ""));
	}

	[Fact]
	public void TheClipNameIsTheLastResortAndIsMatchedOnItsSlug()
	{
		// Every peek trigger in the game is named `P1`, `P2`, `P3`... The clip is the only thing
		// that says which peephole this is.
		Fixtures.Configure(peekMap: "", peekClipMap: "Peephole_Nuns=peek_nuns_threeway");
		Assert.Equal("peek_nuns_threeway", PeekGalleryMap.Resolve("P7", "whatever", "Peephole_Nuns"));
	}

	[Fact]
	public void TheGamesMisspeltPlantashaClipIsMappedToo()
	{
		// The game ships both `Peephole_Plantasha` and `Peephole_Planatasha`. Typing state names
		// from memory is how that gets missed - code/NAMING-AUDIT.md says to read them out of
		// the assets.
		Fixtures.ConfigureFromLiveConfig();
		Assert.Equal("peek_plant_bj", PeekGalleryMap.Resolve("P3", "x", "Peephole_Plantasha"));
		Assert.Equal("peek_plant_bj", PeekGalleryMap.Resolve("P3", "x", "Peephole_Planatasha"));
	}

	[Fact]
	public void LongerClipKeysAreTriedFirst()
	{
		Fixtures.Configure(peekClipMap: "Peephole=peek_zombie_bj;Peephole_Nuns=peek_nuns_threeway");
		Assert.Equal("peek_nuns_threeway", PeekGalleryMap.Resolve("P1", "x", "Peephole_Nuns"));
	}

	[Theory]
	[InlineData("peek_imp_three_way", true)]
	[InlineData("PEEK_Nun_Mimic", true)]
	[InlineData("Nun_Grab", false)]
	[InlineData("", false)]
	[InlineData(null, false)]
	public void IsPeekScriptTestsThePrefix(string name, bool expected)
		=> Assert.Equal(expected, PeekGalleryMap.IsPeekScript(name));

	[Fact]
	public void EveryPeekTargetInTheLiveConfigNamesAKnownRow()
	{
		Fixtures.ConfigureFromLiveConfig();
		foreach (var pair in ConfigMap.Pairs(Fixtures.ConfigValue("PeekGalleryMap")))
		{
			Assert.True(GalleryRegistry.IsKnown(pair.Value),
				$"PeekGalleryMap '{pair.Key}' -> '{pair.Value}', which is in no gallery row");
		}
	}
}

/// <summary>Per-class heat scaling - the one setting parsed as a number rather than a name.</summary>
public class ClassHeatMultiplierTests
{
	[Fact]
	public void UnconfiguredIsNeutral()
	{
		Fixtures.Configure(classHeat: "");
		Assert.Equal(1f, ClassHeatMultipliers.GetMultiplier("Rogue"));
	}

	[Fact]
	public void ReadsAMultiplierAndIsCaseInsensitive()
	{
		Fixtures.Configure(classHeat: "Rogue=1.5;Knight=0.5");
		Assert.Equal(1.5f, ClassHeatMultipliers.GetMultiplier("Rogue"));
		Assert.Equal(1.5f, ClassHeatMultipliers.GetMultiplier("rogue"));
		Assert.Equal(0.5f, ClassHeatMultipliers.GetMultiplier("Knight"));
	}

	[Fact]
	public void ClampsToAFloorRatherThanAllowingZero()
	{
		// A zero multiplier would make heat unreachable and the run unwinnable-in-reverse; the
		// floor keeps a silly config merely silly.
		Fixtures.Configure(classHeat: "Rogue=0;Knight=-5");
		Assert.Equal(0.01f, ClassHeatMultipliers.GetMultiplier("Rogue"));
		Assert.Equal(0.01f, ClassHeatMultipliers.GetMultiplier("Knight"));
	}

	[Fact]
	public void AnUnparsableValueLeavesTheClassNeutral()
	{
		Fixtures.Configure(classHeat: "Rogue=fast;Knight=1.25");
		Assert.Equal(1f, ClassHeatMultipliers.GetMultiplier("Rogue"));
		Assert.Equal(1.25f, ClassHeatMultipliers.GetMultiplier("Knight"));
	}

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	public void NoClassNameIsNeutral(string className)
	{
		Fixtures.Configure(classHeat: "Rogue=1.5");
		Assert.Equal(1f, ClassHeatMultipliers.GetMultiplier(className));
	}
}

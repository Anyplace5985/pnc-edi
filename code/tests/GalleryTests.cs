using System.Linq;

namespace PncEdi.Tests;

/// <summary>
/// Steps 3 and 4 of the dispatch pipeline (PROJECT.md): a slug becomes a gallery row name, and
/// the registry decides whether that name is real.
///
/// `GalleryRegistry` reads `Definitions.csv` at run time, which is what lets a new scene ship
/// with no code change - and is also why it is worth testing: the file may be absent, and the
/// two failures "the file has no such row" and "no file was found at all" used to look
/// identical in the log (§96).
/// </summary>
public class GalleryRegistryTests
{
	[Fact]
	public void FindsTheRealDefinitionsFileBesideTheTestBinary()
	{
		// The csproj copies `Edi/Gallery/Definitions.csv` into the output directory, which is
		// GalleryRegistry's third candidate path. If this fails, every other registry test is
		// only exercising the hardcoded seed list.
		Assert.Contains("Definitions.csv", GalleryRegistry.Source);
		Assert.DoesNotContain("no Definitions.csv found", GalleryRegistry.Source);
	}

	[Fact]
	public void SourceNamesTheFileAndItsRowCount()
	{
		// §96: this string is what the missing-definition log prints, and it exists to tell
		// "no such row" apart from "no file".
		Assert.Contains("row(s) beyond the built-in seed", GalleryRegistry.Source);
	}

	[Fact]
	public void KnowsRowsThatOnlyExistInDefinitionsCsv()
	{
		// `Serpent_Loop` and the goonshroom rows are 0.3.1 content and are not in the seed list
		// compiled into the DLL, so a true answer here proves the file was read.
		Assert.True(GalleryRegistry.IsKnown("Serpent_Loop"));
		Assert.True(GalleryRegistry.IsKnown("GoonShroom_Cum"));
	}

	[Fact]
	public void KnowsTheSeededRowsWithOrWithoutTheFile()
	{
		Assert.True(GalleryRegistry.IsKnown("Nun_Grab"));
		Assert.True(GalleryRegistry.IsKnown("filler"));
	}

	[Fact]
	public void IsCaseInsensitive() => Assert.True(GalleryRegistry.IsKnown("nun_grab"));

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	[InlineData("Definitely_Not_A_Row")]
	public void RejectsWhatIsNotThere(string name) => Assert.False(GalleryRegistry.IsKnown(name));

	[Fact]
	public void LooksPastASeekSuffix()
	{
		// Aliases may carry `?seek=<ms>`; the gate has to test the row, not the query.
		Assert.Equal("Serpent_Loop", GalleryRegistry.StripQuery("Serpent_Loop?seek=1200"));
		Assert.True(GalleryRegistry.IsKnown("Serpent_Loop?seek=1200"));
		Assert.Equal(GalleryRegistry.LoopMs("Serpent_Loop"), GalleryRegistry.LoopMs("Serpent_Loop?seek=1200"));
	}

	[Fact]
	public void StripQueryLeavesANameWithNoQueryAlone()
		=> Assert.Equal("Nun_Grab", GalleryRegistry.StripQuery("Nun_Grab"));

	[Fact]
	public void LoopMsIsTheRowsSliceLength()
	{
		// Used by the phase-preserving `?seek=` on a ladder switch (§87): Edi restarts a row
		// from the top, so the incoming row can only continue where the outgoing one got to if
		// the mod knows how long one loop is.
		int ms = GalleryRegistry.LoopMs("filler");
		Assert.True(ms > 0, "filler has no length; Definitions.csv was not read");
	}

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	[InlineData("Definitely_Not_A_Row")]
	public void LoopMsIsZeroWhenUnknownRatherThanThrowing(string name)
		=> Assert.Equal(0, GalleryRegistry.LoopMs(name));

	[Fact]
	public void SeededRowsCarryNoLength()
	{
		// The seed list is names only. Every caller has to treat 0 as "no length known" rather
		// than as a zero-length loop, and this is the case that would catch it changing.
		Assert.True(GalleryRegistry.IsKnown("Nun_Grab"));
		Assert.Equal(0, GalleryRegistry.LoopMs("Definitely_Not_A_Row"));
	}
}

/// <summary>
/// The alias table that turns a slug into a gallery row, and the two rules that make a gap
/// visible instead of plausible.
/// </summary>
public class GalleryAliasTests
{
	[Fact]
	public void TheBuiltInTableShipsInTheDllAndIsNotEmpty()
	{
		// Ownership was inverted deliberately: the table used to be the config setting's default
		// value, which BepInEx writes only when the key is absent, so every shipped config froze
		// the table as it was on the day it was written.
		Assert.NotEmpty(GalleryTable.Shared);
		Assert.Contains("nun_grab", GalleryTable.Shared);
	}

	[Fact]
	public void ResolvesASlugToItsRow()
	{
		Fixtures.Configure(galleryAliases: "nun_grab=Nun_Grab");
		Assert.Equal("Nun_Grab", GalleryAliases.Resolve("nun_grab", inGame: false));
	}

	[Fact]
	public void InGameAliasesWinOverTheSharedTableInGameplayOnly()
	{
		// The gallery viewer plays a different-length clip than gameplay for several scenes
		// (§52-§53), which is the whole reason for a second table.
		Fixtures.Configure(galleryAliases: "nun_cum=Nun_Cum_Gallery", inGameAliases: "nun_cum=Nun_Cum");
		Assert.Equal("Nun_Cum", GalleryAliases.Resolve("nun_cum", inGame: true));
		Assert.Equal("Nun_Cum_Gallery", GalleryAliases.Resolve("nun_cum", inGame: false));
	}

	[Fact]
	public void AKnownRowNameResolvesToItself()
	{
		Fixtures.Configure(galleryAliases: "");
		Assert.Equal("Nun_Grab", GalleryAliases.Resolve("Nun_Grab", inGame: false));
	}

	[Fact]
	public void AnUnmappedSlugComesBackUnchangedAndIsLoggedOnce()
	{
		// The old behaviour was a per-enemy substring matcher that returned *something* for any
		// string containing an enemy name. That is how peek scenes ended up on grab galleries
		// and why gaps were invisible for months. Returning the slug unchanged lets SendPlay's
		// IsKnown gate drop it and log it.
		Fixtures.Configure(galleryAliases: "nun_grab=Nun_Grab");
		Assert.Equal("nun_nonsense", GalleryAliases.Resolve("nun_nonsense", inGame: true));
		Assert.Contains(Plugin.Logged, l => l.StartsWith("[ALIAS-GAP]") && l.Contains("nun_nonsense"));
	}

	[Fact]
	public void QuietResolutionDoesNotReportAGap()
	{
		// PeekGalleryMap probes this speculatively and recovers with its own heuristic, so a
		// miss there is not a gap worth reporting.
		Fixtures.Configure(galleryAliases: "nun_grab=Nun_Grab");
		GalleryAliases.Resolve("some_peek_probe", inGame: false, quiet: true);
		Assert.DoesNotContain(Plugin.Logged, l => l.Contains("some_peek_probe"));
	}

	[Fact]
	public void ConfigOverridesBeatTheBuiltInTable()
	{
		// The point of the inversion: a user tweak survives a plugin update, and an update
		// reaches the user.
		Fixtures.Configure(galleryAliases: "nun_grab=Zombie_Loop");
		Assert.Equal("Zombie_Loop", GalleryAliases.Resolve("nun_grab", inGame: false));
	}

	[Fact]
	public void EveryTargetInTheShippedConfigIsARealRow()
	{
		// The check `ValidateTargets` runs at load: an alias pointing at a row no
		// `Definitions.csv` has is a scene that will silently play nothing.
		Fixtures.ConfigureFromLiveConfig();
		Assert.DoesNotContain(Plugin.Logged, l => l.StartsWith("[MISSING-DEFINITION]"));
	}

	[Fact]
	public void EveryStateInTheLiveConfigResolvesToAKnownRow()
	{
		// The end-to-end shape of the pipeline, on the settings a real session runs with: a
		// display name and an animator state in, a row `Definitions.csv` has out. This is
		// slugharness's question asked of a handful of pairs that have each cost a session.
		Fixtures.ConfigureFromLiveConfig();
		(string enemy, string state)[] cases =
		{
			("Hood_Enemy NoTape", "GhoulGrabStart"),
			("Imp_Enemy(Clone)", "Imp_Grab_Loop"),
			("Goon Shroom", "Loop"),                     // §92, the display name
			("Goon Shroom", "Cum"),
			("Black Serpent Enemy", "Loop"),
			("Zombie_Enemy", "ZombieGrabScreen_Cum"),
		};
		foreach ((string enemy, string state) in cases)
		{
			string key = NameRemap.ResolveEnemyKey(enemy);
			string slug = NameRemap.BuildGallerySlug(key, state);
			string row = GalleryAliases.Resolve(slug, inGame: true);
			Assert.True(GalleryRegistry.IsKnown(row),
				$"'{enemy}' + '{state}' -> key '{key}' -> slug '{slug}' -> '{row}', which is in no gallery row");
		}
	}
}

namespace PncEdi.Tests;

/// <summary>
/// Step 2 of the dispatch pipeline (PROJECT.md): the game hands the mod an object or display
/// name and an animator state, and `NameRemap` turns them into a slug.
///
/// Every expectation here is ground truth, not a snapshot of current behaviour: the enemy-key
/// cases come from the `EnemyRemap` entries the config actually ships, and the slug cases are
/// rows from `code/slugharness`, which resolves all 170 (enemy, state) pairs against this same
/// source file.
/// </summary>
public class NameRemapTests
{
	// ---- Slug -------------------------------------------------------------------------------

	[Theory]
	[InlineData("GhoulGrabStart", "ghoulgrabstart")]
	[InlineData("Ghoul Attack", "ghoul_attack")]
	[InlineData("Zombie_Grab", "zombie_grab")]
	[InlineData("Hypnosis Start", "hypnosis_start")]
	[InlineData("Nun&Mimic", "nun_mimic")]
	public void SlugLowercasesAndCollapsesSeparators(string raw, string expected)
		=> Assert.Equal(expected, NameRemap.Slug(raw));

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	[InlineData("   ")]
	[InlineData("---")]
	public void SlugOfNothingIsEmpty(string raw) => Assert.Equal("", NameRemap.Slug(raw));

	[Fact]
	public void SlugIsUnaffectedByOuterWhitespace()
	{
		// Relied on by PeekGalleryMap (§117): it slugs a config key that used to be untrimmed.
		Assert.Equal(NameRemap.Slug("Peephole_Nuns"), NameRemap.Slug("  Peephole_Nuns  "));
	}

	// ---- ResolveEnemyKey --------------------------------------------------------------------

	[Theory]
	[InlineData("Imp_Enemy", "imp")]
	[InlineData("Zombie_Enemy", "zombie")]
	[InlineData("Black Serpent Enemy", "serpent")]
	[InlineData("Blinded Beast", "blinded_beast")]
	[InlineData("Plantasha_Enemy", "plantasha")]
	public void ResolvesThePrefabNamesTheGameUses(string given, string expected)
	{
		Fixtures.Configure(enemyRemap: Fixtures.ConfigValue("EnemyRemap"));
		Assert.Equal(expected, NameRemap.ResolveEnemyKey(given));
	}

	[Fact]
	public void ResolvesTheGalleryMenusDisplayName()
	{
		// §92, and the reason this test exists: the gallery menu passes the enemy's *display*
		// name, `Goon Shroom` with a space, which no EnemyRemap entry matched. All five
		// GoonShroom gallery rows played nothing for four days while slugharness reported them
		// resolving cleanly, because the harness was being handed the already-resolved key.
		Fixtures.Configure(enemyRemap: Fixtures.ConfigValue("EnemyRemap"));
		Assert.Equal("goonshroom", NameRemap.ResolveEnemyKey("Goon Shroom"));
		Assert.Equal("goonshroom", NameRemap.ResolveEnemyKey("GoonShroom_Enemy"));
	}

	[Fact]
	public void LongerKeysWinOverShorterOnesTheyContain()
	{
		// `Hood_Enemy NoTape` and `Hood_Enemy` both map to nun today, so the shipped config
		// cannot show the ordering failing. Spell it out with two distinct targets.
		Fixtures.Configure(enemyRemap: "Hood_Enemy=nun;Hood_Enemy NoTape=nun_notape");
		Assert.Equal("nun_notape", NameRemap.ResolveEnemyKey("Hood_Enemy NoTape"));
		Assert.Equal("nun", NameRemap.ResolveEnemyKey("Hood_Enemy"));
	}

	[Fact]
	public void StripsUnitysCloneSuffix()
	{
		// Everything spawned at runtime arrives as `Imp_Enemy(Clone)`.
		Assert.Equal("Imp_Enemy", NameRemap.StripCloneSuffix("Imp_Enemy(Clone)"));
		Assert.Equal("Imp_Enemy", NameRemap.StripCloneSuffix("Imp_Enemy(Clone)  "));
		Fixtures.Configure(enemyRemap: Fixtures.ConfigValue("EnemyRemap"));
		Assert.Equal("imp", NameRemap.ResolveEnemyKey("Imp_Enemy(Clone)"));
	}

	[Fact]
	public void AnUnmappedEnemyFallsBackToItsOwnSlug()
	{
		// Inert and visible rather than silently plausible: an enemy with no remap entry gets a
		// slug that will simply not be in any alias table, instead of borrowing another
		// creature's key.
		Fixtures.Configure(enemyRemap: "Imp_Enemy=imp");
		Assert.Equal("brand_new_enemy", NameRemap.ResolveEnemyKey("Brand New Enemy"));
		// And the clone suffix comes off on that path too, or every runtime-spawned unknown
		// enemy would slug as `..._clone` and never match anything a human had typed. Found by
		// mutation-testing the suite: removing the strip from ResolveEnemyKey broke nothing
		// until this line existed.
		Assert.Equal("brand_new_enemy", NameRemap.ResolveEnemyKey("Brand New Enemy(Clone)"));
	}

	// ---- BuildGallerySlug -------------------------------------------------------------------

	[Theory]
	[InlineData("nun", "GhoulGrabStart", "nun_grab")]
	[InlineData("nun", "GhoulGrabCum", "nun_cum")]
	[InlineData("nun", "GhoulGrabCumContinue", "nun_grab")]
	[InlineData("gooper", "GooperGrabScreen", "gooper_grab")]
	[InlineData("mimic", "MimicGrabInit", "mimic_grab")]
	[InlineData("mimic", "MimicGrabLoop", "mimic_loop")]
	[InlineData("zombie", "ZombieGrabScreen_Loop", "zombie_loop")]
	[InlineData("plantasha", "PlanticaGrab", "plantasha_grab")]
	[InlineData("goonshroom", "Loop", "goonshroom_loop")]
	[InlineData("blinded_beast", "Cum_T", "blinded_beast_cum_t")]
	public void BuildsTheSlugsSlugharnessResolves(string key, string state, string expected)
		=> Assert.Equal(expected, NameRemap.BuildGallerySlug(key, state));

	[Fact]
	public void AltVariantsShareTheBaseEnemysSlug()
	{
		// `nun_alt` is a different prefab with the same scenes; both feed one set of scripts.
		Assert.Equal(NameRemap.BuildGallerySlug("nun", "GhoulGrabStart"),
		             NameRemap.BuildGallerySlug("nun_alt", "GhoulGrabStart"));
	}

	[Fact]
	public void DoesNotRepeatTheEnemyKeyWhenTheStateAlreadyCarriesIt()
	{
		// The state name often starts with the creature's own name; `zombie_zombie_grab` was a
		// real class of bug behind the substring-guessing fallback (code/NAMING-AUDIT.md).
		Assert.Equal("zombie_grab", NameRemap.BuildGallerySlug("zombie", "Zombie_Grab"));
		Assert.Equal("plantasha_grab", NameRemap.BuildGallerySlug("plantasha", "Plantasha_Grab"));
	}
}

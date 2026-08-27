using System.Collections.Generic;
using System.Linq;

namespace PncEdi.Tests;

/// <summary>
/// The `key=value;key=value` config format (§117).
///
/// Nine settings are written this way and six classes used to parse it separately. These are the
/// cases that pinned the format down when those six became one, including the ones the shipped
/// config does not happen to contain - which are exactly the ones a rewrite would break silently.
/// </summary>
public class ConfigMapTests
{
	private static List<KeyValuePair<string, string>> Pairs(string raw, char[] seps = null)
		=> ConfigMap.Pairs(raw, seps).ToList();

	[Fact]
	public void ParsesAPlainPair()
	{
		var pairs = Pairs("a=b");
		Assert.Single(pairs);
		Assert.Equal("a", pairs[0].Key);
		Assert.Equal("b", pairs[0].Value);
	}

	[Theory]
	[InlineData(null)]
	[InlineData("")]
	[InlineData("   ")]
	[InlineData(";")]
	[InlineData(";;;")]
	public void EmptyInputYieldsNothing(string raw) => Assert.Empty(Pairs(raw));

	[Theory]
	[InlineData("=")]          // no key
	[InlineData("=x")]         // no key
	[InlineData("x=")]         // no target
	[InlineData(" = ")]        // neither, once trimmed
	[InlineData("nokey")]      // no separator at all
	public void MalformedEntriesAreDropped(string raw) => Assert.Empty(Pairs(raw));

	[Fact]
	public void SplitsOnTheFirstEqualsOnly()
	{
		// A target may legitimately contain '=' - `GalleryAliases` targets carry `?seek=1200`.
		var pairs = Pairs("a=b=c");
		Assert.Single(pairs);
		Assert.Equal("a", pairs[0].Key);
		Assert.Equal("b=c", pairs[0].Value);
	}

	[Fact]
	public void SeekSuffixSurvivesIntact()
	{
		var pairs = Pairs("serpent_loop=Serpent_Loop?seek=1200");
		Assert.Equal("Serpent_Loop?seek=1200", pairs[0].Value);
	}

	[Fact]
	public void TrimsBothSidesAndDropsEmptyEntries()
	{
		var pairs = Pairs("  a  =  b  ;  ;  c  =  d  ");
		Assert.Equal(2, pairs.Count);
		Assert.Equal("a", pairs[0].Key);
		Assert.Equal("b", pairs[0].Value);
		Assert.Equal("d", pairs[1].Value);
	}

	[Fact]
	public void KeysMayContainSpaces()
	{
		// §92: the gallery menu hands over the enemy's *display* name, `Goon Shroom`, and the
		// fix was a config entry with a space in the key. A parser that split on whitespace
		// would have re-broken it.
		var pairs = Pairs("Goon Shroom=goonshroom");
		Assert.Equal("Goon Shroom", pairs[0].Key);
	}

	[Fact]
	public void DuplicateKeysAreYieldedInOrder()
	{
		// The parser does not decide - a caller filling a dictionary gets last-wins, a caller
		// building an ordered list keeps both. Both behaviours exist in the tree.
		var pairs = Pairs("a=b;a=c");
		Assert.Equal(2, pairs.Count);
		Assert.Equal("b", pairs[0].Value);
		Assert.Equal("c", pairs[1].Value);
	}

	[Fact]
	public void NewlinesSeparateOnlyWhenAsked()
	{
		// `GalleryAliases` is hand-edited in the config file and wraps; the others are not.
		Assert.Single(Pairs("a=b\nc=d"));
		Assert.Equal(2, Pairs("a=b\nc=d", ConfigMap.SemicolonOrNewline).Count);
		Assert.Equal(2, Pairs("a=b\r\nc=d", ConfigMap.SemicolonOrNewline).Count);
	}

	[Fact]
	public void SortLongestKeyFirstIsWhatMakesSubstringMatchingCorrect()
	{
		// `Hood_Enemy NoTape` has to be tried before `Hood_Enemy`, or every alt nun resolves as
		// the base one. Several settings promise the user "longest matching key wins".
		var table = Pairs("Hood_Enemy=nun;Hood_Enemy NoTape=nun_alt;Zombie=zombie");
		ConfigMap.SortLongestKeyFirst(table);
		Assert.Equal("Hood_Enemy NoTape", table[0].Key);
	}

	[Fact]
	public void ParsesTheShippedEnemyRemapWithoutLoss()
	{
		// Guards against a format change quietly dropping live entries. The real value, not a
		// sample of it.
		string raw = Fixtures.ConfigValue("EnemyRemap");
		var pairs = Pairs(raw);
		Assert.Equal(raw.Split(';').Length, pairs.Count);
		Assert.Contains(pairs, p => p.Key == "Goon Shroom" && p.Value == "goonshroom");
	}
}

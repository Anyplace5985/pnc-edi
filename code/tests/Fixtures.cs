using System;
using System.IO;

// Everything under test is `static`, because the mod is a plugin and its tables are process-wide.
// That makes the tests order-dependent unless they run one at a time, and a flaky suite is worse
// than none: this project's whole working practice is that a check either means something or is
// removed.
[assembly: CollectionBehavior(DisableTestParallelization = true)]

namespace PncEdi.Tests;

/// <summary>
/// Repo paths, the live config, and the reset every test needs.
///
/// The classes under test cache into static fields and reload lazily, so a test that leaves
/// `Plugin.CfgGalleryAliases` set changes the next test's answer. <see cref="Reset"/> puts the
/// whole layer back to "nothing configured" and is called at the top of every test that touches
/// configuration.
/// </summary>
public static class Fixtures
{
	private static string _root;

	/// <summary>The repo root, found by walking up from the test binary until PROJECT.md.</summary>
	public static string Root
	{
		get
		{
			if (_root != null)
			{
				return _root;
			}
			DirectoryInfo dir = new DirectoryInfo(AppContext.BaseDirectory);
			while (dir != null && !File.Exists(Path.Combine(dir.FullName, "PROJECT.md")))
			{
				dir = dir.Parent;
			}
			if (dir == null)
			{
				throw new InvalidOperationException(
					$"no PROJECT.md above {AppContext.BaseDirectory} - run the tests from inside the repo");
			}
			return _root = dir.FullName;
		}
	}

	public static string ConfigPath => Path.Combine(Root, "BepInEx", "config", "com.edi.pnc.cfg");

	public static string DefinitionsPath => Path.Combine(Root, "Edi", "Gallery", "Definitions.csv");

	/// <summary>
	/// The live value of one setting out of `com.edi.pnc.cfg`.
	///
	/// Tests read the real config rather than a sample of it on purpose: the failure this project
	/// keeps hitting is a *live* config entry that no longer matches what the code expects (§92),
	/// and a fixture copied by hand is exactly the thing that would still pass.
	/// </summary>
	public static string ConfigValue(string key)
	{
		foreach (string line in File.ReadAllLines(ConfigPath))
		{
			if (line.StartsWith("#") || line.StartsWith("["))
			{
				continue;
			}
			int eq = line.IndexOf(" = ", StringComparison.Ordinal);
			if (eq > 0 && line.Substring(0, eq).Trim() == key)
			{
				return line.Substring(eq + 3);
			}
		}
		throw new InvalidOperationException($"no setting called '{key}' in {ConfigPath}");
	}

	/// <summary>Clear every static table the naming layer caches, and every stubbed setting.</summary>
	public static void Reset()
	{
		Plugin.CfgEnemyNameRemap = null;
		Plugin.CfgGalleryAliases = null;
		Plugin.CfgInGameAliases = null;
		Plugin.CfgDioramaGalleryMap = null;
		Plugin.CfgPeekGalleryMap = null;
		Plugin.CfgPeekClipMap = null;
		Plugin.CfgClassHeatMultipliers = null;
		Plugin.Logged.Clear();
		NameRemap.Reload();
		GalleryAliases.Reload();
		DioramaGalleryMap.Reload();
		PeekGalleryMap.Reload();
		ClassHeatMultipliers.Reload();
	}

	/// <summary>Point the naming layer at the settings this test cares about, then reload.</summary>
	public static void Configure(string enemyRemap = null, string galleryAliases = null,
	                             string inGameAliases = null, string dioramaMap = null,
	                             string dioramaDefault = null, string peekMap = null,
	                             string peekClipMap = null, string classHeat = null)
	{
		Reset();
		Plugin.CfgEnemyNameRemap = new Cfg(enemyRemap);
		Plugin.CfgGalleryAliases = new Cfg(galleryAliases);
		Plugin.CfgInGameAliases = new Cfg(inGameAliases);
		Plugin.CfgDioramaGalleryMap = new Cfg(dioramaMap, dioramaDefault);
		Plugin.CfgPeekGalleryMap = new Cfg(peekMap);
		Plugin.CfgPeekClipMap = new Cfg(peekClipMap);
		Plugin.CfgClassHeatMultipliers = new Cfg(classHeat);
		NameRemap.Reload();
		GalleryAliases.Reload();
		DioramaGalleryMap.Reload();
		PeekGalleryMap.Reload();
		ClassHeatMultipliers.Reload();
	}

	/// <summary>The settings a real session runs with, straight out of `com.edi.pnc.cfg`.</summary>
	public static void ConfigureFromLiveConfig()
	{
		Configure(enemyRemap: ConfigValue("EnemyRemap"),
		          galleryAliases: ConfigValue("GalleryAliases"),
		          inGameAliases: ConfigValue("InGameAliases"),
		          dioramaMap: ConfigValue("DioramaAmbientMap"),
		          peekMap: ConfigValue("PeekGalleryMap"),
		          peekClipMap: ConfigValue("PeekClipMap"));
	}
}

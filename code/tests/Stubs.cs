using System;
using BepInEx.Logging;

namespace PncEdi;

/// <summary>
/// Stands in for the parts of `Plugin` the classes under test reach for.
///
/// The real `Plugin` is a `BaseUnityPlugin` and cannot exist outside a running game, but the
/// naming and alias layer only ever asks it two things: the value of a config entry, and
/// somewhere to log. Both are trivially fakeable, which is why this layer is the part of the mod
/// worth unit-testing at all.
///
/// `Cfg` mirrors the one member of `ConfigEntry&lt;string&gt;` the mod uses. `ConfigEntry` itself
/// cannot be constructed outside BepInEx, and faking `.Value` is enough because every read in
/// the tree is `Plugin.CfgSomething?.Value`. `code/slugharness` has done the same since §71.
/// </summary>
public sealed class Cfg
{
	public string Value;

	/// <summary>
	/// The value coded in `Bind()`, which BepInEx keeps separately from what the user's file
	/// says. `DioramaGalleryMap` reads it deliberately: the built-in D-slot table is the coded
	/// default, so it still applies when a user has blanked or trimmed their own list. Typed
	/// `object` because that is what `ConfigEntryBase.DefaultValue` is, and the mod casts it.
	/// </summary>
	public object DefaultValue;

	public Cfg(string value, string defaultValue = null)
	{
		Value = value;
		DefaultValue = defaultValue;
	}
}

public static class Plugin
{
	public static Cfg CfgEnemyNameRemap;
	public static Cfg CfgGalleryAliases;
	public static Cfg CfgInGameAliases;
	public static Cfg CfgDioramaGalleryMap;
	public static Cfg CfgPeekGalleryMap;
	public static Cfg CfgPeekClipMap;
	public static Cfg CfgClassHeatMultipliers;

	/// <summary>Null in tests: every call site is `Plugin.Log?.` or null-checked.</summary>
	public static ManualLogSource Log;

	/// <summary>Everything the mod logged during the current test, newest last.</summary>
	public static readonly System.Collections.Generic.List<string> Logged =
		new System.Collections.Generic.List<string>();

	public static void DBG(string evt, string detail)
	{
		Logged.Add($"[{evt}] {detail}");
	}

	public static void LogMissingDefinition(string galleryName, string resolvedName)
	{
		Logged.Add($"[MISSING-DEFINITION] {galleryName} -> {resolvedName}");
	}
}

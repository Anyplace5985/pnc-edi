using System;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Configuration;
using BepInEx.Unity.Mono;
using BepInEx.Unity.Mono.Configuration;
using HarmonyLib;
using PncCustomEnemies.Api;
using PncEdi;
using UnityEngine;

namespace PncCustomEnemies;

/// <summary>
/// The custom-enemy framework, as its own BepInEx plugin.
///
/// It was part of PncEdi until §131. Splitting it out is what makes the two things separable in
/// practice: this DLL is a content loader - packages under `BepInEx/custom-enemies/`, their art,
/// their sprite animation, their gallery section, and the API a package's own behaviour assembly
/// compiles against - and deleting it leaves an Edi integration that behaves exactly as it did
/// before any of it existed. Since §165 it carries no enemy of its own: a behaviour lives in the
/// package that uses it, and is published by name so any data-only manifest can select it.
/// The core mod asks it nothing directly; every question goes through
/// <see cref="CustomEnemyBridge"/>, which answers vanilla when nothing is installed.
///
/// The dependency runs one way, and only one way. This plugin uses PncEdi's registries and its Edi
/// channel because a package's scenes *are* Edi content - it plays rows, registers gallery names
/// and takes heat locks. `[BepInDependency]` makes BepInEx load PncEdi first and run its Awake
/// first, which is also the ordering the framework needs: packages register rows and aliases into
/// tables the core mod has already loaded.
///
/// Its settings live in its own file, `com.edi.pnc.customenemies.cfg`, for the same reason: a
/// package's on/off switch and spawn weight belong to the mod that reads packages, not to the one
/// that talks to a device.
/// </summary>
[BepInPlugin(PluginGuid, PluginName, PluginVersion)]
[BepInDependency(PncEdiPluginGuid)]
public sealed class CustomEnemyPlugin : BaseUnityPlugin
{
	public const string PluginGuid = "com.edi.pnc.customenemies";
	public const string PluginName = "PNC Custom Enemies";
	// 1.1.0: packages may ship their own behaviour assemblies, and the framework carries none of
	// its own (§165). The version a package cares about is `PackageApi.Version`, not this one.
	public const string PluginVersion = "1.1.0";
	private const string PncEdiPluginGuid = "com.edi.pnc";

	internal static CustomEnemyPlugin Instance { get; private set; }

	/// <summary>This plugin's own log source. BaseUnityPlugin.Logger is protected, so static code cannot reach it.</summary>
	internal static ManualLogSource Log { get; private set; }

	internal static ConfigEntry<KeyboardShortcut> CfgKeySpawnCustomEnemy;
	internal static ConfigEntry<string> CfgSpawnCustomEnemyId;

	private void Awake()
	{
		Instance = this;
		Log = Logger;
		CfgKeySpawnCustomEnemy = Config.Bind("Tools", "SpawnCustomEnemyKey", new KeyboardShortcut(KeyCode.F9),
			"Spawn the custom-enemy package named by SpawnCustomEnemyId in front of the player (debug). A package that clones a vanilla enemy has no prefab until that enemy exists in the level, so spawn from inside a run rather than from the menu.");
		CfgSpawnCustomEnemyId = Config.Bind("Tools", "SpawnCustomEnemyId", "",
			"Package id - the \"id\" field of BepInEx/custom-enemies/<package>/enemy.json - spawned by SpawnCustomEnemyKey. Empty (the default) spawns the only installed package when there is exactly one, and otherwise logs the ids to choose from: no package's id is a default here, because the framework ships no packages. The log lists every loaded id when the key finds nothing.");

		// Before the packages load: a package registering rows can be asked about immediately.
		CustomEnemyBridgeInstaller.Install();
		// Package assemblies come first, and the order is load-bearing: a module publishes its
		// behaviours in Initialize, and the registry attaches behaviours by name while preparing
		// templates. A package loaded after the registry would publish into an empty room (§165).
		PackageAssemblies.Initialize();
		CustomEnemyRegistry.Initialize();
		CustomEnemyPatches.Apply();
		CustomGallerySectionHooks.RefreshExisting();
		Log.LogInfo($"[{PluginName}] {PluginVersion} ready.");
	}

	private void Update()
	{
		// The debug-spawn gate stays PncEdi's: it is one switch for every spawn hotkey in the
		// install, and having two of them called the same thing is how they end up disagreeing.
		if (Plugin.CfgEnableDebugEnemySpawn == null || !Plugin.CfgEnableDebugEnemySpawn.Value)
		{
			return;
		}
		if (Hotkeys.IsDown(CfgKeySpawnCustomEnemy))
		{
			CustomEnemyRegistry.SpawnById(CfgSpawnCustomEnemyId.Value);
		}
	}
}

/// <summary>Everything PncEdi asks about packages, answered from here. See <see cref="CustomEnemyBridge"/>.</summary>
internal static class CustomEnemyBridgeInstaller
{
	internal static void Install()
	{
		CustomEnemyBridge.SpawnWeightResolver = CustomEnemyRegistry.GetSpawnWeight;
		CustomEnemyBridge.CustomKeyTest = CustomEnemyRegistry.IsCustomKey;
		CustomEnemyBridge.ShufflePoolSource = CustomEnemyRegistry.ShufflePoolContributions;
		CustomEnemyBridge.SceneMinimumSecondsResolver = ResolveSceneMinimumSeconds;
		// Every one of these used to test for a type this plugin contained. They now ask the object
		// itself through the package API, so a behaviour the framework has never seen answers them
		// as well as the two that used to be compiled in (§165).
		CustomEnemyBridge.SceneVisualOwnerTest = enemy => OwnsSceneVisual(enemy);
		CustomEnemyBridge.GrabSceneOwnerTest = OwnsGrabScene;
		CustomEnemyBridge.EdiChannelHeldTest = PackageSceneOwners.AnyHoldsEdiChannel;
		CustomEnemyBridge.GalleryRowResolver = ResolveGalleryRow;
	}

	// The gallery viewer steps by animation *label* - "massage", "Dream 1" - and PncEdi has nothing
	// else to go on there, so without this it slugs the display name and asks for a row no package
	// ever registered (`joker_massage` against a declared `joker_wall_massage`, §138). The manifest
	// is the only thing that knows, and it already answers the same question for gameplay. A package
	// that contributed the entry itself answers for its own; a custom enemy answers through its
	// scene's `gallery`. Null means "not ours, or ours with no row" and leaves PncEdi's own slug in
	// place - which is what the witch's four unscripted dream videos still get.
	private static string ResolveGalleryRow(EnemyGalleryEntry entry, string animationName)
	{
		string provided = PackageGalleryEntries.ResolveRow(entry, animationName);
		if (!string.IsNullOrWhiteSpace(provided))
		{
			return provided;
		}

		CustomEnemyDefinition definition = CustomEnemyRegistry.Find(entry);
		CustomEnemyScene[] scenes = definition?.Manifest?.scenes;
		if (scenes != null)
		{
			foreach (CustomEnemyScene scene in scenes)
			{
				if (scene != null && string.Equals(scene.animation, animationName, StringComparison.OrdinalIgnoreCase))
				{
					return string.IsNullOrWhiteSpace(scene.gallery) ? null : scene.gallery.Trim();
				}
			}
		}
		return null;
	}

	// A package behaviour that captures the player does it through vanilla's own GrabScreen, handing
	// it their own GameObject as the "enemy" - so from PncEdi's side a capture is indistinguishable
	// from a goonshroom grab until it asks this.
	private static bool OwnsGrabScene(GameObject enemy)
	{
		IPackageSceneOwner owner = enemy == null ? null : enemy.GetComponent<IPackageSceneOwner>();
		return owner != null && owner.OwnsGrabScene;
	}

	private static bool OwnsSceneVisual(GameObject enemy)
	{
		IPackageSceneOwner owner = enemy == null ? null : enemy.GetComponent<IPackageSceneOwner>();
		return owner != null && owner.OwnsSceneVisual;
	}

	// Negative means "not one of ours", which is how the escape gate tells a package's own scene
	// length from an enemy it should apply the mod's configured delay to.
	private static float ResolveSceneMinimumSeconds(GameObject enemy)
	{
		IPackageSceneOwner owner = enemy == null ? null : enemy.GetComponent<IPackageSceneOwner>();
		return owner != null ? owner.MinimumSceneSeconds : -1f;
	}
}

/// <summary>
/// This plugin's Harmony registry, and the same rule as PncEdi's: patches are applied by an
/// explicit list, so a new patch class does nothing until it is named here - and `patchaudit.py`
/// reads this file to check that every `[HarmonyPatch]` class in the tree is in it.
/// </summary>
internal static class CustomEnemyPatches
{
	internal static void Apply()
	{
		Patch("com.edi.pnc.customenemies", typeof(CustomEnemyHooks));
		Patch("com.edi.pnc.customgallery", typeof(CustomGallerySectionHooks));
	}

	private static void Patch(string harmonyId, System.Type patchClass)
	{
		try
		{
			new Harmony(harmonyId).PatchAll(patchClass);
		}
		catch (System.Exception ex)
		{
			CustomEnemyPlugin.Log?.LogError($"[{CustomEnemyPlugin.PluginName}] {patchClass.Name} failed to patch: {ex}");
		}
	}
}

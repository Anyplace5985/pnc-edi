using System.Collections.Generic;
using BepInEx.Configuration;
using BepInEx.Unity.Mono.Configuration;
using PncCustomEnemies.Api;
using UnityEngine;

namespace WallPictureTraps;

/// <summary>
/// The wall-picture trap package's entry point.
///
/// **This is the seam's other shape.** A charm-witch package publishes a *behaviour* that any
/// manifest can attach to a cloned enemy; this package is a whole package *kind* - its own manifest
/// (`wall-trap.json`), its own gallery entries, its own placement rules, its own Harmony patch.
/// Both arrive through `IPackageModule`, and neither is anything the framework knows about: it
/// hands over the manifest text and asks, through `IPackageGalleryProvider`, what this package
/// contributes to the gallery and how to draw it (§165).
///
/// The framework keeps the gallery *viewer*. What this returns is a description - stages, frames,
/// rows, a sound - so a package cannot get between the viewer and the device, and every package's
/// gallery behaves the same way.
/// </summary>
public sealed class WallPictureTrapModule : IPackageModule, IPackageGalleryProvider
{
	/// <summary>The config file this package binds into, and the host object it hangs its own components on. Both come from the context; nothing here reaches the framework's own objects.</summary>
	internal static ConfigFile Config { get; private set; }

	internal static GameObject Host { get; private set; }

	internal static MonoBehaviour Runner { get; private set; }

	/// <summary>This package's own placement key, bound in its own section rather than in the framework's `Tools`, because it is this package's key and not the loader's.</summary>
	internal static ConfigEntry<KeyboardShortcut> SpawnKey { get; private set; }

	/// <summary>This package's on/off switch, bound by the framework before this assembly loaded.</summary>
	internal static ConfigEntry<bool> EnabledEntry { get; private set; }

	public void Initialize(PackageContext context)
	{
		Config = context.Config;
		EnabledEntry = context.EnabledEntry;
		Host = context.Host;
		Runner = context.Host.AddComponent<WallPictureTrapRunner>();
		SpawnKey = context.Config.Bind(
			"Wall Picture Traps",
			"PlaceTrapKey",
			new KeyboardShortcut(KeyCode.F10),
			"Place or reposition a wall-picture trap on the vertical wall being aimed at, within 25 m (debug). Destroys the current instance in this scene and puts a replacement where aimed. Needs Tools / EnableDebugEnemySpawn in com.edi.pnc.cfg, which is one gate for every debug spawn key in the install.");
		WallPictureTrapRegistry.Initialize(System.IO.Path.Combine(context.Directory, context.ManifestFileName));
		// Registered here, by name, rather than behind a helper: `patchaudit.py` reads this file as
		// this package's registration list, and a patch class reached through a call it cannot see is
		// exactly the silent "compiled in and does nothing" it exists to catch (§109).
		try
		{
			new HarmonyLib.Harmony("com.edi.pnc.package.walltrappull").PatchAll(typeof(WallPictureTrapPull));
		}
		catch (System.Exception ex)
		{
			ModServices.LogError("[WallPictureTrap] pull patch failed: " + ex);
		}
	}

	public IEnumerable<EnemyGalleryEntry> GalleryEntries => WallPictureTrapRegistry.GalleryEntries();

	public string ResolveGalleryRow(EnemyGalleryEntry entry, string animationName)
	{
		return WallPictureTrapRegistry.ResolveGalleryRow(entry, animationName);
	}

	public PackageGalleryPresentation Describe(EnemyGalleryEntry entry)
	{
		return WallPictureTrapRegistry.Describe(entry);
	}
}

/// <summary>A MonoBehaviour of this package's own, so its coroutines and its placement key do not ride on the framework's object.</summary>
internal sealed class WallPictureTrapRunner : MonoBehaviour
{
}

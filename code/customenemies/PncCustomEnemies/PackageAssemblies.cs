using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using BepInEx;
using BepInEx.Configuration;
using PncCustomEnemies.Api;
using PncEdi;
using UnityEngine;

namespace PncCustomEnemies;

/// <summary>The `"assembly"` block of a package manifest: which DLL, which type in it, and which API it was built against.</summary>
[Serializable]
public sealed class PackageAssemblyDeclaration
{
	public string file;
	public string module;
	public int api;
}

/// <summary>One package that declares an assembly, whether or not it was allowed to load.</summary>
internal sealed class PackageAssembly
{
	internal string Id;
	internal string Directory;
	internal string ManifestPath;
	internal string ManifestJson;
	internal PackageAssemblyDeclaration Declaration;
	internal ConfigEntry<bool> ConsentEntry;
	internal ConfigEntry<bool> EnabledEntry;
	internal PackageContext Context;
	internal IPackageModule Module;
	internal string Refusal;

	internal bool Consented => ConsentEntry != null && ConsentEntry.Value;
	internal bool Loaded => Module != null;
}

/// <summary>
/// Loads the code a package ships, and refuses to until someone says so.
///
/// **There is no sandbox and there cannot be one.** BepInEx runs on Mono with the game's full
/// privileges, and an assembly loaded out of `BepInEx/custom-enemies/&lt;name&gt;/` has the
/// filesystem and the network like any other plugin. Nothing this loader does changes that, so what
/// it owes the player is disclosure and consent rather than containment (§164): every package that
/// ships a DLL gets its own switch in `com.edi.pnc.customenemies.cfg`, **default off**, and a log
/// line naming the assembly whether it loads or is refused. A player who never turns one on never
/// runs third-party code, and one who does was asked first.
///
/// The switch is per package rather than global on purpose: "I trust this download" is the question
/// a player can actually answer, and a single master switch turns the next package's code on by a
/// decision made about a different package.
/// </summary>
internal static class PackageAssemblies
{
	private static readonly List<PackageAssembly> Packages = new List<PackageAssembly>();
	private static readonly List<IPackageGalleryProvider> GalleryProviderList = new List<IPackageGalleryProvider>();
	private static bool _initialized;

	internal static IReadOnlyList<PackageAssembly> All => Packages;

	/// <summary>Modules that add their own gallery rows. Empty until something both declares one and is allowed to load.</summary>
	internal static IReadOnlyList<IPackageGalleryProvider> GalleryProviders => GalleryProviderList;

	/// <summary>
	/// Packages that ship code and are switched off - what the mod manager offers to enable, and
	/// the reason a package can look installed and do nothing.
	/// </summary>
	internal static IEnumerable<PackageAssembly> Blocked
	{
		get
		{
			foreach (PackageAssembly package in Packages)
			{
				if (!package.Loaded && package.Refusal == null)
				{
					yield return package;
				}
			}
		}
	}

	internal static void Initialize()
	{
		if (_initialized)
		{
			return;
		}
		_initialized = true;
		string root = Path.Combine(Paths.BepInExRootPath, "custom-enemies");
		System.IO.Directory.CreateDirectory(root);
		foreach (string directory in System.IO.Directory.GetDirectories(root))
		{
			if (string.Equals(Path.GetFileName(directory), "_example", StringComparison.OrdinalIgnoreCase))
			{
				continue;
			}
			foreach (string manifestPath in System.IO.Directory.GetFiles(directory, "*.json", SearchOption.TopDirectoryOnly))
			{
				TryDeclare(manifestPath);
			}
		}
		foreach (PackageAssembly package in Packages)
		{
			Load(package);
		}
	}

	private static void TryDeclare(string manifestPath)
	{
		try
		{
			string json = File.ReadAllText(manifestPath);
			string block = JsonBlock(json, "assembly");
			if (block == null)
			{
				return;
			}
			PackageAssemblyDeclaration declaration = JsonUtility.FromJson<PackageAssemblyDeclaration>(block);
			if (declaration == null || string.IsNullOrWhiteSpace(declaration.file) || string.IsNullOrWhiteSpace(declaration.module))
			{
				CustomEnemyPlugin.Log?.LogError("[CustomEnemies] " + Path.GetFileName(manifestPath) + " declares an assembly without both 'file' and 'module' - ignored");
				return;
			}
			string directory = Path.GetDirectoryName(manifestPath);
			bool isEnemyPackage = string.Equals(Path.GetFileName(manifestPath), "enemy.json", StringComparison.OrdinalIgnoreCase);
			PackageAssembly package = new PackageAssembly
			{
				Id = ReadId(json) ?? Path.GetFileName(directory),
				Directory = directory,
				ManifestPath = manifestPath,
				ManifestJson = json,
				Declaration = declaration
			};
			// The consent switch is bound whether or not the assembly will load, so a player who
			// installed a package and saw nothing happen finds the reason in the same config
			// section as the package's other settings rather than only in a log.
			// A package kind the framework does not know - a wall trap, anything a package invents -
			// still needs its on/off switch, and it has to exist **before** its code is allowed to
			// run: a package that binds its own switch has none until it loads, so a blocked package
			// would show a "code" toggle and nothing to enable. That was the shape of the first
			// version of this and it read as nonsense in the settings window (§166). An `enemy.json`
			// package keeps CustomEnemyRegistry's switch, which is bound from the manifest it already
			// parses; everything else gets one here.
			if (!isEnemyPackage)
			{
				package.EnabledEntry = CustomEnemyPlugin.Instance.Config.Bind(
					"Custom Enemies",
					package.Id,
					true,
					"Enable " + ReadDisplayName(json, package.Id) + ". Disabled packages stop appearing in the level and leave the custom gallery until re-enabled.");
			}
			package.ConsentEntry = CustomEnemyPlugin.Instance.Config.Bind(
				"Custom Enemies",
				package.Id + " code",
				false,
				"Allow " + package.Id + " to run the code it ships (" + declaration.file + "). This is third-party code with the game's full privileges - the same as any BepInEx plugin - and it cannot be sandboxed, so it stays off until you turn it on. The package's art, sounds and funscripts work either way; its behaviour does not.");
			Packages.Add(package);
		}
		catch (Exception ex)
		{
			CustomEnemyPlugin.Log?.LogError("[CustomEnemies] could not read " + manifestPath + ": " + ex.Message);
		}
	}

	private static void Load(PackageAssembly package)
	{
		string assemblyPath = Path.Combine(package.Directory, package.Declaration.file);
		if (!File.Exists(assemblyPath))
		{
			package.Refusal = "the file it names is not there";
			CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "' declares " + package.Declaration.file + ", which is not in the package - the package's code will not run");
			return;
		}
		if (package.Declaration.api != PackageApi.Version)
		{
			// A mismatch is refused rather than tried: the members the module binds to are gone or
			// renamed, and the failure would otherwise land as a MissingMethodException somewhere in
			// the middle of a run, in a stack that names the package rather than the mismatch.
			package.Refusal = "it was built against API " + package.Declaration.api + ", this framework speaks " + PackageApi.Version;
			CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "' was built against custom-enemy API " + package.Declaration.api +
				" and this framework speaks " + PackageApi.Version + " - " +
				(package.Declaration.api < PackageApi.Version ? "the package needs rebuilding against this version." : "the mod is older than the package; update the mod."));
			return;
		}
		if (!package.Consented)
		{
			CustomEnemyPlugin.Log?.LogWarning("[CustomEnemies] '" + package.Id + "' ships code (" + package.Declaration.file + ") and is NOT allowed to run it. " +
				"Set 'Custom Enemies / " + package.Id + " code' in com.edi.pnc.customenemies.cfg, or turn it on in the mod manager (F11), and restart. " +
				"Until then this package's art and funscripts load and its behaviour does not.");
			return;
		}
		try
		{
			// LoadFrom rather than Load(byte[]): Mono resolves the assembly's own dependencies
			// relative to the file, and a package that ships more than one DLL then works without
			// the loader knowing about the second.
			Assembly assembly = Assembly.LoadFrom(assemblyPath);
			Type moduleType = assembly.GetType(package.Declaration.module, false);
			if (moduleType == null)
			{
				package.Refusal = "the module type it names is not in the assembly";
				CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "': " + package.Declaration.file + " has no type '" + package.Declaration.module + "'");
				return;
			}
			if (!typeof(IPackageModule).IsAssignableFrom(moduleType))
			{
				package.Refusal = "the module type does not implement IPackageModule";
				CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "': '" + package.Declaration.module + "' does not implement IPackageModule");
				return;
			}
			GameObject host = new GameObject("CustomEnemyPackage_" + package.Id);
			UnityEngine.Object.DontDestroyOnLoad(host);
			host.SetActive(true);
			PackageContext context = new PackageContext
			{
				Id = package.Id,
				Directory = package.Directory,
				ManifestJson = package.ManifestJson,
				ManifestFileName = Path.GetFileName(package.ManifestPath),
				Log = CustomEnemyPlugin.Log,
				Config = CustomEnemyPlugin.Instance.Config,
				Host = host,
				IsEnabled = () => package.EnabledEntry != null ? package.EnabledEntry.Value : CustomEnemyRegistry.IsPackageEnabled(package.Id),
				EnabledEntry = package.EnabledEntry,
				RegisterBehaviour = (name, factory) => PackageBehaviours.Register(package.Id, name, factory)
			};
			IPackageModule module = (IPackageModule)Activator.CreateInstance(moduleType);
			module.Initialize(context);
			package.Context = context;
			package.Module = module;
			if (module is IPackageGalleryProvider provider)
			{
				GalleryProviderList.Add(provider);
			}
			CustomEnemyPlugin.Log?.LogWarning("[CustomEnemies] '" + package.Id + "' is running its own code: " + package.Declaration.file + " -> " + package.Declaration.module + " (allowed by configuration)");
		}
		catch (Exception ex)
		{
			package.Refusal = ex.GetType().Name;
			CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "' failed to load " + package.Declaration.file + ": " + ex);
		}
	}

	/// <summary>Tells one package's module that its enemy template now exists. Silent for a package with no assembly, which is every package that is pure data.</summary>
	internal static void RaiseTemplatePrepared(string id, GameObject template)
	{
		foreach (PackageAssembly package in Packages)
		{
			if (package.Loaded && string.Equals(package.Id, id, StringComparison.OrdinalIgnoreCase))
			{
				try
				{
					package.Context.RaiseTemplatePrepared(template);
				}
				catch (Exception ex)
				{
					CustomEnemyPlugin.Log?.LogError("[CustomEnemies] '" + package.Id + "' threw preparing its template: " + ex);
				}
			}
		}
	}

	/// <summary>A package's own display name, for a switch a player reads. Falls back to the id.</summary>
	private static string ReadDisplayName(string json, string fallback)
	{
		string name = ReadString(json, "displayName");
		return string.IsNullOrWhiteSpace(name) ? fallback : name;
	}

	private static string ReadId(string json)
	{
		return ReadString(json, "id");
	}

	private static string ReadString(string json, string field)
	{
		int key = json.IndexOf("\"" + field + "\"", StringComparison.OrdinalIgnoreCase);
		if (key < 0) return null;
		int colon = json.IndexOf(':', key);
		if (colon < 0) return null;
		int open = json.IndexOf('"', colon);
		if (open < 0) return null;
		int close = json.IndexOf('"', open + 1);
		if (close < 0) return null;
		string value = json.Substring(open + 1, close - open - 1).Trim();
		return string.IsNullOrEmpty(value) ? null : value;
	}

	/// <summary>A package's on/off switch, for a module that wants to watch it change rather than poll.</summary>
	internal static ConfigEntry<bool> EnabledEntryFor(string id)
	{
		foreach (PackageAssembly package in Packages)
		{
			if (string.Equals(package.Id, id, StringComparison.OrdinalIgnoreCase))
			{
				return package.EnabledEntry;
			}
		}
		return null;
	}

	// The framework's own manifest reader is a set of private helpers on CustomEnemyRegistry and
	// this file is deliberately standalone - it has to read a manifest whose vocabulary it does not
	// know, from a package kind it has never heard of, before anything else parses it.
	private static string JsonBlock(string json, string field)
	{
		if (string.IsNullOrEmpty(json)) return null;
		int key = json.IndexOf("\"" + field + "\"", StringComparison.OrdinalIgnoreCase);
		int start = key < 0 ? -1 : json.IndexOf('{', key);
		if (start < 0) return null;
		bool inString = false;
		bool escaped = false;
		int depth = 0;
		for (int i = start; i < json.Length; i++)
		{
			char c = json[i];
			if (inString)
			{
				if (escaped) escaped = false;
				else if (c == '\\') escaped = true;
				else if (c == '"') inString = false;
				continue;
			}
			if (c == '"') { inString = true; continue; }
			if (c == '{') depth++;
			else if (c == '}' && --depth == 0) return json.Substring(start, i - start + 1);
		}
		return null;
	}
}

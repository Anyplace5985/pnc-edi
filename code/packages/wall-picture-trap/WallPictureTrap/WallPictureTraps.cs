using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;
using PixelCrushers.GridController;
using PncCustomEnemies.Api;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

using PncCustomEnemies;

namespace WallPictureTraps;

[Serializable]
public sealed class WallPictureTrapManifest
{
	public string id;
	public string displayName = "Wall Picture";
	public bool enabled = true;
	public bool autoPlace = true;
	public int spawnCount = 1;
	public int maxActiveCount = 8;
	public int roamingSpawnBatch = 1;
	public float roamingSpawnInterval = 12f;
	public float roamingSpawnDistance = 12f;
	public bool preferCorners = true;
	public float minimumSpawnSeparation = 5f;
	public string portrait;
	public float portraitPixelsPerUnit = 300f;
	public float portraitBrightness = 1f;
	public string portraitScale = "1,1,1";
	public int maxHealth = 600;
	public float colliderDepth = 0.06f;
	public float placementDelay = 3f;
	public float pullRadius = 7.5f;
	public float captureDistance = 1.15f;
	public float pullStrength = 24f;
	// How fast the pull can drag the player, in metres per second, once `pullStrength` has ramped
	// it up. The player walks at 7, so this is the number that decides whether the trap can be
	// escaped on foot; 5 leaves it losable and is deliberately the default for a package that does
	// not say. Omitting it from a manifest is normal.
	public float maxPullSpeed = 5f;
	public float minimumSceneSeconds = 20f;
	public float captureBackdropAlpha = 0.2f;
	public string captureSound;
	public float captureSoundVolume = 0.8f;
	public bool captureSoundLoop = true;
	public float armDelay = 5f;
	public float cooldown = 10f;
	public float frontArc = 0.15f;
	public WallPictureTrapAnimation[] animations = Array.Empty<WallPictureTrapAnimation>();
}

[Serializable]
public sealed class WallPictureTrapAnimation
{
	public string name;
	public string file;
	public string gallery;
	public string funscript;
	public float fps = 10f;
	public bool loop = true;
	public int columns = 1;
	public int rows = 1;
	public int frameCount;
	public float seconds;
}

internal sealed class WallPictureTrapPackage
{
	internal WallPictureTrapManifest Manifest;
	internal string Directory;
	internal PackageSpriteAnimation Portrait;
	internal PackageSpriteAnimation[] Animations = System.Array.Empty<PackageSpriteAnimation>();
	internal AudioClip CaptureSound;
	internal EnemyGalleryEntry GalleryEntry;
	internal GameObject GalleryPrefab;
	internal ConfigEntry<bool> EnabledEntry;

	internal bool Enabled => EnabledEntry?.Value ?? Manifest.enabled;
}

internal static class WallPictureTrapRegistry
{
	private struct WallCandidate
	{
		internal RaycastHit Hit;
		internal float Score;
	}

	private static readonly List<WallPictureTrapPackage> Packages = new List<WallPictureTrapPackage>();
	private static readonly Regex FunscriptAt = new Regex("\\\"at\\\"\\s*:\\s*(\\d+)", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
	private static bool _initialized;

	/// <summary>
	/// One package's manifest, loaded when its module is initialised.
	///
	/// **This used to scan every package directory for `wall-trap.json`** - it was the framework, so
	/// it could. A module is handed its own manifest and nothing else (§165), so a second wall-trap
	/// package now arrives as a second module with its own assembly, and the shared statics here are
	/// per-assembly rather than per-install. That is the right shape: two packages of the same kind
	/// are two packages, not one registry with two rows.
	/// </summary>
	internal static void Initialize(string manifestPath)
	{
		Load(manifestPath);
		if (Packages.Count == 0) return;
		if (_initialized) return;
		_initialized = true;
		GameObject host = WallPictureTrapModule.Host;
		if (host.GetComponent<WallPictureTrapPlacer>() == null) host.AddComponent<WallPictureTrapPlacer>();
		SceneManager.activeSceneChanged += OnSceneChanged;
		WallPictureTrapModule.Runner.StartCoroutine(SpawnForScene(SceneManager.GetActiveScene()));
		ModServices.Log("[WallPictureTrap] loaded " + Packages.Count + " package(s); the placement key puts the first trap on the aimed wall");
	}

	/// <summary>The gallery entries this package owns - nothing while the package is switched off, which is how a disabled package leaves the gallery.</summary>
	internal static IEnumerable<EnemyGalleryEntry> GalleryEntries()
	{
		foreach (WallPictureTrapPackage package in Packages)
		{
			if (package.Enabled && package.GalleryEntry != null) yield return package.GalleryEntry;
		}
	}

	/// <summary>How the framework should draw one of this package's gallery entries: a stage per animation, each with its own row.</summary>
	internal static PackageGalleryPresentation Describe(EnemyGalleryEntry entry)
	{
		WallPictureTrapPackage package = FindGalleryEntry(entry);
		if (package == null) return null;
		List<PackageGalleryStage> stages = new List<PackageGalleryStage>();
		for (int i = 0; i < package.Animations.Length; i++)
		{
			stages.Add(new PackageGalleryStage
			{
				Name = i < package.Manifest.animations.Length ? package.Manifest.animations[i].name : "Stage " + (i + 1),
				Animation = package.Animations[i],
				Gallery = GetGalleryName(package, i)
			});
		}
		if (stages.Count == 0 && package.Portrait != null)
		{
			stages.Add(new PackageGalleryStage { Name = "Idle", Animation = package.Portrait, Gallery = null });
		}
		return new PackageGalleryPresentation
		{
			Stages = stages.ToArray(),
			Sound = package.CaptureSound,
			SoundLoops = package.Manifest.captureSoundLoop,
			SoundVolume = package.Manifest.captureSoundVolume
		};
	}

	/// <summary>The row one of this package's entries plays at one animation label (§138 - the viewer steps by label, not by index).</summary>
	internal static string ResolveGalleryRow(EnemyGalleryEntry entry, string animationName)
	{
		WallPictureTrapPackage package = FindGalleryEntry(entry);
		WallPictureTrapAnimation[] stages = package?.Manifest?.animations;
		if (stages == null) return null;
		for (int i = 0; i < stages.Length; i++)
		{
			if (stages[i] != null && string.Equals(stages[i].name, animationName, StringComparison.OrdinalIgnoreCase))
			{
				return GetGalleryName(package, i);
			}
		}
		return null;
	}

	internal static void Shutdown()
	{
		if (!_initialized) return;
		SceneManager.activeSceneChanged -= OnSceneChanged;
		_initialized = false;
		Packages.Clear();
	}

	private static void Load(string path)
	{
		try
		{
			string json = File.ReadAllText(path);
			WallPictureTrapManifest manifest = JsonUtility.FromJson<WallPictureTrapManifest>(json);
			// Unity 6's JsonUtility can leave arrays on plugin-defined root objects at their
			// field initializer. Individual serializable objects still deserialize correctly.
			if (manifest != null && (manifest.animations == null || manifest.animations.Length == 0))
				manifest.animations = ParseObjectArray<WallPictureTrapAnimation>(json, "animations");
			if (manifest == null) return;
			if (string.IsNullOrWhiteSpace(manifest.id) || string.IsNullOrWhiteSpace(manifest.portrait)) throw new InvalidDataException("id and portrait are required");
			if (manifest.animations == null || manifest.animations.Length == 0) throw new InvalidDataException("at least one animation is required");
			string directory = Path.GetDirectoryName(path);
			WallPictureTrapPackage package = new WallPictureTrapPackage
			{
				Manifest = manifest,
				Directory = directory
			};
			// The switch is the framework's, bound before this assembly was allowed to load, so a
			// package whose code is blocked still has something to enable (§166). Binding a second
			// one here would have been two settings of the same name in one file.
			package.EnabledEntry = WallPictureTrapModule.EnabledEntry;
			if (package.EnabledEntry != null)
			{
				package.EnabledEntry.SettingChanged += (_, __) => ApplyEnabledState(package);
			}
			List<PackageSpriteAnimation> animations = new List<PackageSpriteAnimation>();
			foreach (WallPictureTrapAnimation stage in manifest.animations)
			{
				animations.Add(PackageMedia.LoadSpriteSheet(directory, stage.file, stage.name,
					stage.columns, stage.rows, stage.frameCount, stage.fps, manifest.portraitPixelsPerUnit, "0.5,0.5", stage.loop));
			}
			package.Portrait = PackageMedia.LoadSpriteSheet(directory, manifest.portrait, "portrait",
				1, 1, 1, 1f, manifest.portraitPixelsPerUnit, "0.5,0.5");
			package.Animations = animations.ToArray();
			if (!string.IsNullOrWhiteSpace(manifest.captureSound))
				package.CaptureSound = PackageMedia.LoadWav(Path.Combine(directory, manifest.captureSound), manifest.id + "_capture");
			CreateGalleryAssets(package);
			RegisterScenes(package);
			SyncFunscripts(package);
			Packages.Add(package);
		}
		catch (Exception ex)
		{
			ModServices.LogError("[WallPictureTrap] " + path + ": " + ex);
		}
	}

	private static void CreateGalleryAssets(WallPictureTrapPackage package)
	{
		WallPictureTrapManifest manifest = package.Manifest;
		EnemyGalleryEntry entry = ScriptableObject.CreateInstance<EnemyGalleryEntry>();
		entry.name = "CustomGalleryEntry_" + manifest.id;
		entry.enemyID = manifest.id;
		entry.alwaysUnlocked = true;
		entry.enemyName = manifest.displayName;
		entry.enemyDescription = "A hidden wall picture that pulls nearby players into a custom animated scene.";
		Sprite sprite = (package.Portrait != null && package.Portrait.Frames != null && package.Portrait.Frames.Length > 0)
			? package.Portrait.Frames[0]
			: ((package.Animations != null && package.Animations.Length > 0 && package.Animations[0].Frames != null && package.Animations[0].Frames.Length > 0)
				? package.Animations[0].Frames[0]
				: null);
		entry.enemyIcon = sprite;
		entry.availableAnimations = new[] { "Idle" };
		entry.grabAnimations = new GrabAnimationData[manifest.animations.Length];
		for (int i = 0; i < manifest.animations.Length; i++)
			entry.grabAnimations[i] = new GrabAnimationData { animationName = manifest.animations[i].name };
		entry.hasGrabScene = true;
		package.GalleryEntry = entry;

		GameObject galleryPrefab = new GameObject("WallPictureGallery_" + manifest.id);
		galleryPrefab.SetActive(false);
		SpriteRenderer renderer = galleryPrefab.AddComponent<SpriteRenderer>();
		Material spriteMat = PackageMedia.SpriteMaterial;
		if (spriteMat != null)
		{
			renderer.sharedMaterial = spriteMat;
		}
		renderer.sprite = sprite;
		renderer.color = Color.white;
		renderer.sortingOrder = 100;
		// No animator on the gallery prefab any more: since §165 the framework draws a provided
		// entry from what `Describe` returns, so this object is only the still the viewer falls back
		// to. The frames it would have played are the same ones the presentation carries.
		UnityEngine.Object.DontDestroyOnLoad(galleryPrefab);
		package.GalleryPrefab = galleryPrefab;
	}

	internal static bool IsGalleryEntry(EnemyGalleryEntry entry) => entry != null && Packages.Exists(package => package.GalleryEntry == entry);

	internal static WallPictureTrapPackage FindGalleryEntry(EnemyGalleryEntry entry) => entry == null ? null : Packages.Find(package => package.GalleryEntry == entry);

	internal static IEnumerable<EnemyGalleryEntry> GetGalleryEntries()
	{
		foreach (WallPictureTrapPackage package in Packages)
			if (package.Enabled && package.GalleryEntry != null) yield return package.GalleryEntry;
	}

	private static void ApplyEnabledState(WallPictureTrapPackage package)
	{
		try
		{
			if (!package.Enabled)
			{
				foreach (WallPictureTrap trap in UnityEngine.Object.FindObjectsByType<WallPictureTrap>(FindObjectsSortMode.None))
					if (trap.Id.Equals(package.Manifest.id, StringComparison.OrdinalIgnoreCase))
						UnityEngine.Object.Destroy(trap.gameObject);
			}
			if (GalleryProgressManager.Instance != null)
			{
				PackageGallery.RefreshGallery(GalleryProgressManager.Instance);
			}
			foreach (EnemyGalleryUI gallery in UnityEngine.Object.FindObjectsByType<EnemyGalleryUI>(FindObjectsInactive.Include, FindObjectsSortMode.None))
			{
				PackageGallery.RefreshGallery(gallery);
			}
			ModServices.Log("[WallPictureTrap] '" + package.Manifest.id + "' " + (package.Enabled ? "enabled" : "disabled") + " from configuration");
		}
		catch (Exception ex)
		{
			ModServices.LogError("[WallPictureTrap] could not apply enabled state for '" + package.Manifest.id + "': " + ex);
		}
	}

	internal static string GetGalleryName(WallPictureTrapPackage package, int stageIndex)
	{
		if (package == null || package.Manifest.animations == null || package.Manifest.animations.Length == 0) return null;
		WallPictureTrapAnimation stage = package.Manifest.animations[Mathf.Clamp(stageIndex, 0, package.Manifest.animations.Length - 1)];
		return string.IsNullOrWhiteSpace(stage.gallery) ? package.Manifest.id + "_" + ModServices.Slug(stage.name) : stage.gallery.Trim();
	}

	private static void RegisterScenes(WallPictureTrapPackage package)
	{
		for (int i = 0; i < package.Manifest.animations.Length; i++) PackageGallery.RegisterRow(GetGalleryName(package, i));
	}

	private static void SyncFunscripts(WallPictureTrapPackage package)
	{
		string sourceRoot = Path.Combine(package.Directory, "funscripts");
		if (!Directory.Exists(sourceRoot)) return;
		string galleryRoot = Path.Combine(Paths.GameRootPath, "Edi", "Gallery");
		if (!Directory.Exists(galleryRoot))
		{
			ModServices.LogWarning("[WallPictureTrap] Edi/Gallery not found; funscripts for '" + package.Manifest.id + "' were not installed");
			return;
		}
		foreach (string variantDir in Directory.GetDirectories(sourceRoot))
		{
			string targetDir = Path.Combine(galleryRoot, Path.GetFileName(variantDir));
			Directory.CreateDirectory(targetDir);
			foreach (string source in Directory.GetFiles(variantDir, "*.funscript", SearchOption.TopDirectoryOnly))
			{
				// Same rule as the enemy packages: never replace a script already installed under
				// that name with different content. The gallery is this project's own, measured
				// against specific game assets, and a package that happens to name a file the way
				// a real row names it must not be able to overwrite it. Identical content copies
				// silently, which is the normal case - deploy.py has put these here already.
				string target = Path.Combine(targetDir, Path.GetFileName(source));
				if (File.Exists(target) && !PackageGallery.SameFileContent(source, target))
				{
					ModServices.LogWarning("[WallPictureTrap] '" + package.Manifest.id + "' ships "
						+ Path.GetFileName(source) + ", but a different script of that name is already in "
						+ Path.GetFileName(targetDir) + " - kept the existing one; rename the package's script");
					continue;
				}
				File.Copy(source, target, true);
			}
		}

		// The rows themselves are merged by CustomEnemyRegistry.MergeDefinitions - the one writer
		// both package kinds share. Building them is all that is specific to a trap, and it has to
		// stay in step with release.custom_enemy_gallery, which produces the same rows from the
		// repo side so a deployed install is already correct and this finds nothing to do.
		List<string> rows = new List<string>();
		for (int i = 0; i < package.Manifest.animations.Length; i++)
		{
			WallPictureTrapAnimation stage = package.Manifest.animations[i];
			string gallery = GetGalleryName(package, i);
			string file = string.IsNullOrWhiteSpace(stage.funscript) ? gallery : Path.GetFileNameWithoutExtension(stage.funscript.Trim());
			int end = FindFunscriptEnd(sourceRoot, file);
			if (end <= 0) continue;
			rows.Add(string.Join(",", gallery, file, "0", end.ToString(CultureInfo.InvariantCulture), "gallery", "true"));
		}
		PackageGallery.MergeRows("WallPictureTrap", package.Manifest.id, package.Directory, galleryRoot, rows);
	}

	private static int FindFunscriptEnd(string root, string file)
	{
		int end = 0;
		foreach (string path in Directory.GetFiles(root, file + ".funscript", SearchOption.AllDirectories))
			foreach (Match match in FunscriptAt.Matches(File.ReadAllText(path)))
				if (int.TryParse(match.Groups[1].Value, NumberStyles.None, CultureInfo.InvariantCulture, out int at)) end = Math.Max(end, at);
		return end;
	}

	private static T[] ParseObjectArray<T>(string json, string field) where T : class
	{
		List<T> result = new List<T>();
		int key = json.IndexOf("\"" + field + "\"", StringComparison.OrdinalIgnoreCase);
		int arrayStart = key < 0 ? -1 : json.IndexOf('[', key);
		if (arrayStart < 0) return result.ToArray();
		bool inString = false;
		bool escaped = false;
		int depth = 0;
		int objectStart = -1;
		for (int i = arrayStart + 1; i < json.Length; i++)
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
			if (c == '{')
			{
				if (depth == 0) objectStart = i;
				depth++;
			}
			else if (c == '}')
			{
				depth--;
				if (depth == 0 && objectStart >= 0)
				{
					T item = JsonUtility.FromJson<T>(json.Substring(objectStart, i - objectStart + 1));
					if (item != null) result.Add(item);
					objectStart = -1;
				}
			}
			else if (c == ']' && depth == 0) break;
		}
		return result.ToArray();
	}

	private static void OnSceneChanged(Scene oldScene, Scene newScene)
	{
		if (WallPictureTrapModule.Runner != null) WallPictureTrapModule.Runner.StartCoroutine(SpawnForScene(newScene));
	}

	private static IEnumerator SpawnForScene(Scene scene)
	{
		float delay = 0f;
		foreach (WallPictureTrapPackage package in Packages) delay = Mathf.Max(delay, package.Manifest.placementDelay);
		yield return new WaitForSecondsRealtime(Mathf.Max(0.5f, delay));
		if (scene != SceneManager.GetActiveScene()) yield break;
		GameObject player = GameObject.FindGameObjectWithTag("Player");
		if (player == null) yield break;
		foreach (WallPictureTrapPackage package in Packages)
		{
			if (!package.Enabled || !package.Manifest.autoPlace) continue;
			List<Vector3> occupied = FindExistingPositions(package.Manifest.id);
			int desired = Mathf.Max(0, package.Manifest.spawnCount);
			while (occupied.Count < desired)
			{
				if (!TryFindWall(player.transform, occupied, package.Manifest, out RaycastHit hit)) break;
				Spawn(package, hit.point, hit.normal);
				occupied.Add(hit.point);
			}
			if (occupied.Count < desired)
				ModServices.LogWarning("[WallPictureTrap] placed " + occupied.Count + "/" + desired + " '" + package.Manifest.id + "' trap(s); no more suitably separated walls were found");
		}
	}

	private static Camera ResolveCamera()
	{
		Camera camera = Camera.main;
		if (camera != null && camera.isActiveAndEnabled) return camera;
		GameObject player = GameObject.FindGameObjectWithTag("Player");
		if (player != null)
		{
			Camera playerCam = player.GetComponentInChildren<Camera>();
			if (playerCam != null && playerCam.isActiveAndEnabled) return playerCam;
		}
		foreach (Camera cam in Camera.allCameras)
		{
			if (cam != null && cam.isActiveAndEnabled) return cam;
		}
		return null;
	}

	private static bool TryFindWall(Transform player, List<Vector3> occupied, WallPictureTrapManifest manifest, out RaycastHit best)
	{
		best = default;
		if (player == null) return false;
		const int samples = 64;
		RaycastHit[] hits = new RaycastHit[samples];
		bool[] valid = new bool[samples];
		Vector3 origin = player.position + Vector3.up * 1.45f;
		for (int i = 0; i < samples; i++)
		{
			float angle = i * (360f / samples);
			Vector3 direction = Quaternion.Euler(0f, angle, 0f) * Vector3.forward;
			RaycastHit[] rayHits = Physics.RaycastAll(origin, direction, 18f, ~0, QueryTriggerInteraction.Ignore);
			Array.Sort(rayHits, (a, b) => a.distance.CompareTo(b.distance));
			foreach (RaycastHit hit in rayHits)
			{
				if (hit.collider == null || hit.collider.isTrigger) continue;
				if (hit.transform == player || hit.transform.IsChildOf(player)) continue;
				if (hit.transform.GetComponentInParent<WallPictureTrap>() != null) continue;
				if (Mathf.Abs(hit.normal.y) > 0.25f || hit.distance < 3f) continue;
				hits[i] = hit;
				valid[i] = true;
				break;
			}
		}

		List<WallCandidate> candidates = new List<WallCandidate>();
		for (int i = 0; i < samples; i++)
		{
			if (!valid[i]) continue;
			RaycastHit hit = hits[i];
			bool separated = true;
			foreach (Vector3 position in occupied)
				if (Vector3.Distance(position, hit.point) < Mathf.Max(1f, manifest.minimumSpawnSeparation)) { separated = false; break; }
			if (!separated) continue;

			bool corner = false;
			foreach (int neighbor in new[] { (i + samples - 1) % samples, (i + 1) % samples })
			{
				if (!valid[neighbor]) { corner = true; continue; }
				if (Vector3.Angle(hit.normal, hits[neighbor].normal) > 22f || Mathf.Abs(hit.distance - hits[neighbor].distance) > 2f) corner = true;
			}
			float score = Mathf.Abs(hit.distance - 9f) + (manifest.preferCorners ? (corner ? -6f : 5f) : 0f);
			Camera camera = ResolveCamera();
			if (camera != null)
			{
				Vector3 viewport = camera.WorldToViewportPoint(hit.point);
				if (viewport.z > 0f && viewport.x > 0.02f && viewport.x < 0.98f && viewport.y > 0.02f && viewport.y < 0.98f) score += 8f;
			}
			candidates.Add(new WallCandidate { Hit = hit, Score = score });
		}
		if (candidates.Count == 0) return false;
		candidates.Sort((a, b) => a.Score.CompareTo(b.Score));
		best = candidates[0].Hit;
		return true;
	}

	internal static WallPictureTrap SpawnFirstAtAim()
	{
		WallPictureTrapPackage package = Packages.Find(p => p.Enabled) ?? (Packages.Count > 0 ? Packages[0] : null);
		if (package == null)
		{
			ModServices.LogWarning("[WallPictureTrap] F10: no loaded wall-trap package");
			return null;
		}

		GameObject playerObj = GameObject.FindGameObjectWithTag("Player");
		Transform player = playerObj != null ? playerObj.transform : null;
		Camera camera = ResolveCamera();

		bool foundWall = false;
		RaycastHit wallHit = default;

		if (camera != null)
		{
			RaycastHit[] hits = Physics.RaycastAll(camera.transform.position, camera.transform.forward, 35f, ~0, QueryTriggerInteraction.Ignore);
			Array.Sort(hits, (a, b) => a.distance.CompareTo(b.distance));
			foreach (RaycastHit hit in hits)
			{
				if (hit.collider == null || hit.collider.isTrigger) continue;
				if (player != null && (hit.transform == player || hit.transform.IsChildOf(player))) continue;
				if (hit.transform.GetComponentInParent<WallPictureTrap>() != null) continue;
				if (Mathf.Abs(hit.normal.y) <= 0.35f)
				{
					wallHit = hit;
					foundWall = true;
					break;
				}
			}
		}

		if (!foundWall && player != null)
		{
			List<Vector3> occupied = FindExistingPositions(package.Manifest.id);
			if (TryFindWall(player, occupied, package.Manifest, out RaycastHit fallbackHit))
			{
				wallHit = fallbackHit;
				foundWall = true;
			}
		}

		if (!foundWall)
		{
			ModServices.LogWarning("[WallPictureTrap] F10: could not find a vertical wall in view or nearby");
			return null;
		}

		foreach (WallPictureTrap old in UnityEngine.Object.FindObjectsByType<WallPictureTrap>(FindObjectsSortMode.None))
		{
			if (old != null && old.Id.Equals(package.Manifest.id, StringComparison.OrdinalIgnoreCase))
			{
				UnityEngine.Object.Destroy(old.gameObject);
			}
		}

		return Spawn(package, wallHit.point, wallHit.normal);
	}

	private static WallPictureTrap Spawn(WallPictureTrapPackage package, Vector3 point, Vector3 normal)
	{
		GameObject root = new GameObject("WallPictureTrap_" + package.Manifest.id);
		root.transform.position = point + normal * 0.035f;
		root.transform.rotation = Quaternion.LookRotation(normal, Vector3.up);
		root.transform.localScale = ParseScale(package.Manifest.portraitScale);
		SpriteRenderer renderer = root.AddComponent<SpriteRenderer>();
		Material spriteMat = PackageMedia.SpriteMaterial;
		if (spriteMat != null) renderer.sharedMaterial = spriteMat;
		renderer.sprite = package.Portrait.Frames[0];
		float brightness = Mathf.Clamp01(package.Manifest.portraitBrightness);
		renderer.color = new Color(brightness, brightness, brightness, 1f);
		renderer.sortingOrder = 20;
		root.layer = 8;
		BoxCollider hitbox = root.AddComponent<BoxCollider>();
		Vector3 spriteSize = renderer.sprite.bounds.size;
		hitbox.size = new Vector3(spriteSize.x, spriteSize.y, Mathf.Max(0.02f, package.Manifest.colliderDepth));
		hitbox.center = renderer.sprite.bounds.center;
		hitbox.isTrigger = false;
		WallPictureTrap trap = root.AddComponent<WallPictureTrap>();
		trap.Initialize(package, renderer);
		ModServices.Log("[WallPictureTrap] placed '" + package.Manifest.id + "' at " + root.transform.position);
		return trap;
	}

	private static Vector3 ParseScale(string raw)
	{
		string[] parts = (raw ?? "").Split(',');
		if (parts.Length < 2 || !float.TryParse(parts[0], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float x) || !float.TryParse(parts[1], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float y)) return Vector3.one;
		float z = parts.Length > 2 && float.TryParse(parts[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float parsed) ? parsed : 1f;
		return new Vector3(x, y, z);
	}

	private static WallPictureTrap FindExisting(string id)
	{
		foreach (WallPictureTrap trap in UnityEngine.Object.FindObjectsByType<WallPictureTrap>(FindObjectsSortMode.None))
			if (trap.Id.Equals(id, StringComparison.OrdinalIgnoreCase)) return trap;
		return null;
	}

	private static List<Vector3> FindExistingPositions(string id)
	{
		List<Vector3> positions = new List<Vector3>();
		foreach (WallPictureTrap trap in UnityEngine.Object.FindObjectsByType<WallPictureTrap>(FindObjectsSortMode.None))
			if (trap.Id.Equals(id, StringComparison.OrdinalIgnoreCase)) positions.Add(trap.transform.position);
		return positions;
	}

	internal static void SpawnWhileExploring(Transform player, bool initialRetry = false)
	{
		if (player == null) return;
		foreach (WallPictureTrapPackage package in Packages)
		{
			if (!package.Enabled || !package.Manifest.autoPlace) continue;
			List<Vector3> occupied = FindExistingPositions(package.Manifest.id);
			int cap = initialRetry ? Mathf.Max(0, package.Manifest.spawnCount) : Mathf.Max(package.Manifest.spawnCount, package.Manifest.maxActiveCount);
			int remaining = cap - occupied.Count;
			if (remaining <= 0) continue;
			int batch = initialRetry ? remaining : Mathf.Clamp(package.Manifest.roamingSpawnBatch, 1, remaining);
			for (int i = 0; i < batch; i++)
			{
				if (!TryFindWall(player, occupied, package.Manifest, out RaycastHit hit)) break;
				Spawn(package, hit.point, hit.normal);
				occupied.Add(hit.point);
			}
		}
	}

	internal static float RoamingInterval
	{
		get
		{
			float value = 30f;
			foreach (WallPictureTrapPackage package in Packages)
				if (package.Enabled && package.Manifest.autoPlace) value = Mathf.Min(value, Mathf.Max(3f, package.Manifest.roamingSpawnInterval));
			return value;
		}
	}

	internal static float RoamingDistance
	{
		get
		{
			float value = 20f;
			foreach (WallPictureTrapPackage package in Packages)
				if (package.Enabled && package.Manifest.autoPlace) value = Mathf.Min(value, Mathf.Max(4f, package.Manifest.roamingSpawnDistance));
			return value;
		}
	}
}

internal sealed class WallPictureTrapPlacer : MonoBehaviour
{
	private int _sceneHandle = int.MinValue;
	private Transform _player;
	private Vector3 _lastSpawnPosition;
	private bool _hasSpawnPosition;
	private float _nextSpawnCheck;

	private void Update()
	{
		if (ModServices.DebugSpawnEnabled)
		{
			if (ModServices.HotkeyPressed(WallPictureTrapModule.SpawnKey))
			{
				WallPictureTrapRegistry.SpawnFirstAtAim();
			}
		}
		Scene scene = SceneManager.GetActiveScene();
		if (_sceneHandle != scene.handle)
		{
			_sceneHandle = scene.handle;
			_player = null;
			_hasSpawnPosition = false;
			_nextSpawnCheck = Time.unscaledTime + 4f;
		}
		if (Time.unscaledTime < _nextSpawnCheck) return;
		_nextSpawnCheck = Time.unscaledTime + WallPictureTrapRegistry.RoamingInterval;
		if (_player == null)
		{
			GameObject playerObject = GameObject.FindGameObjectWithTag("Player");
			if (playerObject == null) return;
			_player = playerObject.transform;
		}
		if (!_hasSpawnPosition)
		{
			_lastSpawnPosition = _player.position;
			_hasSpawnPosition = true;
			WallPictureTrapRegistry.SpawnWhileExploring(_player, initialRetry: true);
			return;
		}
		Vector3 movement = _player.position - _lastSpawnPosition;
		movement.y = 0f;
		if (movement.magnitude < WallPictureTrapRegistry.RoamingDistance) return;
		_lastSpawnPosition = _player.position;
		WallPictureTrapRegistry.SpawnWhileExploring(_player);
	}
}

internal sealed class WallPictureTrap : MonoBehaviour, IDamageable, IPackageSceneOwner
{
	private WallPictureTrapPackage _package;
	private SpriteRenderer _portrait;
	private Transform _player;
	private float _pullSpeed;
	private Vector3 _pullDirection;
	private float _armedAt;
	private float _cooldownUntil;
	private GameObject _overlay;
	private Canvas _overlayCanvas;
	private Image _animationImage;
	private Text _escapeLabel;
	private int _stage;
	private int _frame;
	private float _frameClock;
	private float _stageClock;
	private bool _capturing;
	private bool _restoreStruggleButton;
	private bool _pulling;
	private bool _sceneHidden;
	private bool _ediPlaying;
	private int _health;
	private Color _basePortraitColor;
	private float _damageFlashUntil;
	private GameObject _vanillaGrabImage;
	private Collider _hitbox;
	private AudioSource _captureAudio;
	private GameObject _healthBar;
	private Transform _healthBarFill;
	private Sprite _healthBarSprite;
	private Texture2D _healthBarTexture;

	internal string Id => _package?.Manifest.id ?? "";
	/// <summary>
	/// `IPackageSceneOwner`, and the reason all three members are here rather than two (§172).
	///
	/// Until §165 the framework answered these by testing for this type - `SceneVisualOwnerTest =
	/// enemy => enemy.GetComponent&lt;WallPictureTrap&gt;() != null`, and the same in `OwnsGrabScene`
	/// and `ResolveSceneMinimumSeconds`. The extraction replaced the type tests with this interface
	/// and this class never implemented it, so every one of them silently answered "not a package's
	/// scene" for three sessions. The visible half was that `NearbyEnemyHider` hid the trap at the
	/// instant of capture - a trap *is* the scene, so the mod deactivated the object drawing it, its
	/// `Update` stopped, and the overlay froze on frame 0.
	///
	/// **`OwnsSceneVisual` is unconditional on purpose.** The guard that reads it runs inside
	/// `GrabScreen.StartGrab`, which `BeginCapture` calls *before* it sets `_capturing`, so a
	/// state-gated answer is false at exactly the moment it is asked. A wall trap is its own visual
	/// whether or not it happens to be mid-capture, which is what the type test used to say.
	/// </summary>
	public float MinimumSceneSeconds => Mathf.Max(0f, _package?.Manifest.minimumSceneSeconds ?? 20f);

	/// <summary>True while vanilla's `GrabScreen` is showing this trap's capture. `GrabbingEnemy` is
	/// assigned by `StartGrab` before its postfix runs, so this is already true when PncEdi asks.</summary>
	public bool OwnsGrabScene =>
		_capturing || (GrabScreen.Instance != null && GrabScreen.Instance.GrabbingEnemy == gameObject);

	/// <summary>Always: the picture on the wall is the scene, and the mod's vanilla art handling and
	/// its nearby-enemy sweep both have to stand down for it.</summary>
	public bool OwnsSceneVisual => true;

	/// <summary>What this trap is adding to the player's velocity, read once per physics step by
	/// <see cref="WallPictureTrapPull"/>. Zero unless the trap is actively pulling.</summary>
	internal Vector3 PullVelocity => _pulling ? _pullDirection * _pullSpeed : Vector3.zero;

	internal void Initialize(WallPictureTrapPackage package, SpriteRenderer portrait)
	{
		_package = package;
		_portrait = portrait;
		_hitbox = GetComponent<Collider>();
		_basePortraitColor = portrait.color;
		_health = Mathf.Max(1, package.Manifest.maxHealth);
		CreateHealthBar();
		if (package.CaptureSound != null)
		{
			_captureAudio = gameObject.AddComponent<AudioSource>();
			_captureAudio.clip = package.CaptureSound;
			_captureAudio.loop = package.Manifest.captureSoundLoop;
			_captureAudio.volume = Mathf.Clamp01(package.Manifest.captureSoundVolume);
			_captureAudio.playOnAwake = false;
			_captureAudio.spatialBlend = 0f;
			_captureAudio.ignoreListenerPause = true;
		}
		gameObject.name = package.Manifest.displayName;
		_armedAt = Time.unscaledTime + package.Manifest.armDelay;
	}

	private void Update()
	{
		if (_package == null) return;
		if (_portrait != null && Time.unscaledTime >= _damageFlashUntil && _portrait.color != _basePortraitColor)
			_portrait.color = _basePortraitColor;
		if (_player == null) FindPlayer();
		if (_capturing) UpdateCapture();
		else
		{
			UpdatePull();
			UpdateSceneVisibility();
		}
	}

	private bool IsAnySceneActive()
	{
		if (ModServices.EscapeSceneActive) return true;
		GrabScreen screen = GrabScreen.Instance;
		return screen != null && screen.IsGrabbed;
	}

	private void UpdateSceneVisibility()
	{
		bool sceneActive = IsAnySceneActive();
		if (sceneActive && !_sceneHidden)
		{
			_sceneHidden = true;
			if (_portrait != null) _portrait.enabled = false;
			if (_healthBar != null) _healthBar.SetActive(false);
		}
		else if (!sceneActive && _sceneHidden)
		{
			_sceneHidden = false;
			if (_portrait != null) _portrait.enabled = true;
			UpdateHealthBar();
		}
	}

	public void TakeDamage(int damage)
	{
		if (_package == null || damage <= 0 || _health <= 0) return;
		_health = Mathf.Max(0, _health - damage);
		UpdateHealthBar();
		_damageFlashUntil = Time.unscaledTime + 0.12f;
		if (_portrait != null)
		{
			float flash = Mathf.Max(_basePortraitColor.r, 0.75f);
			_portrait.color = new Color(flash, flash * 0.35f, flash * 0.35f, 1f);
		}
		ModServices.Log("[WallPictureTrap] '" + Id + "' took " + damage + " damage (" + _health + "/" + _package.Manifest.maxHealth + ")");
		if (_health > 0) return;
		ModServices.Log("[WallPictureTrap] '" + Id + "' was destroyed");
		if (_capturing && GrabScreen.Instance != null && GrabScreen.Instance.GrabbingEnemy == gameObject)
			GrabScreen.Instance.EndGrab();
		Destroy(gameObject);
	}

	private void CreateHealthBar()
	{
		_healthBarTexture = new Texture2D(1, 1, TextureFormat.RGBA32, false);
		_healthBarTexture.name = "WallPictureTrapHealthBarPixel";
		_healthBarTexture.filterMode = FilterMode.Point;
		_healthBarTexture.SetPixel(0, 0, Color.white);
		_healthBarTexture.Apply(false, true);
		_healthBarSprite = Sprite.Create(_healthBarTexture, new Rect(0f, 0f, 1f, 1f), new Vector2(0.5f, 0.5f), 1f);
		_healthBarSprite.name = "WallPictureTrapHealthBarSprite";

		_healthBar = new GameObject("WallPictureTrapHealthBar");
		_healthBar.transform.SetParent(transform, false);
		_healthBar.transform.localPosition = new Vector3(0f, (_portrait?.sprite?.bounds.max.y ?? 1f) + 0.18f, 0.08f);
		_healthBar.transform.localRotation = Quaternion.identity;

		SpriteRenderer background = CreateHealthBarPart("Background", new Color(0.06f, 0.01f, 0.08f, 1f), 60);
		background.transform.SetParent(_healthBar.transform, false);
		background.transform.localScale = new Vector3(1.38f, 0.16f, 1f);

		SpriteRenderer fill = CreateHealthBarPart("Fill", new Color(1f, 0.08f, 0.18f, 1f), 61);
		fill.transform.SetParent(_healthBar.transform, false);
		fill.transform.localPosition = new Vector3(0f, 0f, 0.01f);
		_healthBarFill = fill.transform;
		UpdateHealthBar();
	}

	private SpriteRenderer CreateHealthBarPart(string name, Color color, int sortingOrder)
	{
		GameObject part = new GameObject(name);
		SpriteRenderer renderer = part.AddComponent<SpriteRenderer>();
		Material spriteMat = PackageMedia.SpriteMaterial;
		if (spriteMat != null) renderer.sharedMaterial = spriteMat;
		renderer.sprite = _healthBarSprite;
		renderer.color = color;
		renderer.sortingLayerID = _portrait != null ? _portrait.sortingLayerID : 0;
		renderer.sortingOrder = sortingOrder;
		return renderer;
	}

	private void UpdateHealthBar()
	{
		if (_healthBar == null || _healthBarFill == null || _package == null) return;
		float ratio = Mathf.Clamp01((float)_health / Mathf.Max(1, _package.Manifest.maxHealth));
		const float width = 1.28f;
		_healthBarFill.localScale = new Vector3(width * ratio, 0.1f, 1f);
		_healthBarFill.localPosition = new Vector3(-width * (1f - ratio) * 0.5f, 0f, 0.01f);
		// Keep the ambush portrait hidden until combat begins, then leave the bar visible.
		_healthBar.SetActive(_health > 0 && _health < _package.Manifest.maxHealth);
	}

	private void FindPlayer()
	{
		GameObject player = GameObject.FindGameObjectWithTag("Player");
		if (player == null) return;
		_player = player.transform;
	}

	/// <summary>Stop pulling, from wherever - range, a scene, a capture, being destroyed.</summary>
	private void StopPulling()
	{
		_pulling = false;
		_pullSpeed = 0f;
		WallPictureTrapPull.Remove(this);
		if (_portrait != null) _portrait.transform.localScale = Vector3.one;
	}

	private void UpdatePull()
	{
		// A paused game must not be grabbed by a picture: Update runs at timeScale zero, and every
		// clock here is unscaled, so without this the trap arms, pulls and captures behind the
		// pause menu or the mod manager's window.
		if (ModServices.SceneClockHeld) return;
		// Every one of these ends the pull rather than merely skipping a frame of it: the pull now
		// lives on until something clears it, so an early return that leaves `_pulling` set is an
		// invisible drag on the player for as long as the condition holds.
		if (_player == null || Time.unscaledTime < _armedAt || Time.unscaledTime < _cooldownUntil || GrabScreen.Instance == null || GrabScreen.Instance.IsGrabbed)
		{
			if (_pulling) StopPulling();
			return;
		}
		if (IsAnySceneActive())
		{
			if (_pulling)
			{
				ModServices.Log("[WallPictureTrap] another scene is active - pull suspended for '" + Id + "'");
				StopPulling();
			}
			return;
		}
		Vector3 playerCenter = _player.position + Vector3.up * 0.8f;
		Vector3 target = transform.position + transform.forward * 0.25f;
		// Pull along the floor. A wall picture may be above eye level, and including that
		// vertical offset made capture physically unreachable once the capsule hit the wall.
		target.y = playerCenter.y;
		Vector3 delta = target - playerCenter;
		float distance = delta.magnitude;
		// Out of range, or so close that `delta` has no usable direction left - at which point the
		// capture below has long since fired, so there is nothing to pull towards either way.
		if (distance > _package.Manifest.pullRadius || distance < 0.01f)
		{
			if (_pulling) ModServices.Log("[WallPictureTrap] player escaped pull range for '" + Id + "'");
			StopPulling();
			return;
		}
		Vector3 fromPicture = playerCenter - transform.position;
		if (Vector3.Dot(transform.forward, fromPicture.normalized) < _package.Manifest.frontArc || !HasLineOfSight(distance, fromPicture.normalized)) return;
		if (!_pulling)
		{
			_pulling = true;
			_pullSpeed = 0f;
			WallPictureTrapPull.Add(this);
			ModServices.Log("[WallPictureTrap] pulling player into '" + Id + "' from " + distance.ToString("F2") + "m");
		}

		// `pullStrength` is an acceleration, so it is integrated rather than used as a speed: the
		// grab ramps up over the first moments instead of snapping the player to full drag, which
		// is what the manifest's number has always described. `maxPullSpeed` is the cap, and it is
		// the number that decides whether the trap can be walked out of - the player walks at 7,
		// so a cap under that is a trap you escape by noticing it, and one over it is a trap that
		// takes you. The direction is recomputed every frame from the current delta, so circling
		// the picture steers the pull rather than leaving it pointing where the player used to be.
		float proximity = 1f - Mathf.Clamp01(distance / _package.Manifest.pullRadius);
		float acceleration = _package.Manifest.pullStrength * (0.45f + proximity * 1.1f + proximity * proximity * proximity * 2.2f);
		_pullSpeed = Mathf.Min(_pullSpeed + acceleration * Time.deltaTime, Mathf.Max(0f, _package.Manifest.maxPullSpeed));
		_pullDirection = delta.normalized;
		// The pull itself is applied in WallPictureTrapPull, on the far side of CMF's own velocity
		// assignment - read that class before changing anything here. Only when the player is not
		// a CMF controller at all does the trap move them itself.
		if (!WallPictureTrapPull.Bound) _player.position += _pullDirection * _pullSpeed * Time.deltaTime;
		float pulse = 1f + Mathf.Sin(Time.unscaledTime * (5f + proximity * 10f)) * 0.02f * proximity;
		_portrait.transform.localScale = new Vector3(pulse, pulse, 1f);
		if (distance <= _package.Manifest.captureDistance) BeginCapture();
	}

	private bool HasLineOfSight(float distance, Vector3 direction)
	{
		Vector3 origin = transform.position + transform.forward * 0.08f;
		if (!Physics.Raycast(origin, direction, out RaycastHit hit, distance, ~0, QueryTriggerInteraction.Ignore)) return true;
		return hit.transform == _player || hit.transform.IsChildOf(_player);
	}

	private void BeginCapture()
	{
		GrabScreen screen = GrabScreen.Instance;
		if (screen == null || screen.IsGrabbed)
		{
			ModServices.LogWarning("[WallPictureTrap] capture blocked: GrabScreen unavailable or already active");
			return;
		}
		ModServices.Log("[WallPictureTrap] capture threshold reached for '" + Id + "'");
		screen.StartGrab(gameObject, null, default, default, true);
		if (!screen.IsGrabbed || screen.GrabbingEnemy != gameObject)
		{
			ModServices.LogWarning("[WallPictureTrap] GrabScreen refused capture (player may have grab immunity)");
			_cooldownUntil = Time.unscaledTime + 1f;
			return;
		}
		if (screen.StruggleButton != null)
		{
			_restoreStruggleButton = screen.StruggleButton.interactable;
			screen.StruggleButton.interactable = false;
		}
		PackageMedia.HideVanillaGrabArt(screen);
		if (_portrait != null) _portrait.enabled = false;
		if (_hitbox != null) _hitbox.enabled = false;
		_capturing = true;
		_stage = 0;
		_frame = 0;
		_frameClock = 0f;
		_stageClock = 0f;
		CreateOverlay(screen);
		SetOverlayFrame();
		if (_captureAudio != null) _captureAudio.Play();
		PlayStageFunscript();
		ModServices.Log("[WallPictureTrap] erotic animation started for '" + Id + "': phase=" + _package.Manifest.animations[0].name + " frames=" + _package.Animations[0].Frames.Length + " fps=" + _package.Animations[0].Fps);
	}

	private void UpdateCapture()
	{
		GrabScreen screen = GrabScreen.Instance;
		if (screen == null || !screen.IsGrabbed || screen.GrabbingEnemy != gameObject)
		{
			EndCapture();
			return;
		}
		if (_escapeLabel != null) _escapeLabel.text = ModServices.EscapeHintText();
		if (_overlayCanvas != null) _overlayCanvas.sortingOrder = ModServices.GamePaused ? -1000 : 32000;
		// The overlay was already put behind the pause menu on the line above; the clock has to
		// stop too, or the stages keep advancing - and each stage POSTs a row to Edi.
		if (ModServices.SceneClockHeld) return;
		WallPictureTrapAnimation stageSpec = _package.Manifest.animations[_stage];
		PackageSpriteAnimation animation = _package.Animations[_stage];
		float dt = Time.unscaledDeltaTime;
		_frameClock += dt;
		_stageClock += dt;
		float duration = 1f / Mathf.Max(0.01f, animation.Fps);
		while (_frameClock >= duration)
		{
			_frameClock -= duration;
			if (_frame + 1 < animation.Frames.Length) _frame++;
			else if (animation.Loop) _frame = 0;
			SetOverlayFrame();
		}
		if (stageSpec.seconds > 0f && _stageClock >= stageSpec.seconds && _package.Animations.Length > 1)
		{
			_stage = (_stage + 1) % _package.Animations.Length;
			_frame = 0;
			_frameClock = 0f;
			_stageClock = 0f;
			SetOverlayFrame();
			PlayStageFunscript();
			ModServices.Log("[WallPictureTrap] animation phase -> " + _package.Manifest.animations[_stage].name + " frames=" + _package.Animations[_stage].Frames.Length);
		}
	}

	private void EndCapture()
	{
		_capturing = false;
		StopPulling();
		_cooldownUntil = Time.unscaledTime + _package.Manifest.cooldown;
		if (_overlay != null) Destroy(_overlay);
		if (_captureAudio != null) _captureAudio.Stop();
		if (_ediPlaying) ModServices.StopDevice();
		_ediPlaying = false;
		_overlay = null;
		_overlayCanvas = null;
		_animationImage = null;
		_escapeLabel = null;
		if (_restoreStruggleButton && GrabScreen.Instance != null && GrabScreen.Instance.StruggleButton != null)
			GrabScreen.Instance.StruggleButton.interactable = true;
		_restoreStruggleButton = false;
		if (_portrait != null) _portrait.enabled = true;
		if (_hitbox != null) _hitbox.enabled = true;
	}

	private void PlayStageFunscript()
	{
		string gallery = WallPictureTrapRegistry.GetGalleryName(_package, _stage);
		if (string.IsNullOrWhiteSpace(gallery)) return;
		ModServices.PlayGallery(gallery, loop: true, inGame: true);
		_ediPlaying = true;
	}

	private void CreateOverlay(GrabScreen screen)
	{
		_vanillaGrabImage = Traverse.Create(screen).Field("grabImage").GetValue<GameObject>();
		if (_vanillaGrabImage != null) _vanillaGrabImage.SetActive(false);
		_overlay = new GameObject("WallPictureTrapGrabOverlay", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
		_overlayCanvas = _overlay.GetComponent<Canvas>();
		_overlayCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
		_overlayCanvas.sortingOrder = ModServices.GamePaused ? -1000 : 32000;
		CanvasScaler scaler = _overlay.GetComponent<CanvasScaler>();
		scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
		scaler.referenceResolution = new Vector2(1920f, 1080f);

		GameObject background = UiObject("Background", _overlay.transform);
		Image backgroundImage = background.AddComponent<Image>();
		backgroundImage.color = new Color(0f, 0f, 0f, Mathf.Clamp01(_package.Manifest.captureBackdropAlpha));
		backgroundImage.raycastTarget = false;
		Stretch(background.GetComponent<RectTransform>());

		GameObject animationObject = UiObject("Animation", _overlay.transform);
		_animationImage = animationObject.AddComponent<Image>();
		_animationImage.preserveAspect = true;
		_animationImage.raycastTarget = false;
		RectTransform animationRect = animationObject.GetComponent<RectTransform>();
		animationRect.anchorMin = new Vector2(0.08f, 0.12f);
		animationRect.anchorMax = new Vector2(0.92f, 0.98f);
		animationRect.offsetMin = Vector2.zero;
		animationRect.offsetMax = Vector2.zero;

		GameObject labelObject = UiObject("EscapeCountdown", _overlay.transform);
		_escapeLabel = labelObject.AddComponent<Text>();
		_escapeLabel.text = ModServices.EscapeHintText();
		_escapeLabel.alignment = TextAnchor.MiddleCenter;
		_escapeLabel.fontSize = 28;
		_escapeLabel.color = Color.white;
		_escapeLabel.raycastTarget = false;
		if (screen.GrabText != null) _escapeLabel.font = screen.GrabText.font;
		Shadow shadow = labelObject.AddComponent<Shadow>();
		shadow.effectColor = new Color(0f, 0f, 0f, 0.95f);
		shadow.effectDistance = new Vector2(2f, -2f);
		RectTransform labelRect = labelObject.GetComponent<RectTransform>();
		labelRect.anchorMin = new Vector2(0.1f, 0.025f);
		labelRect.anchorMax = new Vector2(0.9f, 0.105f);
		labelRect.offsetMin = Vector2.zero;
		labelRect.offsetMax = Vector2.zero;
	}

	private void SetOverlayFrame()
	{
		if (_animationImage != null)
		{
			_animationImage.sprite = _package.Animations[_stage].Frames[_frame];
			_animationImage.SetAllDirty();
		}
	}

	private static GameObject UiObject(string name, Transform parent)
	{
		GameObject result = new GameObject(name, typeof(RectTransform));
		result.transform.SetParent(parent, false);
		return result;
	}

	private static void Stretch(RectTransform rect)
	{
		rect.anchorMin = Vector2.zero;
		rect.anchorMax = Vector2.one;
		rect.offsetMin = Vector2.zero;
		rect.offsetMax = Vector2.zero;
	}

	private void OnDestroy()
	{
		WallPictureTrapPull.Remove(this);
		if (_capturing && GrabScreen.Instance != null && GrabScreen.Instance.GrabbingEnemy == gameObject) GrabScreen.Instance.EndGrab();
		if (_overlay != null) Destroy(_overlay);
		if (_healthBarSprite != null) Destroy(_healthBarSprite);
		if (_healthBarTexture != null) Destroy(_healthBarTexture);
	}
}

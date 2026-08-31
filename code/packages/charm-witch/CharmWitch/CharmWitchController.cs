using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using HarmonyLib;
using PncCustomEnemies.Api;
using UnityEngine;
using UnityEngine.AI;
using UnityEngine.UI;
using UnityEngine.Video;

namespace CharmWitch;

[Serializable]
public sealed class CharmWitchSettings
{
	public bool enabled = true;
	public float auraRadius = 8.5f;
	public float heatPerSecond = 7f;
	public float lockIntervalSeconds = 10f;
	public float captureDistance = 1.25f;
	public float minimumSceneSeconds = 20f;
	public bool movementOnly = true;
	public float teleportMinSeconds = 5f;
	public float teleportMaxSeconds = 10f;
	public float teleportMinDistance = 4f;
	public float teleportMaxDistance = 11f;
	public float teleportChaseChance = 0.55f;
	public float damageTeleportCooldownSeconds = 5f;
	public float blinkSeconds = 0.16f;
	public float reinforcementIntervalSeconds = 14f;
	public int maxReinforcements = 4;
	public int circleBreakDamage = 80;
	public float circleBreakSeconds = 10f;
	public float circleBreakCooldownSeconds = 10f;
	public string lockSound = "";
	public float lockSoundVolume = 0.85f;
	// No default row names here: a package's gallery rows are the package's own, and a behaviour
	// that ships one enemy's names as its fallback silently plays that enemy's scripts for anyone
	// who omits the field. Empty resolves to null in ResolveCurrentAuraGallery, which is the same
	// "no row" the manifest asked for.
	public string auraGallery = "";
	public string captureGallery = "";
	public string[] dreamVideos = Array.Empty<string>();
	public float videoVolume = 1f;
}

internal sealed class CharmWitchController : MonoBehaviour, IPackageSceneOwner, IPackageEdiChannelOwner
{
	private static readonly List<CharmWitchController> ActiveControllers = new List<CharmWitchController>();
	private static Sprite _dreamCloudSprite;
	private static readonly Dictionary<string, AudioClip> LockSounds = new Dictionary<string, AudioClip>(StringComparer.OrdinalIgnoreCase);
	private readonly List<GameObject> _reinforcements = new List<GameObject>();

	internal static bool IsPlayerInsideAnyAura
	{
		get
		{
			for (int i = 0; i < ActiveControllers.Count; i++)
			{
				CharmWitchController c = ActiveControllers[i];
				if (c != null && c.isActiveAndEnabled && c._insideAura && !c.CircleBroken)
				{
					return true;
				}
			}
			return false;
		}
	}
	[SerializeField]
	private CharmWitchSettings _settings;
	[SerializeField]
	private string _packageDirectory;
	[SerializeField]
	private string _enemyId;
	[SerializeField]
	private CharmWitchRuntimeData _data;
	private Transform _player;
	private SpinningEnemyAI _spinAi;
	private WitchAuraCircle _auraCircle;
	private AudioSource _lockAudio;
	private SpriteRenderer[] _blinkRenderers = Array.Empty<SpriteRenderer>();
	private Traverse[] _attackClocks = Array.Empty<Traverse>();
	private bool _blinking;
	private float _nextDamageTeleportAt;
	private float _nextTeleportAt;
	private float _nextReinforcementAt;
	private float _auraExposure;
	private float _heatAccumulator;
	private MonoBehaviour _healthAi;
	private Traverse _healthField;
	private int _lastKnownHealth;
	private int _damageSinceBreak;
	private float _circleBrokenUntil;
	private float _circleArmedAt;
	private bool _circleBreakAnnounced;
	private bool _insideAura;
	private bool _capturing;
	private bool _restoreAiEnabled;
	private bool _restoreStruggleButton;
	private bool _ediAuraPlaying;
	private bool _ediCapturePlaying;
	private int _lastAuraLocks = -1;
	private string _currentAuraPlayingGallery;
	private GameObject _mediaOverlay;
	private Canvas _mediaCanvas;
	private VideoPlayer _videoPlayer;
	private RenderTexture _videoTexture;
	private AudioSource _videoAudio;
	private Text _escapeLabel;

	public float MinimumSceneSeconds => Mathf.Max(0f, _settings?.minimumSceneSeconds ?? 20f);

	// The three questions PncEdi asks about any scene a package owns, answered through the package
	// API rather than by the framework testing for this type (§165). Her capture runs through
	// vanilla's GrabScreen with this GameObject as the "enemy", and the aura holds the device
	// between scenes, which is what keeps the filler off the channel while the player stands in it.
	public bool OwnsGrabScene => _capturing;

	public bool OwnsSceneVisual => false;

	public bool HoldsEdiChannel => isActiveAndEnabled && _insideAura && !CircleBroken;

	private bool CircleBroken => Time.time < _circleBrokenUntil;

	internal static void Attach(GameObject root, string packageDirectory, CharmWitchSettings settings, string enemyId)
	{
		if (root == null || settings == null || !settings.enabled)
		{
			return;
		}
		ValidateVideos(packageDirectory, settings.dreamVideos);
		LoadLockSound(packageDirectory, settings.lockSound);
		CharmWitchController controller = root.GetComponent<CharmWitchController>() ?? root.AddComponent<CharmWitchController>();
		controller._settings = settings;
		controller._packageDirectory = packageDirectory;
		controller._enemyId = enemyId;
		controller._data = CharmWitchRuntimeData.Find(enemyId);
		ModServices.Log("[CharmWitch] attached boss behaviour to '" + enemyId + "' with " + (settings.dreamVideos?.Length ?? 0) + " dream video(s)");
	}

	private static void ValidateVideos(string packageDirectory, string[] videos)
	{
		if (videos == null || videos.Length == 0)
		{
			throw new InvalidDataException("witch behaviour requires at least one dreamVideos entry");
		}
		foreach (string video in videos)
		{
			// **Resolve exactly the way playback resolves, or a package is valid to play and
			// invalid to load** (§171). `PackageMedia.ResolveVideoUrl` prefers a `.webm` sibling of
			// whatever the manifest names, on every platform, and the package *archive* ships only
			// those siblings - `release.py` drops an H.264 master once a WebM exists, because
			// nothing ever opens it. Validating the literal name with `ResolvePackageFile` therefore
			// passed in the working tree, where both files sit side by side, and threw in every
			// real install - and a throw here means the behaviour never attaches at all, so the
			// witch came up as a plain reskin with no charm circle. It also enforces the same
			// containment rule, so nothing is lost by asking it instead.
			if (string.IsNullOrEmpty(PackageMedia.ResolveVideoUrl(packageDirectory, video)))
			{
				throw new FileNotFoundException(
					"witch dream video was not found inside its package (neither '" + video +
					"' nor a .webm beside it)", video);
			}
		}
	}

	private static string ResolvePackageFile(string packageDirectory, string file, string description)
	{
		string root = Path.GetFullPath(packageDirectory).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
		string path = Path.GetFullPath(Path.Combine(packageDirectory, file ?? ""));
		if (!path.StartsWith(root, StringComparison.OrdinalIgnoreCase) || !File.Exists(path))
		{
			throw new FileNotFoundException(description + " was not found inside its package", path);
		}
		return path;
	}

	// The charm-circle lock cue is shared by every witch instance, so each WAV is decoded once.
	private static AudioClip LoadLockSound(string packageDirectory, string file)
	{
		if (string.IsNullOrWhiteSpace(file))
		{
			return null;
		}
		string path = ResolvePackageFile(packageDirectory, file, "witch lock sound");
		if (LockSounds.TryGetValue(path, out AudioClip cached) && cached != null)
		{
			return cached;
		}
		AudioClip clip = PackageMedia.LoadWav(path, "witch_lock_" + Path.GetFileNameWithoutExtension(path));
		LockSounds[path] = clip;
		return clip;
	}

	private void OnEnable()
	{
		if (!ActiveControllers.Contains(this))
		{
			ActiveControllers.Add(this);
		}
		// Clones made by the game's spawners and the debug spawner lose the custom-class
		// _settings field (see CharmWitchRuntimeData); the runtime data holder's reference
		// survives, so the whole configuration is restored from it before anything else runs.
		if (_settings == null && _data != null)
		{
			_settings = _data.Settings;
			_packageDirectory = _data.PackageDirectory;
			_enemyId = _data.EnemyId;
			ModServices.Log("[CharmWitch] restored boss settings from runtime data for '" + (_enemyId ?? "?") + "'");
		}
		if (_settings == null)
		{
			return;
		}
		_spinAi = GetComponent<SpinningEnemyAI>() ?? GetComponentInChildren<SpinningEnemyAI>(true);
		ResolveHealthSource();
		_lastKnownHealth = int.MinValue;
		_damageSinceBreak = 0;
		_circleBrokenUntil = 0f;
		_circleArmedAt = 0f;
		_circleBreakAnnounced = false;
		_nextTeleportAt = Time.time + RandomInterval(_settings.teleportMinSeconds, _settings.teleportMaxSeconds);
		_nextReinforcementAt = Time.time + Mathf.Max(2f, _settings.reinforcementIntervalSeconds);
		_nextDamageTeleportAt = 0f;
		_blinking = false;
		ResolveAttackClocks();
		CreateAuraCircle();
		CreateLockAudio();
	}

	// The witch borrows the base enemy only for pathing. Rather than patching one AI class, every
	// attack gate is held shut by pushing its cooldown clock forward each frame, so she keeps the
	// tested chase movement while spins, projectiles and the vanilla grab never come up.
	private void ResolveAttackClocks()
	{
		_attackClocks = Array.Empty<Traverse>();
		if (_settings == null || !_settings.movementOnly)
		{
			return;
		}
		MonoBehaviour ai = _healthAi ?? _spinAi;
		if (ai == null)
		{
			return;
		}
		Traverse traverse = Traverse.Create(ai);
		List<Traverse> clocks = new List<Traverse>();
		foreach (string field in new[] { "lastSpinEndTime", "lastGrabTime", "lastShootTime", "lastChargeTime", "lastAttackTime" })
		{
			Traverse clock = traverse.Field(field);
			if (clock.FieldExists()) clocks.Add(clock);
		}
		_attackClocks = clocks.ToArray();
		if (_spinAi != null) _spinAi.canGrab = false;
		ModServices.Log("[CharmWitch] '" + _enemyId + "' movement-only: holding " + _attackClocks.Length + " attack cooldown(s) on " + ai.GetType().Name);
	}

	private void SuppressBaseAttacks()
	{
		for (int i = 0; i < _attackClocks.Length; i++)
		{
			_attackClocks[i].SetValue(Time.time);
		}
	}

	private void Update()
	{
		if (_settings == null || IsDead())
		{
			StopAura();
			if (_auraCircle != null)
			{
				Destroy(_auraCircle.gameObject);
				_auraCircle = null;
			}
			return;
		}
		SuppressBaseAttacks();
		if (_videoAudio != null) _videoAudio.mute = ModServices.GamePaused;
		UpdateCircleBreak();
		if (_player == null)
		{
			GameObject playerObject = GameObject.FindGameObjectWithTag("Player");
			if (playerObject == null) return;
			_player = playerObject.transform;
		}
		UpdateAuraCircle();
		if (_capturing)
		{
			UpdateCapture();
			return;
		}
		GrabScreen screen = GrabScreen.Instance;
		if ((screen != null && screen.IsGrabbed) || CinematicCameraSwapTrigger.IsAnyInCinematicView)
		{
			StopAura();
			return;
		}

		Vector3 delta = _player.position - transform.position;
		delta.y = 0f;
		float distance = delta.magnitude;
		if (_blinking)
		{
			return;
		}
		// Her capture has never once fired in play, and the reason is not decidable from the
		// source: the gate is a horizontal distance against captureDistance, but whether the
		// player can physically get that close depends on the two colliders, and the only
		// distances any log carries are DIAG-SPRITE's 3D ones (closest ever seen: 1.4 m against a
		// 1.2 m gate). So report the closest horizontal approach of each visit, once, when it is
		// beaten by a tenth of a metre - which says either "never closer than X" or "got inside
		// the gate and something else refused".
		if (distance < _closestApproach - 0.1f)
		{
			_closestApproach = distance;
			ModServices.Log("[CharmWitch] '" + _enemyId + "' closest approach " + distance.ToString("0.00")
				+ "m (capture at " + Mathf.Max(0.35f, _settings.captureDistance).ToString("0.00") + "m)");
		}
		if (distance <= Mathf.Max(0.35f, _settings.captureDistance))
		{
			BeginCapture();
			return;
		}
		if (!CircleBroken && distance <= Mathf.Max(_settings.captureDistance, _settings.auraRadius))
		{
			UpdateAuraExposure();
		}
		else
		{
			StopAura();
		}

		if (Time.time >= _nextTeleportAt)
		{
			_nextTeleportAt = Time.time + RandomInterval(_settings.teleportMinSeconds, _settings.teleportMaxSeconds);
			// Walking is only how she closes small gaps. Anything further than the charm circle she
			// crosses by blinking onto the player, which is what makes the aura inescapable on foot.
			bool chase = distance > Mathf.Max(1f, _settings.auraRadius) * 1.35f || UnityEngine.Random.value < Mathf.Clamp01(_settings.teleportChaseChance);
			TryTeleport(chase);
		}
		if (Time.time >= _nextReinforcementAt)
		{
			_nextReinforcementAt = Time.time + Mathf.Max(2f, _settings.reinforcementIntervalSeconds);
			TrySpawnReinforcement();
		}
	}

	private string ResolveCurrentAuraGallery(string excludeCurrent = null)
	{
		string baseGallery = _settings?.auraGallery;
		if (string.IsNullOrWhiteSpace(baseGallery))
		{
			return null;
		}
		int locks = ModServices.CurrentHeatLocks;
		List<string> pool = new List<string>();

		if (locks <= 0)
		{
			string[] tier0Variants = new[] { baseGallery, baseGallery + "_0_b", baseGallery + "_0_c" };
			foreach (string candidate in tier0Variants)
			{
				if (ModServices.IsGalleryRow(candidate))
				{
					pool.Add(candidate);
				}
			}
		}
		else
		{
			for (int tier = locks; tier >= 1; tier--)
			{
				string[] tierVariants = new[] { baseGallery + "_" + tier, baseGallery + "_" + tier + "_b", baseGallery + "_" + tier + "_c" };
				foreach (string candidate in tierVariants)
				{
					if (ModServices.IsGalleryRow(candidate))
					{
						pool.Add(candidate);
					}
				}
				if (pool.Count > 0)
				{
					break;
				}
			}
		}

		if (pool.Count == 0)
		{
			return baseGallery;
		}
		if (pool.Count == 1)
		{
			return pool[0];
		}

		if (!string.IsNullOrEmpty(excludeCurrent) && pool.Count > 1)
		{
			pool.Remove(excludeCurrent);
		}
		return pool[UnityEngine.Random.Range(0, pool.Count)];
	}

	private void UpdateAuraExposure()
	{
		int locks = ModServices.CurrentHeatLocks;
		string targetGallery = ResolveCurrentAuraGallery();

		if (!_insideAura)
		{
			_insideAura = true;
			_lastAuraLocks = locks;
			_currentAuraPlayingGallery = targetGallery;
			CreateDreamOverlay(capture: false);
			if (!string.IsNullOrWhiteSpace(targetGallery))
			{
				ModServices.PlayGallery(targetGallery, loop: true, inGame: true);
				_ediAuraPlaying = true;
			}
			ModServices.Debug("WITCH", _enemyId + " aura entered (locks=" + locks + ", gallery=" + targetGallery + ")");
		}
		else if (_ediAuraPlaying && locks != _lastAuraLocks)
		{
			_lastAuraLocks = locks;
			string nextGallery = ResolveCurrentAuraGallery(_currentAuraPlayingGallery);
			if (!string.IsNullOrWhiteSpace(nextGallery) && !string.Equals(nextGallery, _currentAuraPlayingGallery, StringComparison.OrdinalIgnoreCase))
			{
				_currentAuraPlayingGallery = nextGallery;
				ModServices.PlayGallery(nextGallery, loop: true, inGame: true);
				ModServices.Debug("WITCH", _enemyId + " aura escalated with locks=" + locks + " -> " + nextGallery);
			}
		}

		float dt = Time.deltaTime;
		_auraExposure += dt;
		_heatAccumulator += Mathf.Max(0f, _settings.heatPerSecond) * dt;
		if (_heatAccumulator >= 0.5f)
		{
			PlayerStats stats = _player.GetComponent<PlayerStats>() ?? _player.GetComponentInChildren<PlayerStats>();
			if (stats != null)
			{
				stats.GenerateHeat(_heatAccumulator);
			}
			_heatAccumulator = 0f;
		}
		// Zero or less is "heat only": the aura keeps building pressure for as long as the player
		// stands in it, and stops handing out the permanent thing.
		//
		// A lock is what a played scene costs. The aura granted one every `lockIntervalSeconds`
		// with nothing on screen, so standing near her spent the run's health budget through a
		// mechanism the player never saw - which is what the 2026-08-26 run reported (§130). Heat
		// is the right currency for proximity: it climbs while you are in the circle and falls
		// again when you leave, so the aura still pushes you out without taking anything back.
		if (_settings.lockIntervalSeconds <= 0f)
		{
			return;
		}
		float lockInterval = Mathf.Max(0.1f, _settings.lockIntervalSeconds);
		while (_auraExposure >= lockInterval)
		{
			_auraExposure -= lockInterval;
			if (ModServices.AddAuraLock(_enemyId))
			{
				PlayLockSound();
				int newLocks = ModServices.CurrentHeatLocks;
				if (newLocks != _lastAuraLocks)
				{
					_lastAuraLocks = newLocks;
					string escalated = ResolveCurrentAuraGallery(_currentAuraPlayingGallery);
					if (!string.IsNullOrWhiteSpace(escalated) && !string.Equals(escalated, _currentAuraPlayingGallery, StringComparison.OrdinalIgnoreCase))
					{
						_currentAuraPlayingGallery = escalated;
						ModServices.PlayGallery(escalated, loop: true, inGame: true);
						ModServices.Debug("WITCH", _enemyId + " lock gained in aura -> " + escalated);
					}
				}
			}
		}
	}

	private void StopAura()
	{
		if (!_insideAura) return;
		_insideAura = false;
		_auraExposure = 0f;
		_heatAccumulator = 0f;
		_lastAuraLocks = -1;
		_currentAuraPlayingGallery = null;
		DestroyMediaOverlay();
		if (_ediAuraPlaying)
		{
			_ediAuraPlaying = false;
			ModServices.ReleaseToFiller();
		}
		ModServices.Debug("WITCH", _enemyId + " aura exited -> handed over to filler");
	}

	// Sustained damage collapses the charm circle: circleBreakDamage points of damage take it down
	// for circleBreakSeconds. Hits landed while it is down, or during the refractory window that
	// follows the outage, are ignored, so the next break needs a fresh damage total.
	private void UpdateCircleBreak()
	{
		int health = ReadHealth();
		if (health < 0)
		{
			return;
		}
		int previous = _lastKnownHealth;
		_lastKnownHealth = health;
		// Getting hit costs her the spot she was standing in: she is a boss that refuses to trade.
		if (previous != int.MinValue && health < previous && !_capturing && !_blinking && Time.time >= _nextDamageTeleportAt)
		{
			_nextDamageTeleportAt = Time.time + Mathf.Max(0f, _settings.damageTeleportCooldownSeconds);
			TryTeleport(towardPlayer: false);
		}
		if (CircleBroken)
		{
			return;
		}
		if (_circleBreakAnnounced)
		{
			_circleBreakAnnounced = false;
			ModServices.Debug("WITCH", _enemyId + " charm circle restored, unbreakable for " + Mathf.Max(0f, _settings.circleBreakCooldownSeconds).ToString("0.0") + "s");
		}
		if (previous == int.MinValue || health >= previous || _settings.circleBreakDamage <= 0 || Time.time < _circleArmedAt)
		{
			return;
		}
		_damageSinceBreak += previous - health;
		if (_damageSinceBreak >= _settings.circleBreakDamage)
		{
			BreakCircle();
		}
	}

	private void BreakCircle()
	{
		_damageSinceBreak = 0;
		_circleBrokenUntil = Time.time + Mathf.Max(0f, _settings.circleBreakSeconds);
		_circleArmedAt = _circleBrokenUntil + Mathf.Max(0f, _settings.circleBreakCooldownSeconds);
		_circleBreakAnnounced = true;
		StopAura();
		ModServices.Log("[CharmWitch] '" + _enemyId + "' took " + _settings.circleBreakDamage + " damage: charm circle down for " + Mathf.Max(0f, _settings.circleBreakSeconds).ToString("0.0") + "s");
	}

	private float _closestApproach = float.MaxValue;

	private int ReadHealth()
	{
		if (_healthAi == null || _healthField == null)
		{
			return -1;
		}
		return _healthField.GetValue<int>();
	}

	// Damage is read off the base enemy AI instead of patching one damage method, so any source
	// that lowers currentHealth counts and the behaviour survives a different base enemy.
	private void ResolveHealthSource()
	{
		_healthAi = null;
		_healthField = null;
		MonoBehaviour ai = _spinAi;
		for (int i = 0; ai == null && i < ModServices.EnemyAiTypes.Length; i++)
		{
			ai = (MonoBehaviour)GetComponentInChildren(ModServices.EnemyAiTypes[i], true);
		}
		if (ai == null)
		{
			ModServices.LogWarning("[CharmWitch] '" + _enemyId + "' has no enemy AI: the charm circle cannot be broken by damage");
			return;
		}
		Traverse field = Traverse.Create(ai).Field("currentHealth");
		if (!field.FieldExists())
		{
			ModServices.LogWarning("[CharmWitch] '" + _enemyId + "' AI " + ai.GetType().Name + " has no currentHealth field: the charm circle cannot be broken by damage");
			return;
		}
		_healthAi = ai;
		_healthField = field;
	}
	private void BeginCapture()
	{
		GrabScreen screen = GrabScreen.Instance;
		if (screen == null || screen.IsGrabbed) return;
		bool wasAuraPlaying = _ediAuraPlaying;
		_ediAuraPlaying = false;
		StopAura();
		screen.StartGrab(gameObject, null, default, default, true);
		if (!screen.IsGrabbed || screen.GrabbingEnemy != gameObject)
		{
			if (wasAuraPlaying)
			{
				ModServices.ReleaseToFiller();
			}
			return;
		}
		_capturing = true;
		if (_spinAi != null)
		{
			_restoreAiEnabled = _spinAi.enabled;
			_spinAi.enabled = false;
		}
		if (screen.StruggleButton != null)
		{
			_restoreStruggleButton = screen.StruggleButton.interactable;
			screen.StruggleButton.interactable = false;
		}
		PackageMedia.HideVanillaGrabArt(screen);
		CreateDreamOverlay(capture: true);
		if (!string.IsNullOrWhiteSpace(_settings.captureGallery))
		{
			ModServices.PlayGallery(_settings.captureGallery, loop: true, inGame: true);
			_ediCapturePlaying = true;
		}
		ModServices.Log("[CharmWitch] player captured by '" + _enemyId + "' for at least " + MinimumSceneSeconds.ToString("0.0") + "s");
	}

	private void UpdateCapture()
	{
		GrabScreen screen = GrabScreen.Instance;
		if (screen == null || !screen.IsGrabbed || screen.GrabbingEnemy != gameObject)
		{
			EndCapture();
			return;
		}
		if (_mediaCanvas != null) _mediaCanvas.sortingOrder = ModServices.GamePaused ? -1000 : 32000;
		if (_escapeLabel != null) _escapeLabel.text = ModServices.EscapeHintText();
	}

	private void EndCapture()
	{
		if (!_capturing) return;
		_capturing = false;
		DestroyMediaOverlay();
		if (_spinAi != null) _spinAi.enabled = _restoreAiEnabled;
		if (_restoreStruggleButton && GrabScreen.Instance != null && GrabScreen.Instance.StruggleButton != null)
		{
			GrabScreen.Instance.StruggleButton.interactable = true;
		}
		_restoreStruggleButton = false;
		if (_ediCapturePlaying)
		{
			_ediCapturePlaying = false;
			ModServices.ReleaseToFiller();
		}
	}

	private void CreateDreamOverlay(bool capture)
	{
		DestroyMediaOverlay();
		_mediaOverlay = new GameObject(capture ? "CharmWitchCaptureDream" : "CharmWitchAuraDream", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler));
		_mediaCanvas = _mediaOverlay.GetComponent<Canvas>();
		_mediaCanvas.renderMode = RenderMode.ScreenSpaceOverlay;
		_mediaCanvas.sortingOrder = ModServices.GamePaused ? -1000 : (capture ? 32000 : 31000);
		CanvasScaler scaler = _mediaOverlay.GetComponent<CanvasScaler>();
		scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
		scaler.referenceResolution = new Vector2(1920f, 1080f);

		if (capture)
		{
			GameObject backdrop = UiObject("DreamBackdrop", _mediaOverlay.transform);
			Image backdropImage = backdrop.AddComponent<Image>();
			backdropImage.color = new Color(0f, 0f, 0f, 0.76f);
			backdropImage.raycastTarget = false;
			Stretch(backdrop.GetComponent<RectTransform>());
		}

		GameObject maskObject = UiObject("DreamCloudMask", _mediaOverlay.transform);
		Image maskImage = maskObject.AddComponent<Image>();
		maskImage.sprite = GetDreamCloudSprite();
		maskImage.color = Color.white;
		maskImage.raycastTarget = false;
		Mask mask = maskObject.AddComponent<Mask>();
		mask.showMaskGraphic = false;
		SetDreamRect(maskObject.GetComponent<RectTransform>(), capture);

		GameObject videoObject = UiObject("DreamVideo", maskObject.transform);
		RawImage rawImage = videoObject.AddComponent<RawImage>();
		rawImage.color = Color.white;
		rawImage.raycastTarget = false;
		Stretch(videoObject.GetComponent<RectTransform>());
		_videoTexture = new RenderTexture(capture ? 1280 : 640, capture ? 720 : 360, 0, RenderTextureFormat.ARGB32);
		_videoTexture.Create();
		rawImage.texture = _videoTexture;

		_videoAudio = _mediaOverlay.AddComponent<AudioSource>();
		_videoAudio.playOnAwake = false;
		_videoAudio.loop = true;
		_videoAudio.spatialBlend = 0f;
		_videoAudio.volume = Mathf.Clamp01(_settings?.videoVolume ?? 1f);
		_videoAudio.mute = ModServices.GamePaused;
		_videoPlayer = _mediaOverlay.AddComponent<VideoPlayer>();
		_videoPlayer.playOnAwake = false;
		_videoPlayer.isLooping = true;
		_videoPlayer.skipOnDrop = true;
		_videoPlayer.waitForFirstFrame = false;
		_videoPlayer.audioOutputMode = VideoAudioOutputMode.AudioSource;
		_videoPlayer.controlledAudioTrackCount = 1;
		_videoPlayer.EnableAudioTrack(0, true);
		_videoPlayer.SetTargetAudioSource(0, _videoAudio);
		_videoPlayer.renderMode = VideoRenderMode.RenderTexture;
		_videoPlayer.targetTexture = _videoTexture;
		// PackageVideo, not a bare file:// URL: it prefers a WebM sibling, because Unity's
		// VideoPlayer has no H.264 decoder on Linux and would otherwise leave this overlay blank
		// with nothing said about it.
		string videoUrl = PackageMedia.ResolveVideoUrl(_packageDirectory, PickDreamVideo());
		if (!string.IsNullOrEmpty(videoUrl))
		{
			_videoPlayer.url = videoUrl;
			_videoPlayer.Prepare();
			_videoPlayer.Play();
		}

		if (capture)
		{
			GameObject labelObject = UiObject("EscapeCountdown", _mediaOverlay.transform);
			_escapeLabel = labelObject.AddComponent<Text>();
			_escapeLabel.text = ModServices.EscapeHintText();
			_escapeLabel.alignment = TextAnchor.MiddleCenter;
			_escapeLabel.fontSize = 30;
			_escapeLabel.color = Color.white;
			_escapeLabel.raycastTarget = false;
			if (GrabScreen.Instance != null && GrabScreen.Instance.GrabText != null) _escapeLabel.font = GrabScreen.Instance.GrabText.font;
			Shadow shadow = labelObject.AddComponent<Shadow>();
			shadow.effectColor = new Color(0f, 0f, 0f, 0.95f);
			shadow.effectDistance = new Vector2(2f, -2f);
			RectTransform labelRect = labelObject.GetComponent<RectTransform>();
			labelRect.anchorMin = new Vector2(0.1f, 0.025f);
			labelRect.anchorMax = new Vector2(0.9f, 0.105f);
			labelRect.offsetMin = Vector2.zero;
			labelRect.offsetMax = Vector2.zero;
		}
	}

	private string PickDreamVideo()
	{
		string[] videos = _settings.dreamVideos;
		return videos[UnityEngine.Random.Range(0, videos.Length)];
	}

	private void DestroyMediaOverlay()
	{
		if (_videoPlayer != null)
		{
			_videoPlayer.Stop();
			_videoPlayer.targetTexture = null;
		}
		if (_videoAudio != null)
		{
			_videoAudio.Stop();
		}
		if (_videoTexture != null)
		{
			_videoTexture.Release();
			Destroy(_videoTexture);
		}
		if (_mediaOverlay != null) Destroy(_mediaOverlay);
		_mediaOverlay = null;
		_mediaCanvas = null;
		_videoPlayer = null;
		_videoTexture = null;
		_videoAudio = null;
		_escapeLabel = null;
	}

	private static void SetDreamRect(RectTransform rect, bool capture)
	{
		rect.anchorMin = capture ? new Vector2(0.055f, 0.105f) : new Vector2(0.018f, 0.055f);
		rect.anchorMax = capture ? new Vector2(0.945f, 0.955f) : new Vector2(0.37f, 0.44f);
		rect.offsetMin = Vector2.zero;
		rect.offsetMax = Vector2.zero;
	}

	private static Sprite GetDreamCloudSprite()
	{
		if (_dreamCloudSprite != null) return _dreamCloudSprite;
		const int width = 512;
		const int height = 320;
		Texture2D texture = new Texture2D(width, height, TextureFormat.RGBA32, false);
		texture.name = "CharmWitchDreamCloudMask";
		Color32[] pixels = new Color32[width * height];
		for (int y = 0; y < height; y++)
		{
			for (int x = 0; x < width; x++)
			{
				bool inside = Ellipse(x, y, 270, 172, 205, 116)
					|| Ellipse(x, y, 120, 180, 87, 86)
					|| Ellipse(x, y, 210, 225, 105, 83)
					|| Ellipse(x, y, 322, 232, 105, 78)
					|| Ellipse(x, y, 408, 180, 82, 84)
					|| Ellipse(x, y, 96, 70, 31, 25)
					|| Ellipse(x, y, 46, 34, 17, 14);
				pixels[y * width + x] = inside ? new Color32(255, 255, 255, 255) : new Color32(255, 255, 255, 0);
			}
		}
		texture.SetPixels32(pixels);
		texture.Apply(false, true);
		_dreamCloudSprite = Sprite.Create(texture, new Rect(0f, 0f, width, height), new Vector2(0.5f, 0.5f), 100f);
		_dreamCloudSprite.name = "CharmWitchDreamCloud";
		return _dreamCloudSprite;
	}

	private static bool Ellipse(int x, int y, int centerX, int centerY, int radiusX, int radiusY)
	{
		float dx = (x - centerX) / (float)radiusX;
		float dy = (y - centerY) / (float)radiusY;
		return dx * dx + dy * dy <= 1f;
	}

	private void CreateLockAudio()
	{
		if (_lockAudio != null || _settings == null || string.IsNullOrWhiteSpace(_settings.lockSound))
		{
			return;
		}
		AudioClip clip;
		try
		{
			clip = LoadLockSound(_packageDirectory, _settings.lockSound);
		}
		catch (Exception ex)
		{
			ModServices.LogError("[CharmWitch] lock sound unavailable for '" + _enemyId + "': " + ex.Message);
			return;
		}
		_lockAudio = gameObject.AddComponent<AudioSource>();
		_lockAudio.clip = clip;
		_lockAudio.playOnAwake = false;
		_lockAudio.loop = false;
		_lockAudio.spatialBlend = 0f;
		_lockAudio.ignoreListenerPause = true;
		_lockAudio.volume = Mathf.Clamp01(_settings.lockSoundVolume);
	}

	private void PlayLockSound()
	{
		if (_lockAudio == null || _lockAudio.clip == null)
		{
			return;
		}
		_lockAudio.PlayOneShot(_lockAudio.clip, Mathf.Clamp01(_settings.lockSoundVolume));
	}

	private void CreateAuraCircle()
	{
		if (_auraCircle != null || _settings == null) return;
		_auraCircle = WitchAuraCircle.Create(transform, _settings.auraRadius);
	}

	private void UpdateAuraCircle()
	{
		if (_auraCircle == null) return;
		// No lock to fill towards when the aura is heat-only, so the ring shows no progress.
		float lockInterval = Mathf.Max(0.1f, _settings.lockIntervalSeconds);
		float progress = _insideAura && _settings.lockIntervalSeconds > 0f ? _auraExposure / lockInterval : 0f;
		_auraCircle.SetState(_insideAura, CircleBroken, progress);
	}

	// Two flavours of jump: a chase blink that drops her onto the player so the circle swallows
	// them, and a scatter blink that puts distance back between the two.
	private void TryTeleport(bool towardPlayer)
	{
		if (_player == null || _blinking) return;
		Vector3 destination;
		if (towardPlayer)
		{
			float reach = Mathf.Max(_settings.captureDistance + 0.6f, _settings.auraRadius * 0.55f);
			if (!TryFindGround(_player.position, Mathf.Max(_settings.captureDistance + 0.4f, reach * 0.5f), reach, out destination)) return;
		}
		else if (!TryFindGround(_player.position, _settings.teleportMinDistance, _settings.teleportMaxDistance, out destination))
		{
			return;
		}
		StartCoroutine(Blink(destination, towardPlayer));
	}

	// She is never seen walking a long line: the sprite fades out inside a portal burst, the body
	// is warped, and she fades back in at the far end.
	private IEnumerator Blink(Vector3 destination, bool towardPlayer)
	{
		_blinking = true;
		Vector3 origin = transform.position;
		StartCoroutine(PortalBurst(origin));
		yield return FadeVisual(1f, 0f, Mathf.Max(0.02f, _settings.blinkSeconds));

		Rigidbody body = GetComponent<Rigidbody>();
		if (body != null)
		{
			body.linearVelocity = Vector3.zero;
			body.angularVelocity = Vector3.zero;
		}
		NavMeshAgent agent = GetComponent<NavMeshAgent>();
		if (agent != null && agent.enabled && agent.isOnNavMesh) agent.Warp(destination);
		else transform.position = destination;

		StartCoroutine(PortalBurst(destination));
		yield return FadeVisual(0f, 1f, Mathf.Max(0.02f, _settings.blinkSeconds) * 1.4f);
		_blinking = false;
		ModServices.Debug("WITCH", _enemyId + (towardPlayer ? " chase portal " : " scatter portal ") + origin.ToString("F1") + " -> " + destination.ToString("F1"));
	}

	private IEnumerator FadeVisual(float from, float to, float seconds)
	{
		if (_blinkRenderers.Length == 0)
		{
			_blinkRenderers = GetComponentsInChildren<SpriteRenderer>(true);
		}
		float elapsed = 0f;
		while (elapsed < seconds)
		{
			elapsed += Time.deltaTime;
			SetVisualAlpha(Mathf.Lerp(from, to, Mathf.Clamp01(elapsed / seconds)));
			yield return null;
		}
		SetVisualAlpha(to);
	}

	private void SetVisualAlpha(float alpha)
	{
		foreach (SpriteRenderer renderer in _blinkRenderers)
		{
			if (renderer == null) continue;
			Color color = renderer.color;
			renderer.color = new Color(color.r, color.g, color.b, alpha);
		}
	}

	private IEnumerator PortalBurst(Vector3 position)
	{
		GameObject ringObject = new GameObject("WitchPortalBurst");
		ringObject.transform.position = position + Vector3.up * 0.08f;
		LineRenderer ring = ringObject.AddComponent<LineRenderer>();
		ring.loop = true;
		ring.useWorldSpace = false;
		ring.positionCount = 48;
		ring.widthMultiplier = 0.1f;
		ring.material = new Material(Shader.Find("Sprites/Default"));
		float elapsed = 0f;
		while (elapsed < 0.8f)
		{
			elapsed += Time.deltaTime;
			float t = Mathf.Clamp01(elapsed / 0.8f);
			float radius = Mathf.Lerp(0.2f, 2.1f, t);
			Color color = Color.Lerp(new Color(0.35f, 0.9f, 1f, 1f), new Color(0.95f, 0.15f, 1f, 0f), t);
			ring.startColor = color;
			ring.endColor = color;
			for (int i = 0; i < ring.positionCount; i++)
			{
				float angle = i * Mathf.PI * 2f / ring.positionCount;
				ring.SetPosition(i, new Vector3(Mathf.Cos(angle) * radius, 0f, Mathf.Sin(angle) * radius));
			}
			yield return null;
		}
		Destroy(ringObject);
	}

	private void TrySpawnReinforcement()
	{
		_reinforcements.RemoveAll(IsGoneOrDead);
		if (_reinforcements.Count >= Mathf.Max(0, _settings.maxReinforcements) || _player == null) return;
		GameObject prefab = ModServices.PickReinforcementPrefab();
		if (prefab == null || !TryFindGround(_player.position, 8f, 15f, out Vector3 position)) return;
		Vector3 facing = _player.position - position;
		facing.y = 0f;
		Quaternion rotation = facing.sqrMagnitude > 0.01f ? Quaternion.LookRotation(facing.normalized, Vector3.up) : Quaternion.identity;
		GameObject enemy = Instantiate(prefab, position, rotation);
		ModServices.EnsureSpawnActive(enemy);
		_reinforcements.Add(enemy);
		ModServices.Log("[CharmWitch] boss pressure spawned reinforcement '" + ModServices.StripCloneSuffix(prefab.name) + "' (" + _reinforcements.Count + "/" + _settings.maxReinforcements + ")");
	}

	private static bool IsGoneOrDead(GameObject enemy)
	{
		if (enemy == null) return true;
		EnemyAI enemyAi = enemy.GetComponentInChildren<EnemyAI>();
		if (enemyAi != null && enemyAi.IsDead) return true;
		ChargingEnemyAI charging = enemy.GetComponentInChildren<ChargingEnemyAI>();
		if (charging != null && charging.IsDead) return true;
		SpinningEnemyAI spinning = enemy.GetComponentInChildren<SpinningEnemyAI>();
		return spinning != null && spinning.IsDead;
	}

	// A blink or a reinforcement must never leave the playable area. This game has no Unity
	// NavMesh: enemies navigate the A* Pathfinding Project's recast graph, so the old raw floor
	// raycast was the only source and it happily accepted decorative geometry behind walls, on
	// roofs and in off-map pits - stranding the witch somewhere the player cannot reach and she
	// cannot walk back from. Every candidate is now snapped to the nearest walkable A* node,
	// rejected when the snap drifted far from the requested ring (a hit metres away is a
	// different room), and accepted only when the A* graph itself says a path connects the spot
	// to the anchor (the player). The raycast survives solely as a no-graph emergency fallback
	// with strict sanity limits.
	private static readonly Pathfinding.NNConstraint WalkableConstraint = Pathfinding.NNConstraint.Walkable;

	private static bool TryFindGround(Vector3 center, float minDistance, float maxDistance, out Vector3 position)
	{
		global::AstarPath astar = global::AstarPath.active;
		Pathfinding.GraphNode anchor = astar != null ? astar.GetNearest(center, WalkableConstraint).node : null;
		for (int attempt = 0; attempt < 18; attempt++)
		{
			float angle = UnityEngine.Random.Range(0f, Mathf.PI * 2f);
			float distance = UnityEngine.Random.Range(Mathf.Max(1f, minDistance), Mathf.Max(minDistance + 0.1f, maxDistance));
			Vector3 candidate = center + new Vector3(Mathf.Cos(angle), 0f, Mathf.Sin(angle)) * distance;
			if (anchor != null)
			{
				if (TryFindGraphGround(astar, anchor, candidate, out position)) return true;
			}
			else if (TryFindFallbackGround(center, candidate, out position))
			{
				return true;
			}
		}
		position = default;
		return false;
	}

	private static bool TryFindGraphGround(global::AstarPath astar, Pathfinding.GraphNode anchor, Vector3 candidate, out Vector3 position)
	{
		position = default;
		Pathfinding.NNInfo info = astar.GetNearest(candidate, WalkableConstraint);
		if (info.node == null || !info.node.Walkable)
		{
			return false;
		}
		if ((info.position - candidate).sqrMagnitude > 3.5f * 3.5f)
		{
			return false;
		}
		if (!Pathfinding.PathUtilities.IsPathPossible(anchor, info.node))
		{
			return false;
		}
		position = info.position;
		return true;
	}

	// Only used when no A* graph exists at all (never on normal levels): keep the old raycast,
	// but demand the anchor's own height and standing room so the spot is at least plausible.
	private static bool TryFindFallbackGround(Vector3 center, Vector3 candidate, out Vector3 position)
	{
		position = default;
		if (!Physics.Raycast(candidate + Vector3.up * 8f, Vector3.down, out RaycastHit ground, 20f, ~0, QueryTriggerInteraction.Ignore)
			|| ground.normal.y < 0.55f)
		{
			return false;
		}
		if (Mathf.Abs(ground.point.y - center.y) > 4f)
		{
			return false;
		}
		if (Physics.CheckCapsule(ground.point + Vector3.up * 0.3f, ground.point + Vector3.up * 1.8f, 0.45f, ~0, QueryTriggerInteraction.Ignore))
		{
			return false;
		}
		position = ground.point;
		return true;
	}

	private bool IsDead()
	{
		return _spinAi != null && _spinAi.IsDead;
	}

	private static float RandomInterval(float minimum, float maximum)
	{
		minimum = Mathf.Max(0.5f, minimum);
		maximum = Mathf.Max(minimum, maximum);
		return UnityEngine.Random.Range(minimum, maximum);
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

	private void OnDisable()
	{
		ActiveControllers.Remove(this);
		StopAura();
		if (_capturing && GrabScreen.Instance != null && GrabScreen.Instance.GrabbingEnemy == gameObject) GrabScreen.Instance.EndGrab();
		EndCapture();
		_blinking = false;
		SetVisualAlpha(1f);
		if (_auraCircle != null)
		{
			Destroy(_auraCircle.gameObject);
			_auraCircle = null;
		}
	}

	private void OnDestroy()
	{
		ActiveControllers.Remove(this);
	}
}

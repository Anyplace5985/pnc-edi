using System.Collections.Generic;
using BepInEx.Unity.Mono.Configuration;
using PixelCrushers.GridController;
using UnityEngine;

namespace PncEdi;

public static class FreeCam
{
	private static bool _active;
	private static Transform _player;
	private static Rigidbody _rb;
	private static FirstPersonController _fp;
	private static Camera _cam;
	private static Collider[] _colliders;
	private static bool _savedKinematic;
	private static bool _savedGravity;
	private static bool _savedFpEnabled;
	private static readonly List<bool> _savedColliderEnabled = new List<bool>();
	private static int _ambientCursor = -1;
	private static readonly List<Transform> _ambientList = new List<Transform>();

	private static readonly string[] HSceneKeywords = new string[19]
	{
		"fuck", "cum", "sex", "anal", "blowjob", "bj ", "gangbang", "chain", "ride", "face_sit",
		"face sit", "tentacle", "dildo", "moan", "orgy", "penetra", "intercourse", "wall fuck", "bed blow"
	};

	public static bool Active => _active;

	public static bool WasTogglePressed(KeyboardShortcut shortcut)
	{
		KeyCode mainKey = shortcut.MainKey;
		if ((int)mainKey == 0)
		{
			return false;
		}
		if (_active)
		{
			if (!SafeInput.GetKeyDown(mainKey))
			{
				return false;
			}
			foreach (KeyCode modifier in shortcut.Modifiers)
			{
				if (!SafeInput.GetKey(modifier))
				{
					return false;
				}
			}
			return true;
		}
		return shortcut.IsDown();
	}

	public static void HandleSceneChanged()
	{
		if (!_active)
		{
			ResetPlayerCache();
			return;
		}
		_active = false;
		if (!ResolvePlayer(forceRefresh: true))
		{
			ResetPlayerCache();
			Plugin.DBG("FREECAM", "OFF (scene change, player lost)");
		}
		else
		{
			RestorePlayerState();
			ResetPlayerCache();
			Plugin.DBG("FREECAM", "OFF (scene change)");
		}
	}

	public static void Toggle()
	{
		if (_active)
		{
			Disable();
		}
		else
		{
			Enable();
		}
	}

	private static void ResetPlayerCache()
	{
		_player = null;
		_rb = null;
		_fp = null;
		_cam = null;
		_colliders = null;
		_savedColliderEnabled.Clear();
	}

	private static bool ResolvePlayer(bool forceRefresh = false)
	{
		if (!forceRefresh && _player != null && _rb != null)
		{
			return true;
		}
		GameObject gameObject = GameObject.FindGameObjectWithTag("Player");
		if (gameObject == null)
		{
			return false;
		}
		_player = gameObject.transform;
		_rb = gameObject.GetComponent<Rigidbody>();
		_fp = gameObject.GetComponent<FirstPersonController>();
		_cam = gameObject.GetComponentInChildren<Camera>();
		if (_cam == null)
		{
			GameObject cameraObject = GameObject.FindGameObjectWithTag("MainCamera");
			if (cameraObject != null)
			{
				_cam = cameraObject.GetComponent<Camera>();
			}
		}
		_colliders = gameObject.GetComponentsInChildren<Collider>(false);
		return _rb != null;
	}

	public static void Enable()
	{
		InventoryUI inventoryUI = Object.FindAnyObjectByType<InventoryUI>();
		if (inventoryUI != null && inventoryUI.IsInventoryOpen)
		{
			inventoryUI.ForceCloseInventory();
			Plugin.DBG("FREECAM", "inventory closed before noclip");
		}
		if (!ResolvePlayer())
		{
			Plugin.DBG("FREECAM", "no player tag found");
			return;
		}
		_savedKinematic = _rb.isKinematic;
		_savedGravity = _rb.useGravity;
		_savedFpEnabled = (Object)_fp != (Object)null && _fp.enabled;
		_rb.useGravity = false;
		_rb.linearVelocity = Vector3.zero;
		_rb.angularVelocity = Vector3.zero;
		_rb.isKinematic = true;
		if ((Object)_fp != (Object)null)
		{
			_fp.enabled = false;
		}
		_savedColliderEnabled.Clear();
		if (_colliders != null)
		{
			Collider[] colliders = _colliders;
			foreach (Collider collider in colliders)
			{
				if (collider == null)
				{
					_savedColliderEnabled.Add(item: false);
					continue;
				}
				_savedColliderEnabled.Add(collider.enabled);
				collider.enabled = false;
			}
		}
		_active = true;
		Plugin.DBG("FREECAM", "ON  | WASD=move, Space=up, Ctrl/Shift=down, mouse=look. F1 to exit.");
	}

	public static void Disable()
	{
		_active = false;
		if (!ResolvePlayer())
		{
			ResetPlayerCache();
			Plugin.DBG("FREECAM", "OFF (player lost)");
		}
		else
		{
			RestorePlayerState();
			Plugin.DBG("FREECAM", "OFF");
		}
	}

	private static void RestorePlayerState()
	{
		if (_rb != null)
		{
			_rb.isKinematic = _savedKinematic;
			_rb.useGravity = _savedGravity;
			_rb.linearVelocity = Vector3.zero;
			_rb.angularVelocity = Vector3.zero;
		}
		if ((Object)_fp == (Object)null && _player != null)
		{
			_fp = _player.GetComponent<FirstPersonController>();
		}
		if ((Object)_fp != (Object)null)
		{
			bool enabled = _savedFpEnabled;
			InventoryUI inventoryUI = Object.FindAnyObjectByType<InventoryUI>();
			if (inventoryUI != null && inventoryUI.IsInventoryOpen)
			{
				enabled = false;
			}
			_fp.enabled = enabled;
		}
		if (_colliders == null)
		{
			return;
		}
		for (int i = 0; i < _colliders.Length && i < _savedColliderEnabled.Count; i++)
		{
			if (_colliders[i] != null)
			{
				_colliders[i].enabled = _savedColliderEnabled[i];
			}
		}
	}

	public static void Tick()
	{
		if (_active)
		{
			InventoryUI inventoryUI = Object.FindAnyObjectByType<InventoryUI>();
			if (inventoryUI != null && inventoryUI.IsInventoryOpen)
			{
				return;
			}
		}
		if (_active && ResolvePlayer())
		{
			Transform reference = ((_cam != null) ? _cam.transform : _player);
			Vector3 forward = reference.forward;
			Vector3 right = reference.right;
			Vector3 vector3 = Vector3.zero;
			if (SafeInput.GetKey((KeyCode)119))
			{
				vector3 += forward;
			}
			if (SafeInput.GetKey((KeyCode)115))
			{
				vector3 -= forward;
			}
			if (SafeInput.GetKey((KeyCode)100))
			{
				vector3 += right;
			}
			if (SafeInput.GetKey((KeyCode)97))
			{
				vector3 -= right;
			}
			if (SafeInput.GetKey((KeyCode)32))
			{
				vector3 += Vector3.up;
			}
			if (SafeInput.GetKey((KeyCode)306) || SafeInput.GetKey((KeyCode)304))
			{
				vector3 -= Vector3.up;
			}
			if (vector3.sqrMagnitude > 0.0001f)
			{
				float speed = (SafeInput.GetKey((KeyCode)308) ? 25f : 10f);
				Transform player = _player;
				player.position += vector3.normalized * speed * Time.deltaTime;
			}
			if (_rb != null && !_rb.isKinematic)
			{
				_rb.isKinematic = true;
			}
		}
	}

	private static void RefreshAmbientList()
	{
		_ambientList.Clear();
		AudioSource[] audioSources = Object.FindObjectsByType<AudioSource>((FindObjectsSortMode)0);
		foreach (AudioSource audioSource in audioSources)
		{
			if (!(audioSource == null) && !(audioSource.clip == null) && audioSource.loop)
			{
				string s = audioSource.clip.name?.ToLowerInvariant() ?? "";
				string s2 = audioSource.gameObject.name?.ToLowerInvariant() ?? "";
				if (IsHSceneSounding(s) || IsHSceneSounding(s2))
				{
					_ambientList.Add(audioSource.transform);
				}
			}
		}
		_ambientList.Sort(delegate(Transform a, Transform b)
		{
			if (a == null)
			{
				return 1;
			}
			if (b == null)
			{
				return -1;
			}
			Vector3 vector3 = a.position - _player.position;
			float sqrMagnitude = vector3.sqrMagnitude;
			vector3 = b.position - _player.position;
			float sqrMagnitude2 = vector3.sqrMagnitude;
			return sqrMagnitude.CompareTo(sqrMagnitude2);
		});
	}

	private static bool IsHSceneSounding(string s)
	{
		if (string.IsNullOrEmpty(s))
		{
			return false;
		}
		string[] hSceneKeywords = HSceneKeywords;
		string[] keywords = hSceneKeywords;
		foreach (string keyword in keywords)
		{
			if (s.Contains(keyword))
			{
				return true;
			}
		}
		return false;
	}
}

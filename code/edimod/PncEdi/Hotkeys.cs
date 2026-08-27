using System;
using BepInEx.Configuration;
using BepInEx.Unity.Mono.Configuration;
using UnityEngine;

namespace PncEdi;

// BepInEx's KeyboardShortcut.IsDown() is stricter than it looks. It is
//
//     GetKeyDown(MainKey) && ModifierKeyTest()
//
// and ModifierKeyTest builds `modifierBlockKeyCodes` = every supported KeyCode EXCEPT the
// shortcut's own, then requires that **none of them is currently held**. That is right for a
// UI shortcut - it stops Ctrl+S firing a bare S binding - and wrong for a debug tool, because
// walking forward means W is held, so the key silently does nothing.
//
// Reported 2026-08-17 as "the spawn keys are wonky, often no spawn happens". It is not
// intermittent at all: it fires when standing still and never while moving.
//
// This keeps the explicit modifiers (a shortcut configured as Ctrl+F9 still needs Ctrl) and
// drops only the "no unrelated key held" rule.
internal static class Hotkeys
{
	internal static bool IsDown(ConfigEntry<KeyboardShortcut> entry)
	{
		if (entry == null)
		{
			return false;
		}
		// The branch below goes to BepInEx's own IsDown(), which does not pass through SafeInput,
		// so the mod-manager stand-down has to be repeated here to cover both paths.
		if (ModManagerBridge.WindowOpen)
		{
			return false;
		}
		if (Plugin.CfgDebugHotkeysIgnoreHeldKeys == null || !Plugin.CfgDebugHotkeysIgnoreHeldKeys.Value)
		{
			return entry.Value.IsDown();
		}
		KeyboardShortcut shortcut = entry.Value;
		KeyCode mainKey = shortcut.MainKey;
		if (mainKey == (KeyCode)0)
		{
			return false;
		}
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
		// Ignore unrelated keys, but NOT unrelated modifiers. The config ships
		// FillerOnKey = Alpha1 + LeftControl alongside SpawnZombieKey = Alpha1, so dropping the
		// held-key rule outright would make Ctrl+1 fire both. Blocking on held modifiers that the
		// shortcut does not ask for keeps the two distinct while still letting W stay down.
		foreach (KeyCode blocker in ModifierKeys)
		{
			bool requested = false;
			foreach (KeyCode modifier in shortcut.Modifiers)
			{
				if (modifier == blocker)
				{
					requested = true;
					break;
				}
			}
			if (!requested && SafeInput.GetKey(blocker))
			{
				return false;
			}
		}
		return true;
	}

	private static readonly KeyCode[] ModifierKeys = new KeyCode[]
	{
		(KeyCode)306, (KeyCode)305,   // LeftControl, RightControl
		(KeyCode)308, (KeyCode)307,   // LeftAlt, RightAlt
		(KeyCode)304, (KeyCode)303,   // LeftShift, RightShift
		(KeyCode)310, (KeyCode)309    // LeftCommand, RightCommand
	};

	// Unity's KeyCode enum has no members between 128 and 255 - it runs ASCII up to Delete (127)
	// and resumes at Keypad0 (256). A config value in that hole can never be produced by
	// Input.GetKeyDown, so the binding is dead and says nothing about it.
	//
	// The case that found this: SpawnGloryHoleTrapKey (earlier SpawnChestTrapKey) shipped as 223,
	// an attempt at the German 'ss' key, and had therefore never worked once. On a QWERTZ keyboard
	// that key sits where '-' does on QWERTY, which Unity reports as KeyCode.Minus (45). That key
	// is gone now - it aimed at a scene trigger rather than an enemy - but the check it prompted
	// guards every binding.
	internal static bool IsUnreachableKeyCode(KeyCode key)
	{
		int code = (int)key;
		return code >= 128 && code <= 255;
	}

	internal static void AuditBindings()
	{
		try
		{
			int bad = 0;
			foreach (System.Reflection.FieldInfo field in typeof(Plugin).GetFields(
				System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Public))
			{
				if (field.FieldType != typeof(ConfigEntry<KeyboardShortcut>))
				{
					continue;
				}
				ConfigEntry<KeyboardShortcut> entry = field.GetValue(null) as ConfigEntry<KeyboardShortcut>;
				if (entry == null)
				{
					continue;
				}
				KeyCode mainKey = entry.Value.MainKey;
				if (IsUnreachableKeyCode(mainKey))
				{
					Plugin.DBG("KEYBIND", $"UNREACHABLE: {entry.Definition.Key} = {(int)mainKey}. Unity's KeyCode enum has no member " +
						"between 128 and 255, so this binding can never fire. Pick a key Unity can report.");
					bad++;
				}
			}
			if (bad > 0)
			{
				Plugin.DBG("KEYBIND", bad + " binding(s) can never fire - see above.");
			}
		}
		catch (Exception ex)
		{
			Plugin.DBG("KEYBIND", "audit failed: " + ex.Message);
		}
	}
}

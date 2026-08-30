using System;
using System.Collections.Generic;
using UnityEngine;

namespace CharmWitch;

/// <summary>
/// The behaviour's settings, held where a clone can still reach them.
///
/// Unity does not copy a serialized field whose type is a custom `[Serializable]` class when a
/// runtime-prepared GameObject is cloned: `Object.Instantiate` hands the clone null for those while
/// engine references come through intact. A custom enemy is built once and then cloned by the
/// game's spawners, the debug spawner and the gallery, so every clone would arrive with no settings
/// - the "static sprite, no charm circle, no dream bubbles" failure the framework hit in §131 and
/// solved the same way for its own data.
///
/// A ScriptableObject reference *does* survive the clone, so the settings travel inside one and the
/// controller restores them in `OnEnable`. The framework holds its own copy of this trick for the
/// data it owns; a package has to hold its own, because after §165 the framework never sees a
/// behaviour's settings at all.
/// </summary>
internal sealed class CharmWitchRuntimeData : ScriptableObject
{
	private static readonly Dictionary<string, CharmWitchRuntimeData> Registry = new Dictionary<string, CharmWitchRuntimeData>(StringComparer.OrdinalIgnoreCase);

	internal string EnemyId;

	internal string PackageDirectory;

	internal CharmWitchSettings Settings;

	internal static CharmWitchRuntimeData For(string enemyId, string packageDirectory, CharmWitchSettings settings)
	{
		if (string.IsNullOrEmpty(enemyId))
		{
			return null;
		}
		if (Registry.TryGetValue(enemyId, out CharmWitchRuntimeData existing) && existing != null)
		{
			existing.PackageDirectory = packageDirectory;
			existing.Settings = settings;
			return existing;
		}
		CharmWitchRuntimeData data = CreateInstance<CharmWitchRuntimeData>();
		data.name = "CharmWitchRuntimeData_" + enemyId;
		data.hideFlags = HideFlags.HideAndDontSave;
		data.EnemyId = enemyId;
		data.PackageDirectory = packageDirectory;
		data.Settings = settings;
		Registry[enemyId] = data;
		return data;
	}

	internal static CharmWitchRuntimeData Find(string enemyId)
	{
		return string.IsNullOrEmpty(enemyId) ? null : Registry.TryGetValue(enemyId, out CharmWitchRuntimeData data) ? data : null;
	}
}

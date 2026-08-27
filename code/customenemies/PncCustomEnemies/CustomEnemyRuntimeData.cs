using System;
using System.Collections.Generic;
using UnityEngine;

namespace PncEdi;

// Unity 6000.3.11f1 (Mono, this build) does not copy serialized fields whose type is a custom
// [Serializable] class when a runtime-prepared GameObject is cloned: Object.Instantiate hands
// the clone null for those fields while engine references (Sprite[], SpriteRenderer, bools)
// come through intact. Verified in-game with a probe component: a Sprite[] field survived with
// its entry while two custom-class fields on the same component arrived null.
//
// Custom enemies build their whole configuration at runtime and are then cloned by the game's
// spawners, the debug spawner and the gallery, so every clone would lose the witch settings and
// the sprite animation set - exactly the "static sprite, no charm circle, no dream bubbles"
// failure. The data therefore travels inside a runtime ScriptableObject: only the reference
// crosses the clone boundary, and the object itself is never cloned.
internal sealed class CustomEnemyRuntimeData : ScriptableObject
{
	private static readonly Dictionary<string, CustomEnemyRuntimeData> Registry = new Dictionary<string, CustomEnemyRuntimeData>(StringComparer.OrdinalIgnoreCase);

	internal string EnemyId;

	internal string PackageDirectory;

	internal CustomEnemySpriteVisual SpriteVisual;

	internal CustomEnemyWitchBehaviour Witch;

	internal RuntimeSpriteAnimationData[] Animations = Array.Empty<RuntimeSpriteAnimationData>();

	internal static CustomEnemyRuntimeData For(CustomEnemyDefinition definition)
	{
		if (definition == null)
		{
			return null;
		}
		if (Registry.TryGetValue(definition.Id, out CustomEnemyRuntimeData existing) && existing != null)
		{
			return existing;
		}
		CustomEnemyRuntimeData data = CreateInstance<CustomEnemyRuntimeData>();
		data.name = "CustomEnemyRuntimeData_" + definition.Id;
		data.hideFlags = HideFlags.HideAndDontSave;
		data.EnemyId = definition.Id;
		data.PackageDirectory = definition.Directory;
		data.SpriteVisual = definition.Manifest.spriteVisual;
		data.Witch = definition.Manifest.witch;
		Registry[definition.Id] = data;
		return data;
	}

	// Both holders keep the object alive; this one exists so the dictionary itself is not the
	// only root after a definition is reloaded for a different template instance.
	internal static CustomEnemyRuntimeData Find(string enemyId)
	{
		return string.IsNullOrEmpty(enemyId) ? null : Registry.TryGetValue(enemyId, out CustomEnemyRuntimeData data) ? data : null;
	}
}

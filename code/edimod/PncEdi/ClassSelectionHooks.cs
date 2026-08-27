using System.Collections.Generic;
using HarmonyLib;
using UnityEngine;
using UnityEngine.UI;

namespace PncEdi;

[HarmonyPatch]
public static class ClassSelectionHooks
{
	private static float GetArmorHeatBonus(ClassSelectionUI ui, PlayerClass playerClass)
	{
		return Traverse.Create((object)ui).Method("GetArmorHeatBonus", new object[1] { playerClass }).GetValue<float>();
	}

	[HarmonyPatch(typeof(ClassSelectionUI), "CalculateBarNormalizationValues")]
	[HarmonyPostfix]
	public static void CalculateBarNormalizationValues_Postfix(ClassSelectionUI __instance)
	{
		Traverse traverse = Traverse.Create((object)__instance);
		List<PlayerClass> classes = traverse.Field("availableClasses").GetValue<List<PlayerClass>>();
		if (classes == null)
		{
			return;
		}
		float maxCapacity = 0f;
		foreach (PlayerClass playerClass in classes)
		{
			if (!(playerClass == null))
			{
				float armorHeatBonus = GetArmorHeatBonus(__instance, playerClass);
				float effectiveHeatCapacity = ClassHeatMultipliers.GetEffectiveHeatCapacity(playerClass, armorHeatBonus);
				if (effectiveHeatCapacity > maxCapacity)
				{
					maxCapacity = effectiveHeatCapacity;
				}
			}
		}
		traverse.Field("maxEffectiveHeat").SetValue((object)maxCapacity);
	}

	[HarmonyPatch(typeof(ClassSelectionUI), "DisplayClassDetails")]
	[HarmonyPostfix]
	public static void DisplayClassDetails_Postfix(ClassSelectionUI __instance, PlayerClass playerClass)
	{
		if (!(playerClass == null))
		{
			float armorHeatBonus = GetArmorHeatBonus(__instance, playerClass);
			float effectiveHeatCapacity = ClassHeatMultipliers.GetEffectiveHeatCapacity(playerClass, armorHeatBonus);
			Traverse traverse = Traverse.Create((object)__instance);
			float maxEffectiveHeat = traverse.Field("maxEffectiveHeat").GetValue<float>();
			Image heatBarFill = traverse.Field("heatBarFill").GetValue<Image>();
			if (heatBarFill != null)
			{
				heatBarFill.fillAmount = ((maxEffectiveHeat > 0f) ? (effectiveHeatCapacity / maxEffectiveHeat) : 1f);
			}
			object heatValueText = traverse.Field("heatValueText").GetValue<object>();
			if (heatValueText != null)
			{
				Traverse.Create(heatValueText).Property("text", (object[])null).SetValue((object)Mathf.RoundToInt(effectiveHeatCapacity).ToString());
			}
		}
	}

	[HarmonyPatch(typeof(ClassSelectionUI), "GetClassStatsText")]
	[HarmonyPostfix]
	public static void ClassSelection_GetClassStatsText_Postfix(PlayerClass playerClass, ref string __result)
	{
		AppendHeatModLine(playerClass, ref __result);
	}

	[HarmonyPatch(typeof(ItemUnlocksScreenUI), "GetClassStatsText")]
	[HarmonyPostfix]
	public static void ItemUnlocks_GetClassStatsText_Postfix(PlayerClass playerClass, ref string __result)
	{
		AppendHeatModLine(playerClass, ref __result);
	}

	private static void AppendHeatModLine(PlayerClass playerClass, ref string stats)
	{
		if (!(playerClass == null))
		{
			float multiplier = ClassHeatMultipliers.GetMultiplier(playerClass.className);
			if (!(multiplier <= 1.0001f))
			{
				int capacity = Mathf.RoundToInt(ClassHeatMultipliers.GetVanillaHeatCapacity(playerClass) * multiplier);
				stats += $"\n<b>Max Heat (EDI ×{multiplier:G}):</b> {capacity}\n";
			}
		}
	}
}

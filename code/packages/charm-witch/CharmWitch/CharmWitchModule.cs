using System;
using PncCustomEnemies.Api;
using UnityEngine;

namespace CharmWitch;

/// <summary>
/// The package's entry point, named by its manifest's `"assembly": { "module": "CharmWitch.CharmWitchModule" }`.
///
/// It does one thing: publish the `charm-witch` behaviour by name. **That name is the whole point of
/// publishing rather than attaching.** This assembly ships inside the femboy-witch package, but the
/// behaviour it carries belongs to anyone: another package writes `"behaviour": "charm-witch"` in a
/// plain `enemy.json`, with its own art and its own tuning, and gets a charm-circle boss without a
/// compiler anywhere in sight. Before §165 that was true because the behaviour was compiled into the
/// framework; it stays true now because a behaviour is installed once and reachable by name.
///
/// A manifest that names the behaviour when this package is not installed is not a crash: the
/// framework logs which behaviour was wanted and loads the enemy as a plain reskin.
/// </summary>
public sealed class CharmWitchModule : IPackageModule, IPackageBehaviourFactory
{
	public const string BehaviourName = "charm-witch";

	private PackageContext _context;

	public void Initialize(PackageContext context)
	{
		_context = context;
		context.RegisterBehaviour(BehaviourName, this);
	}

	public void Attach(GameObject template, PackageBehaviourRequest request)
	{
		// The settings block is the manifest object named after the behaviour. `witch` is read as
		// well, because that is what the manifests written before §165 call it and a package that
		// still says `witch` is not wrong - it is old, and breaking it would be this seam's first
		// act rather than its last resort.
		string json = request.SettingsJson ?? ExtractObject(request.ManifestJson, "witch");
		if (string.IsNullOrWhiteSpace(json))
		{
			request.Log?.LogWarning("[CharmWitch] '" + request.Id + "' asked for the " + BehaviourName +
				" behaviour but its manifest has no \"" + BehaviourName + "\" (or legacy \"witch\") block - nothing to tune it with, so it is not attached.");
			return;
		}
		CharmWitchSettings settings = JsonUtility.FromJson<CharmWitchSettings>(json);
		if (settings == null)
		{
			request.Log?.LogError("[CharmWitch] '" + request.Id + "': the " + BehaviourName + " block could not be read as settings");
			return;
		}
		// Unity 6's JsonUtility can leave a nested array at its field initializer, which is the
		// same fallback the framework's own manifest reader keeps for the same reason.
		if (settings.dreamVideos == null || settings.dreamVideos.Length == 0)
		{
			settings.dreamVideos = ExtractStringArray(json, "dreamVideos");
		}
		if (settings.dreamVideos == null || settings.dreamVideos.Length == 0)
		{
			// A package that lists its videos once, under the framework's own `galleryVideos`, is
			// the shape to write today: the gallery plays them with this package's code switched
			// off, and the behaviour reads the same list rather than the manifest carrying two.
			settings.dreamVideos = ExtractStringArray(ExtractObject(request.ManifestJson, "galleryVideos"), "files");
		}
		CharmWitchRuntimeData.For(request.Id, request.Directory, settings);
		CharmWitchController.Attach(template, request.Directory, settings, request.Id);
	}

	// A package parses its own vocabulary. These two are the smallest readers that do it without
	// dragging a JSON library into a package that ships beside a game.
	private static string ExtractObject(string json, string field)
	{
		if (string.IsNullOrEmpty(json)) return null;
		int key = json.IndexOf("\"" + field + "\"", StringComparison.OrdinalIgnoreCase);
		int start = key < 0 ? -1 : json.IndexOf('{', key);
		if (start < 0) return null;
		bool inString = false, escaped = false;
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

	private static string[] ExtractStringArray(string json, string field)
	{
		if (string.IsNullOrEmpty(json)) return Array.Empty<string>();
		int key = json.IndexOf("\"" + field + "\"", StringComparison.OrdinalIgnoreCase);
		int start = key < 0 ? -1 : json.IndexOf('[', key);
		if (start < 0) return Array.Empty<string>();
		int end = json.IndexOf(']', start);
		if (end < 0) return Array.Empty<string>();
		string body = json.Substring(start + 1, end - start - 1);
		System.Collections.Generic.List<string> values = new System.Collections.Generic.List<string>();
		bool inString = false, escaped = false;
		System.Text.StringBuilder current = new System.Text.StringBuilder();
		foreach (char c in body)
		{
			if (inString)
			{
				if (escaped) { current.Append(c); escaped = false; }
				else if (c == '\\') escaped = true;
				else if (c == '"') { inString = false; values.Add(current.ToString()); current.Length = 0; }
				else current.Append(c);
				continue;
			}
			if (c == '"') inString = true;
		}
		return values.ToArray();
	}
}

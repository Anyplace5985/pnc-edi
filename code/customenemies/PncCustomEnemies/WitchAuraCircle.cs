using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace PncEdi;

// The charm circle is the witch's readable tell: the player has to see where the aura ends before
// stepping into it. A LineRenderer hairline is nearly invisible on a lit floor, so the ring is a
// pair of ground-projected rune discs plus a scan ring that rises through the field to give it
// volume, and an arc that fills as the next horny lock charges.
internal sealed class WitchAuraCircle : MonoBehaviour
{
	private const int RingSegments = 72;
	private const float RiserPeriod = 2.6f;
	private const float RiserHeight = 2.3f;

	private static Texture2D _runeTexture;
	private static Texture2D _glyphTexture;
	private static Mesh _discMesh;

	private Transform _owner;
	private float _radius;
	private Transform _runeDisc;
	private Transform _glyphDisc;
	private Material _runeMaterial;
	private Material _glyphMaterial;
	private LineRenderer _riser;
	private LineRenderer _progressArc;
	private float _visibility;
	private float _spin;
	private float _counterSpin;
	private float _riserPhase;
	private bool _inside;
	private bool _broken;
	private float _progress;

	internal static WitchAuraCircle Create(Transform owner, float radius)
	{
		GameObject root = new GameObject("WitchCharmCircle");
		root.transform.SetParent(owner, false);
		WitchAuraCircle circle = root.AddComponent<WitchAuraCircle>();
		circle._owner = owner;
		circle._radius = Mathf.Max(0.5f, radius);
		circle.Build();
		return circle;
	}

	internal void SetState(bool inside, bool broken, float lockProgress)
	{
		_inside = inside;
		_broken = broken;
		_progress = Mathf.Clamp01(lockProgress);
	}

	private void Build()
	{
		_runeDisc = CreateDisc("CharmRunes", RuneTexture(), out _runeMaterial);
		_glyphDisc = CreateDisc("CharmGlyphs", GlyphTexture(), out _glyphMaterial);
		_riser = CreateLine("CharmRiser", RingSegments, loop: true, 0.045f);
		_progressArc = CreateLine("CharmLockCharge", RingSegments, loop: false, 0.11f);
		_progressArc.enabled = false;
	}

	private Transform CreateDisc(string name, Texture2D texture, out Material material)
	{
		GameObject disc = new GameObject(name, typeof(MeshFilter), typeof(MeshRenderer));
		disc.transform.SetParent(transform, false);
		disc.transform.localScale = new Vector3(_radius * 2f, 1f, _radius * 2f);
		disc.GetComponent<MeshFilter>().sharedMesh = DiscMesh();
		material = new Material(Shader.Find("Sprites/Default"));
		material.mainTexture = texture;
		material.renderQueue = 3000;
		MeshRenderer renderer = disc.GetComponent<MeshRenderer>();
		renderer.sharedMaterial = material;
		renderer.shadowCastingMode = ShadowCastingMode.Off;
		renderer.receiveShadows = false;
		renderer.lightProbeUsage = LightProbeUsage.Off;
		return disc.transform;
	}

	private LineRenderer CreateLine(string name, int points, bool loop, float width)
	{
		GameObject lineObject = new GameObject(name);
		lineObject.transform.SetParent(transform, false);
		LineRenderer line = lineObject.AddComponent<LineRenderer>();
		line.useWorldSpace = false;
		line.loop = loop;
		line.positionCount = points;
		line.widthMultiplier = width;
		line.numCornerVertices = 2;
		line.shadowCastingMode = ShadowCastingMode.Off;
		line.receiveShadows = false;
		line.material = new Material(Shader.Find("Sprites/Default"));
		line.material.renderQueue = 3000;
		return line;
	}

	// The ring is parented to the witch so it dies with her, but it must not inherit her facing or
	// her hover height: it is re-planted flat on the floor under her every frame.
	private void LateUpdate()
	{
		if (_owner == null)
		{
			return;
		}
		transform.rotation = Quaternion.identity;
		transform.position = GroundUnder(_owner.position);

		_visibility = Mathf.MoveTowards(_visibility, _broken ? 0f : 1f, Time.deltaTime * (_broken ? 3.5f : 2f));
		bool visible = _visibility > 0.01f;
		_runeDisc.gameObject.SetActive(visible);
		_glyphDisc.gameObject.SetActive(visible);
		_riser.enabled = visible;
		if (!visible)
		{
			_progressArc.enabled = false;
			return;
		}

		float speed = _inside ? 1.9f : 1f;
		_spin = Mathf.Repeat(_spin + Time.deltaTime * 17f * speed, 360f);
		_counterSpin = Mathf.Repeat(_counterSpin - Time.deltaTime * 26f * speed, 360f);
		_runeDisc.localRotation = Quaternion.Euler(0f, _spin, 0f);
		_glyphDisc.localRotation = Quaternion.Euler(0f, _counterSpin, 0f);

		float pulse = 0.5f + 0.5f * Mathf.Sin(Time.time * (_inside ? 6.5f : 2.6f));
		// A broken circle does not simply vanish, it gutters out: that reads as the player's doing.
		float flicker = _broken ? Mathf.Abs(Mathf.Sin(Time.time * 31f)) : 1f;
		Color idle = new Color(0.58f, 0.36f, 1f);
		Color hot = new Color(1f, 0.32f, 0.82f);
		Color tint = Color.Lerp(idle, hot, _inside ? 0.75f + pulse * 0.25f : pulse * 0.35f);
		float alpha = _visibility * flicker * (_inside ? 0.85f + pulse * 0.15f : 0.5f + pulse * 0.2f);
		_runeMaterial.color = new Color(tint.r, tint.g, tint.b, alpha);
		_glyphMaterial.color = new Color(tint.r, tint.g, tint.b, alpha * 0.75f);
		float glyphScale = _radius * 2f * (0.97f + pulse * 0.03f);
		_glyphDisc.localScale = new Vector3(glyphScale, 1f, glyphScale);

		UpdateRiser(tint, alpha, speed);
		UpdateProgressArc(hot);
	}

	// A ring sweeping up from the floor turns a flat decal into a column the player can judge from
	// any camera angle, including the ones where the floor is nearly edge-on.
	private void UpdateRiser(Color tint, float alpha, float speed)
	{
		_riserPhase = Mathf.Repeat(_riserPhase + Time.deltaTime * speed / RiserPeriod, 1f);
		float height = Mathf.Lerp(0.05f, RiserHeight, _riserPhase);
		float radius = _radius * Mathf.Lerp(1f, 0.82f, _riserPhase);
		Color color = new Color(tint.r, tint.g, tint.b, alpha * (1f - _riserPhase) * 0.8f);
		_riser.startColor = color;
		_riser.endColor = color;
		_riser.widthMultiplier = 0.04f + 0.03f * (1f - _riserPhase);
		for (int i = 0; i < _riser.positionCount; i++)
		{
			float angle = i * Mathf.PI * 2f / _riser.positionCount;
			_riser.SetPosition(i, new Vector3(Mathf.Cos(angle) * radius, height, Mathf.Sin(angle) * radius));
		}
	}

	// The arc is the lock timer made visible: one full sweep means another horny lock just landed.
	private void UpdateProgressArc(Color hot)
	{
		bool show = _inside && !_broken && _progress > 0.005f;
		_progressArc.enabled = show;
		if (!show)
		{
			return;
		}
		int points = Mathf.Clamp(Mathf.CeilToInt(_progress * RingSegments) + 1, 2, RingSegments);
		_progressArc.positionCount = points;
		float radius = _radius * 0.93f;
		float sweep = _progress * Mathf.PI * 2f;
		for (int i = 0; i < points; i++)
		{
			float angle = Mathf.PI * 0.5f - sweep * i / (points - 1);
			_progressArc.SetPosition(i, new Vector3(Mathf.Cos(angle) * radius, 0.035f, Mathf.Sin(angle) * radius));
		}
		Color color = new Color(hot.r, hot.g, hot.b, 0.5f + _progress * 0.5f);
		_progressArc.startColor = color;
		_progressArc.endColor = color;
	}

	private Vector3 GroundUnder(Vector3 position)
	{
		RaycastHit[] hits = Physics.RaycastAll(position + Vector3.up * 1.5f, Vector3.down, 6f, ~0, QueryTriggerInteraction.Ignore);
		float best = float.MaxValue;
		Vector3 result = position + Vector3.up * 0.05f;
		foreach (RaycastHit hit in hits)
		{
			if (hit.distance >= best || hit.normal.y < 0.5f || hit.collider == null || hit.collider.transform.IsChildOf(_owner))
			{
				continue;
			}
			best = hit.distance;
			result = hit.point + Vector3.up * 0.05f;
		}
		return result;
	}

	private void OnDestroy()
	{
		if (_runeMaterial != null) Destroy(_runeMaterial);
		if (_glyphMaterial != null) Destroy(_glyphMaterial);
		if (_riser != null && _riser.material != null) Destroy(_riser.material);
		if (_progressArc != null && _progressArc.material != null) Destroy(_progressArc.material);
	}

	private static Mesh DiscMesh()
	{
		if (_discMesh != null)
		{
			return _discMesh;
		}
		_discMesh = new Mesh { name = "WitchCharmCircleQuad" };
		_discMesh.vertices = new[]
		{
			new Vector3(-0.5f, 0f, -0.5f),
			new Vector3(-0.5f, 0f, 0.5f),
			new Vector3(0.5f, 0f, 0.5f),
			new Vector3(0.5f, 0f, -0.5f)
		};
		_discMesh.uv = new[] { new Vector2(0f, 0f), new Vector2(0f, 1f), new Vector2(1f, 1f), new Vector2(1f, 0f) };
		_discMesh.normals = new[] { Vector3.up, Vector3.up, Vector3.up, Vector3.up };
		_discMesh.triangles = new[] { 0, 1, 2, 0, 2, 3 };
		_discMesh.RecalculateBounds();
		return _discMesh;
	}

	private static Texture2D RuneTexture()
	{
		if (_runeTexture == null)
		{
			_runeTexture = BuildTexture("WitchCharmRunes", ShadeRunes);
		}
		return _runeTexture;
	}

	private static Texture2D GlyphTexture()
	{
		if (_glyphTexture == null)
		{
			_glyphTexture = BuildTexture("WitchCharmGlyphs", ShadeGlyphs);
		}
		return _glyphTexture;
	}

	private static float ShadeRunes(float radius, float angle)
	{
		float coverage = Band(radius, 0.965f, 0.016f);
		coverage = Mathf.Max(coverage, Band(radius, 0.885f, 0.007f) * 0.85f);
		coverage = Mathf.Max(coverage, Band(radius, 0.615f, 0.010f) * 0.7f);
		if (radius > 0.895f && radius < 0.955f)
		{
			coverage = Mathf.Max(coverage, Dashes(angle, 32, 0.4f) * 0.9f);
		}
		if (radius > 0.63f && radius < 0.875f)
		{
			coverage = Mathf.Max(coverage, Dashes(angle, 6, 0.045f) * 0.55f);
		}
		// A faint wash inside the ring so the covered floor itself reads as dangerous ground.
		return Mathf.Max(coverage, radius < 0.96f ? 0.09f * (1f - radius * 0.6f) : 0f);
	}

	private static float ShadeGlyphs(float radius, float angle)
	{
		float coverage = 0f;
		if (radius > 0.7f && radius < 0.79f)
		{
			coverage = Dashes(angle, 12, 0.55f) * 0.9f;
		}
		if (radius > 0.34f && radius < 0.52f)
		{
			coverage = Mathf.Max(coverage, Dashes(angle, 3, 0.09f) * 0.8f);
		}
		return Mathf.Max(coverage, Band(radius, 0.245f, 0.012f) * 0.6f);
	}

	private static Texture2D BuildTexture(string name, Func<float, float, float> shade)
	{
		const int size = 512;
		Texture2D texture = new Texture2D(size, size, TextureFormat.RGBA32, false)
		{
			name = name,
			wrapMode = TextureWrapMode.Clamp,
			filterMode = FilterMode.Bilinear
		};
		Color32[] pixels = new Color32[size * size];
		for (int y = 0; y < size; y++)
		{
			for (int x = 0; x < size; x++)
			{
				float nx = (x + 0.5f) / size * 2f - 1f;
				float ny = (y + 0.5f) / size * 2f - 1f;
				float radius = Mathf.Sqrt(nx * nx + ny * ny);
				float alpha = radius > 1f ? 0f : shade(radius, Mathf.Atan2(ny, nx));
				alpha *= Mathf.SmoothStep(1f, 0f, Mathf.InverseLerp(0.97f, 1f, radius));
				pixels[y * size + x] = new Color32(255, 255, 255, (byte)Mathf.Clamp(Mathf.RoundToInt(alpha * 255f), 0, 255));
			}
		}
		texture.SetPixels32(pixels);
		texture.Apply(false, true);
		return texture;
	}

	private static float Band(float radius, float center, float halfWidth)
	{
		return Mathf.SmoothStep(1f, 0f, Mathf.InverseLerp(halfWidth * 0.5f, halfWidth, Mathf.Abs(radius - center)));
	}

	private static float Dashes(float angle, int count, float duty)
	{
		float phase = Mathf.Repeat((angle + Mathf.PI) / (Mathf.PI * 2f) * count, 1f);
		return phase < duty ? 1f : 0f;
	}
}

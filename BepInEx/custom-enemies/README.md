# PncEdi custom enemies

Each package is a directory here with a manifest in it. Two kinds:

- **[CUSTOM-ENEMIES.md](CUSTOM-ENEMIES.md)** — `enemy.json`: a roaming enemy, either a clone of a
  vanilla one with new artwork and behaviour, or a complete prefab from a Unity AssetBundle.
  Includes the runtime PNG sprite-sheet format, which needs no Unity Editor, and the portal-witch
  boss behaviour.
- **[WALL-PICTURE-TRAPS.md](WALL-PICTURE-TRAPS.md)** — `wall-trap.json`: a picture that hangs itself
  on a wall and pulls the player into a scene. PNG only; no Editor either.

Both put their funscripts in `funscripts/<variant>/` beside the manifest, and both appear in the
mod manager (**F11**) under **PNC Custom Enemies → Custom Enemies**.

The `_example` directory is inert because its manifests end in `.example`. Copy it to a new
directory and rename one of them - `enemy.json.example` or `wall-trap.json.example` - to drop the
`.example`, and the package loads on the next launch.

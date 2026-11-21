# AGENTS.md

Notes for an AI coding agent (or a person) working in this repo. `CLAUDE.md` pulls this file in.

## What this is

The hub of [Lombo-Forge](https://github.com/Lombo-Forge): the Jellyfin plugin repository `manifest.json`, the shared brand
assets, and the list of tools. It holds **no app code** and no submodules; every tool lives in its own repository and works
without this one.

## Layout

| Path | What |
|---|---|
| `manifest.json` | Jellyfin plugin repository manifest. Only released plugin versions belong here. |
| `scripts/check-manifest.py` | Validates the manifest (GUIDs, four-part versions, MD5 checksums, Lombo-Forge release URLs). CI runs it. |
| `brand/` | The Lombo-Forge logo and banner, the Cinzel font, and every tool's icon and banner under `brand/apps/`. |
| `docs/branding.md` | The look (the Lombo L is in every icon) and how to render artwork. |
| `scripts/leak-check.sh` | Fails when private or personal strings appear. CI runs it. |
| `site/` | The one-page website (`index.html`, `style.css`, `assets/`). No scripts or external requests. `site/manifest.json` is generated. |
| `scripts/build-site.sh` | Copies `manifest.json` into `site/`. `.github/workflows/pages.yml` runs it and deploys on pushes to `main`. |
| `docs/site.md` | How to change the site, turn Pages on, set the domain and the manifest address (a placeholder until chosen). |
| `tests/` | `python3 -m unittest discover -s tests` |

## Rules

- **Add a plugin version to `manifest.json` only from a real release**: the zip's MD5 from `jprm`, the release URL, a
  four-part version, the Jellyfin ABI it targets. Never commit a placeholder checksum; the checker rejects it.
- When a tool gets a new icon or banner, copy it into `brand/apps/<tool>/` and keep it identical to the tool's own `assets/`.
- Never put private details in the repo: real hostnames, IPs, webhook URLs, keys, local paths.
- Plain language. Never call anything "official" or imply the Jellyfin project made it.
- Changes reach `main` through a pull request. No co-author or "generated with" lines anywhere.

## Test

```sh
python3 scripts/check-manifest.py
python3 -m unittest discover -s tests
sh scripts/leak-check.sh
```

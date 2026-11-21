# The website

A one-page static site in `site/`: plain HTML and one CSS file, no framework, no build step, no scripts, no
external requests. GitHub Pages publishes it, and it also serves the plugin repository `manifest.json` at its root.

## Contents

- [Change the page](#change-the-page)
- [Set the manifest address](#set-the-manifest-address)
- [Turn Pages on](#turn-pages-on)
- [Set the domain](#set-the-domain)
- [Checks](#checks)

## Change the page

- Edit `site/index.html` and `site/style.css`; open `site/index.html` in a browser to look at it.
- Tool cards: the icon is a copy of `brand/apps/<tool>/icon.svg` in `site/assets/apps/`. The status badge text
  comes from the tool's own README ("What is not verified"); update it when the README changes.
- Keep it light and local: no analytics, cookies, web fonts from other sites or scripts. `tests/test_site.py` fails on
  an external image, stylesheet or script, a link to a host that is not on its short allow-list, a missing file or an image without `alt`.
- The Cinzel font is `site/assets/fonts/Cinzel.ttf`, a copy of `brand/fonts/Cinzel.ttf` (SIL Open Font License).

## Set the manifest address

The address shown in "Add the plugin repository to Jellyfin" is `https://lombo-forge.github.io/lombo/manifest.json`, in one place: the `<code id="manifest-url">` element in `site/index.html`,
marked with a `MANIFEST_URL` comment. If it ever moves (a custom domain), change it there and `PLACEHOLDER_HOST` in `tests/test_site.py` (the test checks the address appears exactly once).

## Turn Pages on

1. Repository **Settings**, **Pages**, **Build and deployment**, Source: **GitHub Actions**.
2. Merge to `main`. `.github/workflows/pages.yml` runs `scripts/build-site.sh` (copies `manifest.json` into `site/`) and
   deploys `site/` with the official Pages actions. It only runs on pushes to `main` (or by hand).

`site/manifest.json` is generated and gitignored. Run `sh scripts/build-site.sh` to refresh it locally.

## Set the domain

Without a custom domain the site is at `https://lombo-forge.github.io/lombo/`. For a custom domain:

1. At the DNS provider add a `CNAME` record from the chosen name to `lombo-forge.github.io`.
2. In **Settings**, **Pages**, **Custom domain**, enter the name and enable **Enforce HTTPS** once the certificate is ready.
   With the Actions source, GitHub keeps this setting itself; a `CNAME` file in `site/` is not needed.
3. Set the manifest address (above) to `https://<the domain>/manifest.json`.

Choose the domain carefully: it ends up in every user's Jellyfin settings.

## Checks

```sh
sh scripts/build-site.sh
python3 -m unittest discover -s tests
```

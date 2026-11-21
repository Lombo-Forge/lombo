#!/bin/sh
# Prepares site/ for publishing: copies manifest.json to the site root so GitHub Pages serves it
# at <site address>/manifest.json. The copy is generated (gitignored); tests/test_site.py checks it matches.
set -eu
cd "$(dirname "$0")/.."
cp manifest.json site/manifest.json
echo "site/manifest.json updated."

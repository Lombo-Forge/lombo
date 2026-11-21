#!/usr/bin/env bash
# Contract C1 (docs/contracts.md): the real command lines of LomboShrink and LomboTier, in a throwaway folder.
# Shrink opens a session -> Tier must stand down (run and move); closed, expired -> Tier goes ahead; damaged -> stands down.
# Usage: scripts/contract-check-c1.sh [PATH_TO_LOMBO_SHRINK] [PATH_TO_LOMBO_TIER]   (default: sibling folders)
# Needs docker. Both repos are mounted read-only; nothing is written outside the container.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
shrink=$(cd "${1:-$here/../lombo-shrink}" && pwd)
tier=$(cd "${2:-$here/../lombo-tier}" && pwd)
cat > "${TMPDIR:-/tmp}/c1-inner.$$.sh" <<'INNER'
set -u
export PYTHONPATH=/s/src:/t/src PYTHONDONTWRITEBYTECODE=1
W=/tmp/c1; mkdir -p "$W/ssd/movies/A (2020)" "$W/hdd/movies" "$W/data" "$W/stage"
echo x > "$W/ssd/movies/A (2020)/a.mkv"
SESSION=$W/stage/session.json; fails=0
shrink() { LOMBO_SHRINK_SESSION_FILE=$SESSION LOMBO_SHRINK_STAGE_DIR=$W/stage python -c 'import sys;from lombo_shrink.cli import main;sys.exit(main(sys.argv[1:]))' "$@"; }
tier() { env LOMBO_TIER_JELLYFIN_URL=http://127.0.0.1:9 LOMBO_TIER_JELLYFIN_API_KEY=k LOMBO_TIER_JELLYFIN_PATH_PREFIX=/media \
  LOMBO_TIER_SSD_BRANCHES=$W/ssd LOMBO_TIER_HDD_BRANCHES=$W/hdd LOMBO_TIER_DRY_RUN=false LOMBO_TIER_CHECK_MOUNTS=false \
  LOMBO_TIER_DATA_DIR=$W/data LOMBO_TIER_SESSION_FILE=$SESSION python -c 'import sys;from lombo_tier.cli import main;sys.exit(main(sys.argv[1:]))' "$@" 2>&1; }
expect() { # label, output, pattern that must (or, with !, must not) appear
  if [ "$3" = "!" ]; then if echo "$2" | grep -q -- "$4"; then echo "FAIL $1"; fails=$((fails+1)); else echo "ok   $1"; fi
  elif echo "$2" | grep -q -- "$3"; then echo "ok   $1"; else echo "FAIL $1"; echo "$2" | tail -3; fails=$((fails+1)); fi; }
# With no session Tier gets past the check and then fails on the fake Jellyfin: that failure is the "went ahead" sign.
expect "no session: tier goes ahead" "$(tier run --no-wait)" "JellyfinError"
shrink session open 1 >/dev/null
expect "open: tier run stands down" "$(tier run --no-wait)" "a conversion session is open (held by lombo-shrink"
expect "open: tier run never reached Jellyfin" "$(tier run --no-wait)" ! "JellyfinError"
expect "open: tier move stands down" "$(tier move 'movies/A (2020)')" "a conversion session is open"
shrink session close >/dev/null
expect "closed: tier goes ahead" "$(tier run --no-wait)" "JellyfinError"
python -c "import json,time;json.dump({'version':1,'owner':'lombo-shrink','opened':1,'expires':int(time.time())-5},open('$SESSION','w'))"
expect "expired: tier goes ahead" "$(tier run --no-wait)" "JellyfinError"
echo '{oops' > "$SESSION"
expect "damaged: tier stands down" "$(tier run --no-wait)" "can't be trusted"
[ -f "$W/ssd/movies/A (2020)/a.mkv" ] && echo "ok   nothing was moved" || { echo "FAIL a file was moved"; fails=$((fails+1)); }
exit $fails
INNER
trap 'rm -f "${TMPDIR:-/tmp}/c1-inner.$$.sh"' EXIT
docker run --rm --name "lf-c1-$$" --cpus 1 --memory 512m --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$shrink:/s:ro" -v "$tier:/t:ro" -v "${TMPDIR:-/tmp}/c1-inner.$$.sh:/inner.sh:ro" python:3.12-slim bash /inner.sh

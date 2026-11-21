# Contracts between the apps

## Contents

- [How to read this page](#how-to-read-this-page)
- [C1: the conversion session file](#c1-the-conversion-session-file)
- [C2: tiers.json](#c2-tiersjson)
- [C3: leaving.json and the keep endpoint](#c3-leavingjson-and-the-keep-endpoint)
- [C4: the post-swap command](#c4-the-post-swap-command)
- [Changing a contract](#changing-a-contract)

## How to read this page

Some apps need to cooperate without sharing code. Each hand-off is a small, versioned JSON file or one HTTP call. This
page is the short version. The full field tables live in the app that owns the contract, and that app's page wins if
the two ever differ:

- [LomboTier contracts](https://github.com/Lombo-Forge/lombo-tier/blob/main/docs/contracts.md)
- [LomboFarewell contracts](https://github.com/Lombo-Forge/lombo-farewell/blob/main/docs/contracts.md)
- LomboShrink: the session file and the command setting are described in its README and `.env.example`.

Rules that hold for every file below: it has a `version`; a reader ignores fields it does not know; a reader that sees
a version it does not know does nothing instead of guessing; a writer replaces the file atomically (write a temporary
file, then rename it).

## C1: the conversion session file

**Who:** LomboShrink writes it, LomboTier reads it (any other mover may read it too).
**What:** while Shrink is replacing files in the library, nothing else should be moving them.

```json
{"version": 1, "owner": "lombo-shrink", "opened": 1767225600, "expires": 1767229200}
```

Readers need only `version`, `owner` (not empty) and `expires` (unix seconds). `opened` is for people.

| The file is | A reader |
|---|---|
| missing | goes ahead |
| valid and `expires` is in the future | stands down and says who holds it. Not an error |
| valid and `expires` has passed | goes ahead, because a crashed writer must not block moves forever |
| unreadable (not JSON, unknown version, no owner, no `expires`) | stands down and reports a failure. A lock nobody can read is never read as closed |

Setup: both apps must see the same file, so put it in a folder both containers mount. Set `LOMBO_SHRINK_SESSION_FILE`
for Shrink and `LOMBO_TIER_SESSION_FILE` for Tier to that one path. Shrink opens and closes it with
`lombo-shrink session open [HOURS]` and `session close`. Tier never writes it.

**Tested together:** `scripts/contract-check-c1.sh` runs the real command line of both apps in a throwaway folder
(open, `run` and `move` stand down, close, expired file, damaged file). It passed on 2026-11-21 with Shrink 0.1.3 and
Tier at the version that added the check. It uses a fake Jellyfin address, so it proves the stand-down, not a real move.

## C2: tiers.json

**Who:** LomboTier writes it (in `LOMBO_TIER_DATA_DIR`), anything may read it: a storage-tag plugin, a dashboard.
**What:** where each movie folder or show-season folder lives.

```json
{"version": 1, "updated": 1767225600,
 "units": [{"path": "movies/Jaws (1975)", "tier": "ssd", "bytes": 4294967296, "pinned": true}]}
```

`tier` is `"ssd"` or `"hdd"`; `path` is relative to the pool root. The file can be a day old: use `updated` to judge.
The pin list that feeds `pinned` is `{"version": 1, "titles": [...]}`, written by `lombo-tier pin add`.

## C3: leaving.json and the keep endpoint

**Who:** LomboFarewell writes `leaving.json` and serves the same document and a keep call over HTTP.
**What:** the list of titles about to be deleted, and a way to postpone one.

- `leaving.json` (next to Farewell's state file) and `GET /v1/leaving` return
  `{"version": 1, "updated": <unix>, "entries": [{"id", "title", "days_left", "can_keep"}]}`, soonest first.
- `POST /v1/keep` with body `{"title": "..."}` runs the same check as `lombo-farewell keep`. It answers
  `{"ok": true|false, "message": "..."}`: 200 done, 422 refused by a rule, 502 an upstream problem.
- Every request needs `Authorization: Bearer <token>`. The server listens on loopback by default and sends no CORS
  headers, so a browser page must reach it through the owner's own reverse proxy, which adds the token. After 10 bad
  tries in a minute from one address it answers 429.

Nothing here has been tried against a real browser client yet.

## C4: the post-swap command

**Who:** LomboShrink runs it, anything can be the command.
**What:** a way to react after files were replaced, for example to rescan a title in Sonarr or Radarr.

`LOMBO_SHRINK_POST_SWAP_COMMAND` is split like a shell would, but started **without** a shell. It runs once after a
real swap (never in a dry run, never when nothing was swapped), with `LOMBO_SHRINK_SWAPPED_JSON` in its environment: a
JSON list of the swapped file paths. It gets no input, a 60 second limit, and its output is dropped. A failure is
a note on the result, never a failed swap.

Not built yet: the same kind of command for LomboTier or LomboFarewell. None of them has one today.

## Changing a contract

Adding an optional field is not a change. Renaming or removing a field, or changing what it means, raises `version`;
the owning app's page then lists the old and new shape and the release notes say so. Change the owning app's page and
this one in the same round, and re-run `scripts/contract-check-c1.sh` after touching C1.

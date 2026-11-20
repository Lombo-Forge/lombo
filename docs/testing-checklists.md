# Testing checklists

What has not been proven yet, and how to prove it on a real machine. Each tool's README has the full
"what is not verified" list; this is the short version to work through. Dry run is the default everywhere, so
start with `doctor` and `plan` and read the output before turning `DRY_RUN` off. Report results as an issue in the
tool's repository: what you ran, what you expected, what happened.

## Contents

- [LomboShrink](#lomboshrink)
- [LomboNudge](#lombonudge)
- [LomboNap](#lombonap)
- [LomboTier](#lombotier)
- [LomboShelf](#lomboshelf)

## LomboShrink

Needs: a main PC with a discrete graphics card, an ffmpeg that has its H.265 encoder, a small test library.

1. `pip install .`, copy `.env.example` to `.env`, point `LIBRARY_DIR` at a **copy** of a few files, `OUT_DIR` at a fast local folder.
2. `lombo-shrink doctor`: the encoder you chose (`nvenc`, `amf`, `qsv`, `videotoolbox`) must pass its one-second test encode.
   Pass: `[ok]` for the encoder. Fail on AMD, Intel or macOS is expected to need a settings fix: attach the ffmpeg error.
3. `lombo-shrink candidates`, then `plan`: the list matches what you expect; hard-linked (seeded) files are left out.
4. `lombo-shrink run` on one small file. Pass: an H.265 file appears in `OUT_DIR`, smaller, same length, audio and subtitles kept,
   and it plays.
5. The swap (the dangerous part): do it only against the **copy** library first. `swap` without `--apply` prints the plan;
   with `--apply`, `DRY_RUN=false` and an open session it replaces the original. Check the original is gone only after the
   new file verified, and that a second run changes nothing.
6. Try it on Windows once (paths, keep-awake, the mapped network drive).

## LomboNudge

Needs: a Seerr, Sonarr and Radarr you can read from (read-only keys are enough for `plan`).

1. `lombo-nudge doctor`: every service reports `[ok]`.
2. `lombo-nudge plan` with at least one approved-but-missing request. Pass: each stuck request has a reason that is true.
3. Compare each reason with what Sonarr or Radarr shows. Note any wrong one. Least certain: the Jellyfin lookup (unset the
   Jellyfin settings if it errors), "quality blocked" (guessed from message text) and 4K.
4. Webhook: set `WEBHOOK_URL` to a Discord or Slack test channel and `run` once with `DRY_RUN=false`. Pass: one message.
5. `retry ID` only on a request you are happy to re-search. It removes and blocklists downloads; read its dry-run first.

## LomboNap

Needs: a Jellyfin server and a real client left playing, ideally two different client types (TV app, phone, browser).

1. Make an API key, `lombo-nap doctor`: `[ok]`.
2. `lombo-nap plan` while something plays. Pass: the session is listed with its episode count.
3. Set a low `LIMIT_HOURS` (or episodes) and `DRY_RUN=false`. Watch what each client does with the message, the stop and the go-home
   command. This is the main unknown: write down which clients obey which.
4. Wake report (needs root for the full detail): `lombo-nap wake doctor`, then run the sampler for a day (the systemd timer in
   `examples/`), then `lombo-nap wake report`. Pass: it lists wake events and names a plausible cause.

## LomboTier

Needs: a mergerfs pool with an SSD and an HDD branch, and Jellyfin watch data.

1. `lombo-tier doctor` then `plan`: nothing moves in dry run; the plan lists movies and seasons to demote or promote.
2. Try the real move on a test folder only: a small title on the pool, `DRY_RUN=false`, `lombo-tier move "<name>"`. Pass: the
   folder is on the other branch, hashes verified, and the pool path still shows it (no gap for a viewer).
3. Check the quiet-HDD index: a second `plan` should not wake the HDD.

## LomboShelf

Needs: Jellyfin 12.4 with the File Transformation plugin installed, on a test server (not your main one first).

1. Build the plugin (`plugin/`, see the repo's README) and put it in Jellyfin's plugin folder, then restart.
2. Dashboard > Plugins: LomboShelf appears and its settings page opens. The log shows the File Transformation registration
   (or a warning that it failed: attach the log).
3. Open the web client: the shelf rows, genre rows and theme appear on desktop, phone and a TV browser. View the Home page and
   check nothing else is broken (open a movie, search, the player).
4. Uninstall the plugin: the web client returns to normal.

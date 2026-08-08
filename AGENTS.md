# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
- Single product: `bot.py` — a Telethon-based Telegram bot that posts advertising messages to a target group on a loop, plus a small `aiohttp` keep-alive HTTP server. There is no database, frontend, or other internal service.
- `requirements.txt` holds the only dependencies (`telethon`, `aiohttp`). Dependency install is handled by the startup update script; no manual install is needed in a fresh cloud session.
- `arven_sole_tracks/` contains only `.mp3` audio assets and is unrelated to the code — no build/run step touches it.

### Running
- Run the app with `python3 bot.py` (entry point is `asyncio.run(ana_sistem())`). It concurrently starts the keep-alive web server and the Telegram bot loop.
- The keep-alive HTTP server listens on `0.0.0.0:8080` by default; override with the `PORT` env var. Verify it with `curl http://localhost:8080/` which returns `ParaXTR Botu aktif ve calisiyor.`. This is the only part that can be exercised end-to-end without external credentials.

### Non-obvious caveats
- The `api_id`/`api_hash`/`bot_token` are hardcoded in `bot.py`, and the committed `bot_token` is rejected by Telegram (`The provided token is not valid`). As a result the bot loop never authenticates and never sends messages — it just retries every 30s. Live message-sending cannot be tested without a valid bot token and a group the bot is authorized to post in.
- The bot loop swallows all exceptions and retries forever every 30s, so a failing Telegram connection will not crash the process; the web server stays up regardless.
- There are no automated tests, no linter config, and no build step in this repo.

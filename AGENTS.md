# spotifio

## Binding rules

- **No default network endpoints.** No default port, no default redirect URI, no
  fallback host. Anything that must match a third-party setting exactly comes from
  an argument or an env var, else raise. Enforced in `spotifio/oauth.py`
  (`TokenHandler.__init__`, `require_env` in `spotifio/env.py`): `ValueError` when a
  value is missing, when the URI has no explicit port or non-http scheme, or when the
  host is `localhost`.
- **Public library: do not break downstream users.** Positional and keyword arguments
  keep working; `load_dotenv()` stays opt-in; `SpotifyError` subclasses `Exception`
  and keeps its message shape (`Request failed with status N: ...`). Never invent a
  class name in a message: `Client` / `RequestHandler` / `TokenHandler`. Breaking
  changes go in the PR body, not in repo files.
- **Never commit credentials or account config.** `SPOTIFIO_CLIENT_ID`,
  `SPOTIFIO_CLIENT_SECRET`, `SPOTIFIO_REDIRECT_URI` live in `.env` (gitignored, mode
  600, copy `.env.example`). No key, token, or `db/` output in any commit or PR body.
  New config values go in `.env` and `.env.example` in the same commit, never
  hardcoded.
- **Docs first.** Resolve endpoint questions from
  https://developer.spotify.com/documentation/web-api before changing code. No
  scripts that sweep dozens of endpoints from the maintainer's IP. A request is
  allowed only when it is read-only, needed for one claim, and few in number.
- **Read-only endpoints only.** No library, playlist, follow, or playback mutation
  against the maintainer's account.
- **Library only in the repo.** No diagnostic scripts or probes. Debugging lives in
  `/tmp/spotifio-scratch/`.
- **Repo text stays minimal.** Docstrings, comments, README and config samples carry
  what a caller needs to use the code. History, dates, changelog quotes, advisories
  and verification notes go in the commit message and the PR body.
- **Behaviour gets a test in the same commit.** `python -m pytest` needs no
  credentials and makes no request outside 127.0.0.1. CI runs it on 3.10-3.14 per
  pull request. `requirements.txt` holds the aiohttp floor as a security floor:
  lowering it needs an explicit reason in the PR body.
- **Verify by reading back.** `gh api -f body=@file` posts the literal `@file`; use
  `jq -Rs '{body: .}' file | gh api --input -`, then `gh pr view --json body`. Build
  URLs as `base + "/" + path.lstrip('/')`: Spotify answers 410 for a malformed path
  and that is your bug.
- **Git.** Branch off `origin/master`, never commit to `master`, one scope per branch,
  push and open a PR when work is done.

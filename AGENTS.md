# spotifio

## Binding rules

- **No default network endpoints in code.** No default port, no default
  redirect URI, no fallback host. A value that has to match a third-party
  setting exactly must be supplied by the caller (argument or env var) or the
  code raises immediately. Silent defaults here produce third-party errors the
  user has to debug.
  - Enforced in `spotifio/oauth.py` (`TokenHandler.__init__`): each value is
    `argument or require_env("SPOTIFIO_…")`; `self.host`/`self.port` come
    straight from `urlparse(redirect_uri)`; `ValueError` when a value is
    missing, when the URI has no explicit port or non-http scheme, or when the
    host is `localhost`. Helpers in `spotifio/env.py` (`require_env`,
    `load_dotenv`).
- **Public library: do not break downstream users.** Explicit positional and
  keyword arguments must keep working (`spotifio/env.py` is consulted only when
  an argument is absent); `load_dotenv()` is opt-in so importing spotifio never
  reads a file behind the caller's back; `SpotifyError` subclasses `Exception`
  and keeps the old message wording (`Request failed with status N: ...`). Any
  unavoidable breaking change is listed under "Breaking changes" in README and
  in the PR body. Never invent a class name in an error message — `Spotify()`
  does not exist; it is `Client` / `RequestHandler` / `TokenHandler`.
- **Never commit credentials or account-specific config.** `SPOTIFIO_CLIENT_ID`,
  `SPOTIFIO_CLIENT_SECRET` and `SPOTIFIO_REDIRECT_URI` live in `.env`
  (gitignored, mode 600; copy `.env.example`). A `.env` whose last line has no
  newline glues the last two variables onto one line: `spotifio.load_dotenv()`
  now rejects such a line with `path:lineno` instead of storing a broken secret.
  No key, token, or `db/` output in any commit or PR body. New config values go
  in `.env`, never hardcoded in the library, and are added to `.env.example` in
  the same commit.
- **Test only read-only endpoints.** No library, playlist, follow, or playback
  mutations against the maintainer's personal account.
- **Docs first, never probe in the dark.** Resolve every endpoint question from
  the official docs — https://developer.spotify.com/documentation/web-api — the
  endpoint reference and the changelog
  (`/documentation/web-api/changelog`) — and read those pages before changing
  code. Running a script that hits dozens of endpoints to see which answer 404
  is forbidden: it looks like scraping or API enumeration from the maintainer's
  own IP and risks rate limits or a ban. A request is allowed only when it is
  read-only, needed for one specific claim being tested, and few in number.
- **Repo contains the library only.** No diagnostic scripts, OAuth probes, or
  helper tooling in the repo — the maintainer does not want it. Any debugging
  script lives outside the repo (e.g. `/tmp/spotifio-scratch/`).
- **Behaviour gets a test in the same commit.** `python -m pytest` runs the
  suite; it needs no Spotify credentials, no real network and no outbound
  requests (only 127.0.0.1 loopback servers), so it never touches the account
  rules above. CI runs it on Python 3.10-3.14 for every pull request.
  `requirements.txt` holds the aiohttp floor because older aiohttp is
  vulnerable (CVE-2026-111064, CVE-2026-69244): lowering it needs an explicit
  reason in the PR body.
- **Verify your own work by reading it back.** `gh api -f body=@file` posts the
  literal string `@file`; use `jq -Rs '{body: .}' file > /tmp/in.json` with
  `gh api --input /tmp/in.json`, then confirm with `gh pr view --json body`.
  Build test URLs as `base + "/" + path.lstrip('/')`: Spotify answers **410 for
  a malformed request path**, and that 410 is your bug, not Spotify's.
- Git: branch off `origin/master`, never commit to `master`, one scope per
  branch, push and open a PR when work is done.

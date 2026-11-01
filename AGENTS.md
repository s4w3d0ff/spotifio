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
  (gitignored, mode 600, file must end with a newline or the last two
  variables get glued into one). No key, token, or `db/` output in any commit
  or PR body. New config values go in `.env`, never hardcoded in the library.
- **Test only read-only endpoints.** No library, playlist, follow, or playback
  mutations against the maintainer's personal account.
- **Repo contains the library only.** No diagnostic scripts, OAuth probes, or
  helper tooling in the repo — the maintainer does not want it. Any debugging
  script lives outside the repo (e.g. `/tmp/spotifio-scratch/`).
- **Verify your own work by reading it back.** `gh api -f body=@file` posts the
  literal string `@file`; use `jq -Rs '{body: .}' file > /tmp/in.json` with
  `gh api --input /tmp/in.json`, then confirm with `gh pr view --json body`.
  Build test URLs as `base + "/" + path.lstrip('/')`: Spotify answers **410 for
  a malformed request path**, and that 410 is your bug, not Spotify's.
- Git: branch off `origin/master`, never commit to `master`, one scope per
  branch, push and open a PR when work is done.

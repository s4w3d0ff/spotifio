# spotifio

## Binding rules

- **No default network endpoints in code.** No default port, no default
  redirect URI, no fallback host. A value that has to match a third-party
  setting exactly must be supplied by the caller (argument or env var) or the
  code raises immediately. Silent defaults here produce third-party errors the
  user has to debug.
  - Enforced in `spotifio/oauth.py`: `redirect_uri` is a required positional
    argument of `TokenHandler.__init__`; `self.host`/`self.port` come straight
    from `urlparse(redirect_uri)`; `ValueError` when it is missing, has no
    explicit port, or uses host `localhost`.
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
- Git: branch off `origin/master`, never commit to `master`, one scope per
  branch, push and open a PR when work is done.

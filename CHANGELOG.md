# Changelog

## 0.2.0

Adapts spotifio to Spotify's 2025-2026 API changes. Endpoint facts come from
the Web API reference and changelog, not from guessing which endpoints still
answer.

### Breaking

- `redirect_uri` has no default and is required (argument or
  `SPOTIFIO_REDIRECT_URI`). The old default `http://localhost:8888/callback`
  was already dead: Spotify rejects `localhost` as a redirect host, so anyone
  using it was getting `redirect_uri: Not matching configuration`.
- `client_id` and `client_secret` are required. They used to be accepted as
  absent, with the failure appearing later as an opaque `401`.
- A missing or invalid value now raises `ValueError` when the instance is
  created, naming the argument and the environment variable. A redirect URI
  without an explicit port, or with host `localhost`, is rejected for the same
  reason.
- Failed requests raise `spotifio.SpotifyError` instead of a plain
  `Exception`. It subclasses `Exception` and keeps the old message text
  (`Request failed with status 404: ...`), so `except Exception` and handling
  that matches on the message keep working. It is exported from the package
  root (`from spotifio import SpotifyError`) and lives in `spotifio/errors.py`,
  so `from spotifio.client import SpotifyError` no longer works.
- Python 3.10 is the minimum and `aiohttp>=3.14.4` is required. The old pair
  (`python_requires>=3.7`, `aiohttp>=3.8.0`) was unsatisfiable: aiohttp 3.8
  does not install on Python 3.12 or newer. The aiohttp floor is also a
  security floor, see below.
- A scope check raises `spotifio.ScopeError` instead of a bare `Exception`.
- A success answer that is not JSON returns `bytes`. It used to return the
  aiohttp response object after the response had already been closed.
- A failed or impossible token refresh raises `SpotifyError` and names
  `login(reauth=True)`. It used to fall back to the interactive browser flow,
  which waits forever in a headless process.
- `load_dotenv()` raises on a line that is not `KEY=VALUE`, on an invalid
  variable name, on an unclosed quote, and on two variables glued onto one
  line. It used to accept them and store the junk.
- Requests share one aiohttp session that must be closed: `await client.close()`
  or `async with client:`.

### Changed

- Scope checks use the scopes Spotify granted the token (the `scope` field of
  the token response) instead of only the list passed to the constructor. A
  call that used to be blocked locally goes through when the token really has
  the scope.
- A 403, 404 or 410 on an endpoint the docs no longer offer names the
  documented replacement in the error message.
- The endpoint table keeps the three states the docs use apart: a `[DEPRECATED]`
  banner on the four `/playlists/{id}/tracks` variants, `[REMOVED]` in the
  February 2026 changelog for Development Mode apps, and endpoints whose pages
  still exist with no banner but which are absent from the list of endpoints that
  remain available. The follow endpoints now name `/me/library` and
  `GET /me/library/contains` as their replacement instead of "none documented",
  and each batch lookup names the single-item form that stays available
  (`GET /tracks` to `GET /tracks/{id}`).
- Method docstrings say which of those states applies to the endpoint they call,
  along with the 403 rule on `GET /playlists/{id}/items` (it answers for the
  playlist owner and its collaborators only), the 40-URI limit and URI-not-id form
  of the `/me/library` endpoints, and the documented `GET /search` limit range
  (0-10, default 5). There is no documented `GET /me/library` read endpoint, so
  reading your library stays per type.
- Reading your own library (`GET /me/tracks` and friends) is documented as
  valid and is unchanged; the deprecated save/remove/contains variants are
  still called, they are only reported more clearly.
- Retrying is bounded by `RequestHandler.MAX_ATTEMPTS` (6) in a loop instead of
  recursion, and the raised `SpotifyError` carries the last status Spotify
  actually sent instead of an invented status 0 after one attempt too many.
- A scope requirement may be a tuple, meaning any one of those scopes is enough.
  Playlist reads need no local check at all, and playlist writes accept the
  public or the private scope, matching what Spotify itself accepts.
- `login()` refreshes a saved token that is already expired before it returns, so
  the first request no longer goes out with an expired token and has to be retried
  after a 401.
- The scope check follows the scopes the token response reports. A refresh can
  report more scopes than the request asked for, and that is Spotify's answer.
- The token file is created `0600` through a temporary file in the same
  directory and renamed into place, instead of being written with umask
  permissions and chmodded afterwards. A directory spotifio creates is `0700`,
  and a symlink at the token path is replaced rather than followed.
- `stop()` on a `TokenHandler` that never logged in no longer raises, and it
  cancels the refresh task instead of waiting 15 seconds for a task that does
  not exist.
- Waiting for the authorization code is bounded by
  `TokenHandler.AUTH_CODE_TIMEOUT_SECONDS` (300) and the callback port is
  released whichever way the wait ends.
- The package is split: `spotifio/request.py` (HTTP and scopes),
  `spotifio/errors.py`, `spotifio/scopes.py`, `spotifio/deprecations.py` and one
  module per endpoint group. `Client` keeps every method it had.
- `requirements.txt` is the only dependency list; `setup.py` reads it.

### Added

- `spotifio.load_dotenv()` — opt-in, importing the library reads no file.
- Environment fallbacks: `SPOTIFIO_CLIENT_ID`, `SPOTIFIO_CLIENT_SECRET`,
  `SPOTIFIO_REDIRECT_URI`, `SPOTIFIO_SCOPES`. Arguments always win.
- Methods for the documented replacement endpoints: `save_library_items`,
  `remove_library_items`, `check_saved_items`, `get_playlist_items`,
  `add_playlist_items`, `remove_playlist_items`, `update_playlist_items`.
- `Client.login(reauth=True)` to authorize again for a different scope list.
- `SpotifyError.status`, `.reason`, `.body`.
- A machine readable reason in a failure body is appended to `SpotifyError.reason`
  (`{"error":{"status":429,"message":"Too many requests","reason":"QUOTA_EXCEEDED"}}`
  reads `Too many requests (QUOTA_EXCEEDED)`).
- The token file is written `0600` (it was group-readable).
- `.env.example` documents the four variables, with the format each needs.
- `spotifio.ScopeError`, `Client.close()`, and using a client as an async
  context manager.
- A test suite (`tests/`, `python -m pytest`) and a CI workflow that runs it on
  Python 3.10 through 3.14 for every pull request. Previously the only workflow
  was the PyPI release.

### Security

`aiohttp>=3.14.4` blocks CVE-2026-111064 / GHSA-5wr8-gcqf-gqf3 (High, 8.2: a
request-header timeout flaw in the server spotifio uses for the OAuth callback)
and CVE-2026-69244 / GHSA-cq5v-8q36-5273 (High, 7.1: an out-of-bounds read in the
C HTTP parser used for every API request). Both are fixed in aiohttp 3.14.4; 3.14.3
and older are vulnerable. `MANIFEST.in` keeps `AGENTS.md`, `.agents/` and any real
`.env` out of the published sdist.

### Unchanged

Method names and positional argument order, `scope=[]` meaning "no scopes",
`login()`, response payload shapes.

## 0.1.7 and earlier

No changelog was kept.

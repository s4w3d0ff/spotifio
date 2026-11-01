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
- Failed requests raise `spotifio.client.SpotifyError` instead of a plain
  `Exception`. It subclasses `Exception` and keeps the old message text
  (`Request failed with status 404: ...`), so `except Exception` and handling
  that matches on the message keep working.

### Changed

- Scope checks use the scopes Spotify granted the token (the `scope` field of
  the token response) instead of only the list passed to the constructor. A
  call that used to be blocked locally goes through when the token really has
  the scope.
- A 403, 404 or 410 on an endpoint the docs mark deprecated names the
  documented replacement in the error message.
- Reading your own library (`GET /me/tracks` and friends) is documented as
  valid and is unchanged; the deprecated save/remove/contains variants are
  still called, they are only reported more clearly.

### Added

- `spotifio.load_dotenv()` — opt-in, importing the library reads no file.
- Environment fallbacks: `SPOTIFIO_CLIENT_ID`, `SPOTIFIO_CLIENT_SECRET`,
  `SPOTIFIO_REDIRECT_URI`, `SPOTIFIO_SCOPES`. Arguments always win.
- Methods for the documented replacement endpoints: `save_library_items`,
  `remove_library_items`, `check_saved_items`, `get_playlist_items`,
  `add_playlist_items`, `remove_playlist_items`, `update_playlist_items`.
- `Client.login(reauth=True)` to authorize again for a different scope list.
- `SpotifyError.status`, `.reason`, `.body`.
- The token file is written `0600` (it was group-readable).

### Unchanged

Method names and positional argument order, `scope=[]` meaning "no scopes",
`login()`, response payload shapes, dependencies, supported Python versions.

## 0.1.7 and earlier

No changelog was kept.

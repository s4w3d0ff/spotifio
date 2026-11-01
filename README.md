# spotifio
Async Spotify Api Wrapper

```
pip install spotifio
```

```python
from spotifio import Client

async def main():
    c = Client(
        client_id="client_id_123",
        client_secret="client_secret_123",
        redirect_uri="http://127.0.0.1:5050/spotify_oauth",
        scope=["user-read-currently-playing"]
    )
    await c.login()
    r = await c.get_currently_playing()
    print(r)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

## Configuration

Everything spotifio needs to reach Spotify comes from an argument or from the
environment. There are no defaults: no default port, no default host, no
default redirect URI. A value that has to match your Spotify app settings
exactly cannot be guessed for you, so a missing one raises `ValueError` when
the instance is created.

| argument | environment variable |
|---|---|
| `client_id` | `SPOTIFIO_CLIENT_ID` |
| `client_secret` | `SPOTIFIO_CLIENT_SECRET` |
| `redirect_uri` | `SPOTIFIO_REDIRECT_URI` |
| `scope` | `SPOTIFIO_SCOPES` (space or comma separated) |

An argument always wins over the environment, so existing code that passes
these values keeps working unchanged. `scope` may legitimately be empty: an
empty list means "no scopes", which is enough for app-only calls. A method that
needs a scope raises and names the scope.

spotifio does not read a `.env` file by itself. If you keep your settings in
one, load it explicitly:

```python
import spotifio

spotifio.load_dotenv()          # reads ./.env into os.environ, existing vars win
c = spotifio.Client()            # everything from the environment
```

or export them in the shell: `set -a; . ./.env; set +a`.

## Redirect URIs

`redirect_uri` is required: there is no default. Pass it to `Client(...)` /
`TokenHandler(...)`, or set `SPOTIFIO_REDIRECT_URI` in your environment. If
none is given spotifio raises `ValueError`. The port is part of it — no default
port either; the URL must have an explicit port.

The value must match, character for character, one of the Redirect URIs listed
in your app's settings on the Spotify developer dashboard, otherwise
authorization fails with `redirect_uri: Not matching configuration`.

Spotify no longer accepts `localhost` as a redirect host. Use the loopback IP
literal (`http://127.0.0.1:PORT/callback` or `http://[::1]:PORT/callback`) or
HTTPS; spotifio raises `ValueError` if you pass `localhost`.

## Endpoints removed by Spotify

These spotifio methods now raise `SpotifyError(410, ...)` instead of calling an
endpoint Spotify has removed:

| method | Spotify status |
|---|---|
| `get_track_audio_features`, `get_several_audio_features` | 403 |
| `get_track_audio_analysis` | 403 |
| `get_artist_related_artists` | 404 |
| `get_featured_playlists` | 404 |
| `get_category_playlists` | 404 |
| `get_available_genre_seeds` | 404 |

### Also gone: recommendations

Spotify removed `GET /recommendations` (it answers 404 with no message), so
there is no replacement for the old `create_recommendations` call.

## Changed behaviour (verified 2026-11-01)

- Playlists: Spotify's own editorial playlists (`37i9dQZF...`) return 404, and
  `search(type="playlist")` returns `null` items, so `get_playlist` /
  `get_playlist_tracks` can no longer read them with an app-only token. Private
  playlists still need a user token that is allowed to read them.
- `get_new_releases` answers 200 with an empty `playlists` array.
- Batch endpoints (`/tracks`, `/albums`, `/artists`, `/episodes`, `/shows`,
  `/chapters`, `/audiobooks`) require `ids`; without them they return 400
  "Missing required field: ids".
- Spotify answers **410** for a malformed request path (for example a base URL
  built without a separating slash). spotifio also raises status 410 itself for
  the removed endpoints above.
- `GET /me` with an app-only token returns 401 "Valid user authentication
  required"; `me/player/currently-playing` answers 404 "Invalid username".
- Public profiles: `GET /users/{id}` still works for some accounts and returns
  404 for others. Use `get_current_user()` for your own profile — its
  `account_id` field (added May 2026) is the stable public identifier.

Fields removed from responses: `track.linked_from`, `track.isPlayable`,
`album.album_group`. Still present: `available_markets`, `external_ids`,
`popularity`, `album.label`, `artist.followers`.

## Breaking changes in 0.2.0

- `redirect_uri` has no default. Code that relied on the old
  `http://localhost:8888/callback` default must pass a redirect URI, and it must
  be one registered for your app (`localhost` is rejected by Spotify).
- The endpoints Spotify removed raise `SpotifyError` with status 410 instead of
  issuing a request that answers 403 or 404.
- Failed requests raise `spotifio.client.SpotifyError` instead of a plain
  `Exception`. `SpotifyError` subclasses `Exception` and its message keeps the
  old wording (`Request failed with status 404: ...`), so `except Exception`
  and message parsing still work. `.status`, `.reason` and `.body` are new.
- `Client.login(reauth=True)` is new; `login()` is unchanged.

## Errors

Failed requests raise `spotifio.client.SpotifyError` with `.status` and
`.reason`. Spotify sometimes answers with no message at all (for example
`{"error":{"status":403}}`); `.reason` then explains the likely cause.

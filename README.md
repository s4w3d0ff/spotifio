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

## Upgrading from 0.1.x

Three things can affect existing code. Everything else — method names, argument
order, return payloads, dependencies, Python version — is unchanged.

1. **`redirect_uri` must be supplied** (argument or `SPOTIFIO_REDIRECT_URI`).
   0.1.7 defaulted to `http://localhost:8888/callback`. Spotify rejects
   `localhost` as a redirect host, so that default already failed with
   `redirect_uri: Not matching configuration` for anyone using it; there is no
   longer a value to fall back to. Fix: pass a URI registered in your app's
   dashboard, e.g. `http://127.0.0.1:5050/spotify_oauth`.
2. **`client_id` and `client_secret` must be supplied.** 0.1.7 accepted their
   absence and failed later with an opaque `401`. Now it is a `ValueError` at
   construction naming the argument and the environment variable.
3. **Failed requests raise `spotifio.client.SpotifyError`** instead of a plain
   `Exception`. It subclasses `Exception` and keeps the old message text
   (`Request failed with status 404: ...`), so `except Exception` and handling
   that matches on the message keep working. `.status`, `.reason` and `.body`
   are additions.

One deliberate semantic change: a scope check now looks at the scopes Spotify
actually granted the token, not only the list passed to the constructor. A call
that used to be blocked locally goes through when the token really has the
scope. If your code relied on that local check as a hard "do not write" policy,
enforce the policy yourself.

Additive only, no action needed: `login(reauth=True)`, the new methods for the
documented replacement endpoints, and error messages that name the documented
replacement when an endpoint is deprecated. The deprecated endpoints are still
called, so code that uses `get_playlist_tracks`, `save_tracks` or
`get_artist_related_artists` keeps running exactly as before.

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

## Deprecated endpoints

The Spotify Web API reference marks these endpoints deprecated. spotifio still
calls them — availability differs per app and per account — but when one fails
with 403, 404 or 410 the `SpotifyError` message names the endpoint the docs
point at instead, so you are not left guessing:

```
Request failed with status 404: resource not found, or the endpoint has been
removed [PUT me/tracks is deprecated by Spotify, use PUT /me/library (Save
Items to User's Library)]
```

| deprecated by the docs | documented replacement |
|---|---|
| `PUT`/`DELETE /me/tracks`, `/me/albums`, `/me/shows`, `/me/episodes`, `/me/audiobooks` | `PUT`/`DELETE /me/library` |
| `GET /me/tracks/contains`, `/me/albums/contains`, `/me/shows/contains`, `/me/episodes/contains`, `/me/audiobooks/contains` | `GET /me/library/contains` |
| `GET`/`POST`/`PUT`/`DELETE /playlists/{id}/tracks` | `GET`/`POST`/`PUT`/`DELETE /playlists/{id}/items` |
| `PUT`/`DELETE /playlists/{id}/followers`, `GET /playlists/{id}/followers/contains` | none documented |
| `PUT`/`DELETE /me/following`, `GET /me/following/contains` | none documented |
| `GET /users/{id}`, `GET /users/{id}/playlists`, `POST /users/{id}/playlists` | `GET /me/playlists`, `POST /me/playlists` |
| batch `GET /tracks`, `/albums`, `/artists`, `/episodes`, `/shows`, `/chapters`, `/audiobooks` | request the items one by one |
| `GET /audio-features`, `GET /audio-features/{id}`, `GET /audio-analysis/{id}` | none documented |
| `GET /artists/{id}/related-artists`, `GET /artists/{id}/top-tracks` | none documented |
| `GET /browse/featured-playlists`, `GET /browse/categories`, `GET /browse/categories/{id}`, `GET /browse/categories/{id}/playlists`, `GET /browse/new-releases` | none documented |
| `GET /recommendations`, `GET /recommendations/available-genre-seeds` | none documented |
| `GET /markets` | none documented |

Not deprecated, and unchanged in spotifio: `GET /me/tracks`, `/me/albums`,
`/me/shows`, `/me/episodes`, `/me/audiobooks`, `/me/following` (reading your
library), everything under `/me/player`, `GET /me/top/{type}`, `GET /me/playlists`,
`POST /me/playlists`, `GET /search`, `GET /playlists/{id}`, and the new
`/me/library` and `/playlists/{id}/items` endpoints.

## New methods for the documented replacements

```python
await c.save_library_items(["spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
                            "spotify:album:5zyTDF0mqt23UU6rphZlWl"])   # PUT /me/library
await c.remove_library_items(["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"])  # DELETE /me/library
await c.check_saved_items(["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"])     # GET /me/library/contains

items = await c.get_playlist_items(playlist_id, limit=50)               # GET .../items
await c.add_playlist_items(playlist_id, ["spotify:track:4iV5W9uYEdYUVa79Axb7Rh"])
await c.remove_playlist_items(playlist_id, [{"uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh"}])
await c.update_playlist_items(playlist_id, range_start=1, insert_before=3, range_length=2)
```

`get_playlist_items` returns tracks and episodes together; pass
`additional_types` or `fields` if you need to narrow it. The old per-type and
per-playlist methods still exist so existing code keeps running.

## Behaviour observed with this app (2026-11-01)

What follows is what this app's own credentials got back, not a claim about
every app. The deprecated/replacement table above comes from the docs.

- Playlists: Spotify's own editorial playlists (`37i9dQZF...`) return 404, and
  `search(type="playlist")` returns `null` items, so `get_playlist` /
  `get_playlist_tracks` can no longer read them with an app-only token. Private
  playlists still need a user token that is allowed to read them.
- `get_new_releases` answers 200 with an empty `playlists` array.
- Batch endpoints (`/tracks`, `/albums`, `/artists`, `/episodes`, `/shows`,
  `/chapters`, `/audiobooks`) require `ids`; without them they return 400
  "Missing required field: ids".
- Spotify answers **410** for a malformed request path (for example a base URL
  built without a separating slash). spotifio no longer raises 410 itself; the
  status you see is the status Spotify sent.
- `GET /me` with an app-only token returns 401 "Valid user authentication
  required"; `me/player/currently-playing` answers 404 "Invalid username".
- Public profiles: `GET /users/{id}` still works for some accounts and returns
  404 for others. Use `get_current_user()` for your own profile — its
  `account_id` field (added May 2026) is the stable public identifier.

Fields removed from responses: `track.linked_from`, `track.isPlayable`,
`album.album_group`. Still present: `available_markets`, `external_ids`,
`popularity`, `album.label`, `artist.followers`.

## Errors

Failed requests raise `spotifio.client.SpotifyError` with `.status` and
`.reason`. Spotify sometimes answers with no message at all (for example
`{"error":{"status":403}}`); `.reason` then explains the likely cause.

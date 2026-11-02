# spotifio
Async Spotify Api Wrapper

```
pip install spotifio
```

Needs Python 3.10 or newer and `aiohttp>=3.14.4`. That floor is a security floor:
3.14.3 and older are vulnerable to CVE-2026-111064 (the local OAuth callback server)
and CVE-2026-69244 (every API request).

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
    print(await c.get_currently_playing())

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

## Configuration

Everything comes from an argument or from the environment, and there are no defaults:
no default port, no default host, no default redirect URI. A value that must match
your Spotify app settings exactly cannot be guessed for you, so a missing one raises
`ValueError` when the instance is created. An argument always wins over the
environment, so code that already passes these values keeps working.

| argument | environment variable |
|---|---|
| `client_id` | `SPOTIFIO_CLIENT_ID` |
| `client_secret` | `SPOTIFIO_CLIENT_SECRET` |
| `redirect_uri` | `SPOTIFIO_REDIRECT_URI` |
| `scope` | `SPOTIFIO_SCOPES` (space or comma separated) |

`redirect_uri` needs an explicit port and must match, character for character, a
Redirect URI in your app's dashboard, or authorization fails with
`redirect_uri: Not matching configuration`. Spotify no longer accepts `localhost` as a
redirect host: use `http://127.0.0.1:PORT/callback`, `http://[::1]:PORT/callback`, or
HTTPS, and spotifio raises `ValueError` for `localhost`.

`scope` may be empty, which means "no scopes" and is enough for app-only calls. A
method that needs one raises `spotifio.ScopeError` and names it. The check uses the
scopes Spotify granted (`TokenHandler.granted_scopes`, from the token response), and a
refresh can report more than the request asked for. Where an endpoint accepts either of
two scopes, either one is enough.

spotifio does not read a `.env` file by itself: call `spotifio.load_dotenv()` before
constructing (it fills `os.environ` and never replaces a variable that is already set),
or export them in the shell with `set -a; . ./.env; set +a`. `.env.example` lists all
four with the format each needs. Keep one variable per line and keep the final newline:
without it the last two variables glue onto one line, and `load_dotenv()` rejects such a
line instead of storing a broken secret.

One aiohttp session serves every request a client makes, so a burst of calls reuses the
connection instead of repeating the TCP and TLS setup. Close it when the client is done,
with `await c.close()` or `async with`:

```python
async with spotifio.Client() as c:
    print(await c.get_current_user())
```

## Endpoint availability

The docs describe three states and spotifio keeps them apart in the `SpotifyError`
message: **Deprecated** (the banner on the four `/playlists/{id}/tracks` pages, "Use
... Items instead"), **Removed for Development Mode apps** (the February 2026 changelog
and migration guide, which name a replacement for most), and **in neither list** (the
page exists with no banner, but the docs do not list it among the endpoints that remain
available).

Quota mode decides what an app can call. Apps in Extended Quota Mode need no migration:
every endpoint, field and behaviour stays as it was, and the generic `/me/library`
endpoints are optional. Development Mode apps got the restrictions on 2026-02-11 (apps
created then) and 2026-03-09 (apps that already existed). spotifio still calls every
endpoint it has a method for, so availability is Spotify's answer, not a local guess:

```
Request failed with status 404: resource not found, or the endpoint has been
removed [PUT me/tracks is removed by Spotify for Development Mode apps, use PUT
/me/library with Spotify URIs]
```

| what the docs no longer offer | what the docs give instead |
|---|---|
| `PUT`/`DELETE` on `/me/tracks`, `/me/albums`, `/me/shows`, `/me/episodes`, `/me/audiobooks` and their `/contains` forms | `PUT`/`DELETE /me/library`, `GET /me/library/contains` |
| `PUT`/`DELETE /me/following`, `GET /me/following/contains`, `PUT`/`DELETE /playlists/{id}/followers` and its `/contains` form | the same two, with `spotify:user:` or `spotify:playlist:` URIs |
| `GET`/`POST`/`PUT`/`DELETE /playlists/{id}/tracks` | the matching `/playlists/{id}/items` |
| batch `GET /tracks`, `/albums`, `/artists`, `/episodes`, `/shows`, `/chapters`, `/audiobooks`, `/audio-features` | `GET /tracks/{id}` and friends |
| `GET /users/{id}`, `GET /users/{id}/playlists`, `POST /users/{id}/playlists` | none; `GET /me` and `GET /me/playlists` cover your own |
| `GET /browse/categories`, `GET /browse/categories/{id}`, `GET /browse/new-releases`, `GET /artists/{id}/top-tracks`, `GET /markets` | none documented |
| `GET /audio-features/{id}`, `GET /audio-analysis/{id}`, `GET /artists/{id}/related-artists`, `GET /recommendations`, `GET /recommendations/available-genre-seeds`, `GET /browse/featured-playlists`, `GET /browse/categories/{id}/playlists` | none documented |

Still documented as available, and unchanged in spotifio: reading your own library
(`GET /me/tracks` and friends), `GET /me/following`, everything under `/me/player`,
`GET /me/top/{type}`, `GET /me/playlists`, `POST /me/playlists`, `GET /search`,
`GET /playlists/{id}`, the single-item lookups, and the newer `/me/library` and
`/playlists/{id}/items` endpoints. There is no `GET /me/library`: only the save,
remove and contains forms exist, so reading your library stays per type with
`get_user_saved_tracks`, `get_user_saved_albums`, `get_user_saved_shows`,
`get_user_saved_episodes`, `get_user_saved_audiobooks`.

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

`/me/library` takes up to 40 comma-separated Spotify URIs, not ids.
`get_playlist_items` returns tracks and episodes together, and the docs warn it answers
403 unless the current user owns the playlist or collaborates on it: for someone else's
playlist stay with `get_playlist` and `get_playlist_tracks`. The old methods still
exist, so code that uses `get_playlist_tracks`, `save_tracks` or
`get_artist_related_artists` keeps running.

## Errors

Failed requests raise `spotifio.SpotifyError` with `.status`, `.reason` and `.body`.
Spotify sometimes answers with no message at all (for example `{"error":{"status":403}}`);
`.reason` then explains the likely cause. `spotifio.ScopeError` is raised before a
request when the token lacks a scope the endpoint needs, so it never reaches Spotify.

A 401 refreshes the token and retries; a 429 waits `Retry-After` and retries. A 429 body
carries a machine readable reason (`"reason":"QUOTA_EXCEEDED"`) and spotifio appends it
to `.reason`. `RequestHandler.MAX_ATTEMPTS` (6) bounds both, and the error you get
carries the last status Spotify actually sent. `login()` refreshes a saved token that is
already expired before it returns, and `login(reauth=True)` authorizes again for
`SPOTIFIO_SCOPES` and replaces the saved token.

## Behaviour observed with this app (2026-11-01)

This is what this app's own credentials got back, not a claim about every app. The table
above comes from the docs.

- Spotify's own editorial playlists (`37i9dQZF...`) return 404 and
  `search(type="playlist")` returns `null` items, so an app-only token cannot read them.
- `get_new_releases` answers 200 with an empty `playlists` array, and batch endpoints
  answer 400 "Missing required field: ids" without `ids`.
- `GET /search` documents `limit` as 0-10 with a default of 5 (it was 20). This app still
  gets results at `limit=20`; pass 10 or less with a Development Mode app.
- Spotify answers **410** for a malformed request path, such as a base URL built without
  a separating slash. spotifio no longer raises 410 itself, so the status you see is the
  status Spotify sent.
- `GET /me` with an app-only token returns 401 "Valid user authentication required".
  `GET /users/{id}` works for some accounts and 404s for others; use `get_current_user()`
  and its `account_id` field (added May 2026) for a stable public identifier.
The docs mark `track.linked_from`, `track.isPlayable`, `album.album_group`,
`artist.followers`, `artist.genres`, `artist.popularity`, `album.available_markets` and
`track.available_markets` deprecated in the response schemas. This app (extended quota
mode) still receives `available_markets`, `external_ids`, `popularity`, `album.label` and
`artist.followers`; a Development Mode app has no reason to expect them.

## Breaking changes (0.1.x to 0.2.0)

Method names, positional argument order and response payloads are unchanged. These
changes can affect existing code.

1. **`redirect_uri`, `client_id` and `client_secret` must be supplied.** 0.1.7 defaulted
   the URI to `http://localhost:8888/callback`, which Spotify already rejected, and
   accepted missing credentials until an opaque `401`. Now a missing value is a
   `ValueError` at construction.
2. **`Python 3.10` and `aiohttp>=3.14.4` are required.** `python_requires` said 3.7 while
   `aiohttp>=3.8.0` cannot install on Python 3.12 or newer, so that combination was never
   installable as advertised.
3. **Failed requests raise `spotifio.SpotifyError`, scope checks raise
   `spotifio.ScopeError`.** Both are exported from the package root and subclass
   `Exception`, so `except Exception` and matching on the message keep working.
   `SpotifyError` lives in `spotifio/errors.py`, so `from spotifio.client import
   SpotifyError` no longer works.
4. **A failed token refresh raises `SpotifyError`** telling you to call
   `login(reauth=True)`, instead of falling back to the browser flow that blocks forever
   in a headless process.
5. **Small changes that are easy to absorb:** `load_dotenv()` rejects a malformed `.env`
   line with an error naming `path:lineno`; requests share one aiohttp session, closed by
   `await c.close()` or `async with`; a success answer that is not JSON now returns
   `bytes` rather than the aiohttp response after it was closed.
6. **A scope check looks at what the token was granted**, not only the list passed to the
   constructor, and either of two accepted scopes satisfies the requirement, so a call
   that used to be blocked locally now goes through. If your code relied on that check as
   a hard "do not write" policy, enforce the policy yourself.

## Tests

```
python -m pytest
```

The suite needs no Spotify credentials and makes no request outside 127.0.0.1: the HTTP
tests run against a local aiohttp server. CI runs it on Python 3.10 through 3.14 for
every pull request.

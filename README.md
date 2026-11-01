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

`get_user_profile` and `get_user_playlists` still call Spotify but now return
404 for most accounts; use `get_current_user()` for your own profile (the
`account_id` field added in May 2026 is the stable public identifier).

## Errors

Failed requests raise `spotifio.client.SpotifyError` with `.status` and
`.reason`. Spotify sometimes answers with no message at all (for example
`{"error":{"status":403}}`); `.reason` then explains the likely cause.

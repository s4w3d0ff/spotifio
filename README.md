# spotifio
Async Spotify Api Wrapper

`pip install spotifio` - Python 3.10+.

```python
import asyncio, spotifio
async def main():
    async with spotifio.Client() as c:  # SPOTIFIO_CLIENT_ID, _CLIENT_SECRET, _REDIRECT_URI, _SCOPES
        print(await c.get_current_user())
asyncio.run(main())
```

Nothing defaulted: a missing value raises `ValueError`. Errors: `SpotifyError` (status, reason, body), `ScopeError`. Tests: `python -m pytest`.

# spotifio
Async Spotify Api Wrapper

`pip install spotifio` - Python 3.10+, `aiohttp>=3.14.4` (older aiohttp is vulnerable).

```python
import asyncio, spotifio
async def main():
    async with spotifio.Client() as c:  # SPOTIFIO_CLIENT_ID, _CLIENT_SECRET, _REDIRECT_URI, _SCOPES
        print(await c.get_current_user())
asyncio.run(main())
```

Nothing is defaulted: a missing value raises `ValueError`.

## Breaking changes
Required credentials, redirect URI, floors: CHANGELOG.md.

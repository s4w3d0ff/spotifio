# spotifio
Async Spotify Api Wrapper

`pip install spotifio` - Python 3.10+, `aiohttp>=3.14.4` (CVE-2026-111064, CVE-2026-69244).

```python
import asyncio, spotifio
async def main():
    async with spotifio.Client() as c:  # reads SPOTIFIO_* variables
        print(await c.get_current_user())
asyncio.run(main())
```

Nothing is defaulted: a missing value raises `ValueError`. The docs list availability; spotifio calls everything, so Spotify answers. No `GET /me/library`: library reads stay per type.

## Errors
`SpotifyError.status`, `.reason`, `.body`; `ScopeError`. 401 refreshes, 429 waits `Retry-After`, 6 attempts at most.

## Breaking changes
Credentials, redirect, floors: CHANGELOG.md.

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

Nothing is defaulted: a missing value raises `ValueError`. No `GET /me/library`: library reads stay per type.

## Errors
`SpotifyError.status`, `.reason`, `.body`; `ScopeError`. 401 refreshes, 429 retries after `Retry-After`.

## Breaking changes
0.2.0: credentials and redirect URI required, 3.10 and aiohttp 3.14.4 floors, errors from the package root, refresh failure raises.

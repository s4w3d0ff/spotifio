# spotifio
Async Spotify Api Wrapper

```
pip install git+https://github.com/s4w3d0ff/spotifio.git#egg=spotifio
```

```python
from spotifio import Client

async def main():
    c = Client(
        client_id="client_id_123",
        client_secret="client_secret_123",
        redirect_uri="http://localhost:8080",
        scope=["user-read-currently-playing"]
    )
    await c.login()
    r = await c.get_currently_playing()
    print(r)        

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

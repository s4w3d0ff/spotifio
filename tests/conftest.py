import socket

import aiohttp.web
import pytest


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture
def free_port():
    """A port nobody is listening on, for tests that bind one themselves."""
    return _free_port()


@pytest.fixture
async def local_server():
    """A local stand-in for an HTTP API: script the responses, read the calls."""
    state = {"script": [], "calls": []}

    async def handle(request):
        script = state["script"].pop(0) if state["script"] else (200, {"ok": True}, {})
        status, body, headers = script
        sent = None
        if request.can_read_body:
            sent = await request.json() if request.content_type == "application/json" else await request.text()
        state["calls"].append({
            "body": sent,
            "method": request.method,
            "path": request.match_info["tail"],
            "authorization": request.headers.get("Authorization"),
            "query": dict(request.query),
        })
        if isinstance(body, dict):
            return aiohttp.web.json_response(body, status=status, headers=headers)
        return aiohttp.web.Response(status=status, body=body, headers=headers)

    app = aiohttp.web.Application()
    app.router.add_route("*", "/{tail:.*}", handle)
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    state["base_url"] = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
    yield state
    await runner.cleanup()

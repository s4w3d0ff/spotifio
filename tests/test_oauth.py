import asyncio
import time

import aiohttp
import pytest

from spotifio import oauth
from spotifio.errors import SpotifyError
from spotifio.oauth import TokenHandler


class FakeStorage:
    def __init__(self):
        self.saved = []

    async def save_token(self, token, name=""):
        self.saved.append(token)

    async def load_token(self, name=""):
        return None


def make_handler(monkeypatch, port):
    monkeypatch.setenv("SPOTIFIO_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFIO_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SPOTIFIO_REDIRECT_URI", f"http://127.0.0.1:{port}/cb")
    monkeypatch.delenv("SPOTIFIO_SCOPES", raising=False)
    return TokenHandler(storage=FakeStorage())


def no_browser(monkeypatch):
    monkeypatch.setattr(oauth.webbrowser, "open", lambda url: False)


async def wait_until_listening(port):
    for _ in range(200):
        try:
            _, writer = await asyncio.open_connection("127.0.0.1", port)
        except OSError:
            await asyncio.sleep(0.01)
            continue
        writer.close()
        return True
    return False


async def is_listening(port):
    try:
        _, writer = await asyncio.open_connection("127.0.0.1", port)
    except OSError:
        return False
    writer.close()
    return True


async def test_stop_without_any_login_is_safe(monkeypatch, free_port):
    # Regression: stop() used to await a refresh task that was still None.
    handler = make_handler(monkeypatch, free_port)
    await handler.stop()
    assert handler._refresh_task is None


async def test_redirect_uri_localhost_is_rejected(monkeypatch, free_port):
    monkeypatch.setenv("SPOTIFIO_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFIO_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SPOTIFIO_REDIRECT_URI", "http://localhost:5050/cb")
    with pytest.raises(ValueError) as exc:
        TokenHandler(storage=FakeStorage())
    assert "127.0.0.1" in str(exc.value)


async def test_redirect_uri_without_a_port_is_rejected(monkeypatch, free_port):
    monkeypatch.setenv("SPOTIFIO_CLIENT_ID", "client-id")
    monkeypatch.setenv("SPOTIFIO_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("SPOTIFIO_REDIRECT_URI", "https://example.com/cb")
    with pytest.raises(ValueError) as exc:
        TokenHandler(storage=FakeStorage())
    assert "explicit port" in str(exc.value)


async def test_waiting_for_the_code_is_bounded_and_frees_the_port(monkeypatch, free_port):
    port = free_port
    handler = make_handler(monkeypatch, port)
    no_browser(monkeypatch)
    monkeypatch.setattr(TokenHandler, "AUTH_CODE_TIMEOUT_SECONDS", 0.2)
    with pytest.raises(TimeoutError):
        await handler._get_auth_code()
    assert handler.server._runner is None
    assert not await is_listening(port)


async def test_the_callback_delivers_the_code_and_stops_the_server(monkeypatch, free_port):
    port = free_port
    handler = make_handler(monkeypatch, port)
    no_browser(monkeypatch)
    task = asyncio.create_task(handler._get_auth_code())
    assert await wait_until_listening(port)
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://127.0.0.1:{port}/cb?state=wrong&code=x") as resp:
            assert resp.status == 400
            assert "State mismatch" in await resp.text()
        async with session.get(f"http://127.0.0.1:{port}/cb?state={handler._state}&code=test-code") as resp:
            assert resp.status == 200
    await asyncio.wait_for(task, timeout=5)
    assert handler._auth_code == "test-code"
    assert not await is_listening(port)


async def test_token_request_failure_raises_SpotifyError_with_the_status(monkeypatch, local_server, free_port):
    local_server["script"] = [(400, {"error": {"message": "invalid grant"}}, {})]
    handler = make_handler(monkeypatch, free_port)
    handler._token_url = f"{local_server['base_url']}/api/token"
    with pytest.raises(SpotifyError) as exc:
        await handler._token_request({"grant_type": "refresh_token", "refresh_token": "x"})
    assert exc.value.status == 400
    assert "invalid grant" in exc.value.body


async def test_token_request_saves_the_token_and_remembers_the_granted_scopes(monkeypatch, local_server, free_port):
    local_server["script"] = [(200, {"access_token": "a", "refresh_token": "r",
                                     "expires_in": 3600, "scope": "user-library-read"}, {})]
    handler = make_handler(monkeypatch, free_port)
    handler._token_url = f"{local_server['base_url']}/api/token"
    token = await handler._token_request({"grant_type": "authorization_code",
                                          "code": "c", "redirect_uri": handler.redirect_uri})
    assert token["expires_time"] > time.time()
    assert handler.granted_scopes == {"user-library-read"}
    assert handler.storage.saved == [token]


async def test_refresh_without_a_refresh_token_raises_instead_of_opening_a_browser(monkeypatch, free_port):
    # Regression: this used to start an interactive login inside a headless process.
    handler = make_handler(monkeypatch, free_port)
    handler._token = {"access_token": "a", "expires_time": time.time() + 100}
    with pytest.raises(SpotifyError) as exc:
        await handler._refresh_token()
    assert "login(reauth=True)" in exc.value.reason


async def test_refresher_without_a_token_exits_instead_of_crashing(monkeypatch, free_port):
    handler = make_handler(monkeypatch, free_port)
    await handler._run()
    await asyncio.wait_for(handler._refresh_task, timeout=2)
    assert handler._refresh_task.exception() is None


async def test_get_token_returns_the_old_token_when_refreshing_fails(monkeypatch, free_port):
    handler = make_handler(monkeypatch, free_port)
    handler._token = {"access_token": "old", "expires_time": time.time() - 1}
    await handler._run()
    token = await asyncio.wait_for(handler.get_token(), timeout=5)
    assert token["access_token"] == "old"
    await handler.stop()


async def already(token):
    return token


async def test_get_token_does_not_wait_for_a_refresher_that_is_gone(monkeypatch, free_port):
    handler = make_handler(monkeypatch, free_port)
    handler._token = {"access_token": "a", "expires_time": time.time() + 100}
    await handler._run()
    await handler.stop()
    token = await asyncio.wait_for(handler.get_token(), timeout=2)
    assert token["access_token"] == "a"


async def test_a_refresher_that_already_ended_is_replaced_by_the_next_login(monkeypatch, free_port):
    # A token with no expires_time ends the refresher at once: the next login has
    # to start a fresh one instead of assuming the old task is still running.
    handler = make_handler(monkeypatch, free_port)
    expired = {"access_token": "a"}
    handler.storage.load_token = lambda name="": already(expired)
    await handler._login()
    first = handler._refresh_task
    await asyncio.wait_for(first, timeout=2)
    await handler._login()
    assert handler._refresh_task is not first
    await handler.stop()

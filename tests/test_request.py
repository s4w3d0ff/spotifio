import pytest

from spotifio import request as request_module
from spotifio.errors import SpotifyError
from spotifio.request import RequestHandler


class FakeTokenHandler:
    def __init__(self):
        self.refreshes = 0

    async def get_token(self):
        return {"access_token": "fake-token"}

    async def _refresh_token(self):
        self.refreshes += 1


@pytest.fixture
def api(monkeypatch, local_server):
    """The local server, wired in as the API base URL."""
    monkeypatch.setattr(request_module, "base_url", local_server["base_url"])
    local_server["new_handler"] = lambda: RequestHandler(token_handler=FakeTokenHandler())
    return local_server


async def test_json_response_is_returned_as_a_dict(api):
    api["script"] = [(200, {"id": "abc"}, {})]
    client = api["new_handler"]()
    assert await client._request("GET", "tracks/abc") == {"id": "abc"}
    assert api["calls"][0]["authorization"] == "Bearer fake-token"
    await client.close()


async def test_a_non_json_success_returns_bytes(api):
    api["script"] = [(200, b"plain text", {"Content-Type": "text/plain"})]
    client = api["new_handler"]()
    assert await client._request("GET", "tracks/abc") == b"plain text"
    await client.close()


async def test_no_content_returns_None(api):
    api["script"] = [(204, b"", {})]
    client = api["new_handler"]()
    assert await client._request("DELETE", "me/library") is None
    await client.close()


async def test_params_and_json_body_are_sent(api):
    api["script"] = [(200, {"ok": True}, {})]
    client = api["new_handler"]()
    await client._request("POST", "me/playlists", params={"name": "x"}, data={"public": True})
    assert api["calls"][0]["query"] == {"name": "x"}
    assert api["calls"][0]["body"] == {"public": True}
    await client.close()


async def test_401_refreshes_the_token_then_retries(api):
    api["script"] = [(401, {"error": {"status": 401}}, {}), (200, {"id": "abc"}, {})]
    client = api["new_handler"]()
    assert await client._request("GET", "tracks/abc") == {"id": "abc"}
    assert client.token_handler.refreshes == 1
    assert len(api["calls"]) == 2
    await client.close()


async def test_429_waits_for_retry_after_then_retries(api):
    api["script"] = [(429, {"error": {"status": 429}}, {"Retry-After": "0"}),
                     (200, {"id": "abc"}, {})]
    client = api["new_handler"]()
    assert await client._request("GET", "tracks/abc") == {"id": "abc"}
    assert len(api["calls"]) == 2
    await client.close()


async def test_attempts_are_bounded_and_the_real_status_is_reported(api, monkeypatch):
    monkeypatch.setattr(RequestHandler, "MAX_ATTEMPTS", 3)
    api["script"] = [(401, {"error": {"status": 401}}, {})] * 3
    client = api["new_handler"]()
    with pytest.raises(SpotifyError) as exc:
        await client._request("GET", "tracks/abc")
    assert exc.value.status == 401
    assert len(api["calls"]) == 3
    assert client.token_handler.refreshes == 2
    await client.close()


async def test_failure_without_a_spotify_message_uses_the_hint(api):
    api["script"] = [(403, {"error": {"status": 403}}, {})]
    client = api["new_handler"]()
    with pytest.raises(SpotifyError) as exc:
        await client._request("PUT", "me/tracks", params={"ids": "x"})
    assert exc.value.status == 403
    assert "deprecated" in exc.value.reason
    assert "PUT /me/library" in exc.value.reason
    await client.close()


async def test_one_session_is_reused_until_close(api):
    api["script"] = [(200, {"ok": True}, {})] * 2
    client = api["new_handler"]()
    await client._request("GET", "tracks/1")
    session = client._session
    await client._request("GET", "tracks/2")
    assert client._session is session
    await client.close()
    assert client._session is None

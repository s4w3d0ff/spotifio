import pytest

from spotifio.errors import ScopeError
from spotifio.request import RequestHandler


class FakeTokenHandler:
    """Stands in for TokenHandler: only .scope and .granted_scopes are read."""

    def __init__(self, scope, granted_scopes=None):
        self.scope = list(scope)
        self.granted_scopes = granted_scopes if granted_scopes is not None else list(scope)


def handler(scope, granted_scopes=None):
    return RequestHandler(token_handler=FakeTokenHandler(scope, granted_scopes))


async def test_check_scope_accepts_a_listed_scope():
    await handler(["user-library-read"])._check_scope("get_user_saved_tracks")


async def test_check_scope_reports_a_missing_scope_as_ScopeError():
    with pytest.raises(ScopeError) as exc:
        await handler([])._check_scope("save_library_items")
    assert "user-library-modify" in str(exc.value)
    assert "save_library_items" in str(exc.value)


async def test_playlist_write_neither_public_nor_private_scope_is_enough():
    for scope in ("playlist-modify-public", "playlist-modify-private"):
        await handler([scope])._check_scope("add_playlist_items")
    with pytest.raises(ScopeError):
        await handler([])._check_scope("add_playlist_items")


async def test_current_user_neither_private_nor_email_scope_is_enough():
    for scope in ("user-read-private", "user-read-email"):
        await handler([scope])._check_scope("get_current_user")
    with pytest.raises(ScopeError):
        await handler([])._check_scope("get_current_user")


async def test_endpoints_without_a_scope_need_no_scope():
    await handler([])._check_scope("get_track")
    await handler([])._check_scope("get_playlist_items")


async def test_a_saved_token_without_the_scope_is_rejected():
    # The configured scope list says the app asked for it, the authorized token
    # does not have it, so reauth is needed.
    with pytest.raises(ScopeError) as exc:
        await handler(["user-library-read"], granted_scopes=["user-read-email"])._check_scope("check_saved_items")
    assert "reauth=True" in str(exc.value)


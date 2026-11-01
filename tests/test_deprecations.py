import inspect

from spotifio.client import Client
from spotifio.deprecations import FAILURE_HINTS, deprecation_note
from spotifio.scopes import REQUIRED_SCOPES


def test_failure_hints_cover_the_statuses_spotifio_special_cases():
    assert set(FAILURE_HINTS) == {400, 401, 403, 404, 410, 429}


def test_deprecated_write_endpoint_names_the_documented_replacement():
    note = deprecation_note("PUT", "me/tracks")
    assert note is not None
    assert "PUT /me/library" in note


def test_playlist_tracks_variant_names_the_items_endpoint():
    assert "/playlists/{playlist_id}/items" in deprecation_note("GET", "playlists/abc/tracks")


def test_reading_your_own_library_is_not_marked_deprecated():
    assert deprecation_note("GET", "me/tracks") is None
    assert deprecation_note("GET", "me/albums") is None
    assert deprecation_note("GET", "me/following") is None


def test_patterns_match_the_path_spotifio_actually_requests():
    assert deprecation_note("GET", "tracks") is not None
    assert deprecation_note("GET", "tracks/123") is None
    assert deprecation_note("POST", "me/playlists") is None
    assert deprecation_note("POST", "users/abc/playlists") is not None


def test_scope_table_matches_the_client_methods_exactly():
    methods = {
        name for name, obj in inspect.getmembers(Client, inspect.iscoroutinefunction)
        if not name.startswith("_")
    }
    # login and close are client plumbing, not endpoints.
    assert set(REQUIRED_SCOPES) == methods - {"login", "close"}

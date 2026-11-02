import inspect

from spotifio.client import Client
from spotifio.deprecations import FAILURE_HINTS, REMOVED, UNLISTED, deprecation_note
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


def test_follow_endpoints_name_the_library_endpoint_the_docs_give_them():
    assert "PUT /me/library" in deprecation_note("PUT", "me/following")
    assert "DELETE /me/library" in deprecation_note("DELETE", "me/following")
    assert "GET /me/library/contains" in deprecation_note("GET", "me/following/contains")
    assert "PUT /me/library" in deprecation_note("PUT", "playlists/abc/followers")
    assert "DELETE /me/library" in deprecation_note("DELETE", "playlists/abc/followers")
    assert "GET /me/library/contains" in deprecation_note(
        "GET", "playlists/abc/followers/contains"
    )


def test_a_batch_lookup_names_the_single_item_form_that_stays_available():
    for name in ("albums", "artists", "audiobooks", "chapters", "episodes", "shows", "tracks"):
        assert f"GET /{name}/{{id}}" in deprecation_note("GET", name)
    assert "GET /audio-features/{id}" in deprecation_note("GET", "audio-features")


def test_removed_and_unlisted_endpoints_are_worded_apart():
    for path in ("markets", "browse/new-releases", "browse/categories",
                 "browse/categories/nightlists", "users/abc", "users/abc/playlists",
                 "artists/abc/top-tracks"):
        assert REMOVED in deprecation_note("GET", path), path
    for path in ("browse/featured-playlists", "browse/categories/nightlists/playlists",
                 "recommendations", "recommendations/available-genre-seeds",
                 "audio-features/abc", "audio-analysis/abc", "artists/abc/related-artists"):
        assert UNLISTED in deprecation_note("GET", path), path


def test_the_endpoints_the_docs_still_list_have_no_note():
    for path in ("me", "me/playlists", "me/top/tracks", "me/following", "me/library",
                 "me/library/contains", "search", "albums/abc", "albums/abc/tracks",
                 "artists/abc", "artists/abc/albums", "episodes/abc", "shows/abc",
                 "shows/abc/episodes", "tracks/abc", "playlists/abc",
                 "playlists/abc/items", "playlists/abc/images", "me/player",
                 "me/player/recently-played", "me/queue"):
        assert deprecation_note("GET", path) is None, path


def test_scope_table_matches_the_client_methods_exactly():
    methods = {
        name for name, obj in inspect.getmembers(Client, inspect.iscoroutinefunction)
        if not name.startswith("_")
    }
    assert set(REQUIRED_SCOPES) == methods - {"login", "close"}

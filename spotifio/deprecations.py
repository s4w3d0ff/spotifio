# Endpoints the Spotify Web API docs no longer offer, and what the docs say to use
# instead. The docs use two different words and this table keeps them apart:
#   - the reference pages put a "[DEPRECATED]" banner on the four playlist items
#     variants ("Deprecated: Use ... Items instead")
#   - the February 2026 changelog and its migration guide list endpoints as
#     [REMOVED] for Development Mode apps, name a replacement for most of them,
#     and then list the endpoints that remain available
#   - a few endpoints are in neither list: their pages still exist, they carry no
#     banner, and they are absent from the list of endpoints that remain available
# The migration guide is explicit that extended quota mode apps are not affected:
# for them every endpoint, field and behaviour stays as it was.
# spotifio still calls every endpoint it has a method for: availability is
# Spotify's answer, not a local guess. When Spotify answers 403, 404 or 410 the
# SpotifyError message names the replacement the docs point at.
# Some response fields are marked deprecated even where the endpoint stays:
# track.linked_from, track.isPlayable, album.album_group, artist.followers,
# artist.genres, artist.popularity, album.available_markets,
# track.available_markets. An app in extended quota mode still receives
# available_markets, external_ids, popularity, album.label and artist.followers.
# Source: developer.spotify.com/documentation/web-api/reference,
#         .../documentation/web-api/references/changes/february-2026,
#         .../documentation/web-api/tutorials/february-2026-migration-guide
import re

REMOVED = "removed by Spotify for Development Mode apps"
UNLISTED = "not in the Spotify docs list of endpoints that remain available"

FAILURE_HINTS = {
    400: "bad request - a batch endpoint with no ids answers 'Missing required "
         "field: ids'",
    401: "invalid or expired token",
    403: "forbidden - endpoint deprecated or removed for this app's quota mode, or "
         "the current user is not allowed on this resource",
    404: "resource not found, or the endpoint has been removed",
    410: "gone - Spotify answers this for a malformed request path (a base URL built "
         "without a separating slash does this), or the endpoint is gone",
    429: "rate limited",
}

# Matched with fullmatch against the concrete path spotifio requests, so
# 'me/tracks' (still documented as valid) is never confused with the removed
# save/remove variants of the same path.
DEPRECATED_PATTERNS = [
    ('GET', r'audio-features$', f"{REMOVED} as a batch lookup, request each item with GET /audio-features/{{id}}"),
    ('GET', r'audio-features/[^/]+', f"{UNLISTED}, no replacement documented"),
    ('GET', r'audio-analysis/[^/]+', f"{UNLISTED}, no replacement documented"),
    ('GET', r'artists/[^/]+/related-artists', f"{UNLISTED}, no replacement documented"),
    ('GET', r'artists/[^/]+/top-tracks', f"{REMOVED}, no replacement documented"),
    ('GET', r'browse/featured-playlists', f"{UNLISTED}, no replacement documented"),
    ('GET', r'browse/categories(/[^/]+)?$', f"{REMOVED}, no replacement documented"),
    ('GET', r'browse/categories/[^/]+/playlists', f"{UNLISTED}, no replacement documented"),
    ('GET', r'browse/new-releases', f"{REMOVED}, no replacement documented"),
    ('GET', r'recommendations(/.*)?', f"{UNLISTED}, no replacement documented"),
    ('GET', r'markets', f"{REMOVED}, no replacement documented"),
    ('GET', r'users/[^/]+$', f"{REMOVED}, no replacement; GET /me gives your own profile"),
    ('GET', r'users/[^/]+/playlists',
     f"{REMOVED}, no replacement; GET /me/playlists gives your own playlists"),
    ('POST', r'users/[^/]+/playlists', f"{REMOVED}, use POST /me/playlists"),
    ('PUT', r'me/(albums|audiobooks|episodes|shows|tracks)',
     f"{REMOVED}, use PUT /me/library with Spotify URIs"),
    ('DELETE', r'me/(albums|audiobooks|episodes|shows|tracks)',
     f"{REMOVED}, use DELETE /me/library with Spotify URIs"),
    ('GET', r'me/(albums|audiobooks|episodes|shows|tracks)/contains',
     f"{REMOVED}, use GET /me/library/contains with Spotify URIs"),
    ('PUT', r'me/following',
     f"{REMOVED}, use PUT /me/library (the changelog points follows at it, although "
     "that endpoint's own page lists user and playlist URIs but not artist URIs)"),
    ('DELETE', r'me/following', f"{REMOVED}, use DELETE /me/library"),
    ('GET', r'me/following/contains', f"{REMOVED}, use GET /me/library/contains"),
    ('GET', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use GET /playlists/{playlist_id}/items (Get Playlist Items)"),
    ('POST', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use POST /playlists/{playlist_id}/items (Add Items to Playlist)"),
    ('DELETE', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use DELETE /playlists/{playlist_id}/items (Remove Playlist Items)"),
    ('PUT', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use PUT /playlists/{playlist_id}/items (Update Playlist Items)"),
    ('PUT', r'playlists/[^/]+/followers',
     f"{REMOVED}, use PUT /me/library with the spotify:playlist: URI"),
    ('DELETE', r'playlists/[^/]+/followers',
     f"{REMOVED}, use DELETE /me/library with the spotify:playlist: URI"),
    ('GET', r'playlists/[^/]+/followers/contains',
     f"{REMOVED}, use GET /me/library/contains with the spotify:playlist: URI"),
]

# The batch lookups are removed one endpoint at a time, and each one has a single
# item form that stays available, so the note names that form.
for _type in ('albums', 'artists', 'audiobooks', 'chapters', 'episodes', 'shows', 'tracks'):
    DEPRECATED_PATTERNS.append(
        ('GET', _type, f"{REMOVED} as a batch lookup, request each item with GET /{_type}/{{id}}")
    )


def deprecation_note(method, endpoint):
    """Docs note for an endpoint the docs no longer offer, or None if the docs
    still list it as available."""
    path = endpoint.lstrip('/')
    for req_method, pattern, note in DEPRECATED_PATTERNS:
        if req_method == method and re.fullmatch(pattern, path):
            return note
    return None

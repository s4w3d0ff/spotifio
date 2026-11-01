# Endpoints the Spotify Web API reference marks deprecated, and what the docs
# say to use instead. spotifio still calls them: availability is Spotify's
# answer, not a local guess. When Spotify answers 403, 404 or 410 the
# SpotifyError message names the replacement the docs point at.
# Source: developer.spotify.com/documentation/web-api/reference (the "deprecated"
# flag on each endpoint) and the Web API changelog.
import re

FAILURE_HINTS = {
    400: "bad request",
    401: "invalid or expired token",
    403: "forbidden - endpoint deprecated, or this app is not allowed to call it",
    404: "resource not found, or the endpoint has been removed",
    410: "gone - Spotify answers this for a malformed request path (a base URL built "
         "without a separating slash does this), or the endpoint is gone",
    429: "rate limited",
}

# Matched with fullmatch against the concrete path spotifio requests, so
# 'me/tracks' (still documented as valid) is never confused with the deprecated
# save/remove variants of the same path.
DEPRECATED_PATTERNS = [
    ('GET', r'audio-features(/.*)?', "deprecated by Spotify, no replacement documented"),
    ('GET', r'audio-analysis/[^/]+', "deprecated by Spotify, no replacement documented"),
    ('GET', r'artists/[^/]+/related-artists', "deprecated by Spotify, no replacement documented"),
    ('GET', r'artists/[^/]+/top-tracks', "deprecated by Spotify, no replacement documented"),
    ('GET', r'browse/featured-playlists', "deprecated by Spotify, no replacement documented"),
    ('GET', r'browse/categories(/.*)?', "deprecated by Spotify, no replacement documented"),
    ('GET', r'browse/new-releases', "deprecated by Spotify, no replacement documented"),
    ('GET', r'recommendations(/.*)?', "deprecated by Spotify, no replacement documented"),
    ('GET', r'markets', "deprecated by Spotify, no replacement documented"),
    ('GET', r'users/[^/]+', "deprecated by Spotify, no replacement documented"),
    ('GET', r'users/[^/]+/playlists', "deprecated by Spotify, use GET /me/playlists"),
    ('POST', r'users/[^/]+/playlists', "deprecated by Spotify, use POST /me/playlists"),
    ('GET', r'(albums|artists|audiobooks|chapters|episodes|shows|tracks)',
     "deprecated by Spotify as a batch lookup, request the items one by one"),
    ('PUT', r'me/(albums|audiobooks|episodes|shows|tracks)',
     "deprecated by Spotify, use PUT /me/library (Save Items to User's Library)"),
    ('DELETE', r'me/(albums|audiobooks|episodes|shows|tracks)',
     "deprecated by Spotify, use DELETE /me/library (Remove Items from User's Library)"),
    ('GET', r'me/(albums|audiobooks|episodes|shows|tracks)/contains',
     "deprecated by Spotify, use GET /me/library/contains"),
    ('PUT', r'me/following', "deprecated by Spotify, no replacement documented"),
    ('DELETE', r'me/following', "deprecated by Spotify, no replacement documented"),
    ('GET', r'me/following/contains', "deprecated by Spotify, no replacement documented"),
    ('GET', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use GET /playlists/{playlist_id}/items (Get Playlist Items)"),
    ('POST', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use POST /playlists/{playlist_id}/items (Add Items to Playlist)"),
    ('DELETE', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use DELETE /playlists/{playlist_id}/items (Remove Playlist Items)"),
    ('PUT', r'playlists/[^/]+/tracks',
     "deprecated by Spotify, use PUT /playlists/{playlist_id}/items (Update Playlist Items)"),
    ('PUT', r'playlists/[^/]+/followers', "deprecated by Spotify, no replacement documented"),
    ('DELETE', r'playlists/[^/]+/followers', "deprecated by Spotify, no replacement documented"),
    ('GET', r'playlists/[^/]+/followers/contains',
     "deprecated by Spotify, no replacement documented"),
]


def deprecation_note(method, endpoint):
    """Docs note for a deprecated endpoint, or None if the docs do not mark it
    deprecated."""
    path = endpoint.lstrip('/')
    for req_method, pattern, note in DEPRECATED_PATTERNS:
        if req_method == method and re.fullmatch(pattern, path):
            return note
    return None

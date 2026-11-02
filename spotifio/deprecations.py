# Availability notes for endpoints the Spotify docs no longer offer.
# REMOVED: gone for Development Mode apps. UNLISTED: absent from the docs list of
# endpoints that still work. Extended quota mode apps are unaffected by both.
# spotifio calls what it has a method for; Spotify answers availability.
import re

REMOVED = "removed for Development Mode apps"
UNLISTED = "absent from the docs list of endpoints that still work"

FAILURE_HINTS = {
    400: "bad request",
    401: "invalid or expired token",
    403: "forbidden - endpoint removed for this quota mode, or the user is not "
         "allowed on this resource",
    404: "not found - bad id, or the endpoint is gone",
    410: "gone - endpoint gone, or the request path is malformed",
    429: "rate limited",
}

DEPRECATED_PATTERNS = [
    ('GET', r'audio-features$', f"{REMOVED} as a batch, use GET /audio-features/{{id}}"),
    ('GET', r'audio-features/[^/]+', f"{UNLISTED}, no replacement"),
    ('GET', r'audio-analysis/[^/]+', f"{UNLISTED}, no replacement"),
    ('GET', r'artists/[^/]+/related-artists', f"{UNLISTED}, no replacement"),
    ('GET', r'artists/[^/]+/top-tracks', f"{REMOVED}, no replacement"),
    ('GET', r'browse/featured-playlists', f"{UNLISTED}, no replacement"),
    ('GET', r'browse/categories(/[^/]+)?$', f"{REMOVED}, no replacement"),
    ('GET', r'browse/categories/[^/]+/playlists', f"{UNLISTED}, no replacement"),
    ('GET', r'browse/new-releases', f"{REMOVED}, no replacement"),
    ('GET', r'recommendations(/.*)?', f"{UNLISTED}, no replacement"),
    ('GET', r'markets', f"{REMOVED}, no replacement"),
    ('GET', r'users/[^/]+$', f"{REMOVED}, GET /me gives your own profile"),
    ('GET', r'users/[^/]+/playlists', f"{REMOVED}, GET /me/playlists gives your own"),
    ('POST', r'users/[^/]+/playlists', f"{REMOVED}, use POST /me/playlists"),
    ('PUT', r'me/(albums|audiobooks|episodes|shows|tracks)',
     f"{REMOVED}, use PUT /me/library with Spotify URIs"),
    ('DELETE', r'me/(albums|audiobooks|episodes|shows|tracks)',
     f"{REMOVED}, use DELETE /me/library with Spotify URIs"),
    ('GET', r'me/(albums|audiobooks|episodes|shows|tracks)/contains',
     f"{REMOVED}, use GET /me/library/contains with Spotify URIs"),
    ('PUT', r'me/following', f"{REMOVED}, use PUT /me/library"),
    ('DELETE', r'me/following', f"{REMOVED}, use DELETE /me/library"),
    ('GET', r'me/following/contains', f"{REMOVED}, use GET /me/library/contains"),
    ('GET', r'playlists/[^/]+/tracks', "docs mark it deprecated, use /playlists/{playlist_id}/items"),
    ('POST', r'playlists/[^/]+/tracks', "docs mark it deprecated, use /playlists/{playlist_id}/items"),
    ('DELETE', r'playlists/[^/]+/tracks', "docs mark it deprecated, use /playlists/{playlist_id}/items"),
    ('PUT', r'playlists/[^/]+/tracks', "docs mark it deprecated, use /playlists/{playlist_id}/items"),
    ('PUT', r'playlists/[^/]+/followers', f"{REMOVED}, use PUT /me/library"),
    ('DELETE', r'playlists/[^/]+/followers', f"{REMOVED}, use DELETE /me/library"),
    ('GET', r'playlists/[^/]+/followers/contains', f"{REMOVED}, use GET /me/library/contains"),
]

for _type in ('albums', 'artists', 'audiobooks', 'chapters', 'episodes', 'shows', 'tracks'):
    DEPRECATED_PATTERNS.append(
        ('GET', _type, f"{REMOVED} as a batch, use GET /{_type}/{{id}}")
    )


def deprecation_note(method, endpoint):
    """Availability note for an endpoint, or None."""
    path = endpoint.lstrip('/')
    for req_method, pattern, note in DEPRECATED_PATTERNS:
        if req_method == method and re.fullmatch(pattern, path):
            return note
    return None

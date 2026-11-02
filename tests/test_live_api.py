"""Passive sweep of every GET-only endpoint against the real API.

Opt-in: SPOTIFIO_LIVE=1 plus real credentials and a saved token. CI never runs it.
Paced so no request limit is hit, and a 429 fails the run instead of hiding.
"""
import asyncio
import os
import time

import pytest

from spotifio import Client, load_dotenv
from spotifio.errors import ScopeError, SpotifyError

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(os.environ.get("SPOTIFIO_LIVE") != "1",
                       reason="set SPOTIFIO_LIVE=1 with real credentials"),
]

GAP_SECONDS = 2.0
OK = {200}
GONE = {200, 403, 404}
NO_DEVICE = {200, 404}

SAVED = (
    ("track", "get_user_saved_tracks"),
    ("album", "get_user_saved_albums"),
    ("episode", "get_user_saved_episodes"),
    ("show", "get_user_saved_shows"),
    ("audiobook", "get_user_saved_audiobooks"),
)


class PacedClient(Client):
    """GAP_SECONDS between requests: 0.5 requests per second, well under the
    published 10 per second per IP and under one per second per token."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sent = 0.0

    async def _request(self, method, endpoint, params=None, data=None, headers=None):
        wait = GAP_SECONDS - (time.monotonic() - self._sent)
        if wait > 0:
            await asyncio.sleep(wait)
        self._sent = time.monotonic()
        return await super()._request(method, endpoint, params=params, data=data,
                                      headers=headers)


def _items(page):
    return (page or {}).get("items") or []


SEARCHABLE = ("track", "album", "artist", "show", "episode", "audiobook")


async def _search_id(client, kind):
    """The search endpoint covers albums, artists, playlists, tracks, shows,
    episodes and audiobooks, so an id never has to be invented."""
    page = await client.search("ambient", (kind,), limit=5)
    items = _items((page or {}).get(kind + "s"))
    return items[0]["id"] if items else None


async def _call(make_coroutine):
    """Discovery tolerates a scope the token lacks or an endpoint that is gone."""
    try:
        return await make_coroutine()
    except (ScopeError, SpotifyError):
        return None


async def _first_id(make_coroutine):
    items = _items(await _call(make_coroutine))
    return items[0]["id"] if items else None


async def discover(client):
    """Ids from this account's own library. Nothing is invented."""
    found = {}
    me = await client.get_current_user()
    found["user_id"] = me["id"]
    for kind, method in SAVED:
        page = await getattr(client, method)(limit=5)
        items = [item for item in _items(page) if item]
        if items:
            found[kind + "_id"] = items[0]["id"]
    if "playlist_id" not in found:
        page = await client.get_current_user_playlists(limit=5)
        if _items(page):
            found["playlist_id"] = _items(page)[0]["id"]
    if "track_id" in found:
        track = await client.get_track(found["track_id"])
        if track.get("artists"):
            found["artist_id"] = track["artists"][0]["id"]
    for kind in SEARCHABLE:
        if kind + "_id" not in found:
            found[kind + "_id"] = await _search_id(client, kind)
    if "audiobook_id" in found:
        found["chapter_id"] = await _first_id(
            lambda: client.get_audiobook_chapters(found["audiobook_id"], limit=5))
    if "show_id" in found and "episode_id" not in found:
        found["episode_id"] = await _first_id(
            lambda: client.get_show_episodes(found["show_id"], limit=5))
    page = await _call(lambda: client.get_categories(limit=5))
    if _items(page):
        found["category_id"] = _items(page)[0]["id"]
    page = await _call(lambda: client.get_available_markets())
    if _items(page):
        found["market"] = _items(page)[0]["id"]
    return found


def _skipped(reason):
    async def call():
        return ("skipped", reason)
    return call


def sweep(client, k):
    """(method, statuses that count as an answer, call). A missing id is skipped."""

    def id_of(*names):
        for name in names:
            if name in k:
                return k[name]
        return None

    def track():
        return id_of("track_id")

    def album():
        return id_of("album_id")

    def artist():
        return id_of("artist_id")

    def show():
        return id_of("show_id")

    def episode():
        return id_of("episode_id")

    def audiobook():
        return id_of("audiobook_id")

    def chapter():
        return id_of("chapter_id")

    def playlist():
        return id_of("playlist_id")

    market = k.get("market")
    rows = [
        ("get_current_user", OK, lambda: client.get_current_user()),
        ("get_user_profile", {200, 404}, lambda: client.get_user_profile(k["user_id"])),
        ("get_followed_artists", OK, lambda: client.get_followed_artists(limit=5)),
        ("check_following_users", OK, lambda: client.check_following_users([k["user_id"]])),
        ("get_user_top_items", OK, lambda: client.get_user_top_items("tracks", limit=5)),
        ("get_user_saved_tracks", OK, lambda: client.get_user_saved_tracks(limit=5)),
        ("get_user_saved_albums", OK, lambda: client.get_user_saved_albums(limit=5)),
        ("get_user_saved_episodes", OK, lambda: client.get_user_saved_episodes(limit=5)),
        ("get_user_saved_shows", OK, lambda: client.get_user_saved_shows(limit=5)),
        ("get_user_saved_audiobooks", OK, lambda: client.get_user_saved_audiobooks(limit=5)),
        ("get_current_user_playlists", OK, lambda: client.get_current_user_playlists(limit=5)),
        ("get_user_playlists", OK, lambda: client.get_user_playlists(k["user_id"], limit=5)),
        ("search", OK, lambda: client.search("ambient", ("track",), limit=5)),
        ("get_categories", OK, lambda: client.get_categories(limit=5)),
        ("get_available_genre_seeds", GONE, lambda: client.get_available_genre_seeds()),
        ("get_available_markets", OK, lambda: client.get_available_markets()),
        ("get_new_releases", {200, 404}, lambda: client.get_new_releases(limit=5)),
        ("get_featured_playlists", {200, 403, 404}, lambda: client.get_featured_playlists(limit=5)),
        ("get_playback_state", NO_DEVICE, lambda: client.get_playback_state()),
        ("get_available_devices", NO_DEVICE, lambda: client.get_available_devices()),
        ("get_currently_playing", NO_DEVICE, lambda: client.get_currently_playing()),
        ("get_recently_played", OK, lambda: client.get_recently_played(limit=5)),
        ("get_queue", NO_DEVICE, lambda: client.get_queue()),
    ]
    optional = [
        ("get_track", OK, track, lambda i: client.get_track(i)),
        ("get_several_tracks", OK, track, lambda i: client.get_several_tracks([i])),
        ("check_saved_tracks", OK, track, lambda i: client.check_saved_tracks([i])),
        ("check_saved_items", OK, track, lambda i: client.check_saved_items([f"spotify:track:{i}"])),
        ("get_track_audio_features", {200, 403}, track, lambda i: client.get_track_audio_features(i)),
        ("get_several_audio_features", {200, 403}, track, lambda i: client.get_several_audio_features([i])),
        ("get_track_audio_analysis", {200, 403}, track, lambda i: client.get_track_audio_analysis(i)),
        ("get_album", OK, album, lambda i: client.get_album(i, market=market)),
        ("get_several_albums", OK, album, lambda i: client.get_several_albums([i])),
        ("get_album_tracks", OK, album, lambda i: client.get_album_tracks(i, limit=5)),
        ("check_saved_albums", OK, album, lambda i: client.check_saved_albums([i])),
        ("get_artist", OK, artist, lambda i: client.get_artist(i)),
        ("get_several_artists", OK, artist, lambda i: client.get_several_artists([i])),
        ("get_artist_albums", OK, artist, lambda i: client.get_artist_albums(i, limit=5)),
        ("get_artist_top_tracks", {200, 404}, artist,
         lambda i: client.get_artist_top_tracks(i, market or "US")),
        ("get_artist_related_artists", {200, 403, 404}, artist,
         lambda i: client.get_artist_related_artists(i)),
        ("check_following_artists", OK, artist, lambda i: client.check_following_artists([i])),
        ("get_playlist", OK, playlist, lambda i: client.get_playlist(i)),
        ("get_playlist_items", OK, playlist, lambda i: client.get_playlist_items(i, limit=5)),
        ("get_playlist_tracks", OK, playlist, lambda i: client.get_playlist_tracks(i, limit=5)),
        ("get_show", OK, show, lambda i: client.get_show(i)),
        ("get_several_shows", OK, show, lambda i: client.get_several_shows([i])),
        ("get_show_episodes", OK, show, lambda i: client.get_show_episodes(i, limit=5)),
        ("check_saved_shows", OK, show, lambda i: client.check_saved_shows([i])),
        ("get_episode", OK, episode, lambda i: client.get_episode(i)),
        ("get_several_episodes", OK, episode, lambda i: client.get_several_episodes([i])),
        ("check_saved_episodes", OK, episode, lambda i: client.check_saved_episodes([i])),
        ("get_audiobook", OK, audiobook, lambda i: client.get_audiobook(i)),
        ("get_several_audiobooks", OK, audiobook, lambda i: client.get_several_audiobooks([i])),
        ("get_audiobook_chapters", OK, audiobook, lambda i: client.get_audiobook_chapters(i, limit=5)),
        ("check_saved_audiobooks", OK, audiobook, lambda i: client.check_saved_audiobooks([i])),
        ("get_chapter", OK, chapter, lambda i: client.get_chapter(i)),
        ("get_several_chapters", OK, chapter, lambda i: client.get_several_chapters([i])),
    ]
    if k.get("category_id"):
        optional.append(("get_category", OK, lambda: k["category_id"],
                         lambda i: client.get_category(i)))
        optional.append(("get_category_playlists", {200, 403, 404}, lambda: k["category_id"],
                         lambda i: client.get_category_playlists(i, limit=5)))
    for name, allowed, getter, call in optional:
        found_id = getter()
        if found_id is None:
            rows.append((name, {"skipped"}, _skipped("no id for that type in this account")))
            continue
        rows.append((name, allowed, (lambda c=call, g=found_id: c(g))))
    return rows


async def probe(client, name, call):
    try:
        value = await call()
        if isinstance(value, tuple) and value and value[0] == "skipped":
            return (name, "skipped", value[1])
        return (name, 200, type(value).__name__)
    except SpotifyError as error:
        return (name, error.status, error.reason)
    except ScopeError as error:
        return (name, "scope", str(error))
    except (asyncio.TimeoutError, OSError) as error:
        return (name, "transport", str(error))


async def test_every_passive_endpoint_answers():
    load_dotenv()
    probe_client = Client()
    if not await probe_client.token_handler.storage.load_token(name="spotify"):
        pytest.skip("no saved token: run Client().login() once")

    results = []
    async with PacedClient() as client:
        await client.login()
        ids = await discover(client)
        for name, allowed, call in sweep(client, ids):
            name, status, detail = await probe(client, name, call)
            accepted = status in allowed if isinstance(status, int) else status in ("skipped", "scope")
            results.append((name, status, detail, accepted))

    report = "\n".join(f"{name:31} {str(status):>9}  {detail}" for name, status, detail, _ in results)
    print("\n" + report)
    blocked = [name for name, status, _, _ in results if status == "scope"]
    if blocked:
        print(f"\nno scope for the current token: {', '.join(blocked)}")
    bad = [(n, s, d) for n, s, d, ok in results if not ok]
    limited = [(n, s) for n, s, _, _ in results if s == 429]
    assert not limited, f"rate limited, pacing is wrong: {limited}"
    assert not bad, f"unexpected answers: {bad}"

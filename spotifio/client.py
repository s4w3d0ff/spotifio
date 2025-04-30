import logging
import aiohttp
import asyncio
from .oauth import TokenHandler

logger = logging.getLogger(__name__)

base_url = "https://api.spotify.com/v1"

class RequestHandler:
    SCOPE_REQUIREMENTS = {
        ### PLAYER -----------------------------------------
        'get_playback_state': ['user-read-playback-state'],
        'transfer_playback': ['user-modify-playback-state'],
        'get_available_devices': ['user-read-playback-state'],
        'get_currently_playing': ['user-read-currently-playing'],
        'start_playback': ['user-modify-playback-state'],
        'pause_playback': ['user-modify-playback-state'],
        'skip_to_next': ['user-modify-playback-state'],
        'skip_to_previous': ['user-modify-playback-state'],
        'seek_to_position': ['user-modify-playback-state'],
        'set_repeat_mode': ['user-modify-playback-state'],
        'set_playback_volume': ['user-modify-playback-state'],
        'set_shuffle': ['user-modify-playback-state'],
        'get_recently_played': ['user-read-recently-played'],
        'add_to_queue': ['user-modify-playback-state'],
        'get_queue': ['user-read-playback-state'],
        ### USERS ------------------------------------------
        'get_current_user': ['user-read-private', 'user-read-email'],
        'get_user_profile': [],
        'get_followed_artists': ['user-follow-read'],
        'follow_artists': ['user-follow-modify'],
        'follow_users': ['user-follow-modify'],
        'unfollow_artists': ['user-follow-modify'],
        'unfollow_users': ['user-follow-modify'],
        'check_following_artists': ['user-follow-read'],
        'check_following_users': ['user-follow-read'],
        'follow_playlist': ['playlist-modify-public', 'playlist-modify-private'],
        'unfollow_playlist': ['playlist-modify-public', 'playlist-modify-private'],
        'get_user_top_items': ['user-top-read'],
        ### PLAYLISTS -------------------------------------
        'get_playlist': [],
        'change_playlist_details': ['playlist-modify-public', 'playlist-modify-private'],
        'get_playlist_tracks': [],
        'add_playlist_tracks': ['playlist-modify-public', 'playlist-modify-private'],
        'update_playlist_tracks': ['playlist-modify-public', 'playlist-modify-private'],
        'remove_playlist_tracks': ['playlist-modify-public', 'playlist-modify-private'],
        'get_current_user_playlists': ['playlist-read-private'],
        'get_user_playlists': [],
        'create_playlist': ['playlist-modify-public', 'playlist-modify-private'],
        'get_featured_playlists': [],
        'get_category_playlists': [],
        ### SEARCH ---------------------------------------
        'search': [],
        ### TRACKS --------------------------------------
        'get_track': [],
        'get_several_tracks': [],
        'get_user_saved_tracks': ['user-library-read'],
        'save_tracks': ['user-library-modify'],
        'remove_saved_tracks': ['user-library-modify'],
        'check_saved_tracks': ['user-library-read'],
        'get_track_audio_features': [],
        'get_several_audio_features': [],
        'get_track_audio_analysis': [],
        ### ALBUMS ----------------------------------------
        'get_album': [],
        'get_several_albums': [],
        'get_album_tracks': [],
        'get_user_saved_albums': ['user-library-read'],
        'save_albums': ['user-library-modify'],
        'remove_saved_albums': ['user-library-modify'],
        'check_saved_albums': ['user-library-read'],
        'get_new_releases': [],
        ### ARTISTS --------------------------------------
        'get_artist': [],
        'get_several_artists': [],
        'get_artist_albums': [],
        'get_artist_top_tracks': [],
        'get_artist_related_artists': [],
        ### AUDIOBOOKS ----------------------------------
        'get_audiobook': ['user-read-playback-position'],
        'get_several_audiobooks': ['user-read-playback-position'],
        'get_audiobook_chapters': ['user-read-playback-position'],
        'get_user_saved_audiobooks': ['user-library-read'],
        'save_audiobooks': ['user-library-modify'],
        'remove_saved_audiobooks': ['user-library-modify'],
        'check_saved_audiobooks': ['user-library-read'],
        ### CATEGORIES ------------------------------------
        'get_categories': [],
        'get_category': [],
        ### CHAPTERS ------------------------------------
        'get_chapter': ['user-read-playback-position'],
        'get_several_chapters': ['user-read-playback-position'],
        ### EPISODES ------------------------------------
        'get_episode': ['user-read-playback-position'],
        'get_several_episodes': ['user-read-playback-position'],
        'get_user_saved_episodes': ['user-library-read'],
        'save_episodes': ['user-library-modify'],
        'remove_saved_episodes': ['user-library-modify'],
        'check_saved_episodes': ['user-library-read'],
        ### GENRES ------------------------------------
        'get_available_genre_seeds': [],
        ### MARKETS -----------------------------------
        'get_available_markets': [],
        ### SHOWS ------------------------------------
        'get_show': ['user-read-playback-position'],
        'get_several_shows': ['user-read-playback-position'],
        'get_show_episodes': ['user-read-playback-position'],
        'get_user_saved_shows': ['user-library-read'],
        'save_shows': ['user-library-modify'],
        'remove_saved_shows': ['user-library-modify'],
        'check_saved_shows': ['user-library-read']
    }

    def __init__(self, token_handler=None, *args, **kwargs):
        self.token_handler = token_handler or TokenHandler(*args, **kwargs)

    async def _check_scope(self, method_name):
        current_scopes = set(self.token_handler.scope)
        required_scopes = set(self.SCOPE_REQUIREMENTS.get(method_name, []))
        missing_scopes = required_scopes - current_scopes
        if missing_scopes:
            raise Exception(f"Missing required scopes for {method_name}: {', '.join(missing_scopes)}")

    async def login(self, token=None):
        """ Sets up the token """
        await self.token_handler._login(token)
    
    async def _request(self, method, endpoint, params=None, data=None, headers=None):
        """ Base Request Method for Spotify API calls """
        # Get the current valid token
        token = await self.token_handler.get_token()
        # Setup default headers with authorization
        default_headers = {
            "Authorization": f"Bearer {token['access_token']}",
            "Content-Type": "application/json"
        }
        # Merge default headers with any additional headers
        if headers:
            default_headers.update(headers)
        # Create the full URL
        url = f"{base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"_request({method=}, {url=}, {params=}, {data=})")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method=method, url=url, params=params, json=data, headers=default_headers) as resp:
                    # Check if the response status is successful
                    if resp.status == 204:  # No content
                        return None
                    if resp.status == 401:  # bad token
                        await self.token_handler._refresh_token()
                        return await self._request(method, endpoint, params, data, headers)
                    if resp.status == 429:  # Rate limiting
                        retry_after = int(resp.headers.get('Retry-After', 1))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._request(method, endpoint, params, data, headers)
                    if not resp.ok:
                        error_text = await resp.text()
                        raise Exception(f"Request failed with status {resp.status}: {error_text}")
                    try:
                        return await resp.json()
                    except:
                        return resp
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")



class Client(RequestHandler):
    ### PLAYER Methods -----------------------------------------
    async def get_playback_state(self, market=None, additional_types=None):
        await self._check_scope('get_playback_state')
        params = {}
        if market:
            params['market'] = market
        if additional_types:
            params['additional_types'] = ','.join(additional_types)
        return await self._request('GET', 'me/player', params=params)

    async def transfer_playback(self, device_ids, play=None):
        await self._check_scope('transfer_playback')
        data = {'device_ids': device_ids}
        if play is not None:
            data['play'] = play
        await self._request('PUT', 'me/player', data=data)

    async def get_available_devices(self):
        await self._check_scope('get_available_devices')
        return await self._request('GET', 'me/player/devices')

    async def get_currently_playing(self, market=None, additional_types=None):
        await self._check_scope('get_currently_playing')
        params = {}
        if market:
            params['market'] = market
        if additional_types:
            params['additional_types'] = ','.join(additional_types)
        return await self._request('GET', 'me/player/currently-playing', params=params)

    async def start_playback(self, device_id=None, context_uri=None, uris=None, offset=None, position_ms=None):
        await self._check_scope('start_playback')
        params = {'device_id': device_id} if device_id else {}
        data = {}
        if context_uri:
            data['context_uri'] = context_uri
        if uris:
            data['uris'] = uris
        if offset:
            data['offset'] = offset
        if position_ms is not None:
            data['position_ms'] = position_ms
        await self._request('PUT', 'me/player/play', params=params, data=data)

    async def pause_playback(self, device_id=None):
        await self._check_scope('pause_playback')
        params = {'device_id': device_id} if device_id else {}
        await self._request('PUT', 'me/player/pause', params=params)

    async def skip_to_next(self, device_id=None):
        await self._check_scope('skip_to_next')
        params = {'device_id': device_id} if device_id else {}
        await self._request('POST', 'me/player/next', params=params)

    async def skip_to_previous(self, device_id=None):
        await self._check_scope('skip_to_previous')
        params = {'device_id': device_id} if device_id else {}
        await self._request('POST', 'me/player/previous', params=params)

    async def seek_to_position(self, position_ms, device_id=None):
        await self._check_scope('seek_to_position')
        params = {'position_ms': position_ms}
        if device_id:
            params['device_id'] = device_id
        await self._request('PUT', 'me/player/seek', params=params)

    async def set_repeat_mode(self, state, device_id=None):
        await self._check_scope('set_repeat_mode')
        params = {'state': state}
        if device_id:
            params['device_id'] = device_id
        await self._request('PUT', 'me/player/repeat', params=params)

    async def set_playback_volume(self, volume_percent, device_id=None):
        await self._check_scope('set_playback_volume')
        params = {'volume_percent': volume_percent}
        if device_id:
            params['device_id'] = device_id
        await self._request('PUT', 'me/player/volume', params=params)

    async def set_shuffle(self, state, device_id=None):
        await self._check_scope('set_shuffle')
        params = {'state': str(state).lower()}
        if device_id:
            params['device_id'] = device_id
        await self._request('PUT', 'me/player/shuffle', params=params)

    async def get_recently_played(self, limit=20, after=None, before=None):
        await self._check_scope('get_recently_played')
        params = {'limit': limit}
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        return await self._request('GET', 'me/player/recently-played', params=params)

    async def add_to_queue(self, uri, device_id=None):
        await self._check_scope('add_to_queue')
        params = {'uri': uri}
        if device_id:
            params['device_id'] = device_id
        await self._request('POST', 'me/player/queue', params=params)

    async def get_queue(self):
        await self._check_scope('get_queue')
        return await self._request('GET', 'me/player/queue')

    ### USERS Methods -----------------------------------------
    async def get_current_user(self):
        await self._check_scope('get_current_user')
        return await self._request('GET', 'me')

    async def get_user_profile(self, user_id):
        await self._check_scope('get_user_profile')
        return await self._request('GET', f'users/{user_id}')

    async def get_followed_artists(self, after=None, limit=20):
        await self._check_scope('get_followed_artists')
        params = {
            'type': 'artist',
            'limit': limit
        }
        if after:
            params['after'] = after
        return await self._request('GET', 'me/following', params=params)

    async def follow_artists(self, ids):
        await self._check_scope('follow_artists')
        return await self._request('PUT', 'me/following', params={'type': 'artist'}, data={'ids': ids})

    async def follow_users(self, ids):
        await self._check_scope('follow_users')
        return await self._request('PUT', 'me/following', params={'type': 'user'}, data={'ids': ids})

    async def unfollow_artists(self, ids):
        await self._check_scope('unfollow_artists')
        return await self._request('DELETE', 'me/following', params={'type': 'artist'}, data={'ids': ids})

    async def unfollow_users(self, ids):
        await self._check_scope('unfollow_users')
        return await self._request('DELETE', 'me/following', params={'type': 'user'}, data={'ids': ids})

    async def check_following_artists(self, ids):
        await self._check_scope('check_following_artists')
        params = {
            'type': 'artist',
            'ids': ','.join(ids)
        }
        return await self._request('GET', 'me/following/contains', params=params)

    async def check_following_users(self, ids):
        await self._check_scope('check_following_users')
        params = {
            'type': 'user',
            'ids': ','.join(ids)
        }
        return await self._request('GET', 'me/following/contains', params=params)

    async def follow_playlist(self, playlist_id, public=True):
        await self._check_scope('follow_playlist')
        data = {'public': public}
        return await self._request('PUT', f'playlists/{playlist_id}/followers', data=data)

    async def unfollow_playlist(self, playlist_id):
        await self._check_scope('unfollow_playlist')
        return await self._request('DELETE', f'playlists/{playlist_id}/followers')

    async def get_user_top_items(self, type, limit=20, offset=0, time_range='medium_term'):
        await self._check_scope('get_user_top_items')
        params = {
            'limit': limit,
            'offset': offset,
            'time_range': time_range
        }
        return await self._request('GET', f'me/top/{type}', params=params)

    ### PLAYLIST Methods -----------------------------------
    async def get_playlist(self, playlist_id, market=None, fields=None):
        await self._check_scope('get_playlist')
        params = {}
        if market:
            params['market'] = market
        if fields:
            params['fields'] = fields
        return await self._request('GET', f'playlists/{playlist_id}', params=params)

    async def change_playlist_details(self, playlist_id, name=None, public=None, collaborative=None, description=None):
        await self._check_scope('change_playlist_details')
        data = {}
        if name is not None:
            data['name'] = name
        if public is not None:
            data['public'] = public
        if collaborative is not None:
            data['collaborative'] = collaborative
        if description is not None:
            data['description'] = description
        return await self._request('PUT', f'playlists/{playlist_id}', data=data)

    async def get_playlist_tracks(self, playlist_id, market=None, fields=None, limit=20, offset=0):
        await self._check_scope('get_playlist_tracks')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        if fields:
            params['fields'] = fields
        return await self._request('GET', f'playlists/{playlist_id}/tracks', params=params)

    async def add_playlist_tracks(self, playlist_id, uris, position=None):
        await self._check_scope('add_playlist_tracks')
        params = {'uris': uris if isinstance(uris, str) else ','.join(uris)}
        if position is not None:
            params['position'] = position
        return await self._request('POST', f'playlists/{playlist_id}/tracks', params=params)

    async def update_playlist_tracks(self, playlist_id, uris):
        await self._check_scope('update_playlist_tracks')
        data = {'uris': uris if isinstance(uris, list) else [uris]}
        return await self._request('PUT', f'playlists/{playlist_id}/tracks', data=data)

    async def remove_playlist_tracks(self, playlist_id, tracks):
        await self._check_scope('remove_playlist_tracks')
        data = {'tracks': tracks}
        return await self._request('DELETE', f'playlists/{playlist_id}/tracks', data=data)

    async def get_current_user_playlists(self, limit=20, offset=0):
        await self._check_scope('get_current_user_playlists')
        params = {
            'limit': limit,
            'offset': offset
        }
        return await self._request('GET', 'me/playlists', params=params)

    async def get_user_playlists(self, user_id, limit=20, offset=0):
        await self._check_scope('get_user_playlists')
        params = {
            'limit': limit,
            'offset': offset
        }
        return await self._request('GET', f'users/{user_id}/playlists', params=params)

    async def create_playlist(self, user_id, name, public=True, collaborative=False, description=None):
        await self._check_scope('create_playlist')
        data = {
            'name': name,
            'public': public,
            'collaborative': collaborative
        }
        if description:
            data['description'] = description
        return await self._request('POST', f'users/{user_id}/playlists', data=data)

    async def get_featured_playlists(self, locale=None, country=None, limit=20, offset=0):
        await self._check_scope('get_featured_playlists')
        params = {
            'limit': limit,
            'offset': offset
        }
        if locale:
            params['locale'] = locale
        if country:
            params['country'] = country
        return await self._request('GET', 'browse/featured-playlists', params=params)

    async def get_category_playlists(self, category_id, country=None, limit=20, offset=0):
        await self._check_scope('get_category_playlists')
        params = {
            'limit': limit,
            'offset': offset
        }
        if country:
            params['country'] = country
        return await self._request('GET', f'browse/categories/{category_id}/playlists', params=params)

    ### SEARCH Methods ------------------------------------
    async def search(self, q, types, market=None, limit=20, offset=0, include_external=None):
        await self._check_scope('search')
        params = {
            'q': q,
            'type': ','.join(types) if isinstance(types, list) else types,
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        if include_external:
            params['include_external'] = include_external
        return await self._request('GET', 'search', params=params)

    ### TRACKS Methods -----------------------------------
    async def get_track(self, track_id, market=None):
        await self._check_scope('get_track')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'tracks/{track_id}', params=params)

    async def get_several_tracks(self, track_ids, market=None):
        await self._check_scope('get_several_tracks')
        params = {'ids': ','.join(track_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'tracks', params=params)

    async def get_user_saved_tracks(self, market=None, limit=20, offset=0):
        await self._check_scope('get_user_saved_tracks')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', 'me/tracks', params=params)

    async def save_tracks(self, track_ids):
        await self._check_scope('save_tracks')
        return await self._request('PUT', 'me/tracks', data={'ids': track_ids})

    async def remove_saved_tracks(self, track_ids):
        await self._check_scope('remove_saved_tracks')
        return await self._request('DELETE', 'me/tracks', data={'ids': track_ids})

    async def check_saved_tracks(self, track_ids):
        await self._check_scope('check_saved_tracks')
        params = {'ids': ','.join(track_ids)}
        return await self._request('GET', 'me/tracks/contains', params=params)

    async def get_track_audio_features(self, track_id):
        await self._check_scope('get_track_audio_features')
        return await self._request('GET', f'audio-features/{track_id}')

    async def get_several_audio_features(self, track_ids):
        await self._check_scope('get_several_audio_features')
        params = {'ids': ','.join(track_ids)}
        return await self._request('GET', 'audio-features', params=params)

    async def get_track_audio_analysis(self, track_id):
        await self._check_scope('get_track_audio_analysis')
        return await self._request('GET', f'audio-analysis/{track_id}')


    ### ALBUMS Methods ------------------------------------
    async def get_album(self, album_id, market=None):
        await self._check_scope('get_album')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'albums/{album_id}', params=params)

    async def get_several_albums(self, album_ids, market=None):
        await self._check_scope('get_several_albums')
        params = {'ids': ','.join(album_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'albums', params=params)

    async def get_album_tracks(self, album_id, market=None, limit=20, offset=0):
        await self._check_scope('get_album_tracks')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', f'albums/{album_id}/tracks', params=params)

    async def get_user_saved_albums(self, limit=20, offset=0, market=None):
        await self._check_scope('get_user_saved_albums')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', 'me/albums', params=params)

    async def save_albums(self, album_ids):
        await self._check_scope('save_albums')
        return await self._request('PUT', 'me/albums', data={'ids': album_ids})

    async def remove_saved_albums(self, album_ids):
        await self._check_scope('remove_saved_albums')
        return await self._request('DELETE', 'me/albums', data={'ids': album_ids})

    async def check_saved_albums(self, album_ids):
        await self._check_scope('check_saved_albums')
        params = {'ids': ','.join(album_ids)}
        return await self._request('GET', 'me/albums/contains', params=params)

    async def get_new_releases(self, country=None, limit=20, offset=0):
        await self._check_scope('get_new_releases')
        params = {
            'limit': limit,
            'offset': offset
        }
        if country:
            params['country'] = country
        return await self._request('GET', 'browse/new-releases', params=params)

    ### ARTISTS Methods ----------------------------------
    async def get_artist(self, artist_id):
        await self._check_scope('get_artist')
        return await self._request('GET', f'artists/{artist_id}')

    async def get_several_artists(self, artist_ids):
        await self._check_scope('get_several_artists')
        params = {'ids': ','.join(artist_ids)}
        return await self._request('GET', 'artists', params=params)

    async def get_artist_albums(self, artist_id, include_groups=None, market=None, limit=20, offset=0):
        await self._check_scope('get_artist_albums')
        params = {
            'limit': limit,
            'offset': offset
        }
        if include_groups:
            params['include_groups'] = ','.join(include_groups)
        if market:
            params['market'] = market
        return await self._request('GET', f'artists/{artist_id}/albums', params=params)

    async def get_artist_top_tracks(self, artist_id, market):
        await self._check_scope('get_artist_top_tracks')
        params = {'market': market}
        return await self._request('GET', f'artists/{artist_id}/top-tracks', params=params)

    async def get_artist_related_artists(self, artist_id):
        await self._check_scope('get_artist_related_artists')
        return await self._request('GET', f'artists/{artist_id}/related-artists')

    ### AUDIOBOOKS Methods -------------------------------
    async def get_audiobook(self, audiobook_id, market=None):
        await self._check_scope('get_audiobook')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'audiobooks/{audiobook_id}', params=params)

    async def get_several_audiobooks(self, audiobook_ids, market=None):
        await self._check_scope('get_several_audiobooks')
        params = {'ids': ','.join(audiobook_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'audiobooks', params=params)

    async def get_audiobook_chapters(self, audiobook_id, market=None, limit=20, offset=0):
        await self._check_scope('get_audiobook_chapters')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', f'audiobooks/{audiobook_id}/chapters', params=params)

    async def get_user_saved_audiobooks(self, limit=20, offset=0):
        await self._check_scope('get_user_saved_audiobooks')
        params = {
            'limit': limit,
            'offset': offset
        }
        return await self._request('GET', 'me/audiobooks', params=params)

    async def save_audiobooks(self, audiobook_ids):
        await self._check_scope('save_audiobooks')
        return await self._request('PUT', 'me/audiobooks', data={'ids': audiobook_ids})

    async def remove_saved_audiobooks(self, audiobook_ids):
        await self._check_scope('remove_saved_audiobooks')
        return await self._request('DELETE', 'me/audiobooks', data={'ids': audiobook_ids})

    async def check_saved_audiobooks(self, audiobook_ids):
        await self._check_scope('check_saved_audiobooks')
        params = {'ids': ','.join(audiobook_ids)}
        return await self._request('GET', 'me/audiobooks/contains', params=params)

    ### CATEGORIES Methods ------------------------------------
    async def get_categories(self, country=None, locale=None, limit=20, offset=0):
        await self._check_scope('get_categories')
        params = {
            'limit': limit,
            'offset': offset
        }
        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale
        return await self._request('GET', 'browse/categories', params=params)

    async def get_category(self, category_id, country=None, locale=None):
        await self._check_scope('get_category')
        params = {}
        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale
        return await self._request('GET', f'browse/categories/{category_id}', params=params)

    ### CHAPTERS Methods ------------------------------------
    async def get_chapter(self, chapter_id, market=None):
        await self._check_scope('get_chapter')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'chapters/{chapter_id}', params=params)

    async def get_several_chapters(self, chapter_ids, market=None):
        await self._check_scope('get_several_chapters')
        params = {'ids': ','.join(chapter_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'chapters', params=params)

    ### EPISODES Methods ------------------------------------
    async def get_episode(self, episode_id, market=None):
        await self._check_scope('get_episode')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'episodes/{episode_id}', params=params)

    async def get_several_episodes(self, episode_ids, market=None):
        await self._check_scope('get_several_episodes')
        params = {'ids': ','.join(episode_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'episodes', params=params)

    async def get_user_saved_episodes(self, market=None, limit=20, offset=0):
        await self._check_scope('get_user_saved_episodes')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', 'me/episodes', params=params)

    async def save_episodes(self, episode_ids):
        await self._check_scope('save_episodes')
        return await self._request('PUT', 'me/episodes', data={'ids': episode_ids})

    async def remove_saved_episodes(self, episode_ids):
        await self._check_scope('remove_saved_episodes')
        return await self._request('DELETE', 'me/episodes', data={'ids': episode_ids})

    async def check_saved_episodes(self, episode_ids):
        await self._check_scope('check_saved_episodes')
        params = {'ids': ','.join(episode_ids)}
        return await self._request('GET', 'me/episodes/contains', params=params)

    ### GENRES Methods ------------------------------------
    async def get_available_genre_seeds(self):
        await self._check_scope('get_available_genre_seeds')
        return await self._request('GET', 'recommendations/available-genre-seeds')

    ### MARKETS Methods ------------------------------------
    async def get_available_markets(self):
        await self._check_scope('get_available_markets')
        return await self._request('GET', 'markets')

    ### SHOWS Methods ------------------------------------
    async def get_show(self, show_id, market=None):
        await self._check_scope('get_show')
        params = {}
        if market:
            params['market'] = market
        return await self._request('GET', f'shows/{show_id}', params=params)

    async def get_several_shows(self, show_ids, market=None):
        await self._check_scope('get_several_shows')
        params = {'ids': ','.join(show_ids)}
        if market:
            params['market'] = market
        return await self._request('GET', 'shows', params=params)

    async def get_show_episodes(self, show_id, market=None, limit=20, offset=0):
        await self._check_scope('get_show_episodes')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        return await self._request('GET', f'shows/{show_id}/episodes', params=params)

    async def get_user_saved_shows(self, limit=20, offset=0):
        await self._check_scope('get_user_saved_shows')
        params = {
            'limit': limit,
            'offset': offset
        }
        return await self._request('GET', 'me/shows', params=params)

    async def save_shows(self, show_ids):
        await self._check_scope('save_shows')
        return await self._request('PUT', 'me/shows', data={'ids': show_ids})

    async def remove_saved_shows(self, show_ids):
        await self._check_scope('remove_saved_shows')
        return await self._request('DELETE', 'me/shows', data={'ids': show_ids})

    async def check_saved_shows(self, show_ids):
        await self._check_scope('check_saved_shows')
        params = {'ids': ','.join(show_ids)}
        return await self._request('GET', 'me/shows/contains', params=params)

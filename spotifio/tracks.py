from .request import RequestHandler


class TrackMethods(RequestHandler):
    """Track, saved-track and library-item endpoints."""

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

    async def save_library_items(self, uris):
        """PUT /me/library: the endpoint the docs list as the replacement for saving
        tracks, albums, shows, episodes and audiobooks to the library.
        `uris` is a list of Spotify URIs, e.g. ['spotify:track:4iV5W9uYEdYUVa79Axb7Rh']."""
        await self._check_scope('save_library_items')
        return await self._request('PUT', 'me/library', params={'uris': ','.join(uris)})

    async def remove_library_items(self, uris):
        """DELETE /me/library: replacement for the per-type remove endpoints."""
        await self._check_scope('remove_library_items')
        return await self._request('DELETE', 'me/library', params={'uris': ','.join(uris)})

    async def check_saved_items(self, uris):
        """GET /me/library/contains: replacement for the per-type contains endpoints."""
        await self._check_scope('check_saved_items')
        return await self._request('GET', 'me/library/contains', params={'uris': ','.join(uris)})

    async def get_track_audio_features(self, track_id):
        """Deprecated in the Spotify docs; Spotify answers 403 with no message. No
        replacement is documented."""
        await self._check_scope('get_track_audio_features')
        return await self._request('GET', f'audio-features/{track_id}')

    async def get_several_audio_features(self, track_ids):
        """Deprecated in the Spotify docs; Spotify answers 403 with no message."""
        await self._check_scope('get_several_audio_features')
        params = {'ids': ','.join(track_ids)}
        return await self._request('GET', 'audio-features', params=params)

    async def get_track_audio_analysis(self, track_id):
        """Deprecated in the Spotify docs; Spotify answers 403 with no message."""
        await self._check_scope('get_track_audio_analysis')
        return await self._request('GET', f'audio-analysis/{track_id}')

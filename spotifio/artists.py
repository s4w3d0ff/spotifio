from .request import RequestHandler


class ArtistMethods(RequestHandler):
    """Artist endpoints."""

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
        """Deprecated in the Spotify docs; Spotify answers 404. No replacement is
        documented."""
        await self._check_scope('get_artist_related_artists')
        return await self._request('GET', f'artists/{artist_id}/related-artists')

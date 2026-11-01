from .request import RequestHandler


class AlbumMethods(RequestHandler):
    """Album and saved-album endpoints."""

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

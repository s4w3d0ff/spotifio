from .request import RequestHandler


class PlaylistMethods(RequestHandler):
    """Playlist endpoints: tracks variants and items variants."""

    async def get_playlist(self, playlist_id, market=None, fields=None):
        """GET /playlists/{playlist_id}. Editorial playlists (37i9dQZF...) answer 404."""
        await self._check_scope('get_playlist')
        params = {}
        if market:
            params['market'] = market
        if fields:
            params['fields'] = fields
        return await self._request('GET', f'playlists/{playlist_id}', params=params)

    async def get_playlist_items(self, playlist_id, market=None, fields=None, limit=20,
                                 offset=0, additional_types=None):
        """GET /playlists/{playlist_id}/items. Tracks and episodes together. 403 unless the user owns the playlist or collaborates on it."""
        await self._check_scope('get_playlist_items')
        params = {
            'limit': limit,
            'offset': offset
        }
        if market:
            params['market'] = market
        if fields:
            params['fields'] = fields
        if additional_types:
            params['additional_types'] = ','.join(additional_types)
        return await self._request('GET', f'playlists/{playlist_id}/items', params=params)

    async def add_playlist_items(self, playlist_id, uris, position=None):
        """POST /playlists/{playlist_id}/items. Replaces POST /playlists/{playlist_id}/tracks."""
        await self._check_scope('add_playlist_items')
        params = {'uris': ','.join(uris)}
        if position is not None:
            params['position'] = position
        return await self._request('POST', f'playlists/{playlist_id}/items', params=params)

    async def remove_playlist_items(self, playlist_id, items):
        """DELETE /playlists/{playlist_id}/items. items is a list of objects: [{'uri': 'spotify:track:4iV5W9uYEdYUVa79Axb7Rh'}]."""
        await self._check_scope('remove_playlist_items')
        return await self._request('DELETE', f'playlists/{playlist_id}/items', data={'items': items})

    async def update_playlist_items(self, playlist_id, uris=None, range_start=None,
                                    insert_before=None, range_length=None, snapshot_id=None):
        """PUT /playlists/{playlist_id}/items. uris replaces items; range_start, insert_before, range_length, snapshot_id reorder them."""
        await self._check_scope('update_playlist_items')
        params = {}
        if uris:
            params['uris'] = ','.join(uris)
        data = {}
        for key, value in (('range_start', range_start), ('insert_before', insert_before),
                           ('range_length', range_length), ('snapshot_id', snapshot_id)):
            if value is not None:
                data[key] = value
        return await self._request('PUT', f'playlists/{playlist_id}/items', params=params, data=data or None)

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
        """POST users/{user_id}/playlists. Docs point at POST /me/playlists."""
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
        """GET /browse/featured-playlists. Not in the docs availability list."""
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
        """GET /browse/categories/{category_id}/playlists. Not in the docs availability list."""
        await self._check_scope('get_category_playlists')
        params = {
            'limit': limit,
            'offset': offset
        }
        if country:
            params['country'] = country
        return await self._request('GET', f'browse/categories/{category_id}/playlists', params=params)

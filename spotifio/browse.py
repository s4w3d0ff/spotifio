from .request import RequestHandler


class BrowseMethods(RequestHandler):
    """Search, category, genre seed and market endpoints."""

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

    async def get_available_genre_seeds(self):
        """Deprecated in the Spotify docs along with /recommendations; Spotify answers
        404. No replacement is documented."""
        await self._check_scope('get_available_genre_seeds')
        return await self._request('GET', 'recommendations/available-genre-seeds')

    async def get_available_markets(self):
        await self._check_scope('get_available_markets')
        return await self._request('GET', 'markets')

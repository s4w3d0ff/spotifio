from .request import RequestHandler


class BrowseMethods(RequestHandler):
    """Search, category, genre seed and market endpoints."""

    async def search(self, q, types, market=None, limit=20, offset=0, include_external=None):
        """GET /search. Docs: limit 0-10 default 5, offset up to 1000. Default here 20."""
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
        """GET /browse/categories. Removed for Development Mode apps. No replacement."""
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
        """GET /browse/categories/{category_id}. Removed for Development Mode apps."""
        await self._check_scope('get_category')
        params = {}
        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale
        return await self._request('GET', f'browse/categories/{category_id}', params=params)

    async def get_available_genre_seeds(self):
        """GET /recommendations/available-genre-seeds. Not in the docs availability list. 404."""
        await self._check_scope('get_available_genre_seeds')
        return await self._request('GET', 'recommendations/available-genre-seeds')

    async def get_available_markets(self):
        """GET /markets. Removed for Development Mode apps."""
        await self._check_scope('get_available_markets')
        return await self._request('GET', 'markets')

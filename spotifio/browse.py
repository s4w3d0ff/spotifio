from .request import RequestHandler


class BrowseMethods(RequestHandler):
    """Search, category, genre seed and market endpoints."""

    async def search(self, q, types, market=None, limit=20, offset=0, include_external=None):
        """GET /search. The docs now document limit as 0-10 with a default of 5, and
        offset up to 1000. The default here stays 20 because apps in extended quota
        mode still accept it; pass a smaller limit for a Development Mode app."""
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
        """GET /browse/categories: listed as removed for Development Mode apps in the
        February 2026 changelog, with no replacement. The request is still made, so an
        app in extended quota mode gets its 200."""
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
        """GET /browse/categories/{category_id}: listed as removed for Development Mode
        apps, with no replacement."""
        await self._check_scope('get_category')
        params = {}
        if country:
            params['country'] = country
        if locale:
            params['locale'] = locale
        return await self._request('GET', f'browse/categories/{category_id}', params=params)

    async def get_available_genre_seeds(self):
        """GET /recommendations/available-genre-seeds: not in the Spotify docs list of
        endpoints that remain available, and no replacement is documented. Spotify
        answers 404 here. The request is still made."""
        await self._check_scope('get_available_genre_seeds')
        return await self._request('GET', 'recommendations/available-genre-seeds')

    async def get_available_markets(self):
        """GET /markets: listed as removed for Development Mode apps, with no
        replacement documented."""
        await self._check_scope('get_available_markets')
        return await self._request('GET', 'markets')

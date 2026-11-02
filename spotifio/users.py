from .request import RequestHandler


class UserMethods(RequestHandler):
    """User profile and follow endpoints."""

    async def get_current_user(self):
        await self._check_scope('get_current_user')
        return await self._request('GET', 'me')

    async def get_user_profile(self, user_id):
        """GET /users/{user_id}: listed as removed for Development Mode apps in the
        February 2026 changelog, with no replacement (GET /me covers your own profile).
        Live behaviour still varies: some accounts answer 200, others 404 'Resource not
        found'. Use get_current_user() instead: since the May 2026 changelog its
        'account_id' field is the stable public identifier."""
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
        """PUT /me/following?type=artist: the February 2026 changelog points follows at
        PUT /me/library for Development Mode apps, although that endpoint's own page
        lists user and playlist URIs and not artist URIs."""
        await self._check_scope('follow_artists')
        return await self._request('PUT', 'me/following', params={'type': 'artist'}, data={'ids': ids})

    async def follow_users(self, ids):
        """PUT /me/following?type=user: for Development Mode apps the changelog points
        follows at PUT /me/library, which does list spotify:user: URIs."""
        await self._check_scope('follow_users')
        return await self._request('PUT', 'me/following', params={'type': 'user'}, data={'ids': ids})

    async def unfollow_artists(self, ids):
        """DELETE /me/following?type=artist: for Development Mode apps the changelog
        points unfollows at DELETE /me/library."""
        await self._check_scope('unfollow_artists')
        return await self._request('DELETE', 'me/following', params={'type': 'artist'}, data={'ids': ids})

    async def unfollow_users(self, ids):
        """DELETE /me/following?type=user: for Development Mode apps the changelog points
        unfollows at DELETE /me/library."""
        await self._check_scope('unfollow_users')
        return await self._request('DELETE', 'me/following', params={'type': 'user'}, data={'ids': ids})

    async def check_following_artists(self, ids):
        """GET /me/following/contains?type=artist: for Development Mode apps the docs
        route this through GET /me/library/contains, which lists spotify:artist: URIs."""
        await self._check_scope('check_following_artists')
        params = {
            'type': 'artist',
            'ids': ','.join(ids)
        }
        return await self._request('GET', 'me/following/contains', params=params)

    async def check_following_users(self, ids):
        """GET /me/following/contains?type=user: for Development Mode apps the docs route
        this through GET /me/library/contains."""
        await self._check_scope('check_following_users')
        params = {
            'type': 'user',
            'ids': ','.join(ids)
        }
        return await self._request('GET', 'me/following/contains', params=params)

    async def follow_playlist(self, playlist_id, public=True):
        """PUT /playlists/{playlist_id}/followers: listed as removed for Development Mode
        apps; the docs route saving a playlist through PUT /me/library with the
        spotify:playlist: URI. The `public` flag belongs to this endpoint and has no
        counterpart on /me/library."""
        await self._check_scope('follow_playlist')
        data = {'public': public}
        return await self._request('PUT', f'playlists/{playlist_id}/followers', data=data)

    async def unfollow_playlist(self, playlist_id):
        """DELETE /playlists/{playlist_id}/followers: listed as removed for Development
        Mode apps; the docs route it through DELETE /me/library with the
        spotify:playlist: URI."""
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

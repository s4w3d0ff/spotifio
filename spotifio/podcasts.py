from .request import RequestHandler


class PodcastMethods(RequestHandler):
    """Audiobook, chapter, episode and show endpoints."""

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

from .request import RequestHandler


class PlaybackMethods(RequestHandler):
    """Player endpoints."""

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

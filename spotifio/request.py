import asyncio
import json
import logging

import aiohttp

from .deprecations import FAILURE_HINTS, deprecation_note
from .errors import ScopeError, SpotifyError
from .oauth import TokenHandler
from .scopes import REQUIRED_SCOPES

logger = logging.getLogger(__name__)

base_url = "https://api.spotify.com/v1"

class RequestHandler:
    SCOPE_REQUIREMENTS = REQUIRED_SCOPES
    MAX_ATTEMPTS = 6

    def __init__(self, token_handler=None, *args, **kwargs):
        self.token_handler = token_handler or TokenHandler(*args, **kwargs)
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the HTTP session shared by all requests of this client."""
        if self._session is not None and not self._session.closed:
            await self._session.close()
        self._session = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        await self.close()

    async def _check_scope(self, method_name):
        requirements = self.SCOPE_REQUIREMENTS.get(method_name)
        if not requirements:
            return
        # A requirement is a scope name, or a tuple of names where any one is
        # enough, e.g. playlist writes accept the public or the private scope.
        def granted(names):
            names = {names} if isinstance(names, str) else set(names)
            return bool(names & set(self.token_handler.scope))

        def authorized(names):
            saved = set(self.token_handler.granted_scopes or ())
            if not saved:
                return True
            names = {names} if isinstance(names, str) else set(names)
            return bool(names & saved)

        missing = [req for req in requirements if not granted(req)]
        if missing:
            raise ScopeError(
                f"Missing required scopes for {method_name}: {_describe(missing)}. "
                "Pass scope=[...] to Client()/RequestHandler() or set SPOTIFIO_SCOPES."
            )
        not_authorized = [req for req in requirements if not authorized(req)]
        if not_authorized:
            raise ScopeError(
                f"The saved token was not authorized for {method_name}: it is missing "
                f"{_describe(not_authorized)}. Add them to SPOTIFIO_SCOPES and call "
                "login(reauth=True) to authorize again."
            )

    async def login(self, token=None, reauth=False):
        """ Sets up the token. reauth=True ignores the saved token and authorizes
        again, e.g. to get a token for a different set of scopes. """
        await self.token_handler._login(token, reauth=reauth)

    async def _request(self, method, endpoint, params=None, data=None, headers=None):
        """ Base Request Method for Spotify API calls.

        A 401 refreshes the token and a 429 waits for Retry-After, at most
        MAX_ATTEMPTS requests in total. When the attempts run out the last
        response is raised as a SpotifyError with its real status. A success
        Spotify did not send as JSON is returned as bytes. Transport failures
        raise aiohttp.ClientError.
        """
        url = f"{base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"_request({method=}, {url=}, {params=}, {data=})")
        try:
            for attempt in range(1, self.MAX_ATTEMPTS + 1):
                token = await self.token_handler.get_token()
                request_headers = {
                    "Authorization": f"Bearer {token['access_token']}",
                    "Content-Type": "application/json"
                }
                if headers:
                    request_headers.update(headers)
                session = await self._get_session()
                async with session.request(method=method, url=url, params=params,
                                           json=data, headers=request_headers) as resp:
                    if resp.status == 204:  # No content
                        return None
                    if resp.status == 401 and attempt < self.MAX_ATTEMPTS:  # bad token
                        logger.warning(f"Token rejected. Refreshing and retrying {method} {endpoint}")
                        await self.token_handler._refresh_token()
                        continue
                    if resp.status == 429 and attempt < self.MAX_ATTEMPTS:  # Rate limiting
                        retry_after = int(resp.headers.get('Retry-After', 1))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    if not resp.ok:
                        raise await self._error(method, endpoint, resp)
                    try:
                        return await resp.json()
                    except aiohttp.ContentTypeError:
                        return await resp.read()
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {str(e)}")
            raise
    async def _error(self, method, endpoint, resp):
        """ Build the SpotifyError for a failed response. """
        error_text = await resp.text()
        reason = None
        try:
            reason = json.loads(error_text).get('error', {}).get('message')
        except ValueError:
            pass
        # Spotify now answers some failures with a bare status, e.g. {"error":{"status":403}}
        if not reason:
            reason = FAILURE_HINTS.get(resp.status, "no message returned by Spotify")
        # If the docs mark this endpoint deprecated, say so and name
        # the endpoint the docs point at instead of guessing.
        note = deprecation_note(method, endpoint)
        if note and resp.status in (403, 404, 410):
            reason = f"{reason} [{method} {endpoint} is {note}]"
        return SpotifyError(resp.status, reason, error_text)


def _describe(requirements):
    """Render scope requirements, keeping the alternatives readable."""
    parts = []
    for req in requirements:
        parts.append(req if isinstance(req, str) else " or ".join(req))
    return ", ".join(parts)

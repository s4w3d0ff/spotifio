import logging
import aiohttp
import asyncio
from .deprecations import FAILURE_HINTS, deprecation_note
from .errors import SpotifyError
from .oauth import TokenHandler
from .scopes import REQUIRED_SCOPES

logger = logging.getLogger(__name__)

base_url = "https://api.spotify.com/v1"

class RequestHandler:
    SCOPE_REQUIREMENTS = REQUIRED_SCOPES

    def __init__(self, token_handler=None, *args, **kwargs):
        self.token_handler = token_handler or TokenHandler(*args, **kwargs)

    async def _check_scope(self, method_name):
        required_scopes = set(self.SCOPE_REQUIREMENTS.get(method_name, []))
        if not required_scopes:
            return
        configured = set(self.token_handler.scope)
        missing = required_scopes - configured
        if missing:
            raise Exception(
                f"Missing required scopes for {method_name}: {', '.join(sorted(missing))}. "
                "Pass scope=[...] to Client()/RequestHandler() or set SPOTIFIO_SCOPES."
            )
        granted = self.token_handler.granted_scopes
        if granted:
            missing_now = required_scopes - granted
            if missing_now:
                raise Exception(
                    f"The saved token was not authorized for {method_name}: it is missing "
                    f"{', '.join(sorted(missing_now))}. Add them to SPOTIFIO_SCOPES and call "
                    "login(reauth=True) to authorize again."
                )

    async def login(self, token=None, reauth=False):
        """ Sets up the token. reauth=True ignores the saved token and authorizes
        again, e.g. to get a token for a different set of scopes. """
        await self.token_handler._login(token, reauth=reauth)
    
    async def _request(self, method, endpoint, params=None, data=None, headers=None, _retries=0):
        """ Base Request Method for Spotify API calls """
        if _retries > 5:
            raise SpotifyError(0, f"Giving up on {method} {endpoint} after {_retries} attempts")
        # Get the current valid token
        token = await self.token_handler.get_token()
        # Setup default headers with authorization
        default_headers = {
            "Authorization": f"Bearer {token['access_token']}",
            "Content-Type": "application/json"
        }
        # Merge default headers with any additional headers
        if headers:
            default_headers.update(headers)
        # Create the full URL
        url = f"{base_url}/{endpoint.lstrip('/')}"
        logger.debug(f"_request({method=}, {url=}, {params=}, {data=})")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method=method, url=url, params=params, json=data, headers=default_headers) as resp:
                    # Check if the response status is successful
                    if resp.status == 204:  # No content
                        return None
                    if resp.status == 401:  # bad token
                        await self.token_handler._refresh_token()
                        return await self._request(method, endpoint, params, data, headers, _retries + 1)
                    if resp.status == 429:  # Rate limiting
                        retry_after = int(resp.headers.get('Retry-After', 1))
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._request(method, endpoint, params, data, headers, _retries + 1)
                    if not resp.ok:
                        error_text = await resp.text()
                        reason = None
                        try:
                            reason = (await resp.json()).get('error', {}).get('message')
                        except Exception:
                            pass
                        # Spotify now answers some failures with a bare status, e.g. {"error":{"status":403}}
                        if not reason:
                            reason = FAILURE_HINTS.get(resp.status, "no message returned by Spotify")
                        # If the docs mark this endpoint deprecated, say so and name
                        # the endpoint the docs point at instead of guessing.
                        note = deprecation_note(method, endpoint)
                        if note and resp.status in (403, 404, 410):
                            reason = f"{reason} [{method} {endpoint} is {note}]"
                        raise SpotifyError(resp.status, reason, error_text)
                    try:
                        return await resp.json()
                    except:
                        return resp
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {str(e)}")
            raise Exception(f"Request failed: {str(e)}")

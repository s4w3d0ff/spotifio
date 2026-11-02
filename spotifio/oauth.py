import aiohttp
import asyncio
import webbrowser
import os
import base64
import logging
import time
from aiohttp import web
from urllib.parse import urlparse, urlencode
from .env import require_env
from .errors import SpotifyError
from .storage import JSONStorage

logger = logging.getLogger(__name__)

TOKEN_NAME = "spotify"

closeBrowser = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <script>function closeWindow() {window.close();};</script>
    </head>
    <body>
        <button id="closeButton" onclick="closeWindow()">Close Window</button>
        <script>document.getElementById("closeButton").click();</script>
    </body>
</html>
"""

class WebServer:
    def __init__(self, host, port):
        self.app = web.Application()
        self.host = host
        self.port = port
        self._runner = None
        self._site = None

    def add_route(self, path, handler, method='GET', **kwargs):
        """Add a new route to the application."""
        self.app.router.add_route(method, path, handler, **kwargs)

    async def start(self):
        """Start the web server."""
        if self._runner is None:
            self._runner = web.AppRunner(self.app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self.host, self.port)
            await self._site.start()

    async def stop(self):
        """Stop the web server."""
        if self._site:
            await self._site.stop()
            self._site = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None


class TokenHandler:
    AUTH_CODE_TIMEOUT_SECONDS = 300

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None, scope=None, storage=None, *args, **kwargs):
        self.client_id = client_id or require_env("SPOTIFIO_CLIENT_ID")
        self.client_secret = client_secret or require_env("SPOTIFIO_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or require_env("SPOTIFIO_REDIRECT_URI")
        parsed_uri = urlparse(self.redirect_uri)
        if parsed_uri.scheme not in ("http", "https") or not parsed_uri.hostname or parsed_uri.port is None:
            raise ValueError(
                f"SPOTIFIO_REDIRECT_URI {self.redirect_uri!r} is not a valid http(s) URL with an explicit "
                "port, e.g. http://127.0.0.1:5050/spotify_oauth. It must be identical to a Redirect URI "
                "registered for your app at https://developer.spotify.com/dashboard"
            )
        if parsed_uri.hostname == "localhost":
            raise ValueError(
                f"SPOTIFIO_REDIRECT_URI {self.redirect_uri!r} uses host 'localhost', which Spotify rejects; "
                "use the loopback IP literal instead, e.g. http://127.0.0.1:5050/spotify_oauth"
            )
        self.host = parsed_uri.hostname
        self.port = parsed_uri.port
        # scopes: argument, SPOTIFIO_SCOPES, or none. Empty means no scopes.
        env_scope = (os.environ.get("SPOTIFIO_SCOPES") or "").replace(",", " ").split()
        self.scope = list(scope) if scope is not None else env_scope
        # scopes Spotify granted for this token; empty until a token exists
        self.granted_scopes = set()
        self.storage = storage or JSONStorage(*args, **kwargs)
        self._state = os.urandom(14).hex()
        self._auth_code = None
        self._auth_future = None
        self._token = None
        self._token_url = "https://accounts.spotify.com/api/token"
        self._token_headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        self.server = WebServer(self.host, self.port)
        self.server.add_route(parsed_uri.path or "/", self._callback_handler)
        # refresh token handler stuff
        self._refresh_event = asyncio.Event()
        self._refresh_task = None
        self._running = False
        
    async def _callback_handler(self, request):
        if request.query.get('state') != self._state:
            return web.Response(text="State mismatch. Authorization failed.", status=400)
        if 'error' in request.query:
            return web.Response(text=f"Authorization failed: {request.query['error']}", status=400)
        self._auth_code = request.query.get('code')
        if self._auth_code and self._auth_future is not None and not self._auth_future.done():
            self._auth_future.set_result(self._auth_code)
        return web.Response(text=closeBrowser, content_type='text/html', charset='utf-8')

    async def _get_auth_code(self):
        logger.warning(f"Opening browser to get Oauth code...")
        await self.server.start()
        self._auth_future = asyncio.Future()
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'state': self._state,
        }
        if self.scope:
            params['scope'] = ' '.join(self.scope)
        auth_link = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
        try:
            # open webbrowser with auth link
            webbrowser.open(auth_link)
        except Exception as e:
            # cant open webbrowser, show auth link for user to copy/paste
            logger.error(f"Couldn't open default browser! {e}\n{auth_link}")
        # wait for auth code, then always release the callback port
        try:
            await asyncio.wait_for(self._auth_future, timeout=self.AUTH_CODE_TIMEOUT_SECONDS)
        except (TimeoutError, asyncio.TimeoutError):
            # 3.10 raises asyncio.TimeoutError, not the builtin
            raise TimeoutError(
                f"No authorization code arrived at {self.redirect_uri} within "
                f"{self.AUTH_CODE_TIMEOUT_SECONDS} seconds. Authorize the link above "
                "in a browser, or run this on a machine that can open one."
            ) from None
        finally:
            await self.server.stop()
        logger.warning(f"Got Oauth code!")

    async def _token_request(self, data):
        """POST the token endpoint."""
        # temp store refresh token (spotify doesnt always send one)
        r_token = self._token.get('refresh_token') if self._token else None
        async with aiohttp.ClientSession() as session:
            async with session.post(self._token_url, headers=self._token_headers, data=data) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise SpotifyError(resp.status, "token request failed", error_text)
                self._token = await resp.json()
                if "refresh_token" not in self._token and r_token:
                    self._token['refresh_token'] = r_token
                self._token["expires_time"] = time.time()+int(self._token['expires_in'])
                # scope comes from the token response, not the request
                self.granted_scopes = set((self._token.get('scope') or "").split())
                await self.storage.save_token(token=self._token, name=TOKEN_NAME)
                return self._token

    async def _refresh_token(self):
        """Refresh with the saved refresh token. Raises SpotifyError if none or refused. Re-auth needs a browser: login(reauth=True)."""
        logger.warning(f"Refreshing token...")
        refresh_token = self._token.get('refresh_token') if self._token else None
        if not refresh_token:
            raise SpotifyError(401, "no refresh token was saved, call login(reauth=True) to authorize again")
        return await self._token_request({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        })

    async def _get_new_token(self):
        """Exchange the auth code for a token, requesting a code first if needed."""
        await self._get_auth_code()
        logger.warning(f"Getting new token...")
        return await self._token_request({
            "grant_type": "authorization_code",
            "code": self._auth_code,
            "redirect_uri": self.redirect_uri
        })

    async def _token_refresher(self):
        """Refresh the token before it expires."""
        self._running = True
        logger.debug(f"_token_refresher started...")
        try:
            while self._running:
                if not self._token or 'expires_time' not in self._token:
                    logger.error("_token_refresher has no token with an expires_time; "
                                 "call login() first")
                    break
                time_left = self._token['expires_time'] - time.time()-60
                logger.debug(f"Token expires in {time_left} seconds...")
                if time_left <= 0:
                    # pause 'self.get_token'
                    self._refresh_event.clear()
                    try:
                        # refresh token
                        await self._refresh_token()
                    except Exception as e:
                        # let callers continue; Spotify answers with its own error
                        logger.error(f"Refreshing token failed: {e}. Call login(reauth=True) "
                                     "to authorize again.")
                        self._refresh_event.set()
                        break
                    # resume 'self.get_token'
                    self._refresh_event.set()
                    continue # skip sleep to get new time_left
                # not due yet: the token in hand is usable
                self._refresh_event.set()
                await asyncio.sleep(time_left)
        finally:
            # a dead loop must be visible to _login and to any waiter
            self._running = False
            self._refresh_event.set()

    async def _run(self):
        # the event means "token usable": closed at first, opened by the refresher
        self._refresh_event.clear()
        self._refresh_task = asyncio.create_task(self._token_refresher())

    async def stop(self):
        """Stop the refresh task and the callback server."""
        self._running = False
        if self._refresh_task is not None:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None
        await self.server.stop()

    async def _login(self, token=None, reauth=False):
        """Use the saved token or authorize. reauth=True ignores the saved token."""
        logger.debug(f"Attempting to load saved token...")
        self._token = None if reauth else await self.storage.load_token(name=TOKEN_NAME)
        if self._token:
            logger.warning(f"Loaded saved token from storage!")
            self.granted_scopes = set((self._token.get('scope') or "").split())
        else:
            self._token = await self._get_new_token()
        if self._refresh_task is None or self._refresh_task.done():
            await self._run()
        # refresh an expired saved token before the caller sends it
        await self._refresh_event.wait()

    async def get_token(self):
        """Return a usable token."""
        if not self._token:
            await self._login()
        if self._refresh_task is None or self._refresh_task.done():
            # no refresher running: hand back what is in hand
            return self._token
        # wait for refresh if needed
        await self._refresh_event.wait()
        return self._token
import aiohttp
import asyncio
import webbrowser
import random
import base64
import logging
import time
from aiohttp import web
from urllib.parse import urlparse, urlencode
from .storage import JSONStorage

logger = logging.getLogger(__name__)

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


def randString(length=12, chars=None):
    if not chars:
        import string
        chars = string.ascii_letters + string.digits
    ranstr = ''.join(random.choice(chars) for _ in range(length))
    return ranstr

class WebServer:
    def __init__(self, host, port):
        self.app = web.Application()
        self.host = host
        self.port = port
        self._runner = None
        self._site = None
        self._app_task = None

    def add_route(self, path, handler, method='GET', **kwargs):
        """Add a new route to the application."""
        self.app.router.add_route(method, path, handler, **kwargs)

    async def start(self):
        """Start the web server."""
        if not self._app_task:
            self._runner = web.AppRunner(self.app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self.host, self.port)
            self._app_task = asyncio.create_task(self._site.start())

    async def stop(self):
        """Stop the web server."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        self._app_task = None


class TokenHandler:
    def __init__(self, client_id, client_secret, redirect_uri=None, scope=[], storage=None):
        self.client_id = client_id
        self.redirect_uri = redirect_uri or "http://localhost:8888/callback"
        self.scope = scope
        self.storage = storage or JSONStorage()
        self._state = randString(16)
        self._auth_code = None
        self._auth_future = None
        self._token = None
        self._token_url = "https://accounts.spotify.com/api/token"
        self._token_headers = {
            "Authorization": f"Basic {base64.b64encode(f'{self.client_id}:{client_secret}'.encode()).decode()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        parsed_uri = urlparse(self.redirect_uri)
        self.server = WebServer(parsed_uri.hostname, parsed_uri.port)
        self.server.add_route(f"/{parsed_uri.path.lstrip('/')}", self._callback_handler)
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
        if self._auth_code and not self._auth_future.done():
            self._auth_future.set_result(self._auth_code)
        return web.Response(text=closeBrowser, content_type='text/html', charset='utf-8')

    async def _get_auth_code(self):
        logger.warning(f"Getting Oauth code...")
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
        # open webbrowser with auth link
        webbrowser.open(f"https://accounts.spotify.com/authorize?{urlencode(params)}")
        # wait for auth code
        await self._auth_future
        # stop webserver
        await self.server.stop()

    async def _token_request(self, data):
        """ Base token request method, used for new or refreshing tokens """
        if self._token:
            # temp store refresh token (spotify doesnt always send one)
            r_token = self._token['refresh_token'] 
        async with aiohttp.ClientSession() as session:
            async with session.post(self._token_url, headers=self._token_headers, data=data) as resp:
                if resp.status != 200:
                    raise Exception(f"Token request failed: {await resp.text()}")
                self._token = await resp.json()
                if "refresh_token" not in self._token:
                    self._token['refresh_token'] = r_token 
                self._token["expires_time"] = time.time()+int(self._token['expires_in'])
                await self.storage.save_token(self._token, name="spotify")
                return self._token

    async def _refresh_token(self):
        """ Refresh oauth token, get new token if refresh fails """
        logger.warning(f"Refreshing token...")
        try:
            return await self._token_request({
                "grant_type": "refresh_token",
                "refresh_token": self._token['refresh_token']
            })
        except Exception as e:
            logger.error(f"Refreshing token failed! {e}")
            return await self._get_new_token()

    async def _get_new_token(self):
        """ Get a new oauth token using the oauth code, get code if we dont have one yet """
        logger.warning(f"Getting new token...")
        await self._get_auth_code()
        return await self._token_request({
            "grant_type": "authorization_code",
            "code": self._auth_code,
            "redirect_uri": self.redirect_uri
        })

    async def _token_refresher(self):
        """ Waits for the time to refresh the token and refreshes """
        self._running = True
        self._refresh_event.set()
        while self._running:
            time_left = self._token['expires_time'] - time.time()
            logger.info(f"Token expires in {time_left} seconds...")
            if time_left <= 0:
                # pause 'self.get_token'
                self._refresh_event.clear()
                # refresh token
                await self._refresh_token()
                # resume 'self.get_token'
                self._refresh_event.set()
                continue # skip sleep to get new time_left
            await asyncio.sleep(time_left+0.5)

    async def _login(self, token=None):
        """ Checks storage for saved token, gets new token if one isnt found. Starts the token refresher task."""
        self._token = token
        if not self._token:
            logger.warning(f"Attempting to load saved token...")
            self._refresh_task = None
            self._token = await self.storage.load_token(name="spotify")
        if not self._token:
            logger.warning(f"No token found in storage!")
            self._token = await self._get_new_token()
        self._refresh_task = asyncio.create_task(self._token_refresher())

    async def get_token(self):
        """ Returns current token after checking if the token needs to be refreshed """
        if not self._token:
            await self._login()
        # wait for refresh if needed
        await self._refresh_event.wait()
        return self._token
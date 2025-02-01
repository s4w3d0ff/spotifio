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

logger = logging.getLogger(f"spotify.{__name__}")

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
        self.routes = {}

    def add_route(self, path, handler, method='GET', **kwargs):
        """Add a new route to the application."""
        route_info = {
            'handler': handler,
            'method': method,
            'kwargs': kwargs
        }
        self.routes[path] = route_info
        match method:
            case 'GET':
                self.app.router.add_get(path, handler, **kwargs)
            case 'POST':
                self.app.router.add_post(path, handler, **kwargs)
            case 'PUT':
                self.app.router.add_put(path, handler, **kwargs)
            case 'DELETE':
                self.app.router.add_delete(path, handler, **kwargs)
            case _:
                self.app.router.add_route(method, path, handler, **kwargs)
        logger.info(f"Added {method} route for {path} on Webserver")


    async def start(self):
        """Start the web server."""
        if not self._app_task:
            self._runner = web.AppRunner(self.app)
            await self._runner.setup()
            self._site = web.TCPSite(self._runner, self.host, self.port)
            self._app_task = asyncio.create_task(self._site.start())
            logger.warning(f"Webserver started on {self.host}:{self.port}")

    async def stop(self):
        """Stop the web server."""
        if self._site:
            await self._site.stop()
        if self._runner:
            await self._runner.cleanup()
        self._app_task = None
        logger.warning("Webserver stopped")


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
        async with aiohttp.ClientSession() as session:
            async with session.post(self._token_url, headers=self._token_headers, data=data) as resp:
                if resp.status != 200:
                    raise Exception(f"Token request failed: {await resp.text()}")
                self._token = await resp.json()
                if "expires_in" in self._token:
                    self._token["expires_time"] = time.time()+int(self._token['expires_in'])
                await self.storage.save_token(self._token, name="spotify")
                return self._token

    async def _refresh_token(self):
        """ Refresh oauth token, get new token if refresh fails """
        try:
            return await self._token_request({
                "grant_type": "refresh_token",
                "refresh_token": self._token['refresh_token']
            })
        except Exception as e:
            logger.error(f"Refreshing token failed! {e}")
            return await self.get_new_token()

    async def get_new_token(self):
        """ Get a new oauth token using the oauth code, get code if we dont have one yet """
        if not self._auth_code:
            await self._get_auth_code()
        return await self._token_request({
            "grant_type": "authorization_code",
            "code": self._auth_code,
            "redirect_uri": self.redirect_uri
        })

    async def _check_token(self):
        """ Check token expire time, refresh if needed """
        time_left = self._token['expires_time'] - time.time()
        logger.debug(f"Token expires in {time_left} seconds...")
        if time_left < 0:
            await self._refresh_token()

    async def _login(self):
        """ Checks storage for saved token, gets new token if one isnt found. """
        # try to load from storage
        self._token = None
        self._token = await self.storage.load_token(name="spotify")
        if not self._token:
            # no token in storage, get new one
            self._token = await self.get_new_token()

    async def get_token(self):
        """ Returns current token after checking if the token needs to be refreshed """
        if not self._token:
            await self.login()
        await self._check_token()
        return self._token
from .albums import AlbumMethods
from .artists import ArtistMethods
from .browse import BrowseMethods
from .playback import PlaybackMethods
from .playlists import PlaylistMethods
from .podcasts import PodcastMethods
from .request import RequestHandler
from .tracks import TrackMethods
from .users import UserMethods


class Client(PlaybackMethods, UserMethods, PlaylistMethods, TrackMethods,
             AlbumMethods, ArtistMethods, PodcastMethods, BrowseMethods,
             RequestHandler):
    """Every Spotify Web API endpoint spotifio implements.

    The domain method groups live in their own modules. RequestHandler supplies
    login, the scope check and the HTTP layer.
    """
    pass

from segevmusic.overriders import cli_login, settings_init
from segevmusic.utils import convert_platform_link
from os.path import realpath, join, exists
from deemix.app.cli import cli
from deemix.app.settings import Settings
from typing import List
from sys import stdout
from requests import get

DEEZER_ISRC_QUERY = r"https://api.deezer.com/2.0/track/isrc:{isrc}"

# Override deemix functions
cli.login = cli_login
Settings.__init__ = settings_init


class DeezerFunctions:
    """
    A functions toolbox for using Deezer and deemix.
    """

    @staticmethod
    def login(arl: str, songs_path: str = None):
        """
        Initializing Deezer session.
        """
        localpath = realpath('.')
        config_folder = join(localpath, 'config')
        songs_folder = realpath(songs_path) if songs_path else join(localpath, 'Songs')
        app = cli(songs_folder, config_folder)
        app.login(arl)
        return app

    @staticmethod
    def _amsong_to_url(amsong) -> str:
        """
        Generates and returns deezer link for a given AMSong object (using ISRC).
        """
        return DEEZER_ISRC_QUERY.format(isrc=amsong.isrc)

    @staticmethod
    def _amalbum_to_url(amalbum) -> str:
        return convert_platform_link(amalbum.url, 'deezer')

    @staticmethod
    def song_exists(song, download_path):
        return exists(join(download_path, f"{song.isrc}.mp3"))

    @classmethod
    def download(cls, songs: List, app: cli):
        """
        Downloads given deezer links.
        """
        download_path = app.set.settings['downloadLocation']
        for song in songs:
            print(f"--> Downloading '{song.short_name}'...", end='')
            app.downloadLink([cls._amsong_to_url(song)])
            stdout.flush()
            if cls.song_exists(song, download_path):
                print(f"\r--> Downloaded '{song.short_name}'!")
            else:
                print(f"\r--> ERROR: Song '{song.short_name}' was not downloaded!")

    @classmethod
    def isrcs_from_album(cls, album) -> List[str]:
        url = cls._amalbum_to_url(album)
        tracklist_url = get(url.replace('www', 'api', 1)).json()['tracklist']
        tracks = get(tracklist_url).json()['data']
        return [track['isrc'] for track in tracks]

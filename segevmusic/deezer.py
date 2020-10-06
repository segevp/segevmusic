from .overriders import cli_login, settings_init
from .applemusic import AMSong
from os.path import realpath, join, exists
from deemix.app.cli import cli
from deemix.app.settings import Settings
from typing import List
from sys import stdout

DEEZER_ISRC_QUERY = r"https://api.deezer.com/2.0/track/isrc:{isrc}"
ARL = r"5bbd39c9df0b86568f46c9310cb61f4c9c3e3a1cef78b0a5e142066dca8c1ea495edea03cbb1536a5ba1fd2cff9b15fe21114d221140b57e0ab96484d4a1f4d0acbbfe66af7587a8f2af59ebeb5036c7d09bd1d8ad936f4da1b9c1ed6af46e21"

# Override deemix functions
cli.login = cli_login
Settings.__init__ = settings_init


class DeezerFunctions:
    """
    A functions toolbox for using Deezer and deemix.
    """

    @staticmethod
    def login(songs_path: str = None, arl: str = ARL):
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
    def _amsong_to_url(amsong: AMSong) -> str:
        """
        Generates and returns deezer link for a given AMSong object (using ISRC).
        """
        return DEEZER_ISRC_QUERY.format(isrc=amsong.isrc)

    @staticmethod
    def song_exists(song, download_path):
        return exists(join(download_path, f"{song.isrc}.mp3"))

    @classmethod
    def download(cls, songs: List[AMSong], app: cli):
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

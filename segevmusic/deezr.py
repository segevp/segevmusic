from segevmusic.overriders import load_settings, LogListener
from os.path import realpath, join, exists
from typing import Iterable
from sys import stdout

from deezer import Deezer
from deezer import TrackFormats
from deemix.downloader import Downloader
from deemix import generateDownloadObject
from deemix.itemgen import GenerationError

DEEZER_ISRC_QUERY = r"https://api.deezer.com/2.0/track/isrc:{isrc}"


class DeezerFunctions:
    """
    A functions toolbox for using Deezer and deemix.
    """

    @staticmethod
    def login(arl: str, songs_path=''):
        """
        Initializing Deezer session.
        """
        localpath = realpath('.')
        config_folder = join(localpath, 'config')
        songs_folder = realpath(songs_path) if songs_path else join(localpath, 'Songs')
        app = Deezer()

        app.login_via_arl(arl)
        while not app.logged_in:
            arl = input("Enter your arl here: ")
            app.login_via_arl(arl)
        app.settings = load_settings(config_folder)
        app.settings['downloadLocation'] = songs_folder
        return app

    @staticmethod
    def _amsong_to_url(amsong) -> str:
        """
        Generates and returns deezer link for a given AMSong object (using ISRC).
        """
        return DEEZER_ISRC_QUERY.format(isrc=amsong.isrc)

    @staticmethod
    def song_exists(song, download_path):
        return exists(join(download_path, f"{song.isrc}.mp3"))

    @classmethod
    def download(cls, songs: Iterable, app):
        """
        Downloads given deezer links.
        """
        download_path = app.settings['downloadLocation']
        for song in songs:
            print(f"--> Downloading '{song.short_name}'...", end='')
            try:
                cls.download_link(app, cls._amsong_to_url(song))
            except Exception as e:
                print(e)
            stdout.flush()
            if cls.song_exists(song, download_path):
                print(f"\r--> Downloaded '{song.short_name}'!")
            else:
                print(f"\r--> ERROR: Song '{song.short_name}' was not downloaded!")

    @staticmethod
    def download_link(app, link):
        listener = LogListener()
        bitrate = app.settings.get("maxBitrate", TrackFormats.MP3_320)
        try:
            obj = generateDownloadObject(app, link, bitrate, {}, listener)
        except GenerationError as e:
            print(f"{e.link}: {e.message}")
            return False
        Downloader(app, obj, app.settings, listener).start()

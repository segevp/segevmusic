from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions, AMSong, AM_DOMAIN
from segevmusic.deezr import DeezerFunctions
from segevmusic.wetransfer import WTSession
from segevmusic.utils import get_lines, get_indexes, newline, convert_platform_link
from os.path import realpath
from argparse import ArgumentParser, Namespace
from typing import Iterable

REQUERY_LIMIT = 5
ARL = "3cccd48d1ba2db1fe9067baf059eaa053cba6e5c3f815a54b1fc4e4f5da72f72fbd8c3f30bd704360a88066bc1b1280b44d7e7d8f2a5bf" \
      "33dfcbbf2863de56b123fd0334066f5d2c9da4a279fd29c48c875f497502687107598334b67eb5a37a"


class MusicDownloader:
    def __init__(self):
        args = self.get_args()
        self.download_path = args.path
        self.to_upload = args.upload
        self.file_path = args.file
        self.all_album = args.album
        self.link = args.link
        self.links = args.links
        self.to_check = args.check if not any((args.album, args.link, args.links)) else False

        self.app = DeezerFunctions.login(ARL, self.download_path)
        self.tagger = Tagger(self.download_path)

        self.added_songs = {}
        self.downloaded_songs = []
        self.songs_files = []
        self.wt_link = ''

    @staticmethod
    def get_args() -> Namespace:
        """
        Get user arguments
        :return: The parsed arguments inside an argparse.Namespace object
        """
        parser = ArgumentParser(prog='segevmusic', description="download music effortlessly")
        parser.add_argument("path", help="songs download path", nargs='?', default='./Songs')
        parser.add_argument("-u", "--upload", help="upload songs to wetransfer", action="store_true")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-f", "--file", help="load a file with songs list", type=str)
        group.add_argument("-a", "--album", help="download an entire album", action="store_true")
        group.add_argument("-l", "--link", help="download playlists, albums or songs from a given link",
                           type=str)
        parser.add_argument("-x", "--links-file", help="the loaded file contains links", action="store_true",
                            dest='links')
        parser.add_argument("-d", "--dont-validate", help="don't validate chosen songs",
                            action="store_false", dest='check')
        args = parser.parse_args()
        return args

    def _add_song(self, song: AMSong, name: str):
        self.added_songs.update({song: name})

    def _add_songs(self, songs: Iterable[AMSong]):
        if not songs:
            return None
        for song in songs:
            self._add_song(song, f'{song.name} {song.artist_name} {song.album_name}')

    def _search_song(self, name: str, limit: int = None) -> AMSong:
        """
        Querying Apple Music's API for given song name and query limit
        and adds it if found.
        :param name: The search term - name of song( + artist).
        """
        chosen_song = AMFunctions.search_song(name, limit)
        if chosen_song:
            self._add_song(chosen_song, name)
        return chosen_song

    def get_songs_interactive(self):
        """
        This function interactively asks user for input for each song
        until the user decides to stop adding songs, and adds them.
        """
        to_continue = True
        while to_continue:
            newline()
            song_name = input("--> Enter song name (+ Artist), or Return-key to continue: ")
            if not song_name:
                to_continue = False
                continue
            found_song = self._search_song(song_name)
            if found_song:
                print(f"--> {found_song}")

    def get_songs_file(self):
        """
        This function reads given file lines and adds every song mentioned in the file.
        """
        for line in get_lines(self.file_path):
            if self.links:
                self.get_songs_link(line)
                continue
            self._search_song(line)

    def get_songs_album(self):
        album = None
        while not album:
            newline()
            album_name = input("--> Enter album name (+ Artist), or Return-key to continue: ")
            album = AMFunctions.search_album(album_name)
        self._add_songs(album)

    def get_songs_link(self, link: str):
        if 'apple.com' not in link:
            link = convert_platform_link(link)
            if not link:
                return None
        item = AMFunctions.get_item_from_url(link, 'he')
        songs = [item] if type(item) == AMSong else item
        self._add_songs(songs)

    def list_songs(self, to_print=True) -> enumerate:
        enum_songs = enumerate(self.added_songs, start=1)
        if to_print:
            print("--> Chosen songs:\n")
            for index, song in enum_songs:
                print(f"{index}) {song}")
        return enum_songs

    def _requery(self, bad_song: AMSong):
        """
        Runs query with a larger query limit and prompts user to choose the correct song.
        Replaces bad song with correct song.
        """
        search_term = self.added_songs[bad_song]
        chosen_song = self._search_song(search_term, REQUERY_LIMIT)
        del self.added_songs[bad_song]
        print(f"--> Replaced '{bad_song.short_name}' with '{chosen_song.short_name}'")

    def offer_fix(self):
        bad_indexes = [index - 1 for index in get_indexes(len(self.added_songs))]
        bad_songs = list(self.added_songs)
        for bad_index in bad_indexes:
            self._requery(bad_songs[bad_index])

    def _update_downloaded_songs(self):
        """
        Checks which songs are found in the download folder and adds them to the
        'downloaded_songs' attribute.
        """
        self.downloaded_songs = [song for song in self.added_songs if
                                 DeezerFunctions.song_exists(song, self.download_path)]

    def download(self):
        """
        Downloads all of the songs by generating their links
        and updating downloaded songs afterwards.
        """
        DeezerFunctions.download(self.added_songs, self.app)
        self._update_downloaded_songs()

    def _report_not_downloaded(self):
        """
        Prints a message of the songs that weren't downloaded.
        """
        for failed_song in set(self.added_songs) - set(self.downloaded_songs):
            print(f"--> ERROR: Song '{failed_song.short_name}' was not downloaded!")

    def tag(self):
        """
        Tags all of the downloaded songs.
        """
        for song in self.downloaded_songs:
            self.tagger.tag_song(song)

    def rename(self):
        """
        Renames downloaded songs from their ISRC path to a 'good path' - the renamed
        format is decided in the 'Tagger.generate_good_path' function.
        """
        for song in self.downloaded_songs:
            try:
                song_file = self.tagger.rename_isrc_path(song)
            except FileNotFoundError:
                continue
            self.songs_files.append(song_file)

    def upload(self):
        """
        Uploads all of the downloaded songs to wetransfer.
        """
        self.wt_link = WTSession().upload(self.songs_files, f"Your {len(self.songs_files)} songs!")

    def show_availability(self):
        """
        Prints places the downloaded songs are available.
        - Always prints the local path
        - Will only print wetransfer path if chosen to upload
        """
        print(f"--> Your download is available at:\n{realpath(self.download_path)}")
        if self.to_upload:
            newline()
            print(f"--> Your download is available at:\n{self.wt_link}")

    def download_songs(self, songs: Iterable[AMSong], upload=False):
        self._add_songs(songs)
        self.list_songs()
        newline()
        self.download()
        newline()
        self.tag()
        self.rename()
        if upload:
            self.upload()
        newline()
        self.show_availability()
        newline()
        print("--> DONE!")

    def run(self):
        """
        Runs every function at the right time:
        1) Gets songs interactively/from a file
        2) Downloads the songs
        3) Tags the metadata
        4) Renames the songs paths to human-convenient paths.
        5) Uploads the songs to wetransfer if the option was chosen
        6) Prints songs availability
        7) Alerts when finished
        """
        if self.file_path:
            self.get_songs_file()
        elif self.all_album:
            self.get_songs_album()
        elif self.link:
            self.get_songs_link(self.link)
        else:
            self.get_songs_interactive()
        newline()
        self.list_songs()
        if self.to_check:
            self.offer_fix()
        newline()
        self.download()
        newline()
        self.tag()
        self.rename()
        if self.to_upload:
            self.upload()
        newline()
        self.show_availability()
        newline()
        print("--> DONE!")


def main():
    """
    For entry points.
    """
    downloader = MusicDownloader()
    downloader.run()


if __name__ == '__main__':
    main()

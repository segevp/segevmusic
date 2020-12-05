from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions, AMSong
from segevmusic.deezer import DeezerFunctions
from segevmusic.wetransfer import WTSession
from segevmusic.utils import get_lines, get_indexes, newline
from shutil import rmtree
from os.path import realpath
from argparse import ArgumentParser, Namespace
from logging import shutdown
from typing import Iterable

REQUERY_LIMIT = 5
ARL = "580c41d634e95fef3ef2858c148266fa5573e5bd802719ccf6d40222704f2fe19ec6a3ecf788ac2f37769bc904cac48eb5d6ce3f9eb14e" \
      "8fcfd1a594202de4ca9a83c084f0c674c30e1665495d3596dbd938f9e657e21b1e2fa695e067b2ad41"


class MusicDownloader:
    def __init__(self):
        args = self.get_args()
        self.download_path = args.path
        self.to_upload = args.upload
        self.file_path = args.file
        self.all_album = args.album
        self.link = args.link
        self.to_check = args.check if not any((args.album, args.link)) else False

        self.app = DeezerFunctions.login(ARL, self.download_path)
        self.tagger = Tagger(self.download_path)

        self.added_songs = {}
        # self.search_term = []
        self.downloaded_songs = []
        self.songs_files = []
        self.wt_link = ''

    @staticmethod
    def get_args() -> Namespace:
        """
        Get user arguments
        :return: The parsed arguments inside an argparse.Namespace object
        """
        parser = ArgumentParser(description="download music effortlessly")
        parser.add_argument("path", help="songs download path", nargs='?', default='./Songs')
        parser.add_argument("-f", "--file", help="load a file with songs list", type=str)
        parser.add_argument("-u", "--upload", help="upload songs to wetransfer", action="store_true")
        group = parser.add_mutually_exclusive_group()
        group.add_argument("-a", "--album", help="download an entire album", action="store_true")
        group.add_argument("-l", "--link", help="download an entire collection (playlist/album) from a given link",
                           type=str)
        parser.add_argument("-d", "--dont-validate", help="don't validate chosen songs",
                            action="store_false", dest='check')
        args = parser.parse_args()
        return args

    def _add_song(self, song: AMSong, name: str):
        self.added_songs.update({song: name})

    def _add_songs(self, songs: Iterable[AMSong]):
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
        for song_name in get_lines(self.file_path):
            self._search_song(song_name)

    def get_songs_album(self):
        album = None
        while not album:
            newline()
            album_name = input("--> Enter album name (+ Artist), or Return-key to continue: ")
            album = AMFunctions.search_album(album_name)
        self._add_songs(album)

    def get_songs_link(self):
        collection = AMFunctions.get_item_from_url(self.link, 'he')
        if collection:
            self._add_songs(collection)

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
            song_file = self.tagger.rename_isrc_path(song)
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

    @staticmethod
    def finish():
        """
        Removes deemix config files and prints ending message.
        """
        shutdown()
        rmtree('./config', ignore_errors=True)
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
        7) Removes deemix config folders
        """
        if self.file_path:
            self.get_songs_file()
        elif self.all_album:
            self.get_songs_album()
        elif self.link:
            self.get_songs_link()
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
        self.finish()


def main():
    """
    For entry points.
    """
    downloader = MusicDownloader()
    downloader.run()


if __name__ == '__main__':
    main()

from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions
from segevmusic.deezer import DeezerFunctions
from segevmusic.wetransfer import WTSession
from segevmusic.utils import ask, get_lines
from shutil import rmtree
from os.path import exists, realpath
from argparse import ArgumentParser, Namespace
from typing import List


class MusicDownloader:
    def __init__(self):
        args = self.get_args()
        self.download_path = args.path
        self.query_limit = args.manual
        self.to_upload = args.upload
        self.file_path = args.file

        self.app = DeezerFunctions.login(self.download_path)
        self.tagger = Tagger(self.download_path)
        self.songs = []
        self.downloaded_songs = []
        self.songs_files = []
        self.wt_link = ''

    @staticmethod
    def get_args() -> Namespace:
        """
        Get user arguments
        :return: The parsed arguments inside an argparse.Namespace object
        """
        parser = ArgumentParser()
        parser.add_argument("path", help="songs download path", nargs='?', default='./Songs')
        parser.add_argument("-u", "--upload", help="upload songs to wetransfer", action="store_true")
        parser.add_argument("-m", "--manual", help="manual song selection, max 5 options", type=int,
                            choices=list(range(1, 6)), default=1)
        parser.add_argument("-f", "--file", help="load a file with songs list", type=str)
        args = parser.parse_args()
        return args

    def _add_song(self, name: str):
        """
        Querying Apple Music's API for given song name and query limit
        and adds song to the songs attribute
        :param name: The search term - name of song( + artist).
        """
        chosen_song = AMFunctions.search_song(name, self.query_limit)
        if chosen_song:
            self.songs.append(chosen_song)

    def get_songs_interactive(self):
        """
        This function interactively asks user for input for each song
        until the user decides to stop adding songs, and adds them.
        """
        to_continue = True
        while to_continue:
            song_name = input("--> Enter song name (+ Artist): ")
            self._add_song(song_name)
            to_continue = ask("--> Another song? (y/n): ")

    def get_songs_file(self):
        """
        This function reads given file lines and adds every song mentioned in the file.
        """
        for song_name in get_lines(self.file_path):
            self._add_song(song_name)

    def _generate_links(self) -> List[str]:
        """
        Generates Deezer link for each song, using its ISRC code.
        :return: List of Deezer links.
        """
        return [DeezerFunctions.amsong_to_url(song) for song in self.songs]

    def _update_downloaded_songs(self):
        """
        Checks which songs are found in the download folder and adds them to the
        'downloaded_songs' attribute.
        """
        self.downloaded_songs = [song for song in self.songs if exists(self.tagger.generate_isrc_path(song))]
        self._report_not_downloaded()

    def download(self):
        """
        Downloads all of the songs by generating their links
        and updating downloaded songs afterwards.
        """
        DeezerFunctions.download(self._generate_links(), self.app)
        self._update_downloaded_songs()

    def _report_not_downloaded(self):
        """
        Prints a message of the songs that weren't downloaded.
        """
        for failed_song in set(self.songs) - set(self.downloaded_songs):
            print(f"--> ERROR: Song {failed_song} was not downloaded!")

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
            print(f"--> Your download is available at:\n{self.wt_link}")

    def finish(self):
        """
        Removes deemix config files and prints ending message.
        """
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
        else:
            self.get_songs_interactive()
        self.download()
        self.tag()
        self.rename()
        if self.to_upload:
            self.upload()
        self.show_availability()
        self.finish()

# if __name__ == '__main__':
#     downloader = MusicDownloader()
#     downloader.run()

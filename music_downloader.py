#!/usr/bin/env python3

from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions
from segevmusic.deezer import DeezerFunctions
from segevmusic.wetransfer import WTSession
from segevmusic.utils import ask, get_lines
from shutil import rmtree
from os.path import exists, realpath
from argparse import ArgumentParser


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
        self.wt_link = ''

    @staticmethod
    def get_args():
        parser = ArgumentParser()
        parser.add_argument("path", help="songs download path", nargs='?', default='./Songs')
        parser.add_argument("-u", "--upload", help="upload songs to wetransfer", action="store_true")
        parser.add_argument("-m", "--manual", help="manual song selection, max 5 options", type=int,
                            choices=list(range(1, 6)), default=1)
        parser.add_argument("-f", "--file", help="load a file with songs list", type=str)
        args = parser.parse_args()
        return args
        # return args.path, args.manual, args.upload, args.file

    def _add_song(self, name):
        chosen_song = AMFunctions.search_song(name, self.query_limit)
        if chosen_song:
            self.songs.append(chosen_song)

    def get_songs_interactive(self):
        to_continue = True
        while to_continue:
            song_name = input("--> Enter song name (+ Artist): ")
            self._add_song(song_name)
            to_continue = ask("--> Another song? (y/n): ")

    def get_songs_file(self):
        for song_name in get_lines(self.file_path):
            self._add_song(song_name)

    def _generate_links(self):
        return [DeezerFunctions.amsong_to_url(song) for song in self.songs]

    def download(self):
        DeezerFunctions.download(self._generate_links(), self.app)

    def update_downloaded_songs(self):
        self.downloaded_songs = [song for song in self.songs if exists(self.tagger.generate_isrc_path(song))]
        self._report_not_downloaded()

    @property
    def songs_files(self):
        return [self.tagger.generate_good_path(song) for song in self.downloaded_songs]

    def _report_not_downloaded(self):
        for failed_song in set(self.songs) - set(self.downloaded_songs):
            print(f"--> ERROR: Song {failed_song} was not downloaded!")

    def tag(self):
        for song in self.downloaded_songs:
            self.tagger.tag_song(song)

    def rename(self):
        for song in self.downloaded_songs:
            song_file = self.tagger.rename_isrc_path(song)
            self.songs_files.append(song_file)

    def upload(self):
        self.wt_link = WTSession().upload(self.songs_files, f"Your {len(self.songs_files)} songs!")

    def show_availability(self):
        print(f"--> Your download is available at:\n{realpath(self.download_path)}")
        if self.to_upload:
            print(f"--> Your download is available at:\n{self.wt_link}")

    def finish(self):
        # Remove deemix config files
        rmtree('./config', ignore_errors=True)
        print("--> DONE!")

    def run(self):
        if self.file_path:
            self.get_songs_file()
        else:
            self.get_songs_interactive()
        self.download()
        self.update_downloaded_songs()
        self.tag()
        self.rename()
        if self.to_upload:
            self.upload()
        self.show_availability()
        self.finish()


if __name__ == '__main__':
    downloader = MusicDownloader()
    downloader.run()

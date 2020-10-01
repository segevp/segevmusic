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
        self.songs_files = []

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

    def _get_downloaded_songs(self):
        downloaded_songs = []
        for song in self.songs:
            song_path = self.tagger.generate_isrc_path(song)
            if not exists(song_path):
                print(f"--> ERROR: Song {song.name} was not downloaded!")
                continue
            downloaded_songs.append(song)
        return downloaded_songs

    def tag(self):
        for song in self._get_downloaded_songs():
            self.tagger.tag_song(song)

    def rename(self):
        for song in self._get_downloaded_songs():
            song_file = self.tagger.rename_isrc_path(song)
            self.songs_files.append(song_file)

    def upload(self):
        wt_link = WTSession().upload(self.songs_files, f"Your {len(self.songs_files)} songs!")
        print(f"--> Your download is available at:\n{wt_link}")


# def main():
#     downloader = MusicDownloader()
#     to_continue = True
#     g = None
#     # Create generator for song names
#     if downloader.file_path:
#         g = (song_name for song_name in get_lines(downloader.file_path))
#     # Add songs
#     while to_continue:
#         # Get song name interactively/from a file
#         try:
#             name = next(g) if g else input("--> Enter song name (+ Artist): ")
#         except StopIteration:
#             to_continue = False
#             continue
#         # Get song object
#         chosen_song = AMFunctions.search_song(name, query_limit)
#         songs.append(chosen_song)
#         if not song_names_path:
#             to_continue = ask("--> Another song? (y/n): ")
#     # Generate Deezer URLs
#     songs_links = [DeezerFunctions.amsong_to_url(song) for song in songs]
#     # Download songs
#     DeezerFunctions.download(songs_links, app)
#     # Tagging songs
#     for song in songs:
#         # Check if song was downloaded
#         song_path = tagger.generate_isrc_path(song)
#         if not exists(song_path):
#             print(f"--> ERROR: Song {song.name} was not downloaded!")
#             continue
#         # Tag song
#         tagger.tag_song(song)
#         # Rename song file name
#         song_file = tagger.rename_isrc_path(song)
#         songs_files.append(song_file)
#     print(f"--> Your download is available at:\n{realpath(download_path)}")
#     # Upload files to WeTransfer
#     if to_upload:
#         wt_link = WTSession().upload(songs_files, f"Your {len(songs_files)} songs!")
#         print(f"--> Your download is available at:\n{wt_link}")
#     # Remove deemix config files
#     rmtree('./config', ignore_errors=True)
#     print("--> DONE!")


if __name__ == '__main__':
    # main()
    pass

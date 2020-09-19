#!/usr/bin/env python3

from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions
from segevmusic.deezer import DeezerFunctions
from segevmusic.wetransfer import WTSession
from segevmusic.utils import ask
from shutil import rmtree
from os.path import exists
from argparse import ArgumentParser


def get_args():
    parser = ArgumentParser()
    parser.add_argument("path", help="songs download path", nargs='?', default='./Songs')
    parser.add_argument("-u", "--upload", help="upload songs to wetransfer", action="store_true")
    parser.add_argument("-m", "--manual", help="manual song selection, max 5 options", type=int,
                        choices=list(range(1, 6)), default=1)
    args = parser.parse_args()
    return args.path, args.manual, args.upload


def main():
    songs_path, query_limit, upload = get_args()
    app = DeezerFunctions.login(songs_path)
    tagger = Tagger(songs_path)
    songs = []
    songs_files = []
    to_continue = True
    # Adding songs
    while to_continue:
        try:
            songs.append(AMFunctions.search_song(query_limit))
        except KeyError:
            print("--> ERROR: Nothing found; Check spelling errors.")
            continue
        to_continue = ask("--> Another song? (y/n): ")
    # Generate Deezer URLs
    songs_links = [DeezerFunctions.amsong_to_url(song) for song in songs]
    # Download songs
    DeezerFunctions.download(songs_links, app)
    # Tagging songs
    for song in songs:
        # Check if song was downloaded
        song_path = tagger.generate_isrc_path(song)
        if not exists(song_path):
            print(f"--> ERROR: Song {song.name} was not downloaded!")
            continue
        # Tag song
        tagger.tag_song(song)
        # Rename song file name
        song_file = tagger.rename_isrc_path(song)
        songs_files.append(song_file)
    print(f"--> Your download is available at {songs_path}!")
    # Upload files to WeTransfer
    if upload:
        wt_link = WTSession().upload(songs_files, f"Your {len(songs_files)} songs!")
        print(f"--> Your download is available at {wt_link}")
    # Remove deemix config files
    rmtree('./config', ignore_errors=True)
    print("--> DONE!")


if __name__ == '__main__':
    main()

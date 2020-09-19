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
    parser.add_argument("-f", "--file", help="load a file with songs list", type=str)
    args = parser.parse_args()
    return args.path, args.manual, args.upload, args.file


def get_song_names(song_names_path):
    with open(song_names_path, 'r') as f:
        song_names = f.read().split('\n')
        return filter(None, song_names)


def main():
    download_path, query_limit, to_upload, song_names_path = get_args()
    app = DeezerFunctions.login(download_path)
    tagger = Tagger(download_path)
    songs = []
    songs_files = []
    to_continue = True
    g = None
    # Create generator for song names
    if song_names_path:
        g = (song_name for song_name in get_song_names(song_names_path))
    # Add songs
    while to_continue:
        try:
            # Get song name interactively/from a file
            name = next(g) if g else input("--> Enter song name (+ Artist): ")
        except StopIteration:
            to_continue = False
            continue
        chosen_song = AMFunctions.search_song(name, query_limit)
        songs.append(chosen_song)
        if not song_names_path:
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
    print(f"--> Your download is available at {download_path}!")
    # Upload files to WeTransfer
    if to_upload:
        wt_link = WTSession().upload(songs_files, f"Your {len(songs_files)} songs!")
        print(f"--> Your download is available at {wt_link}")
    # Remove deemix config files
    rmtree('./config', ignore_errors=True)
    print("--> DONE!")


if __name__ == '__main__':
    main()

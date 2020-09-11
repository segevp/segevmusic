#!/usr/bin/env python3

from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions
from segevmusic.deezer import DeezerFunctions
from shutil import rmtree

BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True,
             'n': False, 'N': False, 'no': False, 'No': False}


def ask(question, bool_dict=BOOL_DICT):
    answer = None
    while answer not in bool_dict:
        answer = input(question)
    return answer


def search_song():
    # Search
    search = input("Enter song name (+ Artist): ")
    # Set song language
    language = 'he' if ask("Hebrew? (y/n): ") else 'en'
    query_results = AMFunctions.query(search, language=language)
    # Run query
    song = AMFunctions.choose_song(query_results)
    # Attach album metadata
    AMFunctions.attach_album(song)
    # Translate genres
    AMFunctions.translate_song(song)
    return song


def download_song(song, app):
    # Generate Deezer URL
    deezer_url = DeezerFunctions.amsong_to_url(song)
    # Download song
    DeezerFunctions.download(deezer_url, app)
    # Tag metadata
    Tagger.tag_song(song)
    # Rename 'isrc.mp3 to %artist% - %name% template'
    Tagger.rename_isrc_path(song)


def main():
    to_continue = True
    songs = []
    app = DeezerFunctions.login()
    while to_continue:
        songs.append(search_song())
        answer = ask("Another song? (y/n): ")
        to_continue = BOOL_DICT[answer]
    for song in songs:
        download_song(song, app)
    rmtree('./config', ignore_errors=True)


if __name__ == '__main__':
    main()

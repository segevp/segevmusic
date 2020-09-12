#!/usr/bin/env python3

from segevmusic.tagger import Tagger
from segevmusic.applemusic import AMFunctions
from segevmusic.deezer import DeezerFunctions
from shutil import rmtree
from sys import argv
from os.path import exists

BOOL_DICT = {'y': True, 'Y': True, 'yes': True, 'Yes': True,
             'n': False, 'N': False, 'no': False, 'No': False}


def ask(question, bool_dict=BOOL_DICT):
    answer = None
    while answer not in bool_dict:
        answer = input(question)
    return BOOL_DICT[answer]


def has_hebrew(name):
    return any("\u0590" <= letter <= "\u05EA" for letter in name)


def search_song():
    # Search
    search = input("--> Enter song name (+ Artist): ")
    # Set song language
    language = 'he' if has_hebrew(search) else 'en'
    query_results = AMFunctions.query(search, language=language)
    # Run query
    song = AMFunctions.choose_song(query_results)
    # Attach album metadata
    AMFunctions.attach_album(song, language)
    # Translate genres
    if language == 'he':
        AMFunctions.translate_song(song)
    return song


def tag_song(song, tagger):
    # Tag metadata
    tagger.tag_song(song)
    # Rename 'isrc.mp3 to %artist% - %name% template'
    tagger.rename_isrc_path(song)


def main(songs_path='./Songs'):
    app = DeezerFunctions.login(songs_path)
    tagger = Tagger(songs_path)
    songs = []
    to_continue = True
    # Adding songs
    while to_continue:
        try:
            songs.append(search_song())
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
        tag_song(song, tagger)
    rmtree('./config', ignore_errors=True)


if __name__ == '__main__':
    if len(argv) == 2:
        main(argv[1])
    else:
        main()
        print("--> DONE!")

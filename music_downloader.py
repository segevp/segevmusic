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


def download_song(app):
    # Search
    search = input("Enter song name (+ Artist): ")
    language = 'he' if ask("Hebrew? (y/n): ") else 'en'
    query_results = AMFunctions.query(search, language=language)
    song = AMFunctions.choose_song(query_results)
    # Attach album metadata
    AMFunctions.attach_album(song)
    # Translate genres
    print(AMFunctions.translate_song(song))
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
    app = DeezerFunctions.login()
    while to_continue:
        download_song(app)
        answer = ask("Continue downloading? (y/n): ")
        to_continue = BOOL_DICT[answer]
    rmtree('./config')


if __name__ == '__main__':
    main()

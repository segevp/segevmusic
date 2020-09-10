from requests import get
from deemix.__main__ import download
from tagger import Tagger
from sys import argv

# Constants
AM_QUERY = r"https://tools.applemediaservices.com/api/apple-media/music/IL/search.json?types=songs,albums&term={name}&limit={limit}"
DEEZER_ISRC_QUERY = r"https://api.deezer.com/2.0/track/isrc:{isrc}"
ARL = r"5bbd39c9df0b86568f46c9310cb61f4c9c3e3a1cef78b0a5e142066dca8c1ea495edea03cbb1536a5ba1fd2cff9b15fe21114d221140b57e0ab96484d4a1f4d0acbbfe66af7587a8f2af59ebeb5036c7d09bd1d8ad936f4da1b9c1ed6af46e21"
NOT_FOUND = 'The song "{song_name}" was not found.'
ARTWORK_REPR_SIZE = 600
ARTWORK_EMBED_SIZE = 1400
AMSONG_REPR = """Song: {name} // Artist: {artist_name} // Album: {album_name}{explicit}
Release: {release_date}
Artwork: {artwork_url}"""


class AMObject:
    def __init__(self, json=None):
        self.json = json

    @property
    def id(self):
        return self.json['id']

    @property
    def artist_name(self):
        return self.json['attributes']['artistName']

    @property
    def album_name(self):
        return self.json['attributes']['albumName']

    @property
    def artwork_url(self):
        return self.json['attributes']['artwork']['url']

    @property
    def is_explicit(self):
        if 'contentRating' in self.json['attributes']:
            return self.json['attributes']['contentRating'] == 'explicit'
        return False

    @property
    def genres(self):
        return self.json['attributes']['genreNames']

    @property
    def name(self):
        return self.json['attributes']['name']

    @property
    def release_date(self):
        return self.json['attributes']['releaseDate']

    @property
    def url(self):
        return self.json['attributes']['url']

    def get_artwork(self, w=ARTWORK_EMBED_SIZE, h=ARTWORK_EMBED_SIZE):
        return get(self.artwork_url.format(w=w, h=h)).content


class AMSong(AMObject):
    def __init__(self, json):
        super().__init__(json)
        self.album = AMAlbum()

    @property
    def disc_number(self):
        return self.json['attributes']['discNumber']

    @property
    def isrc(self):
        return self.json['attributes']['isrc']

    @property
    def track_number(self):
        return self.json['attributes']['trackNumber']

    @property
    def preview(self):
        return self.json['attributes']['previews'][0]['url']

    def album_id_from_song_url(self):
        return self.url.split('/')[-1].split('?')[0]

    def __str__(self):
        return AMSONG_REPR.format(name=self.name, artist_name=self.artist_name, album_name=self.album_name,
                                  artwork_url=self.artwork_url.format(w=ARTWORK_REPR_SIZE, h=ARTWORK_REPR_SIZE),
                                  release_date=self.release_date,
                                  explicit="\n(Explicit)" if self.is_explicit else '')


class AMAlbum(AMObject):
    def __init__(self, json=None):
        super().__init__(json)

    @property
    def album_name(self):
        return self.name

    @property
    def copyright(self):
        if 'copyright' in self.json['attributes']:
            return self.json['attributes']['copyright']
        return None

    @property
    def record_label(self):
        return self.json['attributes']['recordLabel']

    @property
    def track_count(self):
        return self.json['attributes']['trackCount']


class AMFunctions:
    @staticmethod
    def query(name, limit=1):
        query = AM_QUERY.format(name=name, limit=limit)
        json = get(query).json()
        return json

    @staticmethod
    def choose_song(json):
        index = 0
        songs = [AMSong(song_json) for song_json in json['songs']['data']]
        print("Choose the correct song:")
        for song in songs:
            print(f"-- OPTION #{index + 1} --", song, sep='\n', end='\n\n')
            index += 1
        chosen_index = int(input(f"What is your choice? (1-{index}) ")) - 1 if len(songs) > 1 else 0
        return songs[chosen_index]

    @classmethod
    def attach_album(cls, amsong):
        wanted_album_id = amsong.album_id_from_song_url()
        results = cls.query(amsong.artist_name + ' ' + amsong.album_name, 4)
        for album in results['albums']['data']:
            if album['id'] == wanted_album_id:
                amsong.album = AMAlbum(album)
                return 0
        return 1


class DeezerFunctions:
    @staticmethod
    def amsong_to_url(amsong):
        return DEEZER_ISRC_QUERY.format(isrc=amsong.isrc)


def download_song():
    # Search
    search = input("Enter song name (+ Artist): ")
    query_results = AMFunctions.query(search)
    song = AMFunctions.choose_song(query_results)
    # Attach album metadata
    AMFunctions.attach_album(song)
    # Generate Deezer URL
    deezer_url = DeezerFunctions.amsong_to_url(song)
    # Download song
    download(deezer_url, ARL)
    # Tag metadata
    Tagger.tag_song(song)
    # Rename 'isrc.mp3 to %artist% - %name% template'
    Tagger.rename_isrc_path(song)


if __name__ == '__main__':
    download_song()

from segevmusic.utils import has_hebrew, ask
from requests import get
from typing import List

ARTWORK_EMBED_SIZE = 1400
ARTWORK_REPR_SIZE = 600
AMOBJECT_REPR_FIRST = "Name: {name} // Artist: {artist_name} "
AMOBJECT_REPR_SECOND = "({release_date}){explicit}"
AMSONG_REPR_MIDDLE = " // Album: {album_name} "
AM_QUERY = r"https://tools.applemediaservices.com/api/apple-media/music/IL/" \
           r"search.json?types=songs,albums&term={name}&limit={limit}&l={language}"
ITUNES_QUERY = 'https://itunes.apple.com/il/lookup?id={id}&entity=song'

SONG_SEARCH_LIMIT = 1
SONG_MATCH_SEARCH_LIMIT = 5
ALBUM_SEARCH_LIMIT = 5
ALBUM_SECOND_SEARCH_LIMIT = 10
ATTEMPTS_DICT = {
    1: {'term': "{artist} + ' ' + {name}",
        'limit': ALBUM_SEARCH_LIMIT,
        'success': '',
        'fail': "--> WARNING: Failed fetching album metadata for '{song_name}'. Trying again..."},
    2: {'term': "{name}",
        'limit': ALBUM_SECOND_SEARCH_LIMIT,
        'success': "--> SUCCESS: Fetched album metadata successfully",
        'fail': "--> ERROR: Failed second attempt for '{song_name}'. Giving up."}
}


# ITUNES_SONGS_FETCH = {
#     'id': lambda song: song['trackId'],
#     'name': lambda song: song['trackName'],
#     'artist': lambda song: song['artistName'],
#     'album': None  # Should be changed
# }


class AMObject:
    """
    A class for handling Apple Music API's mutual attributes for
    Songs and Album objects.
    """

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
    def is_explicit(self) -> bool:
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

    @property
    def short_name(self):
        return f"{self.artist_name} - {self.name}"

    def get_artwork(self, w: int = ARTWORK_EMBED_SIZE, h: int = ARTWORK_EMBED_SIZE) -> bytes:
        """
        Returns the bytes of the artwork, with the given width and height.
        """
        return get(self.artwork_url.format(w=w, h=h)).content

    def _str_part_two(self):
        return AMOBJECT_REPR_SECOND.format(release_date=self.release_date,
                                           explicit=" *Explicit*" if self.is_explicit else '')

    def __bool__(self):
        return bool(self.json)

    def __str__(self):
        return AMOBJECT_REPR_FIRST.format(name=self.name, artist_name=self.artist_name, album_name=self.album_name)


class AMSong(AMObject):
    """
    A class for handling Apple Music API's Song object.
    """

    def __init__(self, json=None):
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
        """
        Returns the link for the song's audio preview.
        """
        return self.json['attributes']['previews'][0]['url']

    def album_id_from_song_url(self) -> str:
        """
        Returns the song's album id.
        """
        return self.url.split('/')[-1].split('?')[0]

    def get_artwork(self, w: int = ARTWORK_EMBED_SIZE, h: int = ARTWORK_EMBED_SIZE) -> bytes:
        """
        Returns the bytes of the artwork, with the given width and height.
        If album metadata was not fetched, artwork will be returned from the song itself.
        """
        if self.album:
            return get(self.artwork_url.format(w=w, h=h)).content
        return super(AMSong, self).get_artwork(w, h)

    def __str__(self):
        return "Song " + super(AMSong, self).__str__() \
               + AMSONG_REPR_MIDDLE.format(album_name=self.album_name) \
               + super(AMSong, self)._str_part_two()


class AMAlbum(AMObject):
    """
    A class for handling Apple Music API's Album object.
    """

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

    def __str__(self):
        return "Album " + super(AMAlbum, self).__str__() + super(AMAlbum, self)._str_part_two()


class AMFunctions:
    """
    A functions toolbox for using Apple Music's API and Song/Album objects.
    """

    @staticmethod
    def _get_language(name):
        return 'he' if has_hebrew(name) else 'en'

    @staticmethod
    def query(name: str, limit: int, language: str = 'en') -> dict:
        """
        Query Apple Music with the given string, search limit and response language.
        Returns the response json
        """
        query = AM_QUERY.format(name=name.replace(' ', '+'), limit=limit, language=language)
        json = get(query).json()
        return json

    @staticmethod
    def json_to_items(json: dict, items_type: type) -> List[AMObject]:
        if not len(json):
            return []
        item_key = 'songs' if items_type == AMSong else 'albums'
        items = [items_type(song_json) for song_json in json[item_key]['data']]
        return items

    @staticmethod
    def _choose_item(items: List[AMObject]):
        items_dict = {str(index): item for index, item in enumerate(items, start=1)}
        for index, item in items_dict.items():
            print(f"{index}) {item}")
        chosen_item = ask(f"\n--> What is your choice (1-{len(items_dict)})? ", bool_dict=items_dict)
        return chosen_item

    @staticmethod
    def _match_item(items: List[AMObject], wanted_id: str) -> AMObject:
        for item in items:
            if item.id == str(wanted_id):
                return item

    @classmethod
    def get_item(cls, items: List[AMSong or AMAlbum], query_term: str = None,
                 wanted_id: str = None) -> AMSong or AMAlbum:
        """
        Returns interactively chosen desired song, or automatically if only one result.
        Options are taken from the given results json.
        """
        if wanted_id:
            return cls._match_item(items, wanted_id)
        # No items case:
        elif not len(items):
            print(f"--> ERROR: Nothing found for '{query_term}'; Check for spelling errors.")
        # One item case:
        elif len(items) == 1:
            return items[0]
        # Multiple items case:
        else:
            print(f"--> Choose the correct item for '{query_term}':\n")
            chosen_item = cls._choose_item(items)
            return chosen_item
        return None

    @classmethod
    def attach_album(cls, song: AMSong, language: str, album: AMAlbum = None, attempt=1) -> int:
        """
        Attaching AMAlbum object to a given AMSong's album attribute.
        Returns 0 if succeed, and 1 otherwise.
        """
        if album:
            song.album = album
            return 0

        wanted_album_id = song.album_id_from_song_url()
        results = cls.query(ATTEMPTS_DICT[attempt]['term'], ATTEMPTS_DICT[attempt]['limit'], language)
        albums = cls.json_to_items(results, AMAlbum)
        matched_album = cls.get_item(albums, wanted_id=wanted_album_id)
        if matched_album:
            print(ATTEMPTS_DICT[attempt]['success'])
            song.album = matched_album
            return 0

        print(ATTEMPTS_DICT[attempt]['fail'].format(song_name=song.name))
        if attempt < 2:
            cls.attach_album(song, language, album, attempt + 1)
        else:
            return 1

    @classmethod
    def translate_item(cls, item: AMSong or AMAlbum) -> int:
        """
        If a language that's not english was chosen for metadata,
        translates genres to English.
        Returns 0 if succeed, and 1 otherwise.
        """
        wanted_song_id = item.id
        results = cls.query(item.artist_name + ' ' + item.album_name, ALBUM_SEARCH_LIMIT)
        for amobject in cls.json_to_items(results, type(item)):
            if amobject.id == wanted_song_id:
                item.json['attributes']['genreNames'] = amobject.genres
                return 0
        return 1

    @classmethod
    def search_song(cls, name, limit=SONG_SEARCH_LIMIT, album: AMAlbum = None, wanted_id: str = None) -> AMSong:
        """
        Querying Apple Music with given limit for a given name, determines
        the song's language, prompts user for choosing the correct song,
        attaches the song the album's object and returns the AMSong object.
        """
        language = cls._get_language(name)
        query_results = cls.query(name, limit, language)
        songs = cls.json_to_items(query_results, AMSong)
        song = cls.get_item(songs, name, wanted_id)
        if not song:
            return AMSong()
        cls.attach_album(song, language, album)
        if language == 'he':
            cls.translate_item(song)
        return song

    @classmethod
    def search_album(cls, name, limit=ALBUM_SEARCH_LIMIT):
        language = cls._get_language(name)
        query_results = cls.query(name, limit, language)
        albums = cls.json_to_items(query_results, AMAlbum)
        album = cls.get_item(albums, name)
        if album:
            cls.translate_item(album)
        return album if album else AMAlbum()

    @classmethod
    def album_to_songs(cls, album: AMAlbum) -> List[AMSong]:
        language = cls._get_language(f"{album.name} {album.artist_name}")
        song_jsons = get(ITUNES_QUERY.format(id=album.id)).json()['results'][1:]
        song_ids = {}
        for song_json in song_jsons:
            song_id = str(song_json['trackId'])
            song_name = song_json['trackName']
            artist = song_json['artistName']
            song_ids.update({song_id: artist + ' ' + song_name})

        results = cls.query(f"{album.name} {album.artist_name}", 25, language)
        items = cls.json_to_items(results, AMSong)
        songs_dict = cls.batch_match(list(song_ids.keys()), items)

        for song_id, song in songs_dict.items():
            if not song:
                print(f"--> ERROR: Couldn't find the song '{song_ids[song_id]}'")
            else:
                song.album = album
                song.json['attributes']['genreNames'] = album.genres

        return list(filter(None, songs_dict.values()))

    @staticmethod
    def batch_match(wanted_ids: list, items: List[AMSong or AMAlbum]):
        match_dict = {wanted_id: None for wanted_id in wanted_ids}
        items_dict = {item.id: item for item in items}
        match_dict.update((item_id, items_dict[item_id]) for item_id in match_dict.keys() & items_dict.keys())
        return match_dict

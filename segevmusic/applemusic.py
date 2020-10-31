from segevmusic.utils import get_language, choose_item, update_url_param
from requests import get
from typing import List
from urllib.parse import quote
from re import search
from json import loads

ARTWORK_EMBED_SIZE = 1400
ARTWORK_REPR_SIZE = 600
ARTWORK_FORMAT = 'jpg'
AMOBJECT_REPR_FIRST = "Name: {name} // Artist: {artist_name} "
AMOBJECT_REPR_SECOND = "({release_date}){explicit}"
AMSONG_REPR_MIDDLE = " // Album: {album_name} "
AM_QUERY = r"https://tools.applemediaservices.com/api/apple-media/music/IL/" \
           r"search.json?types=songs,albums&term={name}&limit={limit}&l={language}"
ITUNES_QUERY = 'https://itunes.apple.com/il/lookup?id={id}&entity=song&l={language}'
AM_REGEX = b'<script type="fastboot/shoebox" id="shoebox-media-api-cache-amp-music">(.*?)</script>'
AM_LANGUAGE_PARAM = 'l'

SONG_SEARCH_LIMIT = 1
ALBUM_SEARCH_LIMIT = 5


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

    @genres.setter
    def genres(self, value):
        self.json['attributes']['genreNames'] = value

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

    def get_artwork(self, w: int = ARTWORK_EMBED_SIZE, h: int = ARTWORK_EMBED_SIZE, f: str = ARTWORK_FORMAT) -> bytes:
        """
        Returns the bytes of the artwork, with the given width and height.
        """
        url = self.artwork_url
        if '{f}' in url:
            return get(url.format(w=w, h=h, f=f)).content
        return get(url.format(w=w, h=h)).content

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

    @isrc.setter
    def isrc(self, value: str):
        self.json['attributes']['isrc'] = value

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

    def get_artwork(self, w: int = ARTWORK_EMBED_SIZE, h: int = ARTWORK_EMBED_SIZE,
                    prefer_album: bool = False) -> bytes:
        """
        Returns the bytes of the artwork, with the given width and height.
        If album metadata was not fetched, artwork will be returned from the song itself.
        """
        if prefer_album and self.album:
            return self.album.get_artwork(w, h)
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

    @property
    def songs(self) -> List[AMSong]:
        found_songs = []
        for track in self.json['relationships']['tracks']['data']:
            if track['type'] == 'songs':
                song = AMSong(track)
                song.genres = self.genres
                found_songs.append(AMSong(track))
        return found_songs

    def __iter__(self):
        for song in self.songs:
            yield song

    def __str__(self):
        return "Album " + super(AMAlbum, self).__str__() + super(AMAlbum, self)._str_part_two()


class AMPlaylist:
    def __init__(self, json=None):
        self.json = json

    @property
    def songs(self) -> List[AMSong]:
        return [AMSong(song) for song in self.json['relationships']['tracks']['data'] if song['type'] == 'songs']

    def __iter__(self):
        for song in self.songs:
            yield song


class AMFunctions:
    """
    A functions toolbox for using Apple Music's API and Song/Album objects.
    """
    AM_TYPES = {
        'albums': AMAlbum,
        'songs': AMSong,
        'playlists': AMPlaylist
    }

    @staticmethod
    def query(name: str, limit: int) -> dict:
        """
        Query Apple Music with the given string, search limit and response language.
        Returns the response json
        """
        encoded_name = quote(name)
        query = AM_QUERY.format(name=encoded_name, limit=limit, language=get_language(name))
        json = get(query).json()
        return json

    @staticmethod
    def json_to_items(json: dict, items_type: type) -> List[AMObject]:
        if not len(json):
            return []
        item_key = 'songs' if items_type == AMSong else 'albums'
        items = [items_type(song_json) for song_json in json[item_key]['data']]
        return items

    @classmethod
    def get_item(cls, items: List[AMObject], query_term: str = None) -> AMObject:
        """
        Returns interactively chosen desired song, or automatically if only one result.
        Options are taken from the given results json.
        """
        # No items case:
        if not len(items):
            print(f"--> ERROR: Nothing found for '{query_term}'; Check for spelling errors.")
        # One item case:
        elif len(items) == 1:
            return items[0]
        # Multiple items case:
        else:
            print(f"--> Choose the correct item for '{query_term}':\n")
            chosen_item = choose_item(items)
            return chosen_item

    @classmethod
    def attach_album(cls, song: AMSong, album: AMAlbum = None):
        """
        Attaching AMAlbum object to a given AMSong's album attribute.
        Returns 0 if succeed, and 1 otherwise.
        """
        if album:
            song.album = album
        song.album = cls.get_item_from_url(song.url)

    @classmethod
    def translate_item(cls, item: AMSong or AMAlbum):
        """
        If a language that's not english was chosen for metadata,
        translates genres to English.
        Returns 0 if succeed, and 1 otherwise.
        """
        patched_url = update_url_param(item.url, AM_LANGUAGE_PARAM, 'en')
        album = cls.get_item_from_url(patched_url)
        item.genres = album.genres

    @classmethod
    def _search_item(cls, name: str, item_type: AMSong or AMAlbum, limit: int) -> AMSong or AMAlbum:
        query_results = cls.query(name, limit)
        items = cls.json_to_items(query_results, item_type)
        item = cls.get_item(items, name)
        return item

    @classmethod
    def search_song(cls, name: str, limit: int = None) -> AMSong:
        """
        Querying Apple Music with given limit for a given name, determines
        the song's language, prompts user for choosing the correct song,
        attaches the song the album's object and returns the AMSong object.
        """
        if not limit:
            limit = SONG_SEARCH_LIMIT
        song = cls._search_item(name, AMSong, limit)
        if not song:
            return AMSong()
        cls.attach_album(song)
        if get_language(name) == 'he':
            song.genres = song.album.genres
        return song

    @classmethod
    def search_album(cls, name: str, limit: int = ALBUM_SEARCH_LIMIT):
        album = cls._search_item(name, AMAlbum, limit)
        if album:
            album = cls.get_item_from_url(album.url)
            cls.translate_item(album)
        return album if album else AMAlbum()

    @classmethod
    def get_item_from_url(cls, url: str):
        response = get(url).content
        m = search(AM_REGEX, response)
        try:
            json = loads(m.group(1))
            json_data = loads(json[list(json.keys())[1]])['d'][0]
        except KeyError:
            return None
        item_type = json_data['type']
        return cls.AM_TYPES[item_type](json_data) if item_type in cls.AM_TYPES else json_data

    @staticmethod
    def _artwork_url_customize(url):
        custom_url = url.split('/')
        return ''.join(custom_url[:-1] + ['{w}x{h}bb.jpeg'])

    @staticmethod
    def query_itunes(item_id: str, language: str = 'en'):
        return get(ITUNES_QUERY.format(id=item_id, language=language)).json()['results']

    @classmethod
    def itunes_to_song(cls, itunes_json: dict, album: AMAlbum = None) -> AMSong:
        song = AMSong({
            'id': itunes_json['trackId'],
            'type': 'songs',
            'href': None,
            'attributes': {
                'previews': [{'url': cls._artwork_url_customize(itunes_json['previewUrl'])}],
                'artwork': {
                    'width': ARTWORK_EMBED_SIZE,
                    'height': ARTWORK_EMBED_SIZE,
                    'url': itunes_json['artworkUrl100'],
                },
                'artistName': itunes_json['artistName'],
                'url': itunes_json['trackViewUrl'],
                'discNumber': itunes_json['discNumber'],
                'genreNames': [itunes_json['primaryGenreName']] if not album else album.genres,
                'durationInMillis': itunes_json['trackTimeMillis'],
                'releaseDate': itunes_json['releaseDate'][:10],
                'name': itunes_json['trackName'],
                'isrc': None,
                'albumName': itunes_json['collectionName'],
                'trackNumber': itunes_json['trackNumber']
            }
        })
        song.album = album
        return song

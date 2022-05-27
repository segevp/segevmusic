from segevmusic.utils import get_language, choose_item, update_url_param, has_hebrew, get_url_param_value
from segevmusic._genres import GENRES_TRANSLATION
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
ITUNES_SONG_QUERY = 'https://itunes.apple.com/il/lookup?id={id}&entity=song&l={language}'
ITUNES_ALBUM_QUERY = 'https://itunes.apple.com/il/lookup?id={id}&entity=album&l={language}'
AM_DOMAIN = 'apple.com'
AM_REGEX = b'<script type="fastboot/shoebox" id="shoebox-media-api-cache-amp-music">(.*?)</script>'
AM_LANGUAGE_PARAM = 'l'

SONG_SEARCH_LIMIT = 1
ALBUM_SEARCH_LIMIT = 5


class AMObject:
    """
    A class for handling Apple Music API's mutual attributes for
    Songs and Album objects.
    """

    def __init__(self, json=None, translate=True):
        self.json = json
        self.language = None
        if self and translate:
            AMFunctions.translate_item(self)

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

    def __repr__(self):
        return f"<{self.__str__()}>"


class AMSong(AMObject):
    """
    A class for handling Apple Music API's Song object.
    """

    def __init__(self, json=None, album=None, add_album=True, translate=True):
        super().__init__(json, translate)
        self.album = album
        if (self and add_album) and not album:
            AMFunctions.attach_album(self)

    @property
    def disc_number(self):
        return self.json['attributes']['discNumber']

    @disc_number.setter
    def disc_number(self, value):
        self.json['attributes']['discNumber'] = value

    @property
    def isrc(self):
        return self.json['attributes']['isrc']

    @isrc.setter
    def isrc(self, value: str):
        self.json['attributes']['isrc'] = value

    @property
    def track_number(self):
        return self.json['attributes']['trackNumber']

    @track_number.setter
    def track_number(self, value):
        self.json['attributes']['trackNumber'] = value

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
            try:
                return self.album.get_artwork(w, h)
            except KeyError:
                pass
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
        self.found_songs = []

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

    @track_count.setter
    def track_count(self, value):
        self.json['attributes']['trackCount'] = value

    @property
    def songs(self) -> List[AMSong]:
        if not self.found_songs:
            for track in self.json['relationships']['tracks']['data']:
                if track['type'] == 'songs':
                    song = AMSong(track, self, translate=False)
                    song.genres = self.genres
                    self.found_songs.append(song)
        return self.found_songs

    def __iter__(self):
        for song in self.songs:
            yield song

    def __str__(self):
        return "Album " + super(AMAlbum, self).__str__() + super(AMAlbum, self)._str_part_two()

    def __getitem__(self, item):
        for song in self.songs:
            if song.id == item:
                return song
        raise IndexError(f"The id {item} was not found in this album.")


class AMPlaylist:
    def __init__(self, json=None):
        self.json = json
        self.found_songs = []

    @property
    def songs(self) -> List[AMSong]:
        if not self.found_songs:
            for track in self.json['relationships']['tracks']['data']:
                if track['type'] == 'songs':
                    song = AMSong(track, add_album=False)
                    self.found_songs.append(song)
            AMFunctions.update_metadata(self, add_album=True)
        return self.found_songs

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
        if not json:
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
            return AMObject()
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
        song.album = cls.get_item_from_url(song.url, song.language).album

    @classmethod
    def translate_item(cls, item: AMSong or AMAlbum):
        """
        Translates first genre to English.
        """
        i = 0
        genre = item.genres[i]
        if not has_hebrew(genre):
            pass
        elif genre in GENRES_TRANSLATION:
            item.genres[i] = GENRES_TRANSLATION[genre]
        else:
            translated_genre = cls.get_item_from_url(update_url_param(item.url, 'l', 'en')).genres[i]
            item.genres[i] = translated_genre
            GENRES_TRANSLATION[genre] = translated_genre

    @classmethod
    def _search_item(cls, name: str, item_type: AMSong or AMAlbum, limit: int) -> AMSong or AMAlbum:
        query_results = cls.query(name, limit)
        items = cls.json_to_items(query_results, item_type)
        item = cls.get_item(items, name)
        item.language = get_language(name)
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
        return song

    @classmethod
    def search_album(cls, name: str, limit: int = ALBUM_SEARCH_LIMIT):
        album = cls._search_item(name, AMAlbum, limit)
        if album:
            album = cls.get_item_from_url(album.url)
        return album if album else AMAlbum()

    @classmethod
    def get_item_from_url(cls, url: str, force_language: str = None):
        if force_language:
            url = update_url_param(url, AM_LANGUAGE_PARAM, force_language)
        response = get(url).content
        item = cls._get_item_from_html(response)
        index = get_url_param_value(url, 'i')
        return item if not index else item[index]

    @classmethod
    def _get_item_from_html(cls, html):
        m = search(AM_REGEX, html)
        try:
            json = loads(m.group(1))
            json_data = loads(json[list(json.keys())[1]])['d'][0]
        except (KeyError, AttributeError):
            print("--> ERROR: The given URL is not supported!")
            return None
        item_type = json_data['type']
        return cls.AM_TYPES[item_type](json_data) if item_type in cls.AM_TYPES else json_data

    @staticmethod
    def _artwork_url_customize(url):
        custom_url = url.split('/')
        return ''.join(custom_url[:-1] + ['{w}x{h}bb.jpeg'])

    @staticmethod
    def query_itunes(item_id: str, language: str = 'he', query_album=False):
        query_url = ITUNES_SONG_QUERY if not query_album else ITUNES_ALBUM_QUERY
        return get(query_url.format(id=item_id, language=language)).json()['results']

    @staticmethod
    def itunes_results_to_dict(query_results):
        results = {
            'tracks': {},
            'collections': {}
        }
        for result in query_results:
            result_type = result['wrapperType']
            result_id = str(result[result_type + 'Id'])
            results[result_type + 's'][result_id] = result
        return results

    @classmethod
    def update_metadata(cls, collection: AMAlbum or AMPlaylist, add_album=False):
        song_ids = [song.id for song in collection.songs]
        results = cls.query_itunes(','.join(song_ids), query_album=True)
        results = cls.itunes_results_to_dict(results)
        for song in collection.found_songs:
            album_id = song.album_id_from_song_url()
            itunes_song = results['tracks'][song.id]
            if add_album:
                itunes_album = results['collections'][album_id]
                album_json = {
                    'id': album_id,
                    'attributes': {
                        'artistName': itunes_album['artistName'],
                        'genreNames': song.genres,
                        'recordLabel': None
                    }
                }
                if 'copyright' in itunes_album:
                    album_json['attributes']['copyright'] = itunes_album['copyright']
                song.album = AMAlbum(album_json)
            song.track_number = str(itunes_song['trackNumber'])
            song.album.track_count = str(itunes_song['trackCount'])
            song.disc_number = f"{itunes_song['discNumber']}/{itunes_song['discCount']}"

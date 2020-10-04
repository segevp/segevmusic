from requests import get
from segevmusic.utils import has_hebrew, ask

ARTWORK_EMBED_SIZE = 1400
ARTWORK_REPR_SIZE = 600
AMSONG_REPR = """Name: {name} // Artist: {artist_name} // Album: {album_name}({release_date}){explicit}"""
SONG_SEARCH_LIMIT = 1
ALBUM_SEARCH_LIMIT = 5
ALBUM_SECOND_SEARCH_LIMIT = 10
AM_QUERY = r"https://tools.applemediaservices.com/api/apple-media/music/IL/" \
           r"search.json?types=songs,albums&term={name}&limit={limit}&l={language}"


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

    def __bool__(self):
        return bool(self.json)


class AMSong(AMObject):
    """
    A class for handling Apple Music API's Song object.
    """

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
        return AMSONG_REPR.format(name=self.name, artist_name=self.artist_name, album_name=self.album_name,
                                  release_date=self.release_date, explicit=" *Explicit*" if self.is_explicit else '')


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


class AMFunctions:
    """
    A functions toolbox for using Apple Music's API and Song/Album objects.
    """

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
    def choose_song(json: dict, query_term: str) -> AMSong:
        """
        Returns interactively chosen desired song, or automatically if only one result.
        Options are taken from the given results json.
        """
        index = 0
        songs = [AMSong(song_json) for song_json in json['songs']['data']]
        # One song case:
        if len(songs) == 1:
            # print(f"--> {songs[0]}")
            return songs[0]
        print(f"--> Choose the correct song for {query_term}:\n")
        # Multiple songs case:
        for song in songs:
            print(f"{index + 1})", song, end='\n')
            index += 1
        options = {str(i): i for i in range(1, index + 1)}
        chosen_index = ask(f"\n--> What is your choice (1-{index})? ", bool_dict=options) - 1
        return songs[chosen_index]

    @classmethod
    def attach_album(cls, amsong: AMSong, language: str) -> int:
        """
        Attaching AMAlbum object to a given AMSong's album attribute.
        Returns 0 if succeed, and 1 otherwise.
        """
        wanted_album_id = amsong.album_id_from_song_url()
        results = cls.query(amsong.artist_name + ' ' + amsong.album_name, ALBUM_SEARCH_LIMIT, language)
        for album in results['albums']['data']:
            if album['id'] == wanted_album_id:
                amsong.album = AMAlbum(album)
                return 0
        print(f"--> WARNING: Failed fetching album metadata for {amsong.name}. Trying again...")
        results = cls.query(amsong.album_name, ALBUM_SECOND_SEARCH_LIMIT, language)
        for album in results['albums']['data']:
            if album['id'] == wanted_album_id:
                amsong.album = AMAlbum(album)
                print("--> SUCCESS: Fetched album metadata successfully")
                return 0
        print("--> ERROR: Failed second attempt. Giving up.")
        return 1

    @classmethod
    def translate_song(cls, amsong: AMSong) -> int:
        """
        If a language that's not english was chosen for metadata,
        translates genres to English.
        Returns 0 if succeed, and 1 otherwise.
        """
        wanted_song_id = amsong.id
        results = cls.query(amsong.artist_name + ' ' + amsong.album_name, SONG_SEARCH_LIMIT)
        for song in results['songs']['data']:
            if song['id'] == wanted_song_id:
                amsong.json['attributes']['genreNames'] = AMSong(song).genres
                return 0
        return 1

    @classmethod
    def search_song(cls, name, limit=SONG_SEARCH_LIMIT) -> AMSong or None:
        """
        Querying Apple Music with given limit for a given name, determines
        the song's language, prompts user for choosing the correct song,
        attaches the song the album's object and returns the AMSong object.
        """
        # Set song language
        language = 'he' if has_hebrew(name) else 'en'
        query_results = cls.query(name, limit=limit, language=language)
        # Run query
        try:
            song = cls.choose_song(query_results, name)
        except KeyError:
            print(f"--> ERROR: Nothing found for '{name}'; Check for spelling errors.")
            return None
        # Attach album metadata
        cls.attach_album(song, language)
        # Translate genres
        if language == 'he':
            cls.translate_song(song)
        return song

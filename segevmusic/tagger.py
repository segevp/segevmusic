from segevmusic.applemusic import AMSong
from mutagen.id3 import ID3, TXXX, TIT2, TPE1, TALB, TPE2, TCON, TPUB, TSRC, APIC, TCOP, TDRC
from os import replace
from os.path import realpath, join
from typing import List

TAGS = {
    "song_name": lambda amsong: TIT2(text=amsong.name),
    "album_name": lambda amsong: TALB(text=amsong.album_name),
    "isrc": lambda amsong: TSRC(text=amsong.isrc),
    "record_label": lambda amsong: TPUB(text=amsong.album.record_label),
    "copyright": lambda amsong: TCOP(text=amsong.album.copyright),
    "genre": lambda amsong: TCON(text=amsong.genres[0]),
    "album_artist": lambda amsong: TPE2(text=amsong.album.artist_name) if amsong.album else None,
    "song_artist": lambda amsong: TPE1(text=amsong.artist_name),
    "itunes_advisory": lambda amsong: TXXX(desc="ITUNESADVISORY", text="1") if amsong.is_explicit else None,
    "release_date": lambda amsong: TDRC(text=amsong.release_date),
    "artwork": lambda amsong: APIC(mime='image/jpeg', desc='cover', data=amsong.get_artwork(prefer_album=True)),
    "disc_position": lambda amsong: amsong.disc_number if '/' in amsong.disc_number else None,
    "track_position": lambda amsong: amsong.track_number if '/' in amsong.track_number else None
}
ERROR_MSG = "--> For '{song}' failed tagging: {tags}"


class Tagger:
    """
    A class for handling songs metadata.
    """

    def __init__(self, path):
        self.path = realpath(path)

    def tag_song(self, song: AMSong):
        """
        Tags ID3 metadata using the TAGS constant and saves changes.
        Prints errors afterwards
        :param song:
        :return:
        """
        file_path = self.generate_isrc_path(song)
        try:
            id3 = ID3(file_path)
        except Exception as e:
            print(f"--> ERROR: Internal mutagen exception: {e}")
            return None
        errors = []
        for key, tag in TAGS.items():
            try:
                id3.add(tag(song))
            except:
                errors.append(key)
        id3.save(v1=2, v2_version=3, v23_sep='/')
        # self._print_errors(song, errors)

    def rename_isrc_path(self, amsong: AMSong) -> str:
        """
        Renaming song's isrc filename to the output of 'generate_good_path' function
        and retuns the new path
        """
        new_path = self.generate_good_path(amsong)
        replace(self.generate_isrc_path(amsong), new_path)
        return new_path

    def generate_isrc_path(self, amsong: AMSong) -> str:
        """
        Returns the given song's ISRC path.
        """
        return join(self.path, f"{amsong.isrc}.mp3")

    def generate_good_path(self, amsong: AMSong) -> str:
        """
        Return the given song's "good" path - in the format:
        "<artist name> - <song name>.mp3"
        """
        return join(self.path, f"{amsong.artist_name} - {amsong.name}.mp3")

    @staticmethod
    def _print_errors(song: AMSong, errors: List[str]):
        """
        Prints any given errors except when it's only an error with
        the iTunes Advisory tag.
        """
        advisory = "itunes_advisory"
        if advisory in errors:
            errors.remove(advisory)
        if errors:
            print(ERROR_MSG.format(song=song.short_name, tags=errors))

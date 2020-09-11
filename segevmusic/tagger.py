from mutagen.id3 import ID3, TXXX, TIT2, TPE1, TALB, TPE2, TCON, TPUB, TSRC, APIC, TCOP, TDRC
from os import rename
from os.path import realpath

TAGS = {
    "song_name": lambda amsong: TIT2(text=amsong.name),
    "album_name": lambda amsong: TALB(text=amsong.album_name),
    "isrc": lambda amsong: TSRC(text=amsong.isrc),
    "record_label": lambda amsong: TPUB(text=amsong.album.record_label),
    "copyright": lambda amsong: TCOP(text=amsong.album.copyright),
    "genre": lambda amsong: TCON(text=amsong.genres[0]),
    "album_artist": lambda amsong: TPE2(text=amsong.album.artist_name),
    "song_artist": lambda amsong: TPE1(text=amsong.artist_name),
    "itunes_advisory": lambda amsong: TXXX(desc="ITUNESADVISORY", text="1") if amsong.is_explicit else None,
    "release_date": lambda amsong: TDRC(text=amsong.release_date),
    "artwork": lambda amsong: APIC(mime='image/jpeg', desc='cover', data=amsong.album.get_artwork())
}
ERROR_MSG = "Failed tags: {tags}"


class Tagger:
    @classmethod
    def tag_song(cls, amsong):
        file_path = cls.generate_isrc_path(amsong)
        id3 = ID3(file_path)
        errors = []
        for key, tag in TAGS.items():
            try:
                id3.add(tag(amsong))
            except:
                errors.append(key)
        id3.save(v1=2, v2_version=3, v23_sep='/')
        cls.print_errors(errors)

    @classmethod
    def rename_isrc_path(cls, amsong):
        rename(cls.generate_isrc_path(amsong), cls.generate_good_path(amsong))

    @staticmethod
    def generate_isrc_path(amsong):
        return realpath(f"./Songs/{amsong.isrc}.mp3")

    @staticmethod
    def generate_good_path(amsong):
        return realpath(f"./Songs/{amsong.artist_name} - {amsong.name}.mp3")

    @staticmethod
    def print_errors(errors):
        advisory = "itunes_advisory"
        if advisory in errors:
            errors.remove(advisory)
        if errors:
            print(ERROR_MSG.format(tags=errors))

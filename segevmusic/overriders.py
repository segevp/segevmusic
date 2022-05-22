import deemix.utils.localpaths as localpaths
from deezer import TrackFormats
from deemix.settings import OverwriteOption, FeaturesOption, save, check
from pathlib import Path
from os import makedirs
import json
from copy import deepcopy
from deemix.utils import formatListener

WANTED_LOG_KEYS = {
    "progress",
    "failed"
}
DEFAULTS = {
    "downloadLocation": str(localpaths.getMusicFolder()),
    "tracknameTemplate": "%isrc%",
    "albumTracknameTemplate": "%tracknumber% - %title%",
    "playlistTracknameTemplate": "%position% - %artist% - %title%",
    "createPlaylistFolder": True,
    "playlistNameTemplate": "%playlist%",
    "createArtistFolder": False,
    "artistNameTemplate": "%artist%",
    "createAlbumFolder": True,
    "albumNameTemplate": "%artist% - %album%",
    "createCDFolder": True,
    "createStructurePlaylist": False,
    "createSingleFolder": False,
    "padTracks": True,
    "paddingSize": "0",
    "illegalCharacterReplacer": "_",
    "queueConcurrency": 3,
    "maxBitrate": str(TrackFormats.MP3_320),
    "feelingLucky": False,
    "fallbackBitrate": True,
    "fallbackSearch": False,
    "fallbackISRC": False,
    "logErrors": True,
    "logSearched": False,
    "overwriteFile": OverwriteOption.DONT_OVERWRITE,
    "createM3U8File": False,
    "playlistFilenameTemplate": "playlist",
    "syncedLyrics": False,
    "embeddedArtworkSize": 800,
    "embeddedArtworkPNG": False,
    "localArtworkSize": 1400,
    "localArtworkFormat": "jpg",
    "saveArtwork": True,
    "coverImageTemplate": "cover",
    "saveArtworkArtist": False,
    "artistImageTemplate": "folder",
    "jpegImageQuality": 90,
    "dateFormat": "Y-M-D",
    "albumVariousArtists": True,
    "removeAlbumVersion": False,
    "removeDuplicateArtists": True,
    "featuredToTitle": FeaturesOption.NO_CHANGE,
    "titleCasing": "nothing",
    "artistCasing": "nothing",
    "executeCommand": "",
    "tags": {
        "title": False,
        "artist": False,
        "album": False,
        "cover": False,
        "trackNumber": True,
        "trackTotal": True,
        "discNumber": True,
        "discTotal": True,
        "albumArtist": True,
        "genre": False,
        "year": False,
        "date": False,
        "explicit": False,
        "isrc": True,
        "length": False,
        "barcode": False,
        "bpm": True,
        "replayGain": False,
        "label": False,
        "lyrics": True,
        "syncedLyrics": True,
        "copyright": False,
        "composer": False,
        "involvedPeople": False,
        "source": False,
        "rating": False,
        "savePlaylistAsCompilation": False,
        "useNullSeparator": False,
        "saveID3v1": True,
        "multiArtistSeparator": "default",
        "singleAlbumArtist": True,
        "coverDescriptionUTF8": False
    }
}


class LogListener:
    @classmethod
    def send(cls, key, value=None):
        if key == "updateQueue":
            if any(WANTED_LOG_KEYS.intersection(set(value))):
                log_string = formatListener(key, value)
                if log_string:
                    print(log_string)


def load_settings(config_folder=None):
    config_folder = Path(config_folder or localpaths.getConfigFolder())
    makedirs(config_folder, exist_ok=True)  # Create config folder if it doesn't exsist
    if not (config_folder / 'config.json').is_file():
        save(DEFAULTS, config_folder)  # Create config file if it doesn't exsist

    # Read config file
    with open(config_folder / 'config.json', 'r', encoding="utf-8") as configFile:
        try:
            settings = json.load(configFile)
        except json.decoder.JSONDecodeError:
            save(DEFAULTS, config_folder)
            settings = deepcopy(DEFAULTS)
        except Exception:
            settings = deepcopy(DEFAULTS)

    if check(settings) > 0:
        save(settings, config_folder)  # Check the settings and save them if something changed
    return settings

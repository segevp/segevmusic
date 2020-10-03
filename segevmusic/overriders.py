# settings_init dependencies
import deemix.utils.localpaths as localpaths
from deemix.api.deezer import TrackFormats
from deemix.app.settings import OverwriteOption, FeaturesOption
from os.path import isdir, isfile, join, realpath
from os import makedirs
import logging

# cli_login dependencies
from pathlib import Path
import json
import datetime
import platform
from os import listdir
from deemix import __version__ as deemixVersion

# settings_init dependencies
DEFAULT_SETTINGS = {
    "downloadLocation": join(realpath('.'), 'deemix Music'),
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
    "fallbackBitrate": True,
    "fallbackSearch": False,
    "logErrors": True,
    "logSearched": False,
    "saveDownloadQueue": False,
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
    "jpegImageQuality": 80,
    "dateFormat": "Y-M-D",
    "albumVariousArtists": True,
    "removeAlbumVersion": False,
    "removeDuplicateArtists": False,
    "tagsLanguage": "",
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
        "trackTotal": False,
        "discNumber": True,
        "discTotal": False,
        "albumArtist": False,
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
        "lyrics": False,
        "syncedLyrics": False,
        "copyright": False,
        "composer": False,
        "involvedPeople": False,
        "savePlaylistAsCompilation": False,
        "useNullSeparator": False,
        "saveID3v1": True,
        "multiArtistSeparator": "default",
        "singleAlbumArtist": False,
        "coverDescriptionUTF8": False
    }
}
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger('deemix')
logger.setLevel(logging.WARN)


def settings_init(self, configFolder=None):
    self.settings = {}
    self.configFolder = configFolder
    if not self.configFolder:
        self.configFolder = localpaths.getConfigFolder()
    self.configFolder = Path(self.configFolder)

    # Create config folder if it doesn't exsist
    makedirs(self.configFolder, exist_ok=True)

    # Create config file if it doesn't exsist
    if not (self.configFolder / 'config.json').is_file():
        with open(self.configFolder / 'config.json', 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)

    # Read config file
    with open(self.configFolder / 'config.json', 'r') as configFile:
        self.settings = json.load(configFile)

    self.settingsCheck()

    # Make sure the download path exsits
    # makedirs(self.settings['downloadLocation'], exist_ok=True)

    # LOGFILES

    # Create logfile name and path
    logspath = self.configFolder / 'logs'
    now = datetime.datetime.now()
    logfile = now.strftime("%Y-%m-%d_%H%M%S") + ".log"
    makedirs(logspath, exist_ok=True)

    # Add handler for logging
    fh = logging.FileHandler(logspath / logfile, 'w', 'utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s'))
    logger.addHandler(fh)
    logger.info(f"{platform.platform(True, True)} - Python {platform.python_version()}, deemix {deemixVersion}")

    # Only keep last 5 logfiles (to preserve disk space)
    logslist = listdir(logspath)
    logslist.sort()
    if len(logslist) > 5:
        for i in range(len(logslist) - 5):
            (logspath / logslist[i]).unlink()


def cli_login(self, arl=None):
    """
    Added the ability to add arl argument, without prompting user input.
    """
    logged_in = 0
    config_folder = self.set.configFolder
    if not isdir(config_folder):
        makedirs(config_folder, exist_ok=True)
    if arl:
        logged_in = self.dz.login_via_arl(arl)
    if not logged_in:
        if isfile(join(config_folder, '.arl')):
            with open(join(config_folder, '.arl'), 'r') as f:
                arl = f.readline().rstrip("\n")
            if not self.dz.login_via_arl(arl):
                arl = self.requestValidArl()
        else:
            arl = self.requestValidArl()
    with open(join(config_folder, '.arl'), 'w') as f:
        f.write(arl)

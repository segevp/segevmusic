from os.path import isdir, isfile, join, expanduser
from os import makedirs, listdir, remove
from deemix import __version__ as deemixVersion
from datetime import datetime
import logging
import json
import platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deemix')


def settings_init(self, configFolder):
    self.settings = {}
    self.configFolder = configFolder
    self.defaultSettings = {
        "downloadLocation": join(expanduser("~"), 'deemix Music'),
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
        "maxBitrate": "3",
        "fallbackBitrate": True,
        "fallbackSearch": False,
        "logErrors": True,
        "logSearched": False,
        "saveDownloadQueue": False,
        "overwriteFile": "n",
        "createM3U8File": False,
        "playlistFilenameTemplate": "playlist",
        "syncedLyrics": False,
        "embeddedArtworkSize": 800,
        "embeddedArtworkPNG": False,
        "localArtworkSize": 1400,
        "localArtworkFormat": "jpg",
        "saveArtwork": False,
        "coverImageTemplate": "cover",
        "saveArtworkArtist": False,
        "artistImageTemplate": "folder",
        "jpegImageQuality": 100,
        "dateFormat": "Y-M-D",
        "albumVariousArtists": True,
        "removeAlbumVersion": False,
        "removeDuplicateArtists": False,
        "featuredToTitle": "0",
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
            "singleAlbumArtist": False
        }
    }

    # Create config folder if it doesn't exist
    makedirs(self.configFolder, exist_ok=True)

    # Create config file if it doesn't exist
    if not isfile(join(self.configFolder, 'config.json')):
        with open(join(self.configFolder, 'config.json'), 'w') as f:
            json.dump(self.defaultSettings, f, indent=2)

    # Read config file
    with open(join(self.configFolder, 'config.json'), 'r') as configFile:
        self.settings = json.load(configFile)

    self.settingsCheck()

    # Make sure the download path exits
    makedirs(self.settings['downloadLocation'], exist_ok=True)

    # LOGFILES

    # Create logfile name and path
    logspath = join(self.configFolder, 'logs')
    now = datetime.now()
    logfile = now.strftime("%Y-%m-%d_%H%M%S") + ".log"
    makedirs(logspath, exist_ok=True)

    # Add handler for logging
    fh = logging.FileHandler(join(logspath, logfile), 'w', 'utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s'))
    logger.addHandler(fh)
    logger.info(f"{platform.platform(True, True)} - Python {platform.python_version()}, deemix {deemixVersion}")

    # Only keep last 5 logfiles (to preserve disk space)
    logslist = listdir(logspath)
    logslist.sort()
    if len(logslist) > 5:
        for i in range(len(logslist) - 5):
            remove(join(logspath, logslist[i]))


def cli_login(self, arl=None):
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

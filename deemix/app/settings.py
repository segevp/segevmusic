#!/usr/bin/env python3
import json
import os.path as path
from os import makedirs, listdir, remove
from deemix import __version__ as deemixVersion
import logging
import datetime
import platform

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deemix')


class Settings:
    def __init__(self, configFolder):
        self.settings = {}
        self.configFolder = configFolder
        self.defaultSettings = {
            "downloadLocation": path.join(path.expanduser("~"), 'deemix Music'),
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
        if not path.isfile(path.join(self.configFolder, 'config.json')):
            with open(path.join(self.configFolder, 'config.json'), 'w') as f:
                json.dump(self.defaultSettings, f, indent=2)

        # Read config file
        with open(path.join(self.configFolder, 'config.json'), 'r') as configFile:
            self.settings = json.load(configFile)

        self.settingsCheck()

        # Make sure the download path exits
        makedirs(self.settings['downloadLocation'], exist_ok=True)

        # LOGFILES

        # Create logfile name and path
        logspath = path.join(self.configFolder, 'logs')
        now = datetime.datetime.now()
        logfile = now.strftime("%Y-%m-%d_%H%M%S") + ".log"
        makedirs(logspath, exist_ok=True)

        # Add handler for logging
        fh = logging.FileHandler(path.join(logspath, logfile), 'w', 'utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] %(message)s'))
        logger.addHandler(fh)
        logger.info(f"{platform.platform(True, True)} - Python {platform.python_version()}, deemix {deemixVersion}")

        # Only keep last 5 logfiles (to preserve disk space)
        logslist = listdir(logspath)
        logslist.sort()
        if len(logslist) > 5:
            for i in range(len(logslist) - 5):
                remove(path.join(logspath, logslist[i]))

    # Saves the settings
    def saveSettings(self, newSettings=None):
        if newSettings:
            self.settings = newSettings
        with open(path.join(self.configFolder, 'config.json'), 'w') as configFile:
            json.dump(self.settings, configFile, indent=2)

    # Checks if the default settings have changed
    def settingsCheck(self):
        changes = 0
        for x in self.defaultSettings:
            if not x in self.settings or type(self.settings[x]) != type(self.defaultSettings[x]):
                self.settings[x] = self.defaultSettings[x]
                changes += 1
        for x in self.defaultSettings['tags']:
            if not x in self.settings['tags'] or type(self.settings['tags'][x]) != type(
                    self.defaultSettings['tags'][x]):
                self.settings['tags'][x] = self.defaultSettings['tags'][x]
                changes += 1
        if self.settings['downloadLocation'] == "":
            self.settings['downloadLocation'] = path.join(path.expanduser("~"), 'deemix Music')
            changes += 1
        for template in ['tracknameTemplate', 'albumTracknameTemplate', 'playlistTracknameTemplate',
                         'playlistNameTemplate', 'artistNameTemplate', 'albumNameTemplate', 'playlistFilenameTemplate',
                         'coverImageTemplate', 'artistImageTemplate']:
            if self.settings[template] == "":
                self.settings[template] = self.defaultSettings[template]
                changes += 1
        if changes > 0:
            self.saveSettings()

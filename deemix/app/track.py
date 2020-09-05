#!/usr/bin/env python3
import logging

from deemix.api.deezer import APIError
from deemix.utils.misc import removeFeatures, andCommaConcat, uniqueArray

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deemix')

class Track:
    def __init__(self, dz, settings, trackAPI_gw, trackAPI=None, albumAPI_gw=None, albumAPI=None):
        self.parseEssentialData(dz, trackAPI_gw)

        self.title = trackAPI_gw['SNG_TITLE'].strip()
        if trackAPI_gw.get('VERSION') and not trackAPI_gw['VERSION'] in trackAPI_gw['SNG_TITLE']:
            self.title += " " + trackAPI_gw['VERSION'].strip()

        self.position = trackAPI_gw.get('POSITION')

        self.localTrack = int(self.id) < 0
        if self.localTrack:
            self.parseLocalTrackData(trackAPI_gw)
        else:
            self.parseData(dz, settings, trackAPI_gw, trackAPI, albumAPI_gw, albumAPI)

        if not 'Main' in self.artist:
            self.artist['Main'] = [self.mainArtist['name']]

        # Fix incorrect day month when detectable
        if int(self.date['month']) > 12:
            monthTemp = self.date['month']
            self.date['month'] = self.date['day']
            self.date['day'] = monthTemp
        if int(self.album['date']['month']) > 12:
            monthTemp = self.album['date']['month']
            self.album['date']['month'] = self.album['date']['day']
            self.album['date']['day'] = monthTemp

        # Add playlist data if track is in a playlist
        self.playlist = None
        if "_EXTRA_PLAYLIST" in trackAPI_gw:
            self.playlist = {}
            if 'dzcdn.net' in trackAPI_gw["_EXTRA_PLAYLIST"]['picture_small']:
                self.playlist['pic'] = trackAPI_gw["_EXTRA_PLAYLIST"]['picture_small'][:-24]
                self.playlist['picUrl'] = "{}/{}x{}-{}".format(
                    self.playlist['pic'],
                    settings['embeddedArtworkSize'], settings['embeddedArtworkSize'],
                    'none-100-0-0.png' if settings['embeddedArtworkPNG'] else f'000000-{settings["jpegImageQuality"]}-0-0.jpg'
                )
            else:
                self.playlist['pic'] = None
                self.playlist['picUrl'] = trackAPI_gw["_EXTRA_PLAYLIST"]['picture_xl']
            self.playlist['title'] = trackAPI_gw["_EXTRA_PLAYLIST"]['title']
            self.playlist['mainArtist'] = {
                'id': trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['id'],
                'name': trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['name'],
                'pic': trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['picture_small'][
                       trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['picture_small'].find('artist/') + 7:-24]
            }
            if settings['albumVariousArtists']:
                self.playlist['artist'] = {"Main": [trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['name'], ]}
                self.playlist['artists'] = [trackAPI_gw["_EXTRA_PLAYLIST"]['various_artist']['name'], ]
            else:
                self.playlist['artist'] = {"Main": []}
                self.playlist['artists'] = []
            self.playlist['trackTotal'] = trackAPI_gw["_EXTRA_PLAYLIST"]['nb_tracks']
            self.playlist['recordType'] = "Compilation"
            self.playlist['barcode'] = ""
            self.playlist['label'] = ""
            self.playlist['explicit'] = trackAPI_gw['_EXTRA_PLAYLIST']['explicit']
            self.playlist['date'] = {
                'day': trackAPI_gw["_EXTRA_PLAYLIST"]["creation_date"][8:10],
                'month': trackAPI_gw["_EXTRA_PLAYLIST"]["creation_date"][5:7],
                'year': trackAPI_gw["_EXTRA_PLAYLIST"]["creation_date"][0:4]
            }
            self.playlist['discTotal'] = "1"

        self.generateMainFeatStrings()

        # Bits useful for later
        self.searched = False
        self.selectedFormat = 0
        self.dateString = None
        self.album['picUrl'] = None
        self.album['picPath'] = None
        self.album['bitrate'] = 0
        self.album['dateString'] = None

        self.artistsString = ""

    def parseEssentialData(self, dz, trackAPI_gw):
        self.id = trackAPI_gw['SNG_ID']
        self.duration = trackAPI_gw['DURATION']
        self.MD5 = trackAPI_gw['MD5_ORIGIN']
        self.mediaVersion = trackAPI_gw['MEDIA_VERSION']
        self.fallbackId = "0"
        if 'FALLBACK' in trackAPI_gw:
            self.fallbackId = trackAPI_gw['FALLBACK']['SNG_ID']
        self.filesizes = dz.get_track_filesizes(self.id)

    def parseLocalTrackData(self, trackAPI_gw):
        self.album = {
            'id': "0",
            'title': trackAPI_gw['ALB_TITLE'],
        }
        self.album['pic'] = trackAPI_gw.get('ALB_PICTURE')
        self.mainArtist = {
            'id': "0",
            'name': trackAPI_gw['ART_NAME'],
            'pic': ""
        }
        self.artists = [trackAPI_gw['ART_NAME']]
        self.artist = {
            'Main': [trackAPI_gw['ART_NAME']]
        }
        self.date = {
            'day': "00",
            'month': "00",
            'year': "XXXX"
        }
        # All the missing data
        self.ISRC = ""
        self.album['artist'] = self.artist
        self.album['artists'] = self.artists
        self.album['barcode'] = "Unknown"
        self.album['date'] = self.date
        self.album['discTotal'] = "0"
        self.album['explicit'] = False
        self.album['genre'] = []
        self.album['label'] = "Unknown"
        self.album['mainArtist'] = self.mainArtist
        self.album['recordType'] = "Album"
        self.album['trackTotal'] = "0"
        self.bpm = 0
        self.contributors = {}
        self.copyright = ""
        self.discNumber = "0"
        self.explicit = False
        self.lyrics = {}
        self.replayGain = ""
        self.trackNumber = "0"

    def parseData(self, dz, settings, trackAPI_gw, trackAPI, albumAPI_gw, albumAPI):
        self.discNumber = trackAPI_gw.get('DISK_NUMBER')
        self.explicit = bool(int(trackAPI_gw.get('EXPLICIT_LYRICS') or "0"))
        self.copyright = trackAPI_gw.get('COPYRIGHT')
        self.replayGain = ""
        if 'GAIN' in trackAPI_gw:
            self.replayGain = "{0:.2f} dB".format((float(trackAPI_gw['GAIN']) + 18.4) * -1)
        self.ISRC = trackAPI_gw['ISRC']
        self.trackNumber = trackAPI_gw['TRACK_NUMBER']
        self.contributors = trackAPI_gw['SNG_CONTRIBUTORS']

        self.lyrics = {
            'id': trackAPI_gw.get('LYRICS_ID'),
            'unsync': None,
            'sync': None
        }
        if not "LYRICS" in trackAPI_gw and int(self.lyrics['id']) != 0:
            logger.info(f"[{trackAPI_gw['ART_NAME']} - {self.title}] Getting lyrics")
            trackAPI_gw["LYRICS"] = dz.get_lyrics_gw(self.id)
        if int(self.lyrics['id']) != 0:
            self.lyrics['unsync'] = trackAPI_gw["LYRICS"].get("LYRICS_TEXT")
            if "LYRICS_SYNC_JSON" in trackAPI_gw["LYRICS"]:
                self.lyrics['sync'] = ""
                lastTimestamp = ""
                for i in range(len(trackAPI_gw["LYRICS"]["LYRICS_SYNC_JSON"])):
                    if "lrc_timestamp" in trackAPI_gw["LYRICS"]["LYRICS_SYNC_JSON"][i]:
                        self.lyrics['sync'] += trackAPI_gw["LYRICS"]["LYRICS_SYNC_JSON"][i]["lrc_timestamp"]
                        lastTimestamp = trackAPI_gw["LYRICS"]["LYRICS_SYNC_JSON"][i]["lrc_timestamp"]
                    else:
                        self.lyrics['sync'] += lastTimestamp
                    self.lyrics['sync'] += trackAPI_gw["LYRICS"]["LYRICS_SYNC_JSON"][i]["line"] + "\r\n"

        self.mainArtist = {
            'id': trackAPI_gw['ART_ID'],
            'name': trackAPI_gw['ART_NAME'],
            'pic': trackAPI_gw.get('ART_PICTURE')
        }

        self.date = None
        if 'PHYSICAL_RELEASE_DATE' in trackAPI_gw:
            self.date = {
                'day': trackAPI_gw["PHYSICAL_RELEASE_DATE"][8:10],
                'month': trackAPI_gw["PHYSICAL_RELEASE_DATE"][5:7],
                'year': trackAPI_gw["PHYSICAL_RELEASE_DATE"][0:4]
            }

        self.album = {
            'id': trackAPI_gw['ALB_ID'],
            'title': trackAPI_gw['ALB_TITLE'],
            'pic': trackAPI_gw.get('ALB_PICTURE'),
            'barcode': "Unknown",
            'label': "Unknown",
            'explicit': False,
            'date': None,
            'genre': []
        }
        try:
            # Try the public API first (as it has more data)
            if not albumAPI:
                logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting album infos")
                albumAPI = dz.get_album(self.album['id'])
            self.album['title'] = albumAPI['title']
            self.album['mainArtist'] = {
                'id': albumAPI['artist']['id'],
                'name': albumAPI['artist']['name'],
                'pic': albumAPI['artist']['picture_small'][albumAPI['artist']['picture_small'].find('artist/') + 7:-24]
            }

            self.album['artist'] = {}
            self.album['artists'] = []
            for artist in albumAPI['contributors']:
                if artist['id'] != 5080 or artist['id'] == 5080 and settings['albumVariousArtists']:
                    if artist['name'] not in self.album['artists']:
                        self.album['artists'].append(artist['name'])
                    if artist['role'] == "Main" or artist['role'] != "Main" and artist['name'] not in self.album['artist']['Main']:
                        if not artist['role'] in self.album['artist']:
                            self.album['artist'][artist['role']] = []
                        self.album['artist'][artist['role']].append(artist['name'])
            if settings['removeDuplicateArtists']:
                self.album['artists'] = uniqueArray(self.album['artists'])
                for role in self.album['artist'].keys():
                    self.album['artist'][role] = uniqueArray(self.album['artist'][role])

            self.album['trackTotal'] = albumAPI['nb_tracks']
            self.album['recordType'] = albumAPI['record_type']

            self.album['barcode'] = albumAPI.get('upc') or self.album['barcode']
            self.album['label'] = albumAPI.get('label') or self.album['label']
            self.album['explicit'] = bool(albumAPI.get('explicit_lyrics'))
            if 'release_date' in albumAPI:
                self.album['date'] = {
                    'day': albumAPI["release_date"][8:10],
                    'month': albumAPI["release_date"][5:7],
                    'year': albumAPI["release_date"][0:4]
                }
            self.album['discTotal'] = albumAPI.get('nb_disk')
            self.copyright = albumAPI.get('copyright')

            if not self.album['pic']:
                self.album['pic'] = albumAPI['cover_small'][albumAPI['cover_small'].find('cover/') + 6:-24]

            if 'genres' in albumAPI and 'data' in albumAPI['genres'] and len(albumAPI['genres']['data']) > 0:
                for genre in albumAPI['genres']['data']:
                    self.album['genre'].append(genre['name'])
        except APIError:
            if not albumAPI_gw:
                logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting more album infos")
                albumAPI_gw = dz.get_album_gw(self.album['id'])
            self.album['title'] = albumAPI_gw['ALB_TITLE']
            self.album['mainArtist'] = {
                'id': albumAPI_gw['ART_ID'],
                'name': albumAPI_gw['ART_NAME'],
                'pic': None
            }
            logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting artist picture fallback")
            artistAPI = dz.get_artist(self.album['mainArtist']['id'])
            self.album['artists'] = [albumAPI_gw['ART_NAME']]
            self.album['mainArtist']['pic'] = artistAPI['picture_small'][artistAPI['picture_small'].find('artist/') + 7:-24]
            self.album['trackTotal'] = albumAPI_gw['NUMBER_TRACK']
            self.album['discTotal'] = albumAPI_gw['NUMBER_DISK']
            self.album['recordType'] = "Album"
            self.album['label'] = albumAPI_gw.get('LABEL_NAME') or self.album['label']
            if 'EXPLICIT_ALBUM_CONTENT' in albumAPI_gw and 'EXPLICIT_LYRICS_STATUS' in albumAPI_gw['EXPLICIT_ALBUM_CONTENT']:
                self.album['explicit'] = albumAPI_gw['EXPLICIT_ALBUM_CONTENT']['EXPLICIT_LYRICS_STATUS'] in [1,4]
            if not self.album['pic']:
                self.album['pic'] = albumAPI_gw['ALB_PICTURE']
            if 'PHYSICAL_RELEASE_DATE' in albumAPI_gw:
                self.album['date'] = {
                    'day': albumAPI_gw["PHYSICAL_RELEASE_DATE"][8:10],
                    'month': albumAPI_gw["PHYSICAL_RELEASE_DATE"][5:7],
                    'year': albumAPI_gw["PHYSICAL_RELEASE_DATE"][0:4]
                }

        self.album['mainArtist']['save'] = self.album['mainArtist']['id'] != 5080 or self.album['mainArtist']['id'] == 5080 and settings['albumVariousArtists']

        if self.album['date'] and not self.date:
            self.date = self.album['date']

        if not trackAPI:
            logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting extra track infos")
            trackAPI = dz.get_track(self.id)
        self.bpm = trackAPI['bpm']

        if not self.replayGain and 'gain' in trackAPI:
            self.replayGain = "{0:.2f} dB".format((float(trackAPI['gain']) + 18.4) * -1)
        if not self.explicit:
            self.explicit = trackAPI['explicit_lyrics']
        if not self.discNumber:
            self.discNumber = trackAPI['disk_number']

        self.artist = {}
        self.artists = []
        for artist in trackAPI['contributors']:
            if artist['id'] != 5080 or artist['id'] == 5080 and len(trackAPI['contributors']) == 1:
                if artist['name'] not in self.artists:
                    self.artists.append(artist['name'])
                if artist['role'] != "Main" and artist['name'] not in self.artist['Main'] or artist['role'] == "Main":
                    if not artist['role'] in self.artist:
                        self.artist[artist['role']] = []
                    self.artist[artist['role']].append(artist['name'])
        if settings['removeDuplicateArtists']:
            self.artists = uniqueArray(self.artists)
            for role in self.artist.keys():
                self.artist[role] = uniqueArray(self.artist[role])

        if not self.album['discTotal']:
            if not albumAPI_gw:
                logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting more album infos")
                albumAPI_gw = dz.get_album_gw(self.album['id'])
            self.album['discTotal'] = albumAPI_gw['NUMBER_DISK']
        if not self.copyright:
            if not albumAPI_gw:
                logger.info(f"[{self.mainArtist['name']} - {self.title}] Getting more album infos")
                albumAPI_gw = dz.get_album_gw(self.album['id'])
            self.copyright = albumAPI_gw['COPYRIGHT']

    # Removes featuring from the title
    def getCleanTitle(self):
        return removeFeatures(self.title)

    # Removes featuring from the album name
    def getCleanAlbumTitle(self):
        return removeFeatures(self.album['title'])

    def getFeatTitle(self):
        if self.featArtistsString and not "(feat." in self.title.lower():
            return self.title + " ({})".format(self.featArtistsString)
        return self.title

    def generateMainFeatStrings(self):
        self.mainArtistsString = andCommaConcat(self.artist['Main'])
        self.featArtistsString = None
        if 'Featured' in self.artist:
            self.featArtistsString = "feat. "+andCommaConcat(self.artist['Featured'])

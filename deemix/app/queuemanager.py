#!/usr/bin/env python3
from deemix.app.downloadjob import DownloadJob
from deemix.utils.misc import getIDFromLink, getTypeFromLink, getBitrateInt
from deemix.api.deezer import APIError
from spotipy.exceptions import SpotifyException
from deemix.app.queueitem import QISingle, QICollection, QIConvertable
import logging
import os.path as path
import json
from os import remove
from time import sleep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deemix')

class QueueManager:
    def __init__(self):
        self.queue = []
        self.queueList = {}
        self.queueComplete = []
        self.currentItem = ""

    def generateQueueItem(self, dz, sp, url, settings, bitrate=None, albumAPI=None, interface=None):
        forcedBitrate = getBitrateInt(bitrate)
        bitrate = forcedBitrate if forcedBitrate else settings['maxBitrate']
        type = getTypeFromLink(url)
        id = getIDFromLink(url, type)


        if type == None or id == None:
            logger.warn("URL not recognized")
            return QueueError(url, "URL not recognized", "invalidURL")

        elif type == "track":
            if id.startswith("isrc"):
                try:
                    trackAPI = dz.get_track(id)
                    if 'id' in trackAPI and 'title' in trackAPI:
                        id = trackAPI['id']
                    else:
                        return QueueError(url, "Track ISRC is not available on deezer", "ISRCnotOnDeezer")
                except APIError as e:
                    e = json.loads(str(e))
                    return QueueError(url, f"Wrong URL: {e['type']+': ' if 'type' in e else ''}{e['message'] if 'message' in e else ''}")
            try:
                trackAPI = dz.get_track_gw(id)
            except APIError as e:
                e = json.loads(str(e))
                message = "Wrong URL"
                if "DATA_ERROR" in e:
                    message += f": {e['DATA_ERROR']}"
                return QueueError(url, message)
            if albumAPI:
                trackAPI['_EXTRA_ALBUM'] = albumAPI
            if settings['createSingleFolder']:
                trackAPI['FILENAME_TEMPLATE'] = settings['albumTracknameTemplate']
            else:
                trackAPI['FILENAME_TEMPLATE'] = settings['tracknameTemplate']
            trackAPI['SINGLE_TRACK'] = True

            title = trackAPI['SNG_TITLE']
            if 'VERSION' in trackAPI and trackAPI['VERSION']:
                title += " " + trackAPI['VERSION']
            return QISingle(
                id,
                bitrate,
                title,
                trackAPI['ART_NAME'],
                f"https://e-cdns-images.dzcdn.net/images/cover/{trackAPI['ALB_PICTURE']}/75x75-000000-80-0-0.jpg",
                'track',
                settings,
                trackAPI,
            )

        elif type == "album":
            try:
                albumAPI = dz.get_album(id)
            except APIError as e:
                e = json.loads(str(e))
                return QueueError(url, f"Wrong URL: {e['type']+': ' if 'type' in e else ''}{e['message'] if 'message' in e else ''}")
            if id.startswith('upc'):
                id = albumAPI['id']
            albumAPI_gw = dz.get_album_gw(id)
            albumAPI['nb_disk'] = albumAPI_gw['NUMBER_DISK']
            albumAPI['copyright'] = albumAPI_gw['COPYRIGHT']
            if albumAPI['nb_tracks'] == 1:
                return self.generateQueueItem(dz, sp, f"https://www.deezer.com/track/{albumAPI['tracks']['data'][0]['id']}",
                                         settings, bitrate, albumAPI)
            tracksArray = dz.get_album_tracks_gw(id)
            if albumAPI['nb_tracks'] == 255:
                albumAPI['nb_tracks'] = len(tracksArray)


            if albumAPI['cover_small'] != None:
                cover = albumAPI['cover_small'][:-24] + '/75x75-000000-80-0-0.jpg'
            else:
                cover = f"https://e-cdns-images.dzcdn.net/images/cover/{albumAPI_gw['ALB_PICTURE']}/75x75-000000-80-0-0.jpg"
            totalSize = len(tracksArray)
            collection = []
            for pos, trackAPI in enumerate(tracksArray, start=1):
                trackAPI['_EXTRA_ALBUM'] = albumAPI
                trackAPI['POSITION'] = pos
                trackAPI['SIZE'] = totalSize
                trackAPI['FILENAME_TEMPLATE'] = settings['albumTracknameTemplate']
                collection.append(trackAPI)

            return QICollection(
                id,
                bitrate,
                albumAPI['title'],
                albumAPI['artist']['name'],
                cover,
                totalSize,
                'album',
                settings,
                collection,
            )


        elif type == "playlist":
            try:
                playlistAPI = dz.get_playlist(id)
            except:
                try:
                    playlistAPI = dz.get_playlist_gw(id)
                except APIError as e:
                    e = json.loads(str(e))
                    message = "Wrong URL"
                    if "DATA_ERROR" in e:
                        message += f": {e['DATA_ERROR']}"
                    return QueueError(url, message)
            if not playlistAPI['public'] and playlistAPI['creator']['id'] != str(dz.user['id']):
                logger.warn("You can't download others private playlists.")
                return QueueError(url, "You can't download others private playlists.", "notYourPrivatePlaylist")

            playlistTracksAPI = dz.get_playlist_tracks_gw(id)
            playlistAPI['various_artist'] = dz.get_artist(5080)

            totalSize = len(playlistTracksAPI)
            collection = []
            for pos, trackAPI in enumerate(playlistTracksAPI, start=1):
                if 'EXPLICIT_TRACK_CONTENT' in trackAPI and trackAPI['EXPLICIT_TRACK_CONTENT'].get('EXPLICIT_LYRICS_STATUS') in [1,4]:
                    playlistAPI['explicit'] = True
                trackAPI['_EXTRA_PLAYLIST'] = playlistAPI
                trackAPI['POSITION'] = pos
                trackAPI['SIZE'] = totalSize
                trackAPI['FILENAME_TEMPLATE'] = settings['playlistTracknameTemplate']
                collection.append(trackAPI)
            if not 'explicit' in playlistAPI:
                playlistAPI['explicit'] = False

            return QICollection(
                id,
                bitrate,
                playlistAPI['title'],
                playlistAPI['creator']['name'],
                playlistAPI['picture_small'][:-24] + '/75x75-000000-80-0-0.jpg',
                totalSize,
                'playlist',
                settings,
                collection,
            )

        elif type == "artist":
            try:
                artistAPI = dz.get_artist(id)
            except APIError as e:
                e = json.loads(str(e))
                return QueueError(url, f"Wrong URL: {e['type']+': ' if 'type' in e else ''}{e['message'] if 'message' in e else ''}")

            if interface:
                interface.send("startAddingArtist", {'name': artistAPI['name'], 'id': artistAPI['id']})

            artistAPITracks = dz.get_artist_albums(id)
            albumList = []
            for album in artistAPITracks['data']:
                albumList.append(self.generateQueueItem(dz, sp, album['link'], settings, bitrate))

            if interface:
                interface.send("finishAddingArtist", {'name': artistAPI['name'], 'id': artistAPI['id']})

            return albumList

        elif type == "artistdiscography":
            try:
                artistAPI = dz.get_artist(id)
            except APIError as e:
                e = json.loads(str(e))
                return QueueError(url, f"Wrong URL: {e['type']+': ' if 'type' in e else ''}{e['message'] if 'message' in e else ''}")

            if interface:
                interface.send("startAddingArtist", {'name': artistAPI['name'], 'id': artistAPI['id']})

            artistDiscographyAPI = dz.get_artist_discography_gw(id, 100)
            albumList = []
            for type in artistDiscographyAPI:
                if type != 'all':
                    for album in artistDiscographyAPI[type]:
                        albumList.append(self.generateQueueItem(dz, sp, album['link'], settings, bitrate))

            if interface:
                interface.send("finishAddingArtist", {'name': artistAPI['name'], 'id': artistAPI['id']})

            return albumList

        elif type == "artisttop":
            try:
                artistAPI = dz.get_artist(id)
            except APIError as e:
                e = json.loads(str(e))
                return QueueError(url, f"Wrong URL: {e['type']+': ' if 'type' in e else ''}{e['message'] if 'message' in e else ''}")

            playlistAPI = {
                'id': str(artistAPI['id'])+"_top_track",
                'title': artistAPI['name']+" - Top Tracks",
                'description': "Top Tracks for "+artistAPI['name'],
                'duration': 0,
                'public': True,
                'is_loved_track': False,
                'collaborative': False,
                'nb_tracks': 0,
                'fans': artistAPI['nb_fan'],
                'link': "https://www.deezer.com/artist/"+str(artistAPI['id'])+"/top_track",
                'share': None,
                'picture': artistAPI['picture'],
                'picture_small': artistAPI['picture_small'],
                'picture_medium': artistAPI['picture_medium'],
                'picture_big': artistAPI['picture_big'],
                'picture_xl': artistAPI['picture_xl'],
                'checksum': None,
                'tracklist': "https://api.deezer.com/artist/"+str(artistAPI['id'])+"/top",
                'creation_date': "XXXX-00-00",
                'creator': {
                    'id': "art_"+str(artistAPI['id']),
                    'name': artistAPI['name'],
                    'type': "user"
                },
                'type': "playlist"
            }

            artistTopTracksAPI_gw = dz.get_artist_toptracks_gw(id)
            playlistAPI['various_artist'] = dz.get_artist(5080)
            playlistAPI['nb_tracks'] = len(artistTopTracksAPI_gw)

            totalSize = len(artistTopTracksAPI_gw)
            collection = []
            for pos, trackAPI in enumerate(artistTopTracksAPI_gw, start=1):
                if 'EXPLICIT_TRACK_CONTENT' in trackAPI and trackAPI['EXPLICIT_TRACK_CONTENT'].get('EXPLICIT_LYRICS_STATUS') in [1,4]:
                    playlistAPI['explicit'] = True
                trackAPI['_EXTRA_PLAYLIST'] = playlistAPI
                trackAPI['POSITION'] = pos
                trackAPI['SIZE'] = totalSize
                trackAPI['FILENAME_TEMPLATE'] = settings['playlistTracknameTemplate']
                collection.append(trackAPI)
            if not 'explicit' in playlistAPI:
                playlistAPI['explicit'] = False

            return QICollection(
                id,
                bitrate,
                playlistAPI['title'],
                playlistAPI['creator']['name'],
                playlistAPI['picture_small'][:-24] + '/75x75-000000-80-0-0.jpg',
                totalSize,
                'playlist',
                settings,
                collection,
            )

        elif type == "spotifytrack":
            if not sp.spotifyEnabled:
                logger.warn("Spotify Features is not setted up correctly.")
                return QueueError(url, "Spotify Features is not setted up correctly.", "spotifyDisabled")

            try:
                track_id = sp.get_trackid_spotify(dz, id, settings['fallbackSearch'])
            except SpotifyException as e:
                return QueueError(url, "Wrong URL: "+e.msg[e.msg.find('\n')+2:])

            if track_id != "0":
                return self.generateQueueItem(dz, sp, f'https://www.deezer.com/track/{track_id}', settings, bitrate)
            else:
                logger.warn("Track not found on deezer!")
                return QueueError(url, "Track not found on deezer!", "trackNotOnDeezer")

        elif type == "spotifyalbum":
            if not sp.spotifyEnabled:
                logger.warn("Spotify Features is not setted up correctly.")
                return QueueError(url, "Spotify Features is not setted up correctly.", "spotifyDisabled")

            try:
                album_id = sp.get_albumid_spotify(dz, id)
            except SpotifyException as e:
                return QueueError(url, "Wrong URL: "+e.msg[e.msg.find('\n')+2:])

            if album_id != "0":
                return self.generateQueueItem(dz, sp, f'https://www.deezer.com/album/{album_id}', settings, bitrate)
            else:
                logger.warn("Album not found on deezer!")
                return QueueError(url, "Album not found on deezer!", "albumNotOnDeezer")

        elif type == "spotifyplaylist":
            if not sp.spotifyEnabled:
                logger.warn("Spotify Features is not setted up correctly.")
                return QueueError(url, "Spotify Features is not setted up correctly.", "spotifyDisabled")

            try:
                return sp.generate_playlist_queueitem(dz, id, bitrate, settings)
            except SpotifyException as e:
                return QueueError(url, "Wrong URL: "+e.msg[e.msg.find('\n')+2:])

        else:
            logger.warn("URL not supported yet")
            return QueueError(url, "URL not supported yet", "unsupportedURL")

    def addToQueue(self, dz, sp, url, settings, bitrate=None, interface=None):
        if not dz.logged_in:
            if interface:
                interface.send("loginNeededToDownload")
            return False

        def parseLink(link):
            link = link.strip()
            if link == "":
                return False
            logger.info("Generating queue item for: "+link)
            return self.generateQueueItem(dz, sp, link, settings, bitrate, interface=interface)

        if type(url) is list:
            queueItem = []
            for link in url:
                item = parseLink(link)
                if not item:
                    continue
                elif type(item) is list:
                    queueItem += item
                else:
                    queueItem.append(item)
            if not len(queueItem):
                return False
        else:
            queueItem = parseLink(url)
            if not queueItem:
                return False

        if type(queueItem) is list:
            ogLen = len(self.queue)
            slimmedItems = []
            for x in queueItem:
                if isinstance(x, QueueError):
                    logger.error(f"[{x.link}] {x.message}")
                    continue
                if x.uuid in list(self.queueList.keys()):
                    logger.warn(f"[{x.uuid}] Already in queue, will not be added again.")
                    continue
                self.queue.append(x.uuid)
                self.queueList[x.uuid] = x
                logger.info(f"[{x.uuid}] Added to queue.")
                slimmedItems.append(x.getSlimmedItem())
            if len(self.queue) <= ogLen:
                return False
            if interface:
                interface.send("addedToQueue", slimmedItems)
        else:
            if isinstance(queueItem, QueueError):
                logger.error(f"[{queueItem.link}] {queueItem.message}")
                if interface:
                    interface.send("queueError", queueItem.toDict())
                return False
            if queueItem.uuid in list(self.queueList.keys()):
                logger.warn(f"[{queueItem.uuid}] Already in queue, will not be added again.")
                if interface:
                    interface.send("alreadyInQueue", {'uuid': queueItem.uuid, 'title': queueItem.title})
                return False
            if interface:
                interface.send("addedToQueue", queueItem.getSlimmedItem())
            logger.info(f"[{queueItem.uuid}] Added to queue.")
            self.queue.append(queueItem.uuid)
            self.queueList[queueItem.uuid] = queueItem

        self.nextItem(dz, sp, interface)
        return True

    def nextItem(self, dz, sp, interface=None):
        if self.currentItem != "":
            return None
        else:
            if len(self.queue) > 0:
                self.currentItem = self.queue.pop(0)
            else:
                return None
            if interface:
                interface.send("startDownload", self.currentItem)
            logger.info(f"[{self.currentItem}] Started downloading.")
            DownloadJob(dz, sp, self.queueList[self.currentItem], interface).start()
            self.afterDownload(dz, sp, interface)

    def afterDownload(self, dz, sp, interface):
        if self.queueList[self.currentItem].cancel:
            del self.queueList[self.currentItem]
        else:
            self.queueComplete.append(self.currentItem)
        logger.info(f"[{self.currentItem}] Finished downloading.")
        self.currentItem = ""
        self.nextItem(dz, sp, interface)


    def getQueue(self):
        return (self.queue, self.queueComplete, self.slimQueueList(), self.currentItem)

    def saveQueue(self, configFolder):
        if len(self.queueList) > 0:
            if self.currentItem != "":
                self.queue.insert(0, self.currentItem)
            with open(path.join(configFolder, 'queue.json'), 'w') as f:
                json.dump({
                    'queue': self.queue,
                    'queueComplete': self.queueComplete,
                    'queueList': self.exportQueueList()
                }, f)

    def exportQueueList(self):
        queueList = {}
        for uuid in self.queueList:
            if uuid in self.queue:
                queueList[uuid] = self.queueList[uuid].getResettedItem()
            else:
                queueList[uuid] = self.queueList[uuid].toDict()
        return queueList

    def slimQueueList(self):
        queueList = {}
        for uuid in self.queueList:
            queueList[uuid] = self.queueList[uuid].getSlimmedItem()
        return queueList

    def loadQueue(self, configFolder, settings, interface=None):
        if path.isfile(path.join(configFolder, 'queue.json')) and not len(self.queue):
            if interface:
                interface.send('restoringQueue')
            with open(path.join(configFolder, 'queue.json'), 'r') as f:
                qd = json.load(f)
            remove(path.join(configFolder, 'queue.json'))
            self.restoreQueue(qd['queue'], qd['queueComplete'], qd['queueList'], settings)
            if interface:
                interface.send('init_downloadQueue', {
                    'queue': self.queue,
                    'queueComplete': self.queueComplete,
                    'queueList': self.slimQueueList(),
                    'restored': True
                })

    def restoreQueue(self, queue, queueComplete, queueList, settings):
        self.queue = queue
        self.queueComplete = queueComplete
        self.queueList = {}
        for uuid in queueList:
            if 'single' in queueList[uuid]:
                self.queueList[uuid] = QISingle(queueItemDict = queueList[uuid])
            if 'collection' in queueList[uuid]:
                self.queueList[uuid] = QICollection(queueItemDict = queueList[uuid])
            if '_EXTRA' in queueList[uuid]:
                self.queueList[uuid] = QIConvertable(queueItemDict = queueList[uuid])
            self.queueList[uuid].settings = settings

    def removeFromQueue(self, uuid, interface=None):
        if uuid == self.currentItem:
            if interface:
                interface.send("cancellingCurrentItem", uuid)
            self.queueList[uuid].cancel = True
        elif uuid in self.queue:
            self.queue.remove(uuid)
            del self.queueList[uuid]
            if interface:
                interface.send("removedFromQueue", uuid)
        elif uuid in self.queueComplete:
            self.queueComplete.remove(uuid)
            del self.queueList[uuid]
            if interface:
                interface.send("removedFromQueue", uuid)


    def cancelAllDownloads(self, interface=None):
        self.queue = []
        self.queueComplete = []
        if self.currentItem != "":
            if interface:
                interface.send("cancellingCurrentItem", self.currentItem)
            self.queueList[self.currentItem].cancel = True
        for uuid in list(self.queueList.keys()):
            if uuid != self.currentItem:
                del self.queueList[uuid]
        if interface:
            interface.send("removedAllDownloads", self.currentItem)


    def removeFinishedDownloads(self, interface=None):
        for uuid in self.queueComplete:
            del self.queueList[uuid]
        self.queueComplete = []
        if interface:
            interface.send("removedFinishedDownloads")

class QueueError:
    def __init__(self, link, message, errid=None):
        self.link = link
        self.message = message
        self.errid = errid

    def toDict(self):
        return {
            'link': self.link,
            'error': self.message,
            'errid': self.errid
        }

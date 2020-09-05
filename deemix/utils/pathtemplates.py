#!/usr/bin/env python3
import re
from os.path import sep as pathSep
from unicodedata import normalize

bitrateLabels = {
    15: "360 HQ",
    14: "360 MQ",
    13: "360 LQ",
    9: "FLAC",
    3: "320",
    1: "128",
    8: "128",
    0: "MP3"
}


def fixName(txt, char='_'):
    txt = str(txt)
    txt = re.sub(r'[\0\/\\:*?"<>|]', char, txt)
    txt = normalize("NFC", txt)
    return txt

def fixEndOfData(bString):
    try:
        bString.decode()
        return True
    except:
        return False

def fixLongName(name):
    if pathSep in name:
        name2 = name.split(pathSep)
        name = ""
        for txt in name2:
            txt = txt.encode('utf-8')[:200]
            while not fixEndOfData(txt):
                txt = txt[:-1]
            txt = txt.decode()
            name += txt + pathSep
        name = name[:-1]
    else:
        name = name.encode('utf-8')[:200]
        while not fixEndOfData(name):
            name = name[:-1]
        name = name.decode()
    return name


def antiDot(string):
    while string[-1:] == "." or string[-1:] == " " or string[-1:] == "\n":
        string = string[:-1]
    if len(string) < 1:
        string = "dot"
    return string


def pad(num, max, dopad=True):
    paddingsize = len(str(max))
    if paddingsize == 1:
        paddingsize = 2
    if dopad:
        return str(num).zfill(paddingsize)
    else:
        return str(num)


def generateFilename(track, trackAPI, settings):
    if trackAPI['FILENAME_TEMPLATE'] == "":
        filename = "%artist% - %title%"
    else:
        filename = trackAPI['FILENAME_TEMPLATE']
    return settingsRegex(filename, track, settings,
                         trackAPI['_EXTRA_PLAYLIST'] if '_EXTRA_PLAYLIST' in trackAPI else None)


def generateFilepath(track, trackAPI, settings):
    filepath = settings['downloadLocation']
    if filepath[-1:] != pathSep:
        filepath += pathSep
    artistPath = None
    coverPath = None
    extrasPath = None

    if settings['createPlaylistFolder'] and '_EXTRA_PLAYLIST' in trackAPI and not settings['tags'][
        'savePlaylistAsCompilation']:
        filepath += antiDot(
            settingsRegexPlaylist(settings['playlistNameTemplate'], trackAPI['_EXTRA_PLAYLIST'], settings)) + pathSep

    if '_EXTRA_PLAYLIST' in trackAPI and not settings['tags']['savePlaylistAsCompilation']:
        extrasPath = filepath

    if (
            settings['createArtistFolder'] and not '_EXTRA_PLAYLIST' in trackAPI or
            (settings['createArtistFolder'] and '_EXTRA_PLAYLIST' in trackAPI and settings['tags'][
                'savePlaylistAsCompilation']) or
            (settings['createArtistFolder'] and '_EXTRA_PLAYLIST' in trackAPI and settings['createStructurePlaylist'])
    ):
        if (int(track.id) < 0 and not 'mainArtist' in track.album):
            track.album['mainArtist'] = track.mainArtist
        filepath += antiDot(
            settingsRegexArtist(settings['artistNameTemplate'], track.album['mainArtist'], settings)) + pathSep
        artistPath = filepath

    if (settings['createAlbumFolder'] and
            (not 'SINGLE_TRACK' in trackAPI or ('SINGLE_TRACK' in trackAPI and settings['createSingleFolder'])) and
            (not '_EXTRA_PLAYLIST' in trackAPI or (
                    '_EXTRA_PLAYLIST' in trackAPI and settings['tags']['savePlaylistAsCompilation']) or (
                     '_EXTRA_PLAYLIST' in trackAPI and settings['createStructurePlaylist']))
    ):
        filepath += antiDot(
            settingsRegexAlbum(settings['albumNameTemplate'], track.album, settings,
                trackAPI['_EXTRA_PLAYLIST'] if'_EXTRA_PLAYLIST' in trackAPI else None)) + pathSep
        coverPath = filepath

    if not ('_EXTRA_PLAYLIST' in trackAPI and not settings['tags']['savePlaylistAsCompilation']):
        extrasPath = filepath

    if (
            int(track.album['discTotal']) > 1 and (
            (settings['createAlbumFolder'] and settings['createCDFolder']) and
            (not 'SINGLE_TRACK' in trackAPI or ('SINGLE_TRACK' in trackAPI and settings['createSingleFolder'])) and
            (not '_EXTRA_PLAYLIST' in trackAPI or (
                    '_EXTRA_PLAYLIST' in trackAPI and settings['tags']['savePlaylistAsCompilation']) or (
                     '_EXTRA_PLAYLIST' in trackAPI and settings['createStructurePlaylist']))
    )):
        filepath += 'CD' + str(track.discNumber) + pathSep

    return (filepath, artistPath, coverPath, extrasPath)


def settingsRegex(filename, track, settings, playlist=None):
    filename = filename.replace("%title%", fixName(track.title, settings['illegalCharacterReplacer']))
    filename = filename.replace("%artist%", fixName(track.mainArtist['name'], settings['illegalCharacterReplacer']))
    filename = filename.replace("%artists%", fixName(", ".join(track.artists), settings['illegalCharacterReplacer']))
    filename = filename.replace("%allartists%", fixName(track.artistsString, settings['illegalCharacterReplacer']))
    filename = filename.replace("%mainartists%", fixName(track.mainArtistsString, settings['illegalCharacterReplacer']))
    filename = filename.replace("%featartists%", fixName('('+track.featArtistsString+')', settings['illegalCharacterReplacer']) if track.featArtistsString else "")
    filename = filename.replace("%album%", fixName(track.album['title'], settings['illegalCharacterReplacer']))
    filename = filename.replace("%albumartist%",
                                fixName(track.album['mainArtist']['name'], settings['illegalCharacterReplacer']))
    filename = filename.replace("%tracknumber%", pad(track.trackNumber, track.album['trackTotal'] if int(
        settings['paddingSize']) == 0 else 10 ** (int(settings['paddingSize']) - 1), settings['padTracks']))
    filename = filename.replace("%tracktotal%", str(track.album['trackTotal']))
    filename = filename.replace("%discnumber%", str(track.discNumber))
    filename = filename.replace("%disctotal%", str(track.album['discTotal']))
    if len(track.album['genre']) > 0:
        filename = filename.replace("%genre%",
                                    fixName(track.album['genre'][0], settings['illegalCharacterReplacer']))
    else:
        filename = filename.replace("%genre%", "Unknown")
    filename = filename.replace("%year%", str(track.date['year']))
    filename = filename.replace("%date%", track.dateString)
    filename = filename.replace("%bpm%", str(track.bpm))
    filename = filename.replace("%label%", fixName(track.album['label'], settings['illegalCharacterReplacer']))
    filename = filename.replace("%isrc%", track.ISRC)
    filename = filename.replace("%upc%", track.album['barcode'])
    filename = filename.replace("%explicit%", "(Explicit)" if track.explicit else "")

    filename = filename.replace("%track_id%", str(track.id))
    filename = filename.replace("%album_id%", str(track.album['id']))
    filename = filename.replace("%artist_id%", str(track.mainArtist['id']))
    if playlist:
        filename = filename.replace("%playlist_id%", str(playlist['id']))
        filename = filename.replace("%position%", pad(track.position, playlist['nb_tracks'] if int(
            settings['paddingSize']) == 0 else 10 ** (int(settings['paddingSize']) - 1), settings['padTracks']))
    else:
        filename = filename.replace("%position%", pad(track.trackNumber, track.album['trackTotal'] if int(
            settings['paddingSize']) == 0 else 10 ** (int(settings['paddingSize']) - 1), settings['padTracks']))
    filename = filename.replace('\\', pathSep).replace('/', pathSep)
    return antiDot(fixLongName(filename))


def settingsRegexAlbum(foldername, album, settings, playlist=None):
    if playlist and settings['tags']['savePlaylistAsCompilation']:
        foldername = foldername.replace("%album_id%", "pl_" + str(playlist['id']))
        foldername = foldername.replace("%genre%", "Compilation")
    else:
        foldername = foldername.replace("%album_id%", str(album['id']))
        if len(album['genre']) > 0:
            foldername = foldername.replace("%genre%", fixName(album['genre'][0], settings['illegalCharacterReplacer']))
        else:
            foldername = foldername.replace("%genre%", "Unknown")
    foldername = foldername.replace("%album%", fixName(album['title'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%artist%",
                                    fixName(album['mainArtist']['name'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%artist_id%", str(album['mainArtist']['id']))
    foldername = foldername.replace("%tracktotal%", str(album['trackTotal']))
    foldername = foldername.replace("%disctotal%", str(album['discTotal']))
    foldername = foldername.replace("%type%", fixName(album['recordType'][0].upper() + album['recordType'][1:].lower(),
                                                      settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%upc%", album['barcode'])
    foldername = foldername.replace("%explicit%", "(Explicit)" if album['explicit'] else "")
    foldername = foldername.replace("%label%", fixName(album['label'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%year%", str(album['date']['year']))
    foldername = foldername.replace("%date%", album['dateString'])
    foldername = foldername.replace("%bitrate%", bitrateLabels[int(album['bitrate'])])

    foldername = foldername.replace('\\', pathSep).replace('/', pathSep)
    return antiDot(fixLongName(foldername))


def settingsRegexArtist(foldername, artist, settings):
    foldername = foldername.replace("%artist%", fixName(artist['name'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%artist_id%", str(artist['id']))
    foldername = foldername.replace('\\', pathSep).replace('/', pathSep)
    return antiDot(fixLongName(foldername))


def settingsRegexPlaylist(foldername, playlist, settings):
    foldername = foldername.replace("%playlist%", fixName(playlist['title'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%playlist_id%", fixName(playlist['id'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%owner%",
                                    fixName(playlist['creator']['name'], settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%owner_id%", str(playlist['creator']['id']))
    foldername = foldername.replace("%year%", str(playlist['creation_date'][:4]))
    foldername = foldername.replace("%date%", str(playlist['creation_date'][:10]))
    foldername = foldername.replace("%explicit%", "(Explicit)" if playlist['explicit'] else "")
    foldername = foldername.replace('\\', pathSep).replace('/', pathSep)
    return antiDot(fixLongName(foldername))

def settingsRegexPlaylistFile(foldername, queueItem, settings):
    foldername = foldername.replace("%title%", fixName(queueItem.title, settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%artist%", fixName(queueItem.artist, settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%size%", str(queueItem.size))
    foldername = foldername.replace("%type%", fixName(queueItem.type, settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%id%", fixName(queueItem.id, settings['illegalCharacterReplacer']))
    foldername = foldername.replace("%bitrate%", bitrateLabels[int(queueItem.bitrate)])
    foldername = foldername.replace('\\', pathSep).replace('/', pathSep).replace(pathSep, settings['illegalCharacterReplacer'])
    return antiDot(fixLongName(foldername))

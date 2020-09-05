#!/usr/bin/env python3
import re
import string


def getBitrateInt(txt):
    txt = str(txt).lower()
    if txt in ['flac', 'lossless', '9']:
        return 9
    elif txt in ['mp3', '320', '3']:
        return 3
    elif txt in ['128', '1']:
        return 1
    elif txt in ['360', '360_hq', '15']:
        return 15
    elif txt in ['360_mq', '14']:
        return 14
    elif txt in ['360_lq', '13']:
        return 13
    else:
        return None


def changeCase(str, type):
    if type == "lower":
        return str.lower()
    elif type == "upper":
        return str.upper()
    elif type == "start":
        return string.capwords(str)
    elif type == "sentence":
        return str.capitalize()
    else:
        return str


def removeFeatures(title):
    clean = title
    if "(feat." in clean.lower():
        pos = clean.lower().find("(feat.")
        tempTrack = clean[:pos]
        if ")" in clean:
            tempTrack += clean[clean.find(")", pos + 1) + 1:]
        clean = tempTrack.strip()
    return clean


def andCommaConcat(lst):
    tot = len(lst)
    result = ""
    for i, art in enumerate(lst):
        result += art
        if tot != i + 1:
            if tot - 1 == i + 1:
                result += " & "
            else:
                result += ", "
    return result


def getIDFromLink(link, type):
    if '?' in link:
        link = link[:link.find('?')]
    if link.endswith("/"):
        link = link[:-1]

    if link.startswith("http") and 'open.spotify.com/' in link:
        if type == "spotifyplaylist":
            return link[link.find("/playlist/") + 10:]
        if type == "spotifytrack":
            return link[link.find("/track/") + 7:]
        if type == "spotifyalbum":
            return link[link.find("/album/") + 7:]
    elif link.startswith("spotify:"):
        if type == "spotifyplaylist":
            return link[link.find("playlist:") + 9:]
        if type == "spotifytrack":
            return link[link.find("track:") + 6:]
        if type == "spotifyalbum":
            return link[link.find("album:") + 6:]
    elif type == "artisttop":
        return re.search(r"\/artist\/(\d+)\/top_track", link)[1]
    elif type == "artistdiscography":
        return re.search(r"\/artist\/(\d+)\/discography", link)[1]
    else:
        return link[link.rfind("/") + 1:]


def getTypeFromLink(link):
    type = ''
    if 'spotify' in link:
        type = 'spotify'
        if 'playlist' in link:
            type += 'playlist'
        elif 'track' in link:
            type += 'track'
        elif 'album' in link:
            type += 'album'
    elif 'deezer' in link:
        if '/track' in link:
            type = 'track'
        elif '/playlist' in link:
            type = 'playlist'
        elif '/album' in link:
            type = 'album'
        elif re.search("\/artist\/(\d+)\/top_track", link):
            type = 'artisttop'
        elif re.search("\/artist\/(\d+)\/discography", link):
            type = 'artistdiscography'
        elif '/artist' in link:
            type = 'artist'
    return type


def uniqueArray(arr):
    for iPrinc, namePrinc  in enumerate(arr):
        for iRest, nRest in enumerate(arr):
            if iPrinc!=iRest and namePrinc.lower() in nRest.lower():
                del arr[iRest]
    return arr

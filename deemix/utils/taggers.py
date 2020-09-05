#!/usr/bin/env python3
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, ID3NoHeaderError, TXXX, TIT2, TPE1, TALB, TPE2, TRCK, TPOS, TCON, TYER, TDAT, TLEN, TBPM, \
    TPUB, TSRC, USLT, APIC, IPLS, TCOM, TCOP, TCMP

# Adds tags to a MP3 file
def tagID3(stream, track, save):
    # Delete exsisting tags
    try:
        tag = ID3(stream)
        tag.delete()
    except ID3NoHeaderError:
        tag = ID3()

    if save['title']:
        tag.add(TIT2(text=track.title))

    if save['artist'] and len(track.artists):
        if save['multiArtistSeparator'] != "default":
            if save['multiArtistSeparator'] == "nothing":
                tag.add(TPE1(text=track.mainArtist['name']))
            else:
                tag.add(TPE1(text=track.artistsString))
            tag.add(TXXX(desc="ARTISTS", text=track.artists))
        else:
            tag.add(TPE1(text=track.artists))

    if save['album']:
        tag.add(TALB(text=track.album['title']))

    if save['albumArtist'] and len(track.album['artists']):
        if save['singleAlbumArtist'] and track.album['mainArtist']['save']:
            tag.add(TPE2(text=track.album['mainArtist']['name']))
        else:
            tag.add(TPE2(text=track.album['artists']))

    if save['trackNumber']:
        tag.add(TRCK(
            text=str(track.trackNumber) + ("/" + str(track.album['trackTotal']) if save['trackTotal'] else "")))
    if save['discNumber']:
        tag.add(
            TPOS(text=str(track.discNumber) + ("/" + str(track.album['discTotal']) if save['discTotal'] else "")))
    if save['genre']:
        tag.add(TCON(text=track.album['genre']))
    if save['year']:
        tag.add(TYER(text=str(track.date['year'])))
    if save['date']:
        tag.add(TDAT(text=str(track.date['month']) + str(track.date['day'])))
    if save['length']:
        tag.add(TLEN(text=str(int(track.duration)*1000)))
    if save['bpm']:
        tag.add(TBPM(text=str(track.bpm)))
    if save['label']:
        tag.add(TPUB(text=track.album['label']))
    if save['isrc']:
        tag.add(TSRC(text=track.ISRC))
    if save['barcode']:
        tag.add(TXXX(desc="BARCODE", text=track.album['barcode']))
    if save['explicit']:
        tag.add(TXXX(desc="ITUNESADVISORY", text="1" if track.explicit else "0"))
    if save['replayGain']:
        tag.add(TXXX(desc="REPLAYGAIN_TRACK_GAIN", text=track.replayGain))
    if track.lyrics['unsync'] and save['lyrics']:
        tag.add(USLT(text=track.lyrics['unsync']))

    involved_people = []
    for role in track.contributors:
        if role in ['author', 'engineer', 'mixer', 'producer', 'writer']:
            for person in track.contributors[role]:
                involved_people.append([role, person])
        elif role == 'composer' and save['composer']:
            tag.add(TCOM(text=track.contributors['composer']))
    if len(involved_people) > 0 and save['involvedPeople']:
        tag.add(IPLS(people=involved_people))

    if save['copyright']:
        tag.add(TCOP(text=track.copyright))
    if save['savePlaylistAsCompilation'] and track.playlist:
        tag.add(TCMP(text="1"))

    if save['cover'] and track.album['picPath']:
        with open(track.album['picPath'], 'rb') as f:
            tag.add(
                APIC(3, 'image/jpeg' if track.album['picPath'].endswith('jpg') else 'image/png', 3, desc='cover', data=f.read()))

    tag.save(stream, v1=2 if save['saveID3v1'] else 0, v2_version=3,
             v23_sep=None if save['useNullSeparator'] else '/')

# Adds tags to a FLAC file
def tagFLAC(stream, track, save):
    # Delete exsisting tags
    tag = FLAC(stream)
    tag.delete()
    tag.clear_pictures()

    if save['title']:
        tag["TITLE"] = track.title

    if save['artist'] and len(track.artists):
        if save['multiArtistSeparator'] != "default":
            if save['multiArtistSeparator'] == "nothing":
                tag["ARTIST"] = track.mainArtist['name']
            else:
                tag["ARTIST"] = track.artistsString
            tag["ARTISTS"] = track.artists
        else:
            tag["ARTIST"] = track.artists

    if save['album']:
        tag["ALBUM"] = track.album['title']

    if save['albumArtist'] and len(track.album['artists']):
        if save['singleAlbumArtist']:
            tag["ALBUMARTIST"] = track.album['mainArtist']['name']
        else:
            tag["ALBUMARTIST"] = track.album['artists']

    if save['trackNumber']:
        tag["TRACKNUMBER"] = str(track.trackNumber)
    if save['trackTotal']:
        tag["TRACKTOTAL"] = str(track.album['trackTotal'])
    if save['discNumber']:
        tag["DISCNUMBER"] = str(track.discNumber)
    if save['discTotal']:
        tag["DISCTOTAL"] = str(track.album['discTotal'])
    if save['genre']:
        tag["GENRE"] = track.album['genre']
    if save['date']:
        tag["DATE"] = track.dateString
    elif save['year']:
        tag["YEAR"] = str(track.date['year'])
    if save['length']:
        tag["LENGTH"] = str(track.duration)
    if save['bpm']:
        tag["BPM"] = str(track.bpm)
    if save['label']:
        tag["PUBLISHER"] = track.album['label']
    if save['isrc']:
        tag["ISRC"] = track.ISRC
    if save['barcode']:
        tag["BARCODE"] = track.album['barcode']
    if save['explicit']:
        tag["ITUNESADVISORY"] = "1" if track.explicit else "0"
    if save['replayGain']:
        tag["REPLAYGAIN_TRACK_GAIN"] = track.replayGain
    if track.lyrics['unsync'] and save['lyrics']:
        tag["LYRICS"] = track.lyrics['unsync']

    for role in track.contributors:
        if role in ['author', 'engineer', 'mixer', 'producer', 'writer', 'composer']:
            if save['involvedPeople'] and role != 'composer' or role == 'composer' and save['composer']:
                tag[role] = track.contributors[role]
        elif role == 'musicpublisher' and save['involvedPeople']:
            tag["ORGANIZATION"] = track.contributors['musicpublisher']

    if save['copyright']:
        tag["COPYRIGHT"] = track.copyright
    if save['savePlaylistAsCompilation'] and track.playlist:
        tag["COMPILATION"] = "1"

    if save['cover'] and track.album['picPath']:
        image = Picture()
        image.type = 3
        image.mime = 'image/jpeg' if track.album['picPath'].endswith('jpg') else 'image/png'
        with open(track.album['picPath'], 'rb') as f:
            image.data = f.read()
        tag.add_picture(image)

    tag.save(deleteid3=True)

# MusicDownload
![Apple Music](https://www.apple.com/v/apple-music/m/images/overview/icon_apple_music__v9epn6m1oj6u_large.png) ![Deezer](https://lh3.googleusercontent.com/proxy/ZCUIQGxQ0Eov1tHKZ0xkRU8L3I48q6GkrysY-MGGQyXSUlil07AveIFqT62WOcnJrR2pthRGqsPgHXsbZlqWYVHhvTOnOEpboWiJztyhsiE9V5Tpv8qO6tZFtlFC4qwF3g =84x84)

A python3 library to downloads songs using Deemix API and Apple Music's API for finding the songs and tagging ID3 metadata.

As for songs searching support:
- Interactively searching for songs
- Loading song names from a file _(-f)_
- Automatic/Manual song selection. _(-m)_

At last it supports uploading downloaded files to WeTransfer! Useful if you use a remote server. _(-u)_

## Installation
### Pre-requisites
- Python3.x
- deemix (1.5.6)
- mutagen

```bash
python3 -m pip install deemix==1.5.6
python3 -m pip install mutagen
```


```bash
git clone git@github.com:segevp/music-downloader.git
```

## Usage
```
music_downloader.py [-h] [-u] [-m {1,2,3,4,5}] [-f FILE] [path]

positional arguments:
  path                  songs download path

optional arguments:
  -h, --help            show this help message and exit
  -u, --upload          upload songs to wetransfer
  -m {1,2,3,4,5}, --manual {1,2,3,4,5}
                        manual song selection, max 5 options
  -f FILE, --file FILE  load a file with songs list
```
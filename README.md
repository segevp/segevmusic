# MusicDownload
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

 # SegevMusic 
 <img src="https://camo.githubusercontent.com/5eda29273e871718abf8f4f7f4da48dbe677a7bb/68747470733a2f2f7777772e6170706c652e636f6d2f762f6170706c652d6d757369632f6d2f696d616765732f6f766572766965772f69636f6e5f6170706c655f6d757369635f5f763965706e366d316f6a36755f6c617267652e706e67" width="84" height="84">  <img src="http://millionmedia.com/wp-content/uploads/2014/11/deezer-logo-circle.png" width="84" height="84">

A Python library to download songs using:
- **Apple Music API** for finding the songs and tagging ID3 metadata
- **Deezer API** for the downloading itself, using the [deemix](https://codeberg.org/RemixDev/deemix) library

As for songs searching support:
- Automatic song selection
- Interactively searching for songs _(the default)_
- Loading song names from a file _(-f)_
- Validation and modifying of chosen songs _(-c)_
- **currently beta:** Download an entire album - new feature! _(-a)_

At last it supports uploading downloaded files to WeTransfer _(-u)_! Useful if you use a remote server.

## Installation
> Requires Python3.6 and higher

Installation is as simple as a one line of code:

```bash
pip3 install git+https://github.com/segevp/segevmusic.git
```
Or via SSH:

```bash
pip3 install git+ssh://git@github.com/segevp/segevmusic.git
```

<img src="https://camo.githubusercontent.com/355adb6374f51d5c0fb084e709e7d3c09361c698/687474703a2f2f7365676576666c69782e746b3a383030302f612e676966"/>

## Usage
```
segevmusic [-h] [-f FILE] [-u] [-a] [-d] [path]

download music effortlessly

positional arguments:
  path                  songs download path

optional arguments:
  -h, --help            show this help message and exit
  -f FILE, --file FILE  load a file with songs list
  -u, --upload          upload songs to wetransfer
  -a, --album           download an entire album
  -d, --dont-validate   don't validate chosen songs
```

**SegevMusic** can be run in multiple ways:
#### From terminal (as a binary):
```bash
segevmusic --help
```
#### From terminal, via Python:
```bash
python -m segevmusic --help
```
#### Inside your Python code:
```python
import segevmusic.music_downloader

if __name__ == "__main__":
    segevmusic.music_downloader.main()

```

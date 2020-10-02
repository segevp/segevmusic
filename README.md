 # SegevMusic 
 <img src="https://camo.githubusercontent.com/5eda29273e871718abf8f4f7f4da48dbe677a7bb/68747470733a2f2f7777772e6170706c652e636f6d2f762f6170706c652d6d757369632f6d2f696d616765732f6f766572766965772f69636f6e5f6170706c655f6d757369635f5f763965706e366d316f6a36755f6c617267652e706e67" width="84" height="84">  <img src="https://camo.githubusercontent.com/3b1077909ce329af890a6820ceb78f9c77b15a4d/68747470733a2f2f6c68332e676f6f676c6575736572636f6e74656e742e636f6d2f70726f78792f5a4355495147785130456f763174484b5a30786b5255384c334934387136476b727973592d4d474751795853556c696c3037417665494671543632574f636e4a725232707468524771735067485873625a6c71575956486876544f6e4f4570626f57694a7a74796873694539563554707638714f36745a46746c4643347177463367" width="84" height="84">

A Python library to download songs using:
- **Apple Music API** for finding the songs and tagging ID3 metadata
- **Deezer API** for the downloading itself, using the [deemix](https://codeberg.org/RemixDev/deemix) library

As for songs searching support:
- Interactively searching for songs _(the default)_
- Loading song names from a file _(-f)_
- Automatic/Manual song selection. _(-m)_

At last it supports uploading downloaded files to WeTransfer! Useful if you use a remote server. _(-u)_

<img src="https://camo.githubusercontent.com/c20f060672287e7fead8773e11a4e835f3326a21/687474703a2f2f7365676576666c69782e746b3a383030302f6f75742e676966"/>

## Installation
> Requires Python3.6 and higher

Installation is as simple as a one line of code:

```bash
python3 -m pip install git+ssh://git@github.com/segevp/music-downloader.git
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

SegevMusic can be run in multiple ways:
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

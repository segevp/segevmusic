#!/usr/bin/env python3
from deemix.api.deezer import Deezer
from deemix.app.settings import Settings
from deemix.app.queuemanager import QueueManager
from deemix.app.spotifyhelper import SpotifyHelper

class deemix:
    def __init__(self, configFolder=None):
        self.set = Settings(configFolder)
        self.dz = Deezer()
        self.sp = SpotifyHelper(configFolder)
        self.qm = QueueManager()

#!/usr/bin/env python3
import os.path as path
import sys
from os import getenv

userdata = ""
homedata = path.expanduser("~")

if getenv("APPDATA"):
    userdata = getenv("APPDATA") + path.sep + "deemix" + path.sep
elif sys.platform.startswith('darwin'):
    userdata = homedata + '/Library/Application Support/deemix/'
elif getenv("XDG_CONFIG_HOME"):
    userdata = getenv("XDG_CONFIG_HOME") + '/deemix/'
else:
    userdata = homedata + '/.config/deemix/'

def getHomeFolder():
    return homedata

def getConfigFolder():
    return userdata

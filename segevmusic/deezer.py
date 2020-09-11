from os.path import realpath, join
from deemix.app.cli import cli

DEEZER_ISRC_QUERY = r"https://api.deezer.com/2.0/track/isrc:{isrc}"
ARL = r"5bbd39c9df0b86568f46c9310cb61f4c9c3e3a1cef78b0a5e142066dca8c1ea495edea03cbb1536a5ba1fd2cff9b15fe21114d221140b57e0ab96484d4a1f4d0acbbfe66af7587a8f2af59ebeb5036c7d09bd1d8ad936f4da1b9c1ed6af46e21"


class DeezerFunctions:
    @staticmethod
    def amsong_to_url(amsong):
        return DEEZER_ISRC_QUERY.format(isrc=amsong.isrc)

    @staticmethod
    def login(arl=ARL):
        localpath = realpath('..')
        config_folder = join(localpath, '../config')
        app = cli(localpath + '/Songs', config_folder)
        app.login(arl)
        return app

    @staticmethod
    def download(url, app):
        app.downloadLink(url)

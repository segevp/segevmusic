from deemix.app.cli import cli
import os.path


def download(url, arl=None):
    localpath = os.path.realpath('.')
    config_folder = os.path.join(localpath, 'config')
    app = cli(localpath, config_folder)
    app.login(arl)
    url = [url] if type(url) == str else url
    app.downloadLink(url)

from typing import List
from re import search
from zlib import crc32
import requests
import os.path

WETRANSFER_API_URL = 'https://wetransfer.com/api/v4/transfers'
WETRANSFER_UPLOAD_LINK_URL = WETRANSFER_API_URL + '/link'
WETRANSFER_FILES_URL = WETRANSFER_API_URL + '/{transfer_id}/files'
WETRANSFER_PART_PUT_URL = WETRANSFER_FILES_URL + '/{file_id}/part-put-url'
WETRANSFER_FINALIZE_MPP_URL = WETRANSFER_FILES_URL + '/{file_id}/finalize-mpp'
WETRANSFER_FINALIZE_URL = WETRANSFER_API_URL + '/{transfer_id}/finalize'

WETRANSFER_DEFAULT_CHUNK_SIZE = 5242880


def _prepare_session() -> requests.Session:
    """Prepare a wetransfer.com session.
    Return a requests session that will always pass the initial X-CSRF-Token:
    and with cookies properly populated that can be used for wetransfer
    requests.
    """
    s = requests.Session()
    r = s.get('https://wetransfer.com/')
    m = search('name="csrf-token" content="([^"]+)"', r.text)
    s.headers.update({'X-CSRF-Token': m.group(1)})

    return s


def _prepare_link_upload(filenames: List[str], message: str, session: requests.Session) -> dict:
    """Given a list of filenames and a message prepare for the link upload.
    Return the parsed JSON response.
    """
    j = {
        "files": [_file_name_and_size(f) for f in filenames],
        "message": message,
        "ui_language": "en",
    }

    r = session.post(WETRANSFER_UPLOAD_LINK_URL, json=j)
    return r.json()


def _file_name_and_size(file: str) -> dict:
    """Given a file, prepare the "name" and "size" dictionary.
    Return a dictionary with "name" and "size" keys.
    """
    filename = os.path.basename(file)
    filesize = os.path.getsize(file)

    return {
        "name": filename,
        "size": filesize
    }


def _prepare_file_upload(transfer_id: str, file: str, session: requests.Session) -> dict:
    """Given a transfer_id and file prepare it for the upload.
    Return the parsed JSON response.
    """
    j = _file_name_and_size(file)
    r = session.post(WETRANSFER_FILES_URL.format(transfer_id=transfer_id),
                     json=j)
    return r.json()


def _upload_chunks(transfer_id: str, file_id: str, file: str, session: requests.Session,
                   default_chunk_size: int = WETRANSFER_DEFAULT_CHUNK_SIZE) -> str:
    """Given a transfer_id, file_id and file upload it.
    Return the parsed JSON response.
    """
    f = open(file, 'rb')

    chunk_number = 0
    while True:
        chunk = f.read(default_chunk_size)
        chunk_size = len(chunk)
        if chunk_size == 0:
            break
        chunk_number += 1

        j = {
            "chunk_crc": crc32(chunk),
            "chunk_number": chunk_number,
            "chunk_size": chunk_size,
            "retries": 0
        }

        r = session.post(
            WETRANSFER_PART_PUT_URL.format(transfer_id=transfer_id,
                                           file_id=file_id),
            json=j)
        url = r.json().get('url')
        requests.options(url,
                         headers={
                             'Origin': 'https://wetransfer.com',
                             'Access-Control-Request-Method': 'PUT',
                         })
        requests.put(url, data=chunk)

    j = {
        'chunk_count': chunk_number
    }
    r = session.put(
        WETRANSFER_FINALIZE_MPP_URL.format(transfer_id=transfer_id,
                                           file_id=file_id),
        json=j)

    return r.json()


def _finalize_upload(transfer_id: str, session: requests.Session) -> dict:
    """Given a transfer_id finalize the upload.
    Return the parsed JSON response.
    """
    r = session.put(WETRANSFER_FINALIZE_URL.format(transfer_id=transfer_id))

    return r.json()


def upload(files: List[str], message: str = '') -> str:
    # Check that all files exists
    for f in files:
        if not os.path.exists(f):
            raise FileNotFoundError(f)

    # Check that there are no duplicates filenames
    # (despite possible different dirname())
    filenames = [os.path.basename(f) for f in files]
    if len(files) != len(set(filenames)):
        raise FileExistsError('Duplicate filenames')

    s = _prepare_session()
    transfer_id = _prepare_link_upload(files, message, s)['id']

    for f in files:
        file_id = _prepare_file_upload(transfer_id, f, s)['id']
        _upload_chunks(transfer_id, file_id, f, s)

    return _finalize_upload(transfer_id, s)['shortened_url']

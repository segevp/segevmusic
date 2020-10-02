from typing import List
from re import search
from zlib import crc32
import requests
import os.path

WETRANSFER_URL = 'https://wetransfer.com/'
WETRANSFER_API_URL = WETRANSFER_URL + 'api/v4/transfers'
WETRANSFER_UPLOAD_LINK_URL = WETRANSFER_API_URL + '/link'
WETRANSFER_FILES_URL = WETRANSFER_API_URL + '/{transfer_id}/files'
WETRANSFER_PART_PUT_URL = WETRANSFER_FILES_URL + '/{file_id}/part-put-url'
WETRANSFER_FINALIZE_MPP_URL = WETRANSFER_FILES_URL + '/{file_id}/finalize-mpp'
WETRANSFER_FINALIZE_URL = WETRANSFER_API_URL + '/{transfer_id}/finalize'
WETRANSFER_DEFAULT_CHUNK_SIZE = 5242880

PUT_JSON = {
    'Origin': WETRANSFER_URL,
    'Access-Control-Request-Method': 'PUT'
}
CSRF_REGEX = 'name="csrf-token" content="([^"]+)"'

BIG_SPACE = 22 * ' '


class WTSession(requests.Session):
    """
    A class for handling WeTransfer sessions.
    """

    def __init__(self):
        super().__init__()
        self.prepare_session()
        self.total_chunks = 0
        self.current_chunk = 0

    def prepare_session(self):
        """Prepare a wetransfer.com session.
        Return a requests session that will always pass the initial X-CSRF-Token:
        and with cookies properly populated that can be used for wetransfer
        requests.
        """
        r = self.get(WETRANSFER_URL)
        m = search(CSRF_REGEX, r.text)
        self.headers.update({'X-CSRF-Token': m.group(1)})

    def create_transfer_id(self, filenames: List[str], message: str) -> str:
        """Given a list of filenames and a message prepare for the link upload.
        Return the parsed JSON response.
        """
        j = {
            "files": [self.file_name_and_size(f) for f in filenames],
            "message": message,
            "ui_language": "en",
        }

        r = self.post(WETRANSFER_UPLOAD_LINK_URL, json=j)
        return r.json()['id']

    @staticmethod
    def file_name_and_size(file: str) -> dict:
        """Given a file, prepare the "name" and "size" dictionary.
        Return a dictionary with "name" and "size" keys.
        """
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)

        return {
            "name": filename,
            "size": filesize
        }

    def prepare_file_upload(self, transfer_id: str, file: str) -> dict:
        """Given a transfer_id and file prepare it for the upload.
        Return the parsed JSON response.
        """
        j = self.file_name_and_size(file)
        r = self.post(WETRANSFER_FILES_URL.format(transfer_id=transfer_id), json=j)
        return r.json()

    def upload_chunks(self, transfer_id: str, file_id: str, file: str,
                      default_chunk_size: int = WETRANSFER_DEFAULT_CHUNK_SIZE) -> str:
        """Given a transfer_id, file_id and file upload it.
        Return the parsed JSON response.
        """
        f = open(file, 'rb')
        file_name = os.path.basename(file)
        chunk_number = 0
        while True:
            chunk = f.read(default_chunk_size)
            chunk_size = len(chunk)
            if chunk_size == 0:
                print(f"\r--> Finished uploading {file_name}.", BIG_SPACE)
                break
            chunk_number += 1
            self.current_chunk += 1

            print("\r--> {0:.2f}% uploaded...".format(self.current_chunk * 100 / self.total_chunks),
                  f"Started uploading {file_name}...",
                  sep=' \\ ', end='')

            j = {
                "chunk_crc": crc32(chunk),
                "chunk_number": chunk_number,
                "chunk_size": chunk_size,
                "retries": 0
            }

            r = self.post(WETRANSFER_PART_PUT_URL.format(transfer_id=transfer_id, file_id=file_id), json=j)
            url = r.json().get('url')
            requests.options(url, headers=PUT_JSON)
            requests.put(url, data=chunk)

        j = {'chunk_count': chunk_number}
        r = self.put(WETRANSFER_FINALIZE_MPP_URL.format(transfer_id=transfer_id, file_id=file_id), json=j)

        return r.json()

    def finalize_upload(self, transfer_id: str) -> dict:
        """Given a transfer_id finalize the upload.
        Return the parsed JSON response.
        """
        r = self.put(WETRANSFER_FINALIZE_URL.format(transfer_id=transfer_id))

        return r.json()

    def upload(self, files: List[str], message: str = '') -> str:
        """
        Upload given files to wetransfer.com.
        Return the shortened link.
        """
        # Check that all files exists
        for f in files:
            if not os.path.exists(f):
                raise FileNotFoundError(f)

        self.total_chunks = round(sum([one_file['size'] for one_file in
                                       [self.file_name_and_size(f) for f in files]]) / WETRANSFER_DEFAULT_CHUNK_SIZE)

        # Check that there are no duplicates filenames, despite possible different directories
        filenames = [os.path.basename(f) for f in files]
        if len(files) != len(set(filenames)):
            raise FileExistsError('Duplicate filenames')

        transfer_id = self.create_transfer_id(files, message)

        for f in files:
            file_id = self.prepare_file_upload(transfer_id, f)['id']
            self.upload_chunks(transfer_id, file_id, f)

        return self.finalize_upload(transfer_id)['shortened_url']

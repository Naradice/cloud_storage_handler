import os
import unittest

import dotenv

from cloud_storage_handler import DropboxHandler


dotenv.load_dotenv(".env")


class TesDrobox(unittest.TestCase):

    def test_authentication(self):
        file_handler = DropboxHandler(os.environ['box_client_id'], os.environ['box_redirect_uri'])
        file_handler.authenticate()
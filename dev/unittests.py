import os

# Credentials
ROOT_DIR=os.getcwd()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".credentials/service_credentials.json")

from dev import drive
from dev import sheets
from dev import slides
import pandas as pd
import numpy as np
import unittest

# https://www.digitalocean.com/community/tutorials/python-unittest-unit-test-example
class TestingGoogleDriveFile(unittest.TestCase):
    def test_create(self, file_name, 
                    mime_type='application/vnd.google-apps.spreadsheet', 
                    parent_folder_id=None,
                    transfer_permissions=False,
                    **kwargs):
        test_title = 'tmp__test_created_file'
        created_file = drive.GoogleDriveFile(file_name=file_name, 
                                             mime_type=mime_type,
                                             parent_folder_id=parent_folder_id,
                                             transfer_permissions=transfer_permissions,
                                             **kwargs)
        name_created_file = created_file.file_name
        type_created_file = created_file.mime_type
        created_file.delete()
        self.assertEqual(file_name, name_created_file)
        self.assertEqual(mime_type, type_created_file)

    def test_rename(self, file_obj, new_file_name='tmp__new_file_name'):
        old_name = file_obj.file_name
        file_obj.rename(new_file_name=new_file_name)
        new_name = file_obj.file_name
        self.assertEqual(new_name, new_file_name)
        self.assertNotEqual(new_name, old_name)s      
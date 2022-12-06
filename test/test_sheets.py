import unittest

from GoogleApiSupport import sheets
from GoogleApiSupport import drive


class TestCreate(unittest.TestCase):
    def test_create(self):
        """
        Check if the function creates a file
        """
        test_title = 'tmp__test_created_file'
        id_created_file = sheets.create(test_title)
        sheet_data = sheets.get_sheet_info(id_created_file)
        drive.delete_file(sheet_data['spreadsheetId'])
        self.assertEqual( sheet_data['properties']['title'], test_title)

if __name__ == '__main__':
    unittest.main()
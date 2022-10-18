import unittest

from GoogleApiSupport import spreadsheets
from GoogleApiSupport import drive

TEST_WRITE_FILE_ID = '19Q8y1uR8SD27GiVN200e87ufoMklH2KBh2NfyQTEt9Q'
TEST_READONLY_FILE_ID = '1cMTfxikXMAgmdVXj3PKuD1fX_vPnQmO5teg15zGarOc'

class TestsReadOnly(unittest.TestCase):
    def test_get_sheet_names(self):
        """
        Check if the function creates a file
        """
        response = spreadsheets.get_sheet_names(TEST_READONLY_FILE_ID)
        
        self.assertEqual(
            response, 
            ['hello', 'world', 'third_sheet']
        )
    


class TestCreate(unittest.TestCase):
    def test_create(self):
        """
        Check if the function creates a file
        """
        test_title = 'tmp__test_created_file'
        id_created_file = spreadsheets.create(test_title)
        sheet_data = spreadsheets.get_info(id_created_file)
        drive.delete_file(sheet_data['spreadsheetId'])
        self.assertEqual( sheet_data['properties']['title'], test_title)


 
class TestAddSheet(unittest.TestCase):
    
    test_sheet_name = 'tmp__new_page_test'
    
    def test_add_sheet(self):
        """
        Check if the function creates a sheet on the spreadsheet
        """
        response = spreadsheets.add_sheet(TEST_WRITE_FILE_ID, self.test_sheet_name)
        self.assertEqual(response['replies'][0]['addSheet']['properties']['title'], self.test_sheet_name)
    
    def test_delete_sheet(self):
        """Check if the function deletes a sheet on the spreadsheet
        """
        response = ''
        spreadsheet_sheets = spreadsheets.get_sheets(TEST_WRITE_FILE_ID)
        for sheet in spreadsheet_sheets:
            if sheet['properties']['title'] == self.test_sheet_name:
                response = spreadsheets.delete_sheet(TEST_WRITE_FILE_ID, sheet['properties']['sheetId'])
                break
        self.assertEqual(response['replies'], [{}])

                

if __name__ == '__main__':
    unittest.main()
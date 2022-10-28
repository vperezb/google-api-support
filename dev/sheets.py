import re, webbrowser
import pandas as pd
from apiclient import errors
from dev.drive import GoogleDriveFile
from GoogleApiSupport import auth, apis

class GoogleSheets(GoogleDriveFile):
    
    services = {api_name: auth.get_service(api_name) for api_name in apis.api_configs}
    
    def __new__(cls, file_id=None):
        mime_type = cls.services.get('drive').files().get(fileId=file_id, fields='*').execute().get('mimeType')
        assert mime_type == 'application/vnd.google-apps.spreadsheet', 'The file is of type "{type}", but it needs to be Google Sheets to be of this class type.'.format(type=mime_type)
        return super().__new__(cls)
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)
        
        # Additional spreadsheet specific info
        spreadsheet_info = self.services.get('sheets').spreadsheets().get(spreadsheetId=file_id, fields='*').execute()
        
        # TODO: Update python version to >= 3.9 and do z = x | y
        self._info = {**self._info, **spreadsheet_info}
 
    # Additional properties with respect to GoogleDriveFile
    @property
    def locale(self):
        return self._info.get('properties').get('locale')
    
    @property
    def timezone(self):
        return self._info.get('properties').get('timezone')
    
    @property
    def sheets(self):
        return {sheet.get('properties').get('sheetId'):{key:value for key, value in sheet.get('properties').items() if key != 'sheetId'} for sheet in self._info.get('sheets')}
    
    @property
    def sheets_ids(self):
        return [*self.sheets.keys()]
        
    @property
    def sheets_names(self):
        return [sheet.get('title') for sheet in self.sheets.values()]
    
    # Export chart as image/pdf
    # Currently not possible, proposed here: https://issuetracker.google.com/issues/230039395?pli=1
    # With Javascript: https://stackoverflow.com/questions/61491782/how-to-download-charts-in-png-from-google-sheet
    
    @classmethod
    def create(cls, file_name, parent_folder_id=None, transfer_permissions=False, **kwargs):
        new_file = super().create(file_name=file_name, 
                                  mime_type='application/vnd.google-apps.spreadsheet',
                                  parent_folder_id=parent_folder_id, 
                                  transfer_permissions=transfer_permissions, 
                                  **kwargs)
        return new_file
        
    def add_sheet(self, sheet_name, index=None):
        """Adds a new page to an existing spreadsheet.

        Args:
            sheet_name (str): The desired name for the new sheet.
            index (int): The desired index where to place the sheet. If not given, defaults to the end.
        """
        
        index = len(self.sheets) if index is None else index
               
        request = {'requests': [{'addSheet':{'properties':{'title': sheet_name, 
                                                           'index': index}}}]}
        
        try:
            sheet_info = self.services.get('sheets').spreadsheets().batchUpdate(spreadsheetId=self.file_id, body=request).execute()
            spreadsheet_info = self.services.get('sheets').spreadsheets().get(spreadsheetId=self.file_id, fields='sheets').execute()
            self.sheets = {sheet.get('properties').get('sheetId'):{key:value for key, value in sheet.get('properties').items() if key != 'sheetId'} for sheet in spreadsheet_info.get('sheets')}
            print('Sheet {name} created at index {index}.'.format(name=sheet_name, index=index))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    # TODO: add method to move sheet to different position
    
    def delete_sheet(self, sheet_id):
        """Delete a sheet from the existing spreadsheet.

        Args:
            sheet_id (int): ID of the sheet to remove.
        """
        
        request = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
        sheet_info = self.services.get('sheets').spreadsheets().batchUpdate(spreadsheetId=self.file_id, body=request).execute()
        spreadsheet_info = self.services.get('sheets').spreadsheets().get(spreadsheetId=self.file_id, fields='sheets').execute()
        self.sheets = {sheet.get('properties').get('sheetId'):{key:value for key, value in sheet.get('properties').items() if key != 'sheetId'} for sheet in spreadsheet_info.get('sheets')}
       
    def sheet_url(self, sheet_id):
        """Return URL of specific sheet inside the presentation

        Args:
            sheet_id (str): ID of the sheet.

        Raises:
            ValueError: If given sheet ID is not included in the presentation.

        Returns:
            str: URL of the given sheet.
        """
        if sheet_id not in self.sheets_ids:
            raise ValueError('This Sheet ID does not exist in this spreadsheet. Check the values from the attribute "sheets_ids" for the list of IDs.')
        return 'https://docs.google.com/spreadsheets/d/' + self.file_id + '/edit#gid=' + str(sheet_id)
        
    def open(self, sheet_id=None, new=0, autoraise=True):
        """Method that opens a sheet in the browser.
        It uses the function webbrowser.open() and has the same arguments.
        None will open the file, thus the first sheet. Specify a sheet_id if you want to open another one.

        Args:
            sheet_id (str, optional): ID of the sheet.
            new (int, optional): If new is 0, the url is opened in the same browser window if possible. If new is 1, a new browser window is opened if possible. If new is 2, a new browser page (“tab”) is opened if possible. Defaults to 0.
            autoraise (bool, optional):  If autoraise is True, the window is raised if possible (note that under many window managers this will occur regardless of the setting of this variable). Defaults to True.
        
        Raises:
            ValueError: If given sheet ID is not included in the presentation.
        """
        if sheet_id==None:
            super().open(self)
        elif sheet_id not in self.sheets_ids:
            raise ValueError('This Sheet ID does not exist in this spreadsheet. Check the values from the attribute "sheets_ids" for the list of IDs.')
        else:
            url = self.sheet_url(sheet_id=sheet_id)
            try: 
                webbrowser.open(url, new=new, autoraise=autoraise)
            except errors.HttpError as error:
                print('An error occurred: %s' % error)
        
    def sheet_to_df(self, sheet_name='', sheet_range='', index='', header_index=0):
        """Extract data from a sheet and save it in a pandas data frame.

        Args:
            sheet_name (str, optional): Name of the sheet to extract data from. Defaults to '' (first sheet).
            sheet_range (str, optional): Range of cells to extract data. Defaults to '' (entire sheet).
            index (str, optional): Column to be the index of resulting data frame. Defaults to '' (none).
            header_index (int, optional): Row index in for header/column names. Defaults to 0.

        Returns:
            pd.DataFrame: Data from sheet.
        """

        # If not defined, take first sheet
        if (sheet_name == ''):
            sheet_name = self.sheet_names[0]

        # If not defined, import entire sheet
        if (sheet_range != ''):
            sheet_range = '!'+sheet_range

        result = self.services.get('sheets').spreadsheets().values().get(
            spreadsheetId=self.file_id,
            valueRenderOption='FORMATTED_VALUE',
            range=sheet_name+sheet_range
        ).execute()

        values = result.get("values", [])
        for i in range(header_index):
            values.pop(0)
        headers = values.pop(0)

        if (index == ''):
            df = pd.DataFrame(values, columns=headers)
        else:
            df = pd.DataFrame(values, columns=headers).set_index(index, drop=False)
        return df
        
    def df_to_sheet(self, df, sheet_name, starting_cell='A1', how='replace'):
        """Uploads a pandas.DataFrame to the desired sheet of a Google Sheets.
        SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET. 
        Data must be utf-8 encoded to avoid errors.

        Args:
            df (pd.DataFrame): The dataframe to be uploaded.
            sheet_name (str): The target name of the page to upload the DataFrame.
            starting_cell (str, optional): The cell in the sheet where the data will be uploaded. Defaults to 'A1'.
            how (str, optional): Whether the data should replace the current data, if present (replace) or if it should be added below it (append). Defaults to 'replace'.
        """
        
        # Check that the given value for "how" is accepted
        try:     
            assert how in set(['replace', 'append'])
        except Exception as ex:
            print('{ex}: The accepted values for the argument "how" are "replace" and "append".'.format(ex=ex.__class__.__name__))
        
        # Get data into correct state for the API request
        df.fillna(value='', inplace=True)
        column_list = df.columns.tolist()
        value_list = df.values.tolist()
        starting_cell = starting_cell.upper()
        range = sheet_name+'!'+starting_cell

        try:
            if how == 'replace':
                data = [
                    {
                        'range': range,
                        'values': [column_list] + value_list
                    },
                ]
                body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': data
                }
                result = self.services.get('sheets').spreadsheets().values().batchUpdate(
                    spreadsheetId=self.file_id,
                    body=body
                ).execute()
                print('Data inserted.')
            elif how == 'append':
                body = {
                        'values': value_list
                    }
                result = self.services.get('sheets').spreadsheets().values().append(spreadsheetId=self.file_id,
                                                                range=range,
                                                                body=body,
                                                                valueInputOption='USER_ENTERED').execute()
                print('Data appended.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def pivot_table(self, 
                    data_sheet_name='', data_range='', 
                    where='New Sheet', 
                    pt_sheet_name='Pivot Table', pt_starting_cell='A1'):
        """Create pivot table out of data located in the spreadsheet.

        Args:
            data_sheet_name (str, optional): Sheet name where the data is located. Defaults to '' (first sheet).
            data_range (str, optional): Range where the data is located. Defaults to '' (entire sheet).
            where (str, optional): Where to place pivot table: 'New Sheet' or 'Existing Sheet'. Defaults to 'New Sheet'.
            pt_sheet_name (str, optional): If where='New Sheet', how to name the sheet. Defaults to 'Pivot Table'.
            pt_starting_cell (str, optional): If where='New Sheet', which cell the pivot table is associated with. Defaults to 'A1'.
        """
        
        pass
            
    def clear_sheet(self, sheet_name='', sheet_range=''):
        """Deletes the data in the selected area

        Args:
            sheet_name (str):  Name of the sheet to extract data from. Defaults to '' (first sheet).
            sheet_range (str, optional): Range of cells to extract data. Defaults to '' (entire sheet).
        """
        if (sheet_range != ''):
            sheet_range = '!'+sheet_range

        try:
            result = self.services.get('sheets').spreadsheets().values().clear(
                spreadsheetId=self.file_id,
                range=sheet_name+sheet_range
            ).execute()
            print('Data from {} deleted.'.format(sheet_name+sheet_range))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
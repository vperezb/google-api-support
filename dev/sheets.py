import pandas as pd
from apiclient import errors
from dev.drive import GoogleDriveFile
from GoogleApiSupport import auth
from GoogleApiSupport import apis

class GoogleSheets(GoogleDriveFile):
    
    services = {api_name: auth.get_service(api_name) for api_name in apis.api_configs}
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)
        try:     
            assert self.mime_type == 'application/vnd.google-apps.spreadsheet'
        except Exception as ex:
            print('{ex}: The file needs to be a Google Sheet to be of this class type.'.format(ex=ex.__class__.__name__))
        
        # Additional spreadsheet specific info
        spreadsheet_info = self.services.get('sheets').spreadsheets().get(spreadsheetId=file_id, fields='*').execute()
        self.locale = spreadsheet_info.get('properties').get('locale')
        self.timezone = spreadsheet_info.get('properties').get('timezone')
        self.sheets = {sheet.get('properties').get('sheetId'):{key:value for key, value in sheet.get('properties').items() if key != 'sheetId'} for sheet in spreadsheet_info.get('sheets')}
        
    @property
    def sheets_ids(self):
        return [*self.sheets.keys()]
        
    @property
    def sheets_names(self):
        return [sheet.get('title') for sheet in self.sheets.values()]
        
    # NOT WORKING PROPERLY
    # @classmethod
    # def create(cls, file_name, parent_folder_id=None, transfer_permissions=False, **kwargs):
    #     super().create(file_name=file_name, mime_type='application/vnd.google-apps.spreadsheet',
    #                    parent_folder_id=parent_folder_id, transfer_permissions=transfer_permissions, **kwargs)
        
    def add_sheet(self, sheet_name):
        """Adds a new page to an existing spreadsheet.

        Args:
            sheet_name (str): The desired name for the new sheet.
        """
        
        # TODO: add sheet in a certain position
        request = {'requests': [{'addSheet':{'properties':{'title': sheet_name}}}]}
        sheet_info = self.services.get('sheets').spreadsheets().batchUpdate(spreadsheetId=self.file_id, body=request).execute()
        properties = sheet_info.get('replies')[0].get('addSheet').get('properties')
        new_sheet={properties.get('sheetId'):{key:value for key, value in properties.items() if key != 'sheetId'}}
        self.sheets.update(new_sheet)
        
    # TODO: add method to move sheet to different position
    
    def delete_sheet(self, sheet_id):
        """Delete a sheet from the existing spreadsheet.

        Args:
            sheet_id (int): ID of the sheet to remove.
        """
        
        request = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
        sheet_info = self.services.get('sheets').spreadsheets().batchUpdate(spreadsheetId=self.file_id, body=request).execute()
        spreadsheet_info = self.services.get('sheets').spreadsheets().get(spreadsheetId=self.file_id, fields='properties').execute()
        self.sheets = {sheet.get('properties').get('sheetId'):{key:value for key, value in sheet.get('properties').items() if key != 'sheetId'} for sheet in spreadsheet_info.get('sheets')}
        
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
        
    def df_to_sheet(self, df, sheet_name, starting_cell='A1'):
        """Uploads a pandas.DataFrame to the desired sheet of a Google Sheets.
        SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET.
        Aditionally, pass a list with the new names of the columns.    
        Data must be utf-8 encoded to avoid errors.

        Args:
            data (pd.DataFrame): The dataframe to be uploaded.
            sheet_name (str): The target name of the page to upload the DataFrame.
            starting_cell (str, optional): The cell in the sheet where the data will be uploaded. Defaults to 'A1'.
        """

        df.fillna(value='', inplace=True)
        column_list = df.columns.tolist()
        value_list = df.values.tolist()

        try:
            data = [
                {
                    'range': sheet_name+'!'+starting_cell,
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
            print('Data uploaded')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
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
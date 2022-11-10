import pandas as pd

from GoogleApiSupport import auth

"""A set of functions to interact with Google Spreadsheets documents. 
Sales-wise the product is called "sheets" but I'm modifying the naming
because it will help make the library unambiguous. As the entity "sheets" 
inside the API is the name it has each of the sheets (pages) of the spreadsheet (document).
https://www.google.com/intl/ca/sheets/about/

.xlsx files can't be managed with the actual version of this library. You should "save as google sheets" 
for the module to work.

Naming convention:
    `spreadsheet` : The file, the full document. Its identifier it's the 
        `spreadsheet_id` and has its `spreadsheet_name`. Can be multiple spreadsheets with
        the same name as it does not represent anything, it's just another attribute.
    `sheet` : Each of the pages of a `spreadsheet`. The `sheet_name` is both the
        identifier and the "user friendly name". Because of that must be unique 
        within a spreadsheet.
        
Google API naming | Library naming
spreadsheet | spreadsheet
spreadsheetId | spreadsheet_id
spreadsheet.properties.title | spreadsheet_title
sheet.properties.title | sheet_name
sheet.properties.sheetId | sheet_id
"""

def get_info(spreadsheet_id, include_grid_data=False):
    """Returns an spreadsheet info object

    Args:
        spreadsheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters
        include_grid_data (bool): Passed to False, the function does not query the spreadsheet data, only the document information.
    Returns:
        dict: Object with a lot of sheet information such title, url, colors, alignment and much more.
    Deprecates: sheets.get_sheet_info
    """
    service = auth.get_service("spreadsheets")
    response = service.spreadsheets().get(spreadsheetId=spreadsheet_id, includeGridData=include_grid_data).execute()
    return response


def create(spreadsheet_title):
    """Creates in your root user folder a file typed spreadsheet with a single sheet. Use move file from drive api to move it to the desired final location.

    Args:
        spreadsheet_title (str): The desired title for the created spreadsheet.

    Returns:
        string: The id from the created file
    """
    service = auth.get_service("spreadsheets")
    spreadsheet = {
        'properties': {
            'title': spreadsheet_title
        }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                                fields='spreadsheetId') \
        .execute()
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get('spreadsheetId')


def add_sheet(spreadsheet_id, sheet_name):
    """Adds a new page to an existing spreadsheet.

    Args:
        spreadsheet_id (str): The objective spreadsheet id.
        sheet_name (str): The desired name for the new sheet.

    Returns:
        dict: Full response object from the Google API
    Deprecates: sheets.add_sheet_to_spreadsheet
    """

    service = auth.get_service("spreadsheets")
    
    data = {'requests': [
        {
            'addSheet':{
                'properties':{'title': sheet_name}
            }
        }
    ]}

    response = service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=data).execute()
    return response


def change_title(spreadsheet_title, spreadsheet_id):
    """Updates spreadsheet title.

    Args:
        spreadsheet_title (str): The new title we want to set to the spreadsheet
        spreadsheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters
    Deprecates: sheets.change_sheet_title
    """
    service = auth.get_service("spreadsheets")

    body = {
        "requests": [{
            "updateSpreadsheetProperties": {
                "properties": {"title": spreadsheet_title},
                "fields": "title"
            }
        }]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    return

def delete_sheet(spreadsheet_id, sheet_id):
    """_summary_

    Args:
        spreadsheet_id (_type_): _description_
        sheet_name (_type_): _description_
    """
    service = auth.get_service("spreadsheets")

    body = {
        "requests": [{
            "deleteSheet": {
                "sheetId": sheet_id
            }
        }]
    }

    response = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body=body
    ).execute()

    return response


def pandas_to_sheet(spreadsheet_id, page_name, df, starting_cell='A1'):
    """Uploads a pandas.dataframe to the desired page of a google sheets sheet.
    SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET.
    Aditionally, pass a list with the new names of the columns.    
    Data must be utf-8 encoded to avoid errors.

    Args:
        sheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters
        page_name (str): The target name of the page to upload the DataFrame
        df (pd.DataFrame): The dataframe to be uploaded.
        starting_cell (str, optional): The cell in the sheet where the data will be uploaded. Defaults to 'A1'.

    Returns:
        dict: A response object
    """

    service = auth.get_service("spreadsheets")

    df.fillna(value=0, inplace=True)
    columnsList = df.columns.tolist()
    valuesList = df.values.tolist()

    try:
        data = [
            {
                'range': page_name+'!'+starting_cell,
                'values': [columnsList] + valuesList
            },
        ]

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }

        response = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()

        return response

    except Exception as e:
        print(e)


def get_sheets(spreadsheet_id, only_names = False):
    """Get the names of the sheets in a spreadsheet.

    Args:
        spreadsheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters

    Returns:
        list: A list of the names of the sheets.
    """
    response = get_info(spreadsheet_id)
    
    if only_names:
        [a['properties']['title'] for a in response['sheets']]
    else: 
        return response['sheets']
    

def get_sheet_names(spreadsheet_id):
    """Get the names of the sheets in a spreadsheet.

    Args:
        spreadsheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters

    Returns:
        list: A list of the names of the sheets.
    """
    response = get_info(spreadsheet_id)
    return [a['properties']['title'] for a in response['sheets']]


def get_sheet_charts(spreadsheet_id, sheet_name):
    """Returns a list of the charts in a specific sheet

    Args:
        spreadsheet_id (str): Id of the desired document
        sheet_name - Name of the desired page 'Hoja1'

    Returns:
        list: returns a list of the charts.
    """
    sheet = get_info(spreadsheet_id)
    for sheet_page in sheet['sheets']:
        if sheet_page['properties']['title']==sheet_name:
            return sheet_page['charts']


def download_sheet_to_pandas(spreadsheet_id, sheet_name='', sheet_range='', index='', has_header=True ):
    """Downloads and instances a pd.DataFrame object with the sheets values. Parameters are important to manage the format of the info.
    Args:
        spreadsheet_id (_type_): Id of the desired document
        sheet_name (str, optional): Name of the desired page 'Hoja1'. (by default: first page). Defaults to ''.
        sheet_range (str, optional): Range of the desired info 'A1:C6'.(by default: WHOLE PAGE). Defaults to ''.
        index (str, optional): column you want to be the index of the resulting dataframe (by default: none of the columns is set as index). Defaults to ''.
        has_header (bool, optional): If the sheet has a header. If not, a dummy header is created. Defaults to True.

    Returns:
        pd.DataFrame: The output dataframe.
    Deprecates: sheets.sheet_to_pandas
    """
    service = auth.get_service("spreadsheets")
    if (sheet_range != ''):
        sheet_range = '!'+sheet_range

    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        valueRenderOption='FORMATTED_VALUE',
        range=sheet_name+sheet_range
    ).execute()

    if has_header:
        headers = response['values'].pop(0)
    else:
        max_len = 0 
        for row in response['values']:
            if len(row) > max_len:
                max_len = len(row)
        headers = __get_range_column_names(max_len)

    if (index == ''):
        return pd.DataFrame(response['values'], columns=headers)
    else:
        return pd.DataFrame(response['values'], columns=headers).set_index(index, drop=False)


def clear_sheet(spreadsheet_id, sheet_name, sheet_range=''):
    """Deletes the data in the selected area

    Args:
        spreadsheet_id (str): _description_
        sheet_name (str): _description_
        sheet_range (str, optional): _description_. Defaults to ''.
    """
    service = auth.get_service("spreadsheets")
    if (sheet_range != ''):
        sheet_range = '!'+sheet_range

    response = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=sheet_name+sheet_range
    ).execute()
    return response

# Complementary functions

def __get_column_name(n):
    """Given a numbers returns the name of a column following
        the known spreadsheet naming: A, B, C, D, ..., AA, AB.

    Args:
        n (int): number of column you want to retrieve

    Returns:
        str: The letter of the desired column. Index 0 corresponds to `A`, and 25 corresponds to `Z`
    """
	
    result = ''
 
    while n > 0:
        
        index = (n - 1) % 26
        result += chr(index + ord('A'))
        n = (n - 1) // 26
    return result[::-1]


def __get_range_column_names(r):
    output = []
    for i in range(1,r+1):
        output.append(__get_column_name(i))
    return output
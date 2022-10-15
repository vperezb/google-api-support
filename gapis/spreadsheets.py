import pandas as pd

from GoogleApiSupport import auth

"""A set of functions to interact with Google Spreadsheets. 
Sales-wise the product is called "sheets" but I'm modifying the naming
because it will help make the library unambiguous. As the entity "sheets" 
inside the API its use for each of the sheets (pages) of the spreadsheet (document).
https://www.google.com/intl/ca/sheets/about/

Naming convention:
    `spreadsheet` : The file, the full document. Its identifier it's the 
        `spreadsheet_id` and has its `spreadsheet_name`. Can be multiple spreadsheets with
        the same name as it does not represent anything, it's just another attribute.
    `sheet` : Each of the pages of a `spreadsheet`. The `sheet_name` is both the
        identifier and the "user friendly name". Because of that must be unique 
        within a spreadsheet.
"""

def get_sheet_info(sheet_id, include_grid_data=False):
    """Returns an spreadsheet info object

    Args:
        sheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters
        include_grid_data (bool): Passed to False, the function does not query the spreadsheet data, only the document information.
    Returns:
        dict: Object with a lot of sheet information such title, url, colors, alignment and much more.
    """
    service = auth.get_service("spreadsheets")
    response = service.spreadsheets().get(spreadsheetId=sheet_id, includeGridData=include_grid_data).execute()
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


def add_sheet_to_spreadsheet(sheet_id, sheet_name):
    """Adds a new page to an existing spreadsheet.

    Args:
        sheet_id (str): The objective spreadsheet id.
        sheet_name (str): The desired name for the new sheet.

    Returns:
        dict: Full response object from the Google API
    """

    service = auth.get_service("spreadsheets")
    
    data = {'requests': [
        {
            'addSheet':{
                'properties':{'title': sheet_name}
            }
        }
    ]}

    response = service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body=data).execute()
    #SHEET_ID = res['replies'][0]['addSheet']['properties']['sheet_id']
    return response


def change_sheet_title(newFileName, fileId):
    """Updates spreadsheet title.

    Args:
        newFileName (str): _description_
        fileId (str): The id from the Spreadsheet. Long string with letters, numbers and characters
    """
    service = auth.get_service("spreadsheets")

    body = {
        "requests": [{
            "updateSpreadsheetProperties": {
                "properties": {"title": newFileName},
                "fields": "title"
            }
        }]
    }

    service.spreadsheets().batchUpdate(
        spreadsheetId=fileId,
        body=body
    ).execute()

    return


def pandas_to_sheet(sheet_id, page_name, df, starting_cell='A1'):
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
        _type_: _description_
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

        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheet_id,
            body=body
        ).execute()

        return 'True'

    except Exception as e:
        print(e)



def get_sheet_names(sheet_id):
    """Get the names of the sheets in a spreadsheet.

    Args:
        sheet_id (str): The id from the Spreadsheet. Long string with letters, numbers and characters

    Returns:
        list: A list of the names of the sheets.
    """
    response = get_sheet_info(sheet_id)
    return [a['properties']['title'] for a in response['sheets']]


def get_sheet_charts(spreadsheet_id, sheet_name):
    """Returns a list of the charts in a specific sheet

    Args:
        spreadsheet_id (str): Id of the desired document
        sheet_name - Name of the desired page 'Hoja1'

    Returns:
        list: returns a list of the charts.
    """
    sheet = get_sheet_info(spreadsheet_id)
    for sheet_page in sheet['sheets']:
        if sheet_page['properties']['title']==sheet_name:
            return sheet_page['charts']


def sheet_to_pandas(spreadsheet_id, sheet_name='', sheet_range='', index='', has_header=True ):
    """spreadsheet_id - Id of the desired document
        sheet_name - Name of the desired page 'Hoja1' (by default: first page)
        sheet_range - Range of the desired info 'A1:C6' (optional) (by default: WHOLE PAGE)
        index - column you want to be the index of the resulting dataframe (optional) (by default: none of the columns is set as index)

    Args:
        spreadsheet_id (_type_): Id of the desired document
        sheet_name (str, optional): Name of the desired page 'Hoja1'. (by default: first page). Defaults to ''.
        sheet_range (str, optional): Range of the desired info 'A1:C6'.(by default: WHOLE PAGE). Defaults to ''.
        index (str, optional): column you want to be the index of the resulting dataframe (by default: none of the columns is set as index). Defaults to ''.
        has_header (bool, optional): If the sheet has a header. If not, a dummy header is created. Defaults to True.

    Returns:
        pd.DataFrame: The output dataframe.
    """
    service = auth.get_service("spreadsheets")
    if (sheet_range != ''):
        sheet_range = '!'+sheet_range

    newresult = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        valueRenderOption='FORMATTED_VALUE',
        range=sheet_name+sheet_range
    ).execute()

    if has_header:
        headers = newresult['values'].pop(0)
    else:
        max_len = 0 
        for row in newresult['values']:
            if len(row) > max_len:
                max_len = len(row)
        headers = __get_range_column_names(max_len)

    if (index == ''):
        return pd.DataFrame(newresult['values'], columns=headers)
    else:
        return pd.DataFrame(newresult['values'], columns=headers).set_index(index, drop=False)


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

    newresult = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=sheet_name+sheet_range
    ).execute()

# Complementary functions

def __get_column_name(n):

	# initialize output string as empty
	result = ''

	while n > 0:

		# find the index of the next letter and concatenate the letter
		# to the solution

		# here index 0 corresponds to `A`, and 25 corresponds to `Z`
		index = (n - 1) % 26
		result += chr(index + ord('A'))
		n = (n - 1) // 26

	return result[::-1]

def __get_range_column_names(r):
    output = []
    for i in range(r):
        output.append(__get_column_name(i))
    return output
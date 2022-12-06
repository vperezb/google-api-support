import pandas as pd
import logging

from GoogleApiSupport import auth


logging.warning("""
            [DeprecationWarning] sheets module will be deprecated in favor to spreadsheets.
            1 - modify the import from `sheets` to `spreadsheets`. (from GoogleApiSupport import spreadsheets)
            2 - Some functions are been renamed to make it more easy to read. If you have a name error check for the new function's name""")
    

def get_sheet_info(sheetId, includeGridData=False):
    """Returns an spreadsheet info object

    Args:
        sheetId (str): The id from the Spreadsheet. Long string with letters, numbers and characters
        includeGridData (bool): Passed to False, the function does not query the spreadsheet data, only the document information.
    Returns:
        dict: Object with a lot of sheet information such title, url, colors, alignment and much more.
    """
    logging.warning('module sheets now is named spreadsheets and this function `get_sheet_info` renamed to `get_info`')
    service = auth.get_service("sheets")
    response = service.spreadsheets().get(spreadsheetId=sheetId, includeGridData=includeGridData).execute()
    return response


def create(title):
    """Creates in your root user folder a file type spreadsheet with a single sheet. Use move file from drive api to move it to the desired final location.

    Args:
        title (str): The desired title for the created sheet.

    Returns:
        string: The id from the created file
    """
    service = auth.get_service("sheets")
    spreadsheet = {
        'properties': {
            'title': title
        }
    }
    spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                                fields='spreadsheetId') \
        .execute()
    print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
    return spreadsheet.get('spreadsheetId')


def add_sheet_to_spreadsheet(sheetId, newSheetName):
    """Adds a new page to an existing spreadsheet.

    Args:
        sheetId (str): The objective spreadsheet id.
        newSheetName (str): The desired name for the new sheet.

    Returns:
        dict: Full response object from the Google API
    """
    logging.warning('module sheets now is named spreadsheets and this function `add_sheet_to_spreadsheet` renamed to `add_sheet`')

    service = auth.get_service("sheets")
    
    data = {'requests': [
        {
            'addSheet':{
                'properties':{'title': newSheetName}
            }
        }
    ]}

    response = service.spreadsheets().batchUpdate(spreadsheetId=sheetId, body=data).execute()
    return response


def change_sheet_title(newFileName, fileId):
    """Updates spreadsheet title.

    Args:
        newFileName (str): _description_
        fileId (str): The id from the Spreadsheet. Long string with letters, numbers and characters
    """
    logging.warning('module sheets now is named spreadsheets and this function `change_sheet_title` renamed to `change_title`')
    service = auth.get_service("sheets")

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


def pandas_to_sheet(sheetId, pageName, df, startingCell='A1'):
    """Uploads a pandas.dataframe to the desired page of a google sheets sheet.
    SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET.
    Aditionally, pass a list with the new names of the columns.    
    Data must be utf-8 encoded to avoid errors.

    Args:
        sheetId (str): The id from the Spreadsheet. Long string with letters, numbers and characters
        pageName (str): The target name of the page to upload the DataFrame
        df (pd.DataFrame): The dataframe to be uploaded.
        startingCell (str, optional): The cell in the sheet where the data will be uploaded. Defaults to 'A1'.

    Returns:
        _type_: _description_
    """

    service = auth.get_service("sheets")

    df.fillna(value=0, inplace=True)
    columnsList = df.columns.tolist()
    valuesList = df.values.tolist()

    try:
        data = [
            {
                'range': pageName+'!'+startingCell,
                'values': [columnsList] + valuesList
            },
        ]

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': data
        }

        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=sheetId,
            body=body
        ).execute()

        return 'True'

    except Exception as e:
        print(e)



def get_sheet_names(sheetId):
    """Get the names of the sheets in a spreadsheet.

    Args:
        sheetId (str): The id from the Spreadsheet. Long string with letters, numbers and characters

    Returns:
        list: A list of the names of the sheets.
    """
    response = get_sheet_info(sheetId)
    return [a['properties']['title'] for a in response['sheets']]


def get_sheet_charts(spreadsheetId, sheetName):
    """Returns a list of the charts in a specific sheet

    Args:
        spreadsheetId (str): Id of the desired document
        sheetName - Name of the desired page 'Hoja1'

    Returns:
        list: returns a list of the charts.
    """
    sheet = get_sheet_info(spreadsheetId)
    for sheet_page in sheet['sheets']:
        if sheet_page['properties']['title']==sheetName:
            return sheet_page['charts']


def sheet_to_pandas(spreadsheetId, sheetName='', sheetRange='', index='', has_header=True ):
    """spreadsheetId - Id of the desired document
        sheetName - Name of the desired page 'Hoja1' (by default: first page)
        sheetRange - Range of the desired info 'A1:C6' (optional) (by default: WHOLE PAGE)
        index - column you want to be the index of the resulting dataframe (optional) (by default: none of the columns is set as index)

    Args:
        spreadsheetId (_type_): Id of the desired document
        sheetName (str, optional): Name of the desired page 'Hoja1'. (by default: first page). Defaults to ''.
        sheetRange (str, optional): Range of the desired info 'A1:C6'.(by default: WHOLE PAGE). Defaults to ''.
        index (str, optional): column you want to be the index of the resulting dataframe (by default: none of the columns is set as index). Defaults to ''.
        has_header (bool, optional): If the sheet has a header. If not, a dummy header is created. Defaults to True.

    Returns:
        pd.DataFrame: The output dataframe.
    """
    logging.warning('module sheets now is named spreadsheets and this function `sheet_to_pandas` renamed to `download_sheet_to_pandas`')
    service = auth.get_service("sheets")
    if (sheetRange != ''):
        sheetRange = '!'+sheetRange

    newresult = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId,
        valueRenderOption='FORMATTED_VALUE',
        range=sheetName+sheetRange
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


def clear_sheet(spreadsheetId, sheetName, sheetRange=''):
    """Deletes the data in the selected area

    Args:
        spreadsheetId (str): _description_
        sheetName (str): _description_
        sheetRange (str, optional): _description_. Defaults to ''.
    """
    service = auth.get_service("sheets")
    if (sheetRange != ''):
        sheetRange = '!'+sheetRange

    newresult = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheetId,
        range=sheetName+sheetRange
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
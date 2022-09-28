import pandas as pd

from GoogleApiSupport import auth


def create(title):
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
    '''Adds a new page.'''

    service = auth.get_service("sheets")
    
    data = {'requests': [
        {
            'addSheet':{
                'properties':{'title': newSheetName}
            }
        }
    ]}

    response = service.spreadsheets().batchUpdate(spreadsheetId=sheetId, body=data).execute()
    #SHEET_ID = res['replies'][0]['addSheet']['properties']['sheetId']
    return response


def change_sheet_title(newFileName, fileId):
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
    '''
    Uploads a pandas.dataframe to the desired page of a google sheets sheet.
    SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET.
    Aditionally, pass a list with the new names of the columns.    
    Data must be utf-8 encoded to avoid errors.
    '''

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

def get_sheet_info(sheetId):
    service = auth.get_service("sheets")
    response = service.spreadsheets().get(spreadsheetId=sheetId).execute()
    return response


def get_sheet_names(sheetId):
    response = get_sheet_info(sheetId)
    return [a['properties']['title'] for a in response['sheets']]


def get_sheet_charts(spreadsheetId, sheetName):
    sheet = get_sheet_info(spreadsheetId)
    for sheet_page in sheet['sheets']:
        if sheet_page['properties']['title']==sheetName:
            return sheet_page['charts']


def sheet_to_pandas(spreadsheetId, sheetName='', sheetRange='', index='', has_header=True ):
    '''
    PARAMETERS:
        service - Api service
        spreadsheetId - Id of the desired document
        sheetName - Name of the desired page 'Hoja1' (optional) (by default: first page)
        sheetRange - Range of the desired info 'A1:C6' (optional) (by default: WHOLE PAGE)
        index - column you want to be the index of the resulting dataframe (optional) (by default: none of the columns is set as index)
    '''
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
        headers = get_range_column_names(max_len)

    if (index == ''):
        return pd.DataFrame(newresult['values'], columns=headers)
    else:
        return pd.DataFrame(newresult['values'], columns=headers).set_index(index, drop=False)


def clear_sheet(spreadsheetId, sheetName, sheetRange=''):
    service = auth.get_service("sheets")
    if (sheetRange != ''):
        sheetRange = '!'+sheetRange

    newresult = service.spreadsheets().values().clear(
        spreadsheetId=spreadsheetId,
        range=sheetName+sheetRange
    ).execute()

# Complementary functions

def get_column_name(n):

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

def get_range_column_names(r):
    output = []
    for i in range(r):
        output.append(get_column_name(i))
    return output
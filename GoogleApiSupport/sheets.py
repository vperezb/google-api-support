import pandas as pd


def change_sheet_title(service, newFileName, fileId):
    
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

def pandas_to_sheet(service, sheetId, pageName, df):
    
    '''
    Uploads a pandas.dataframe to the desired page of a google sheets sheet.
    SERVICE ACCOUNT MUST HAVE PERMISIONS TO WRITE IN THE SHEET.
    Aditionally, pass a list with the new names of the columns.    
    Data must be utf-8 encoded to avoid errors.
    '''
    
    df.fillna(value = 0, inplace=True)
    columnsList = df.columns.tolist()
    valuesList = df.values.tolist()

    try:
        data = [
            {
                'range': pageName+'!A1',
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
    
    except e as Exception:
        print (e)

def get_sheet_names(sheets_service,sheetId):
    response = sheets_service.spreadsheets().get(spreadsheetId=sheetId).execute()
    return [ a['properties']['title'] for a in response['sheets']]

def sheet_to_pandas(service, spreadsheetId ,sheetName='',sheetRange='',index=''):
    '''
    PARAMETERS:
        service - Api service
        spreadsheetId - Id of the desired document
        sheetName - Name of the desired page 'Hoja1' (optional) (by default: first page)
        sheetRange - Range of the desired info 'A1:C6' (optional) (by default: WHOLE PAGE)
        index - column you want to be the index of the resulting dataframe (optional) (by default: none of the columns is set as index)
    '''
    
    if (sheetRange != ''): sheetRange='!'+sheetRange
        
    newresult = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId,
        valueRenderOption='FORMATTED_VALUE', 
        range = sheetName+sheetRange
    ).execute()
        
    headers = newresult['values'].pop(0)
    
    if (index == ''): 
        return pd.DataFrame(newresult['values'],columns = headers)
    else:
        return pd.DataFrame(newresult['values'],columns = headers).set_index(index, drop=False)

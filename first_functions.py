from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http
import pandas as pd
import os
import configparser

def get_configs(CONFIG_PATH):
    parserconfig = configparser.ConfigParser()
    parserconfig.read(os.path.join("./" , CONFIG_PATH))
    return parserconfig
	
def start_service(Config, SERVICE_NAME):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        Config.get("Credentials", 'secretsPath'), 
        scopes='https://www.googleapis.com/auth/' + Config.get("Services", SERVICE_NAME)
    )
    service = build(
        SERVICE_NAME,
        Config.get("Services", "v_" + SERVICE_NAME),
        http=credentials.authorize(Http()),
        cache_discovery=False
    )
    return service

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

def pandas_to_sheet(service, sheetId, pageName, columnsList ,valuesList):

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
        return e

def get_sheet_names(sheets_service,sheetId):
    response = sheets_service.spreadsheets().get(spreadsheetId=sheetId).execute()
    return [ a['properties']['title'] for a in response['sheets']]

def sheet_to_pandas(service, spreadsheetId ,sheetName='',sheetRange='',index=''):
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
    
    #PARAMETERS:
        #service - Api service
        #spreadsheetId - Id of the desired document
        #sheetName - Name of the desired page 'Hoja1' (optional) (by default: first page)
        #sheetRange - Range of the desired info 'A1:C6' (optional) (by default: WHOLE PAGE)
        #index - column you want to be the index of the resulting dataframe (optional) (by default: none of the columns is set as index)
    

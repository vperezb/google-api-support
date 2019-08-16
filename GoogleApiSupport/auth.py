import os
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

import logging

service_credentials_path = [os.path.join(os.environ['HOME'], '.credentials', 'service_credentials.json'), '.credentials/service_credentials.json']

API_REFERENCES = {
    'slides': {
        'scope':'https://www.googleapis.com/auth/presentations',
        'build':'slides',
        'version': 'v1'},
    'drive': {
        'scope':'https://www.googleapis.com/auth/drive',
        'build':'drive',
        'version': 'v3'},
    'sheets':{
        'scope':'https://www.googleapis.com/auth/spreadsheets',
        'build':'sheets',
        'version': 'v4'}
}

def get_service(service_type):
    service = None
    for file in service_credentials_path:
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                file,
                scopes= API_REFERENCES[service_type]['scope']
            )
        
            service = build(
                API_REFERENCES[service_type]['build'],
                API_REFERENCES[service_type]['version'],
                http=credentials.authorize(Http()),
                cache_discovery=False
            )
            logging.info('Using credentials found in ' + file)
        except Exception as e:
            continue
    if not service:
        logging.error(' UNABLE TO RETRIEVE CREDENTIALS | Expected credential paths: ' + ', '.join(service_credentials_path) + ' | More info in project Documentation folder setup_credentials.md file')
    return service

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

SERVICE_CREDENTIALS = '.credentials/service_credentials.json'

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
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_CREDENTIALS,
        scopes= API_REFERENCES[service_type]['scope']
    )
    service = build(
        API_REFERENCES[service_type]['build'],
        API_REFERENCES[service_type]['version'],
        http=credentials.authorize(Http()),
        cache_discovery=False
    )
    return service
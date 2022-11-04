import os
import logging
from oauth2client.client import _raise_exception_for_reading_json

#service account
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

#oauth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from GoogleApiSupport import apis


def get_service(api_name, service_credentials_path=None, oauth_credentials_path=None, additional_apis=[]):
    """
    First section of this function checks credentials for service accounts. If no service account credentials are present,
    it will then check for OAuth credentials. If no OAuth creds found, it will error. 
    """
    service_credentials_path = get_service_credentials_path(service_credentials_path)
    service = None
    scopes = apis.get_api_config(api_name)['scope']
    if additional_apis:
        scopes = [scopes]
        for additional_api_name in additional_apis:
            scopes.append(apis.get_api_config(additional_api_name)['scope'])
    
    if service_credentials_path: 

        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            service_credentials_path,
            scopes=scopes
        )

        service = build(apis.get_api_config(api_name)['build'],
            apis.get_api_config(api_name)['version'],
            http=credentials.authorize(Http()),
            cache_discovery=False
        )

        return service
       
    elif not service_credentials_path: 
        oauth_credentials_path = get_oauth_credentials_path(oauth_credentials_path)

        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    oauth_credentials_path, scopes)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        service = build(apis.get_api_config(api_name)['build'],
        apis.get_api_config(api_name)['version'],
        credentials=creds)
        if not service:
            logging.error(' UNABLE TO RETRIEVE CREDENTIALS | Expected credential paths: ' + ', '.join(
                oauth_credentials_path) + ' | More info in project Documentation folder setup_credentials.md file')

        return service

def get_service_credentials_path(service_credentials_path=None):
    if service_credentials_path:
        service_credentials_path = service_credentials_path
        logging.info('Trying to use credentials from ' + 'Method 0: Path from function argument | ' + service_credentials_path)
    elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        service_credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        logging.info('Trying to use credentials from ' + 'Method 1: Environment variable GOOGLE_APPLICATION_CREDENTIALS | ' + service_credentials_path)
    elif os.environ.get('SERVICE_CREDENTIALS_PATH'): ## TO DO: DELETE - DEPRECATED
        service_credentials_path = os.environ['SERVICE_CREDENTIALS_PATH']
        logging.warning('Trying to use credentials from ' +  'Method 2 (deprecated): Environment variable SERVICE_CREDENTIALS_PATH | ' + service_credentials_path)
    else:
        service_credentials_path = os.path.join(os.path.expanduser('~'), '.credentials', 'service_credentials.json')
        logging.info('Tying to use credentials from ' + 'Method 3: Default path for credentials ~/.credentials/service_credentials.json | ' + service_credentials_path + ' | Nor path passed neither environment variables, take a look into `docs/setup_credentials.md` file')      
      
    if (os.path.isfile(service_credentials_path)):
        logging.info('Found file credentials in' + service_credentials_path)
        return service_credentials_path

        
        
        
def get_oauth_credentials_path(oauth_credentials_path=None):
    if oauth_credentials_path:
        oauth_credentials_path = oauth_credentials_path
        logging.info('Trying to use credentials from ' + 'Method 0: Path from function argument | ' + oauth_credentials_path)
    elif os.environ.get('GOOGLE_OAUTH_CREDENTIALS'):
        oauth_credentials_path = os.environ['GOOGLE_OAUTH_CREDENTIALS']
        logging.info('Trying to use credentials from ' + 'Method 1: Environment variable GOOGLE_OAUTH_CREDENTIALS | ' + oauth_credentials_path)     
      
    if (os.path.isfile(oauth_credentials_path)):
        logging.info('Found file credentials in' + oauth_credentials_path)
        return oauth_credentials_path
    else:
        raise Exception('UNABLE TO FIND OAUTH OR SERVICE CREDENTIALS FILE | Environment variable not defined or file from provided path does not exist | More info in project docs folder setup_credentials.md file')

        


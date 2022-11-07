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


def get_service(api_name, service_credentials_path=None, 
                oauth_credentials_path=None, additional_apis=[]):
    """ First section of this function checks credentials for service accounts. 
        If no service account credentials are present, it will then check for OAuth credentials. 
        If no OAuth credentials found, it will return an exception. 


    Args:
        api_name (_type_): _description_
        service_credentials_path (_type_, optional): _description_. Defaults to None.
        oauth_credentials_path (_type_, optional): _description_. Defaults to None.
        additional_apis (list, optional): Some times a request needs access to multiple scopes.
            Here you can add as many as you want. Apis must be in apis.py file in order to be allowed.
            Defaults to [].

    Returns:
        Service object: Authenticated service to query against apis.
    """
    service_credentials_path = get_service_credentials_path(service_credentials_path)
    oauth_credentials_path = get_oauth_credentials_path(oauth_credentials_path)
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
        logging.info(f'Using authorisation via service_credentials found on `{service_credentials_path}`')
       
    elif not service_credentials_path and oauth_credentials_path:
        # we enable at once all the scopes needed when using the lib, otherwise we'll need to manage
        # deleting old token.json files when changing from one scope to the other
        scopes = apis.all_scopes()
        
        credentials = oauth_credentials_from_file(oauth_credentials_path, scopes)

        service = build(apis.get_api_config(api_name)['build'],
                        apis.get_api_config(api_name)['version'],
                        credentials=credentials
                        )
        logging.info(f'Using authorisation via oauth_credentials found on `{oauth_credentials_path}`')
        
    elif not (service_credentials_path or oauth_credentials_path):
        raise Exception('UNABLE TO FIND OAUTH OR SERVICE CREDENTIALS FILE | \
                        Environment variable not defined or file from provided path does not exist | \
                        More info in project folder docs/setup_credentials.md')

    return service


def get_service_credentials_path(service_credentials_path=None):
    """This function manages the retrievement of the service credentials file, 
        trying first on the local path and then to the path set in the environment variable.

    Args:
        service_credentials_path (_type_, optional): The known location of a service credentials file. Defaults to None.

    Returns:
        str: Returns a string with the path from a file unless the file is not found, then returns None. 
    """
    folder_service_credentials_path = os.path.join(os.path.expanduser('~'), '.credentials', 'service_credentials.json')
    if service_credentials_path:
        service_credentials_path = service_credentials_path
        logging.info('Trying to use credentials from ' + 'Method 0: Path from function argument | ' + service_credentials_path)
    elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        service_credentials_path = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        logging.info('Trying to use credentials from ' + 'Method 1: Environment variable GOOGLE_APPLICATION_CREDENTIALS | ' + service_credentials_path)
    elif os.environ.get('SERVICE_CREDENTIALS_PATH'): ## TO DO: DELETE - DEPRECATED
        service_credentials_path = os.environ['SERVICE_CREDENTIALS_PATH']
        logging.warning('Trying to use credentials from ' +  'Method 2 (deprecated): Environment variable SERVICE_CREDENTIALS_PATH | ' + service_credentials_path)
    elif os.path.isfile(folder_service_credentials_path):
        service_credentials_path = folder_service_credentials_path
        logging.info('Tying to use credentials from ' + 'Method 3: Default path for credentials ~/.credentials/service_credentials.json | ' + service_credentials_path + ' | Nor path passed neither environment variables, take a look into `docs/setup_credentials.md` file')      
    else :
        return None
    
    if (os.path.isfile(service_credentials_path)):
        logging.info('Found file credentials in' + service_credentials_path)
        return service_credentials_path     
        
        
def get_oauth_credentials_path(oauth_credentials_path=None):
    """This function manages the retrievement of the oauth credentials file, 
        trying first on the local path and then to the path set in the environment variable.

    Args:
        oauth_credentials_path (_type_, optional): _description_. Defaults to None.

    Returns:
        str: Returns a string with the path from a file unless the file is not found, then returns None.
    """
    if oauth_credentials_path:
        oauth_credentials_path = oauth_credentials_path
        logging.info('Trying to use credentials from ' + 'Method 0: Path from function argument | ' + oauth_credentials_path)
    elif os.environ.get('GOOGLE_OAUTH_CREDENTIALS'):
        oauth_credentials_path = os.environ['GOOGLE_OAUTH_CREDENTIALS']
        logging.info('Trying to use credentials from ' + 'Method 1: Environment variable GOOGLE_OAUTH_CREDENTIALS | ' + oauth_credentials_path)     
    else: 
        return None
    if (os.path.isfile(oauth_credentials_path)):
        logging.info('Found file credentials in' + oauth_credentials_path)
        return oauth_credentials_path
    

def oauth_credentials_from_file(oauth_credentials_path, scopes, local_credentials_path = 'token.json'):
    """The file token.json stores the user's access and refresh tokens, 
        and is created automatically when the authorization flow completes for the first time.

    Args:
        oauth_credentials_path (str): The path from the credentials oauth file.
        scopes (list): The list of scopes that want to be used, all of those 
        will need to be cheched on the window that opens to authorise.
        local_credentials_path (str, optional): Once authorised, an authorisation file
        is saved locally so you don't need to authorise on later requests. Defaults to 'token.json'.

    Returns:
        Credentials object:
    """
    credentials = None
    
    if os.path.exists(local_credentials_path):
        credentials = Credentials.from_authorized_user_file(local_credentials_path, scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                oauth_credentials_path, scopes)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(local_credentials_path, 'w') as token:
            token.write(credentials.to_json())
    return credentials
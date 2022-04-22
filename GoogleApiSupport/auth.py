import os
import logging
from oauth2client.client import _raise_exception_for_reading_json

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

from GoogleApiSupport import apis


def get_service(api_name, service_credentials_path=None, additional_apis=[]):
    service_credentials_path = get_service_credentials_path(service_credentials_path)

    service = None
    scopes = apis.get_api_config(api_name)['scope']
    if additional_apis:
        scopes = [scopes]
        for additional_api_name in additional_apis:
            scopes.append(apis.get_api_config(additional_api_name)['scope'])

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        service_credentials_path,
        scopes=scopes
    )

    service = build(apis.get_api_config(api_name)['build'],
        apis.get_api_config(api_name)['version'],
        http=credentials.authorize(Http()),
        cache_discovery=False
    )

    if not service:
        logging.error(' UNABLE TO RETRIEVE CREDENTIALS | Expected credential paths: ' + ', '.join(
            service_credentials_path) + ' | More info in project Documentation folder setup_credentials.md file')
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
    else:
        raise Exception('UNABLE TO FIND CREDENTIALS FILE | Environment variable not defined or file from provided path does not exist | More info in project docs folder setup_credentials.md file')


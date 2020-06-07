import os
import logging

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http

from GoogleApiSupport import apis


def get_service(api_name, service_credentials_path=None):
    if service_credentials_path == None:
        service_credentials_path = get_service_credentials_path()

    service = None

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        service_credentials_path,
        scopes=apis.api_configs(api_name)['scope']
    )

    service = build(apis.api_configs(api_name)['build'],
        apis.api_configs(api_name)['version'],
        http=credentials.authorize(Http()),
        cache_discovery=False
    )

    logging.info('Using credentials found in ' + file)

    if not service:
        logging.error(' UNABLE TO RETRIEVE CREDENTIALS | Expected credential paths: ' + ', '.join(
            service_credentials_path) + ' | More info in project Documentation folder setup_credentials.md file')
    return service


def get_service_credentials_path():
    if os.environ.get('SERVICE_CREDENTIALS_PATH')
    service_credentials_path = os.environ['SERVICE_CREDENTIALS_PATH']
    logging.info('Using credentials from ' + service_credentials_path)
    if os.path.isfile(service_credentials_path):
            logging.info('Found file credentials in' +
                         service_credentials_path)
        else:
            raise.Exception('File in SERVICE_CREDENTIALS_PATH not found')
    elif os.path.isfile(os.path.join(os.path.expanduser('~'), '.credentials', 'service_credentials.json')):
        service_credentials_path = os.path.join(os.path.expanduser('~'), '.credentials', 'service_credentials.json')
        logging.info('Using credentials from ' + service_credentials_path)
    elif os.path.isfile(os.path.join('.credentials','service_credentials.json')):
        service_credentials_path = os.path.join('.credentials','service_credentials.json')
    else:
        raise.Exception(
            'UNABLE TO FIND CREDENTIALS FILE | More info in project Documentation folder setup_credentials.md file'
        )
    return service_credentials_path

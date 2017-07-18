from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
from httplib2 import Http
import pandas as pd
import os
import configparser

def getConfigs(CONFIG_PATH):
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

    

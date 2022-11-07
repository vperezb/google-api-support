# Credentials
import os
ROOT_DIR=os.getcwd()
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".credentials/service_credentials.json")
os.environ['GOOGLE_OAUTH_CREDENTIALS'] = os.path.join(ROOT_DIR, ".oauth_credentials/credentials.json")

# Doing this to import local versions
import sys
sys.path.append('../GoogleApiSupport')
from GoogleApiSupport import apis, auth

apis.api_configs

service = auth.get_service('tasks')

results = service.tasklists().list(maxResults=10).execute()
items = results.get('items', [])
for item in items:
    print(u'{0} ({1})'.format(item['title'], item['id']))
    
task_list = service.tasklists().get(tasklist='MTMyNDg3MzI1NzkyMDMwNzc3NTM6MDow').execute()

tasks = service.tasks().list(tasklist='MTMyNDg3MzI1NzkyMDMwNzc3NTM6MDow').execute()

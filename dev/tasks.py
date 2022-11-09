import datetime as dt
from dateutil import parser
from apiclient import errors

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


class GoogleTasks:
    service = auth.get_service('tasks')
    
    def __init__(self):
        self.__tasklists = self.service.tasklists().list(maxResults=999999999).execute()
        tasklists_ids = [list.get('id') for list in self.__tasklists.get('items')]
        self.__tasks = dict()
        for id in tasklists_ids:
            tasks = self.service.tasks().list(tasklist=id,
                                              completedMax=None, completedMin=None,
                                              dueMax=None, dueMin=None,
                                              maxResults=999999999, pageToken=None,
                                              showCompleted=True, showDeleted=True,
                                              showHidden=True, updatedMin=None).execute()
            self.__tasks.update({id:tasks.get('items')})
    
    @property
    def tasklists(self):
        lists = self.__tasklists.get('items')
        return {list.get('id'):{key:value for key, value in list.items() if key != 'id'} for list in lists}

    @property
    def tasklists_titles(self):
        return {value.get('title'):key for key, value in self.tasklists.items()}
    
    @property
    def tasks_titles(self):
        all_tasks = dict()
        for tasklist, tasks in self.__tasks.items():
            for task in tasks:
                task_id = task.get('id')
                task_title = task.get('title')
                all_tasks.update({task_title:{'task_id':task_id, 'tasklist_id':tasklist}})
        return all_tasks
    
    def get_tasks(self, tasklist):
        tasklist_id = self.tasklists_titles.get(tasklist)
        if tasklist_id is None:
            raise ValueError('tasklist needs to be the name of a task list.')
                
    def add_task(self, tasklist, parent=None, previous=None, **kwargs):
        """Add new task in tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/insert
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasks#Task

        Args:
            tasklist (str): Name of the tasklist where to insert task.
            parent (str, optional): Parent task identifier. Defaults to None.
            previous (str, optional): Previous sibling task identifier. Defaults to None.

        Returns:
            str: ID of the newly created task.
        """
        
        tasklist_id = self.tasklists_titles.get(tasklist)
        body = kwargs
        try: 
            response = service.tasks().insert(tasklist=tasklist_id, 
                                            parent=parent,
                                            previous=previous,
                                            body=body).execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        print('New task with ID {} created.'.format(response.get('id')))
        return response.get('id')
    
    def update_task(self, task, **kwargs):
        """Update a task.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/update
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasks#Task

        Args:
            task (str): Title of the task to update.

        Returns:
            dict: Response of API call.
        """
        
        task_info = self.__tasks_titles.get(task)
        if task_info is None:
            raise ValueError('There is no task with this title.')
        
        body = kwargs
        try: 
            response = service.tasks().update(tasklist=task_info.get('tasklist_id'), 
                                              task=task_info.get('task_id'),
                                              body=body).execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        print('Task {} successfully updated.'.format(task))
        return response
    
    def delete_task(self, task):
        task_info = self.__tasks_titles.get(task)
        if task_info is None:
            raise ValueError('There is no task with this title.')

        try: 
            response = service.tasks().delete(tasklist=task_info.get('tasklist_id'),
                                              task=task_info.get('task_id')).execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        print('Task {} successfully deleted.'.format(task))
        
    
    
            
        
        
body = {'title':title}
body = {'requests':requests}
        
response = service.tasks().insert(tasklist='MDQ5OTQxMDY3NDQyMDg1MTc5MjI6MDow', body=body).execute()
response.get('id')
        
        
response = service.tasks().update()     
    
gt = GoogleTasks()    

gt._GoogleTasks__tasks.get('MDQ5OTQxMDY3NDQyMDg1MTc5MjI6MDow')

all_tasks = dict()
for tasklist, tasks in gt._GoogleTasks__tasks.items():
    for task in tasks:
        task_id = task.get('id')
        task_name = task.get('title')
        all_tasks.update({task_name:{'task_id':task_id, 'tasklist_id':tasklist}})





{value.get('title'):key for key, value in gt.tasklists.items()}

tasklists_ids = [list.get('id') for list in gt.__tasklists.get('items')]
self.__tasks = dict()
for id in tasklists_ids:
    tasks = self.service.tasks().list(tasklist=id,
                                        completedMax=None, completedMin=None,
                                        dueMax=None, dueMin=None,
                                        maxResults=999999999, pageToken=None,
                                        showCompleted=True, showDeleted=True,
                                        showHidden=True, updatedMin=None).execute()
    self.__tasks.update({id:tasks})




items = results.get('items', [])
for item in items:
    print(u'{0} ({1})'.format(item['title'], item['id']))
    
    
list_id = 'MDQ5OTQxMDY3NDQyMDg1MTc5MjI6MDow'
task_list = service.tasklists().get(tasklist=list_id).execute()



completed_max=None
completed_min=None
due_max=None
due_min=None
max_results=float('inf')
page_token=None
show_completed=True
show_deleted=False
show_hidden=False
updated_min=None



tasks = service.tasks().list(tasklist=list_id, 
                             completedMax=completed_max, completedMin=completed_min,
                             dueMax=due_max, dueMin=due_min,
                             maxResults=max_results, pageToken=page_token,
                             showCompleted=show_completed, showDeleted=show_deleted,
                             showHidden=show_hidden, updatedMin=updated_min).execute()


len(tasks.get('items'))

# all datetime related things can either be datetime object or string

due_min = '2022-10-07'



date_params = {'completed_max':completed_max, 'completed_min':completed_min, 
               'due_max':due_max, 'due_min':due_min, 'updated_min':updated_min}

for key, value in date_params.items():
    if isinstance(value, str):
        date_params[key] = parser.parse(value)
    elif isinstance(value, dt.datetime):
        pass
    elif isinstance(value, dt.date):
        pass
    elif value == None:
        pass
    else:
        raise ValueError('{} can either be None, a date/datetimestring or a date/datetime object.')
    

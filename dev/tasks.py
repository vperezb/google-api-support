from dev.utils import to_rfc339
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

class GoogleTasks:
    service = auth.get_service('tasks')
        
    def __init__(self):
        self.__tasklists = self._update_tasklists_info()
        self.__tasks = self._update_tasks_info()
    
    @property
    def tasklists(self):
        lists = self.__tasklists.get('items')
        return {list.get('id'):{key:value for key, value in list.items() if key != 'id'} for list in lists}
    
    @property
    def tasks(self):
        all_tasks = dict()
        for tasklist, tasks in self.__tasks.items():
            for task in tasks:
                task_id = task.get('id')
                task = {key:value for key, value in task.items() if key != 'id'}
                task['tasklist_id'] = tasklist
                all_tasks.update({task_id:task})
        return all_tasks
    
    # Tasklist methods
            
    def create_tasklist(self, **kwargs):
        """Add new tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasklists/insert
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasklists#TaskList
        If additional arguments include dates or datetimes, a parser will be used to transform them to RFC 3339 format. Add "dayfirst" and/or "yearfirst" to change the default behavior, as described here: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parserinfo.
        """
        
        body = self._prepare_request_body(arguments=kwargs)
        try: 
            response = self.service.tasklists().insert(body=body).execute()
            print('New tasklist with ID {} created.'.format(response.get('id')))
            self.__tasklists = self._update_tasklists_info()
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return response.get('id')        
        
    def update_tasklist(self, tasklist, **kwargs):
        """Update a tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasklists/update
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasklists#TaskList
        If additional arguments include dates or datetimes, a parser will be used to transform them to RFC 3339 format. Add "dayfirst" and/or "yearfirst" to change the default behavior, as described here: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parserinfo.
        
        Args:
            tasklist (str): Title of the tasklist.
        """

        tasklist_id = self._check_tasklist(tasklist)
        body = self._prepare_request_body(arguments=kwargs, tasklist_id=tasklist_id)
        try: 
            response = self.service.tasklists().update(tasklist=tasklist_id, body=body).execute()
            print('Tasklist "{}" successfully updated.'.format(tasklist))
            self.__tasklists = self._update_tasklists_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return response
    
    def delete_tasklist(self, tasklist):
        """Update a tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasklists/update
        It will first check if the argument tasklist is an ID and afterwards if it's a title.

        Args:
            tasklist (str): ID or title of a tasklist.
        """
        
        tasklist_id = self._check_tasklist(tasklist)
        try: 
            response = self.service.tasklists().delete(tasklist=tasklist_id).execute()
            print('Tasklist "{}" successfully deleted.'.format(tasklist)) 
            self.__tasklists = self._update_tasklists_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)  
            
    def get_tasks(self, tasklist,
                  completed_max=None, completed_min=None,
                  due_max=None, due_min=None,
                  max_results=20, page_token=None,
                  show_completed=True, show_deleted=False,
                  show_hidden=False, updated_min=None,
                  dayfirst=False, yearfirst=False):
        """Get list of specific tasks in a tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/list
        Datetime parameters can be given as a string or a date/datetime object. For these a parser will be used to transform them to RFC 3339 format. Add "dayfirst" and/or "yearfirst" to change the default behavior, as described here: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parserinfo.

        Args:
            tasklist (str): ID or title of tasklist
            completed_max (str or datetime.date/datetime, optional): Upper bound for a task's completion date. Defaults to None.
            completed_min (str or datetime.date/datetime, optional): Lower bound for a task's completion date. Defaults to None.
            due_max (str or datetime.date/datetime, optional): Upper bound for a task's due date. Defaults to None.
            due_min (str or datetime.date/datetime, optional): Lower bound for a task's due date. Defaults to None.
            max_results (int, optional): Maximum number of task lists returned on one page. Defaults to 20.
            page_token (str, optional): Token specifying the result page to return.. Defaults to None.
            show_completed (bool, optional): Whether completed tasks are returned.  Defaults to True.
            show_deleted (bool, optional): Whether deleted tasks are returned. Defaults to False.
            show_hidden (bool, optional): Whether hidden tasks are returned. Defaults to False.
            updated_min (str or datetime.date/datetime, optional): Lower bound for a task's last modification time. Defaults to None.
            dayfirst (bool, optional): Whether to interpret the first value in an ambiguous 3-integer date as the day (True) or month (False). Defaults to False.
            yearfirst (bool, optional): Whether to interpret the first value in an ambiguous 3-integer date as the year. Defaults to False.

        Returns:
            list: List of dictionaries for tasks and their info.
        """
        
        tasklist_id = self._check_tasklist(tasklist)
        
        completed_max = to_rfc339(value=completed_max, dayfirst=dayfirst, yearfirst=yearfirst) if completed_max is not None else None
        completed_min = to_rfc339(value=completed_min, dayfirst=dayfirst, yearfirst=yearfirst) if completed_min is not None else None
        due_max = to_rfc339(value=due_max, dayfirst=dayfirst, yearfirst=yearfirst) if due_max is not None else None
        due_min = to_rfc339(value=due_min, dayfirst=dayfirst, yearfirst=yearfirst) if due_min is not None else None
        updated_min = to_rfc339(value=updated_min, dayfirst=dayfirst, yearfirst=yearfirst) if updated_min is not None else None
        
        try: 
            tasks = self.service.tasks().list(tasklist=tasklist_id,
                                            completedMax=completed_max, completedMin=completed_min,
                                            dueMax=due_max, dueMin=due_min,
                                            maxResults=max_results, pageToken=page_token,
                                            showCompleted=show_completed, showDeleted=show_deleted,
                                            showHidden=show_hidden, updatedMin=updated_min).execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return tasks.get('items')
        
    def clear_tasklist(self, tasklist):
        """Clear completed tasks in tasklist.

        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/clear
        
        Args:
            tasklist (str): ID or title of the tasklist.
        """
        
        tasklist_id = self._check_tasklist(tasklist)
        try: 
            response = self.service.tasks().clear(tasklist=tasklist_id).execute()
            print('Tasklist "{}" successfully cleared.'.format(tasklist))
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    # Task methods        
                
    def create_task(self, tasklist, parent=None, previous=None, **kwargs):
        """Add new task in tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/insert
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasks#Task
        Datetime parameters such as updated, due and completed can be given as a string or a date/datetime object. For these a parser will be used to transform them to RFC 3339 format. Add "dayfirst" and/or "yearfirst" to change the default behavior, as described here: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parserinfo.

        Args:
            tasklist (str): ID or title of the tasklist.
            parent (str, optional): Parent task identifier. Defaults to None.
            previous (str, optional): Previous sibling task identifier. Defaults to None.

        Returns:
            str: ID of the newly created task.
        """
        
        tasklist_id = self._check_tasklist(tasklist)
        body = self._prepare_request_body(arguments=kwargs)
        try: 
            response = self.service.tasks().insert(tasklist=tasklist_id, 
                                            parent=parent,
                                            previous=previous,
                                            body=body).execute()
            print('New task with ID {} created.'.format(response.get('id')))
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return response.get('id')
    
    def update_task(self, task, **kwargs):
        """Update a task.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/update
        For a list of possible parameters in kwargs check here: https://developers.google.com/tasks/reference/rest/v1/tasks#Task
        Datetime parameters such as updated, due and completed can be given as a string or a date/datetime object. For these a parser will be used to transform them to RFC 3339 format. Add "dayfirst" and/or "yearfirst" to change the default behavior, as described here: https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parserinfo.

        Args:
            task (str): ID or title of the task.
        """
        
        task_id = self._check_task(task)
        tasklist_id = self.tasks.get(task_id).get('tasklist_id')
        body = self._prepare_request_body(arguments=kwargs, task_id=task_id)
        try: 
            response = self.service.tasks().update(tasklist=tasklist_id, 
                                              task=task_id,
                                              body=body).execute()
            print('Task "{}" successfully updated.'.format(task))
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
    
    def delete_task(self, task):
        """Delete a task.

        Args:
            task (str): ID or title of the task.

        Raises:
            ValueError: If there is no task with the given title.
        """
        
        task_id = self._check_task(task)
        tasklist_id = self.tasks.get(task_id).get('tasklist_id')
        try: 
            response = self.service.tasks().delete(tasklist=tasklist_id,
                                                   task=task_id).execute()
            print('Task "{}" successfully deleted.'.format(task))
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    def move_task_internally(self, task, new_parent=None, new_previous=None):
        """Move task to a different position in the tasklist.
        
        This method is the implementation of this API call: https://developers.google.com/tasks/reference/rest/v1/tasks/move

        Args:
            task (str): ID or title of the task.
            parent (str, optional): Parent task identifier. Defaults to None (i.e. move to top level).
            previous (str, optional): Previous sibling task identifier. Defaults to None (i.e. move to first position among siblings).
        """
        
        task_id = self._check_task(task)
        tasklist_id = self.tasks.get(task_id).get('tasklist_id')
        try: 
            response = self.service.tasks().move(tasklist=tasklist_id,
                                                 task=task_id,
                                                 parent=new_parent,
                                                 previous=new_previous).execute()
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        print('Task {} successfully internally moved.'.format(task))
        
    def move_task_externally(self, task, new_tasklist):
        """Move task to a new tasklist.
        
        Since there is no implementation in the API to perform this directly, this method will firstly delete the task in the original tasklist and then create a copy in the goal tasklist.

        Args:
            task (str): ID or title of the task.
            new_tasklist (str): ID or title of the goal tasklist.

        Returns:
            str: ID of the copied task.
        """
        
        # Get info about current task
        current_task_id = self._check_task(task)
        current_tasklist_id = self.tasks.get(current_task_id).get('tasklist_id')
        task_info = [t for t in self.__tasks.get(current_tasklist_id) if t.get('id') == current_task_id][0]
            
        # Prepare request for future task
        new_tasklist_id = self._check_tasklist(new_tasklist)
        body = {key:value for key, value in task_info.items() if key not in ['id', 'etag']}
        try: 
            # Delete current task
            response = self.service.tasks().delete(tasklist=current_tasklist_id,
                                                   task=current_task_id).execute()
            # Create new task with same info in new tasklist
            response = self.service.tasks().insert(tasklist=new_tasklist_id,
                                                #    parent=parent,
                                                #    previous=previous,
                                                   body=body).execute()
            print('Task "{}" successfully moved to tasklist "{}".'.format(task, new_tasklist))
            self.__tasks = self._update_tasks_info()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return response.get('id')
    
    # Helper methods
    def _update_tasklists_info(self):
        return self.service.tasklists().list(maxResults=999999999).execute()
    
    def _update_tasks_info(self):
        tasklists_ids = [list.get('id') for list in self.__tasklists.get('items')]
        tasks_info = dict()
        for id in tasklists_ids:
            tasks = self.service.tasks().list(tasklist=id,
                                              completedMax=None, completedMin=None,
                                              dueMax=None, dueMin=None,
                                              maxResults=999999999, pageToken=None,
                                              showCompleted=True, showDeleted=True,
                                              showHidden=True, updatedMin=None).execute()
            tasks_info.update({id:tasks.get('items')})
        return tasks_info
    
    def _check_tasklist(self, tasklist):
        tasklist_info = self.tasklists.get(tasklist)
        tasklists_ids = [key for key, value in self.tasklists.items() if value.get('title') == tasklist]
        if tasklist_info is not None:
            tasklist_id = tasklist
        elif len(tasklists_ids) == 1:
            tasklist_id = tasklists_ids[0]
        elif len(tasklists_ids) > 1:
            raise ValueError('There are multiple taskslists with the title {}, use the ID instead.'.format(tasklist))
        else:
            raise ValueError('No taskslists with either ID or title equal to {}.'.format(tasklist))
        return tasklist_id
    
    def _check_task(self, task):
        task_info = self.tasks.get(task)
        tasks_ids = [key for key, value in self.tasks.items() if value.get('title') == task]
        if task_info is not None:
            task_id = task
        elif len(tasks_ids) == 1:
            task_id = tasks_ids[0]
        elif len(tasks_ids) > 1:
            raise ValueError('There are multiple tasks with the title {}, use the ID instead.'.format(task))
        else:
            raise ValueError('No tasks with either ID or title equal to {}.'.format(task))
        return task_id
    
    def _prepare_request_body(self, arguments, tasklist_id=None, task_id=None):
        # Get initial values of a resource (tasklist or task)
        if tasklist_id is not None and task_id is not None:
            raise ValueError('Only one of tasklist_id or task_id can be included.')
        elif tasklist_id is not None:
            resource = self.tasklists.get(tasklist_id)
            resource['id'] = tasklist_id
        elif task_id is not None:
            resource = {key:value for key, value in self.tasks.get(task_id).items() if key != 'tasklist_id'}
            resource['id'] = task_id
        elif tasklist_id is None and task_id is None:
            resource = dict()

        # Transform date/datetime arguments to RFC 3339 format
        date_params = ['updated', 'due', 'completed', # for insert
                       'completed_max', 'completed_min', 'due_max', 'due_min', 'updated_min'] # for get  
        dayfirst = arguments.get('dayfirst') if arguments.get('dayfirst') is not None else False   
        yearfirst = arguments.get('yearfirst') if arguments.get('yearfirst') is not None else False      
        for param in date_params:
            value = arguments.get(param)
            if value is not None:
                arguments[param] = to_rfc339(value=value, dayfirst=dayfirst, yearfirst=yearfirst)
                
        # Substitute resource values with the new ones
        if resource == {}:
            resource = arguments
        else:
            resource = {key: arguments.get(key, resource[key]) for key in resource}
        
        return resource


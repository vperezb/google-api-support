import pandas as pd
from apiclient import errors
from dev.drive import GoogleDriveFile
from GoogleApiSupport import auth, apis

class GoogleDocs(GoogleDriveFile):
    """A Google Docs file.

    This class enherits attributes, properties and methods from GoogleDriveFile and expands with document-only capabilities.
    """
    
    services = {api_name: auth.get_service(api_name) for api_name in apis.api_configs}
    
    def __new__(cls, file_id=None):
        mime_type = cls.services.get('drive').files().get(fileId=file_id, fields='*').execute().get('mimeType')
        assert mime_type == 'application/vnd.google-apps.document', 'The file is of type "{type}", but it needs to be Google Docs to be of this class type.'.format(type=mime_type)
        return super().__new__(cls)
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)
        
        # Additional spreadsheet specific info
        self.__document_info = self.services.get('docs').documents().get(documentId=file_id, fields='*').execute()
        
    @property
    def document_style(self):
        return self.__document_info.get('documentStyle')
        
    @property
    def named_styles(self):
        styles = dict()
        for style in self.__document_info.get('namedStyles').get('styles'):
            name = style.get('namedStyleType')
            info = {key:value for key, value in style.items() if key != 'namedStyleType'}
            styles.update({name:info})
        return styles
    
    @property
    def body(self):
        text = list()
        for body_part in self.__document_info.get('body').get('content'):
            if body_part.get('paragraph') is not None:
                for body_element in body_part.get('paragraph').get('elements'):
                    text.append(body_element.get('textRun').get('content'))
        return text
               
    @classmethod
    def create(cls, file_name, parent_folder_id=None, transfer_permissions=False, **kwargs):
        """Class method to create a Google Docs file.

        Args:
            file_name (str): Name of new file.
            parent_folder_id (str, optional): ID of parent folder. Defaults to None.
            transfer_permissions (bool, optional): Whether to copy permissions from parent folder. Defaults to False.
            
        Returns:
            GoogleSheets object.
        """
        new_file = super().create(file_name=file_name, 
                                  mime_type='application/vnd.google-apps.document',
                                  parent_folder_id=parent_folder_id, 
                                  transfer_permissions=transfer_permissions, 
                                  **kwargs)
        return new_file
    
    def execute_batch_update(self, requests):
        """Applies one or more updates to the document.
        Implementation of: https://developers.google.com/docs/api/reference/rest/v1/documents/batchUpdate.
        Beside updating the document, it also updates the __document_info attribute.

        Args:
            requests (list): List of update requests.

        Returns:
            dict: Response to the update requests.
        """
        
        body = {'requests': requests}
        response = self.services.get('docs').documents().batchUpdate(spreadsheetId=self.file_id,
                                                                     body=body).execute()
        # Update presentation info
        self.__document_info = self.services.get('docs').documents().get(documentId=self.file_id, fields='*').execute()
        return response
        
doc = GoogleDocs(file_id='1oF0oZfTeZLJwD5zXhmZLd-VEPHLY0jFuLRwjtVdKNHY')

doc.standard_styles.keys()

doc._GoogleDocs__document_info.keys()
# dict_keys(['title', 'body', 'documentStyle', 'namedStyles', 'revisionId', 'suggestionsViewMode', 'documentId'])

text = list()
for body_part in doc._GoogleDocs__document_info.get('body').get('content'):
    if body_part.get('paragraph') is not None:
        for body_element in body_part.get('paragraph').get('elements'):
            text.append(body_element.get('textRun').get('content'))

[1].get('paragraph').get('elements')[0].get('textRun').get('content')

body_part = doc._GoogleDocs__document_info.get('body').get('content')[9]
body_part.keys()
import pandas as pd
from dev.utils import download_image_from_url
from apiclient import errors
from dev.drive import GoogleDriveFile

# Credentials
import os
ROOT_DIR=os.getcwd()
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".credentials/service_credentials.json")
os.environ['GOOGLE_OAUTH_CREDENTIALS'] = os.path.join(ROOT_DIR, ".oauth_credentials/credentials.json")

# Doing this to import local versions
import sys
sys.path.append('../GoogleApiSupport')
from GoogleApiSupport import apis, auth

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
    def text(self):
        elements = self.__document_info.get('body').get('content')
        return self.read_text_elements(elements)
               
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

    def read_text_elements(self, elements):
        """Read text from a structural element.
        
        For detailed information, read here: https://developers.google.com/docs/api/samples/extract-text

        Args:
            elements: List of Structural Elements that can contain text (i.e. paragraph, table or table of contects).
            
        Returns:
            list: List of text from the different elements.
        """
        
        text = list()
        for value in elements:
            if 'paragraph' in value:
                elements = value.get('paragraph').get('elements')
                for elem in elements:
                    text_run = elem.get('textRun')
                    if not text_run:
                        text.append('')
                    else:
                        text.append(text_run.get('content'))
            elif 'table' in value:
                # The text in table cells are in nested Structural Elements and tables may be
                # nested.
                table = value.get('table')
                for row in table.get('tableRows'):
                    cells = row.get('tableCells')
                    for cell in cells:
                        text.append(read_structural_elements(cell.get('content')))
            elif 'tableOfContents' in value:
                # The text in the TOC is also in a Structural Element.
                toc = value.get('tableOfContents')
                text.append(read_structural_elements(toc.get('content')))
        return text
    
    def download_images(self, images_ids=[], destination_folder='', file_name=None, open_file=False):
        """Download images from document.

        Args:
            images_ids (list, optional): List of IDs for images to download. Defaults to [] (i.e. all images).
            destination_folder (str, optional): Folder where to download the file. Defaults to ''.
            file_name (str, optional): Name of the file downloaded. Defaults to None, in which case it takes the original name.
            open_file (bool, optional): Whether to open the downloaded file. Defaults to False.

        Raises:
            ValueError: If an ID is not valid.
        """
        
        objects = self.__document_info.get('inlineObjects')
        if images_ids == []:
            images_ids = list(objects.keys())
        for id in images_ids:
            obj_info = objects.get(id)
            if obj_info is None:
                raise ValueError('{} is not a valid ID for an image.'.format(id))
            obj_properties = obj_info.get('inlineObjectProperties').get('embeddedObject').get('imageProperties')
            if 'sourceUri' in obj_properties:
                url = obj_properties.get('sourceUri')
                # If file from drive, it will have a specific structure from which we can get file ID
                if url.startswith('https://lh3.google.com/'):
                    file_id = url.split('/')[-1].split('=')[0]
                    drive_image = GoogleDriveFile(file_id=file_id)
                    drive_image.download(destination_folder=destination_folder,
                                        file_name=file_name,
                                        open_file=open_file)
                # Otherwise, download the file from its url
                else:
                    download_image_from_url(url,
                                            destination_folder=destination_folder,
                                            file_name=file_name,
                                            open_file=open_file)
            else:
                url = obj_properties.get('contentUri')
                download_image_from_url(url,
                                        destination_folder=destination_folder,
                                        file_name=file_name,
                                        open_file=open_file)




        
doc = GoogleDocs(file_id='1oF0oZfTeZLJwD5zXhmZLd-VEPHLY0jFuLRwjtVdKNHY')

file_id = '1xLIOy7-nXzD1ANmC0thygf-MazOIAngv7cQKeufSLeE'
doc = GoogleDocs(file_id)
doc.text

vars(doc).keys()

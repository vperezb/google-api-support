from GoogleApiSupport import auth
from dev import utils
from apiclient import errors
import mimetypes
import io
import os
import pandas as pd
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.http import MediaFileUpload
import webbrowser

# TODO: type hinting

class GoogleDriveFile:
    """Any file in Google Drive.
    
    Class for a file in Google Drive, which can be of external type (picture, video) or Google Workspace (Google Docs, Google Sheets).

    Attributes:
        file_id (str): ID of the file in Google Drive.
        file_name (str): Name of the file in Google Drive. If it's an external type, it also contains the extension.
        mime_type (str): MIME type of the file in Google Drive.
        parent_folder_id (str): ID of the folder in Google Drive in which the file is located.
        permissions (list): List of dictionaries containing the permissions to the file in Google Drive. 

    Methods:
        create: Create new file in Google Drive.
        rename: Change file name.
        share: Share file with someone (or anyone).
        open: Open file in browser.
        download: Download file (for non Google Workspace files).
        export: Export file (for Google Workspace files).
        move: Move file into a new folder.
        delete: Delete file from Google Drive.
        copy: Copy file.
    """
    
    service = auth.get_service('drive')
            
    def __init__(self, file_id=None):
        if file_id is not None: 
            # File information 
            self._info = self.service.files().get(fileId=file_id, fields='*').execute()

    # Properties
    @property
    def file_id(self):
        return self._info.get('id')

    @property
    def file_name(self):
        return self._info.get('name')

    @property
    def mime_type(self):
        return self._info.get('mimeType')

    @property
    def url(self):
        return self._info.get('webViewLink')
    
    @property
    def parent_folder_id(self):
        return self._info.get('parents')[0] if self._info.get('parents') is not None else None
        
    @property
    def permissions(self):
        return self._info.get('permissions')
            
    @classmethod
    def create(cls, file_name, mime_type, parent_folder_id=None, transfer_permissions=False, **kwargs):
        """Class method to create a file.

        Args:
            file_name (str): Name of new file.
            mime_type (str): MIME type, check https://developers.google.com/drive/api/guides/mime-types for list of options.
            parent_folder_id (str, optional): ID of parent folder. Defaults to None.
            transfer_permissions (bool, optional): Whether to copy permissions from parent folder. Defaults to False.
            
        Returns:
            GoogleDriveFile object.
        """
        
        file_metadata = {
            'name': file_name,
            'mimeType': mime_type,
            'parents': [parent_folder_id],
        }

        try:
            new_file_id = cls.service.files().create(body=file_metadata,
                                                    fields='id',
                                                    supportsAllDrives=True).execute().get('id')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

        # File information
        new_file = cls(file_id=new_file_id)
        print('Created file {} with name "{}"'.format(new_file_id, file_name))

        if transfer_permissions:
            parent_folder = GoogleDriveFile(file_id=parent_folder_id)
            utils.copy_permissions(start_file=parent_folder, end_file=new_file, **kwargs)
            # new_permissions = self.service.files().get(fileId=new_file_id, fields='permissions').execute()
            # self.permissions = new_permissions.get('permissions')

        return new_file

    def rename(self, new_file_name):
        old_file_name = self.file_name
        try:
            response = self.service.files().update(fileId=self.file_id, body={'name':new_file_name}, fields='*').execute()
            self._info = response
            print('File name changed from "{old}" to "{new}".'.format(old=old_file_name, new=new_file_name))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    def share(self, perm_type, role, email_address=None, domain=None, **kwargs):
        """Method to add new permission to file or change current one.

        Args:
            perm_type (str): Permission type, it can be the value 'user', 'group', 'domain', 'anyone' or 'default'.
            role (str): Role, it can be the value 'owner', 'writer' or 'reader'
            email_address (str, optional): User or group e-mail address (needed if perm_type is 'user' or 'group'). Defaults to None.
            domain (str, optional): Domain name (needed if perm_type is 'domain'). Defaults to None.
        """
        
        if perm_type in ('user', 'group'):
            shared_to = email_address
        elif perm_type == 'domain':
            shared_to = domain
        elif perm_type in ('anyone', 'default'):
            shared_to = perm_type
        
        new_permission = {
            'type': perm_type,
            'role': role,
            'emailAddress': email_address,
            'domain': domain
        }
        try:
            new_permission_resource = self.service.permissions().create(fileId=self.file_id, 
                                                                        body=new_permission, 
                                                                        fields='*',
                                                                        **kwargs).execute()
            new_permission_id = new_permission_resource.get('id')
            # If permission is changed, remove old version
            if new_permission_id in [perm.get('id') for perm in self.permissions]:
                old_permission = [perm for perm in self.permissions if perm.get('id') == new_permission_id][0]
                self.permissions.remove(old_permission)
            self.permissions.append(new_permission_resource)  
            print('Inserted {} permission for "{}"'.format(new_permission_resource.get('role'), shared_to))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
    
    def open(self, new=0, autoraise=True):
        """Method that opens the file in the browser.
        It uses the function webbrowser.open() and has the same arguments.

        Args:
            new (int, optional): If new is 0, the url is opened in the same browser window if possible. If new is 1, a new browser window is opened if possible. If new is 2, a new browser page (“tab”) is opened if possible. Defaults to 0.
            autoraise (bool, optional):  If autoraise is True, the window is raised if possible (note that under many window managers this will occur regardless of the setting of this variable). Defaults to True.
        """
        
        try: 
            webbrowser.open(self.url, new=new, autoraise=autoraise)
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def download(self, destination_folder='', file_name=None, open_file=False):
        """Method to download the file if it's stored in Google Drive. If it's a Google Worspace file, use the method export().
        Reflects the first use case described here: https://developers.google.com/drive/api/guides/manage-downloads

        Args:
            destination_folder (str, optional): Folder where to download the file. Defaults to ''.
            file_name (str, optional): Name of the file downloaded. Defaults to None, in which case it takes the original name.
            open_file (bool, optional): Whether to open the downloaded file. Defaults to False.
        """
        
        if file_name is None:
            file_name = self.file_name
            
        try:
            request = self.service.files().get_media(fileId=self.file_id)
            fh = io.BytesIO() 
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(F'Download {int(status.progress() * 100)}.')
        
        except errors.HttpError as error:
            print(F'An error occurred: {error}')
            file = None
            
        destination_path = os.path.join(destination_folder, file_name)
            
        with io.open(destination_path, 'wb') as file:
            fh.seek(0)
            file.write(fh.read())
            file.close()
            
        if open_file:
            utils.start_file(path=destination_path)
        else:
            print(f"File downloaded under {destination_path}") 
           
    def export(self, destination_folder='', file_name=None, mime_type=None, extension=None, open_file=False):
        """Method to export the file if it's a Google Worspace file, i.e. Google Docs, Sheets, and Slides.
        Reflects the second use case described here: https://developers.google.com/drive/api/guides/manage-downloads
        The order of presedence to check if values are allowed: file_name, mime_type, extension.

        Args:
            destination_folder (str, optional): Folder path where to save the downloaded file. Defaults to ''.
            file_name (str, optional): File name to give to downloaded file, extension included. Defaults to None.
            mime_type (str, optional): Type of file to download. Defaults to None.
            extension (str, optional): Extension of file to download. Defaults to None.
            open_file (bool, optional):  Whether to open the downloaded file. Defaults to False.
        """

        # file_name takes precedence over mine_type and extension
        export_formats = utils.google_export_types()
        
        # Extract formats that are accepted for the specific file type
        acceptable_formats = export_formats[export_formats['from_mime_type'] == self.mime_type]
        acceptable_extensions = acceptable_formats['extension']
        acceptable_mime_types = acceptable_formats['to_mime_type']

        desired_result = pd.DataFrame(columns=['name', 'mime_type','extension'])

        # File name
        if file_name is not None:
            (name_ext, extension_ext) = os.path.splitext(file_name)
            mime_type_ext = acceptable_mime_types[acceptable_extensions == extension_ext].iloc[0]
        else:
            name_ext = self.file_name
            extension_ext = acceptable_extensions[acceptable_formats['default']==True].iloc[0]
            mime_type_ext = acceptable_mime_types[acceptable_formats['default']==True].iloc[0]
        file_name_dict = {'name':name_ext, 'mime_type':mime_type_ext, 'extension':extension_ext, }
        index = len(desired_result)
        desired_result = pd.concat([desired_result, pd.DataFrame(file_name_dict, index=[index])])

        # MIME type
        if mime_type is not None:
            extension_ext = acceptable_extensions[acceptable_mime_types == mime_type].iloc[0]
        else:
            mime_type = acceptable_mime_types[acceptable_formats['default']==True].iloc[0]
            extension_ext = acceptable_extensions[acceptable_formats['default']==True].iloc[0]
        mime_type_dict = {'name':name_ext, 'mime_type':mime_type, 'extension':extension_ext,}
        index = len(desired_result)
        desired_result = pd.concat([desired_result, pd.DataFrame(mime_type_dict, index=[index])])

        # Extension
        if extension is not None:
            mime_type_ext = acceptable_mime_types[acceptable_extensions == extension].iloc[0]
        else:
            mime_type = acceptable_mime_types[acceptable_formats['default']==True]
            extension = acceptable_extensions[acceptable_formats['default']==True]
        extension_dict = {'name':name_ext, 'mime_type':mime_type_ext, 'extension':extension}
        index = len(desired_result)
        desired_result = pd.concat([desired_result, pd.DataFrame(extension_dict, index=[index])])

        # Order of importance: file_name, mime_type, extension
        # Keep first values that have no NaNs
        desired_result.dropna(inplace=True)
        final_format = desired_result.iloc[0]        

        destination_path = os.path.join(destination_folder, 
                                        final_format['name']+final_format['extension'])  

        data = self.service.files().export_media(fileId=self.file_id,
                                                 mimeType=final_format['mime_type']).execute()

        f = open(destination_path, 'wb')
        f.write(data)
        f.close()
        
        if open_file:
            utils.start_file(path=destination_path)
        else:
            print(f"File downloaded as under {destination_path}")     
        
    def move(self, destination_folder_id):
        """Method to move file from current location to new folder

        Args:
            destination_folder_id (str): Id of the folder where to move the file
        """
        try: 
            # https://stackoverflow.com/questions/59361613/google-drive-api-changes-api-shared-files-missing-parents-field
            response = self.service.files().update(fileId=self.file_id,
                                                   addParents=destination_folder_id,
                                                   removeParents=self.parent_folder_id,
                                                   supportsAllDrives=True,
                                                #    fields='id, parents').execute()
                                                    fields='*').execute()
            self._info = response
            # self.parent_folder_id = response.get('parents')[0]
            print("File moved")
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def delete(self):
        """Method to delete file.
        """
        try:
            id = self.file_id
            name = self.file_name
            self.service.files().delete(fileId=self.file_id).execute()
            self._info = 'File does not exist.'
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        print(f"Deleted file: {id} - {name}")
        
    def copy(self, new_file_name='', supports_all_drives=True, transfer_permissions=False, **kwargs):
        """Method to create a copy of the current file.

        Args:
            new_file_name (str, optional): File name of copy file. Defaults to ''.
            supports_all_drives (bool, optional): Whether the copy supports all drives. Defaults to True.
            transfer_permissions (bool, optional): True if the permissions should also be copied. Defaults to False.

        Returns:
            GoogleDriveFile: Copy of file.
        """
        body = {'name': new_file_name}

        drive_response = self.service.files().copy(fileId=self.file_id,
                                                   body=body,
                                                   supportsAllDrives=supports_all_drives).execute()
        
        new_file = GoogleDriveFile(file_id=drive_response.get('id'))
        
        if transfer_permissions:
            new_file = utils.copy_permissions(start_file=self, end_file=new_file, 
                                              supportsAllDrives=supports_all_drives, **kwargs)
            # file_info = self.service.files().get(fileId=self.file_id, fields='*').execute()
            # new_file.permissions = file_info.get('permissions')
        
        print('Copying file {} with name {}'.format(self.file_id, new_file_name))

        return new_file
       
class GoogleDriveFolder(GoogleDriveFile):
    
    def __new__(cls, file_id=None):
        mime_type = cls.service.files().get(fileId=file_id, fields='*').execute().get('mimeType')
        assert mime_type == 'application/vnd.google-apps.folder', 'The file is of type "{type}", but it needs to be a folder to be of this class type.'.format(type=mime_type)
        return super().__new__(cls)
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)

    @classmethod
    def create(cls, file_name, parent_folder_id=None, transfer_permissions=False, **kwargs):
        new_file = super().create(file_name=file_name, 
                                  mime_type='application/vnd.google-apps.folder',
                                  parent_folder_id=parent_folder_id, 
                                  transfer_permissions=transfer_permissions, 
                                  **kwargs)     
        return new_file

    def children(self, which='all', mime_type=None):
        """Show child files of the folder.
        
        Args:
            which (str, optional): Which types of files: 'all' for everything, 'folders' for folders or 'specific' for a specific type (indicate the MIME type). Defaults to 'all'.
            mime_type (str, optional): MIME type of specific file to show (only if which='specific'). Defaults to None.
        """
        
        general_query="parents='{folder}'".format(folder=self.file_id)
        # If you want to show all files, inpute nothing
        if which=='all':
            query=general_query
        # If you want to show child folders, inpute the mime type for folders
        elif which=='folders':
            query=general_query+" and mimeType='application/vnd.google-apps.folder'"
        # Otherwise, try the give MIME type
        elif which=='specific':
            try:
                 query=general_query+" and mimeType='{mime_type}'".format(mime_type=mime_type)
            except errors.HttpError as error:
                print('An error occurred: %s' % error)
                
        response = self.service.files().list(q=query).execute()
        
        # TODO: Maybe return list of files as GoogleDriveFile object
        # [GoogleDriveFile(file_id=file.get('id')) for file in response.get('files')]      
        # Issue: How to handle case in which the files are folders?
        return response.get('files')
    
    def upload_file(self, origin_path, transfer_permissions=False, start_url=False, **kwargs):
        
        # Get information of original file
        (folder_path, file_name) = os.path.split(origin_path)
        (name_ext, extension_ext) = os.path.splitext(file_name)
        extension_ext = extension_ext.lower()
        types = mimetypes.types_map
        mime_type = types.get(extension_ext)
        
        # Request
        try:
            file_metadata = {'name': file_name,
                            'parents': [self.file_id]}
            media = MediaFileUpload(origin_path,
                                    mimetype=mime_type,
                                    resumable=True)
            response = self.service.files().create(body=file_metadata,
                                                   media_body=media,
                                                   fields='id').execute()
            print('Uploaded file "{name}" with ID {id}'.format(name=file_name, id=response.get('id')))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

        if transfer_permissions:
            new_file = GoogleDriveFile(file_id=response.get('id'))
            new_file = utils.copy_permissions(start_file=self, end_file=new_file, 
                                              supportsAllDrives=True, **kwargs)
            
        if start_url:
            new_file = GoogleDriveFile(file_id=response.get('id'))
            new_file.open()

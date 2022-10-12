from GoogleApiSupport import auth
from apiclient import errors

# Permissions functions

# https://developers.google.com/drive/api/v2/reference/permissions/list
def retrieve_permissions(file_id, **kwargs):
    """Retrieve a list of permissions.
    Args:
    file_id: ID of the file to retrieve permissions for.
    Returns:
    List of permissions.
    """
    service = auth.get_service("drive")
    try:
        permissions = service.permissions().list(fileId=file_id, **kwargs).execute()
        return permissions.get('permissions', [])
    except errors.HttpError as error:
        print('An error occurred: %s' % error)

# https://developers.google.com/drive/api/v2/reference/permissions/insert
def insert_permission(file_id, perm_type, role, email_address=None, domain=None, **kwargs):
    """Insert a new permission.
    Args:
    file_id: ID of the file to insert permission for.
    perm_type: The value 'user', 'group', 'domain', 'anyone' or 'default'.
    role: The value 'owner', 'writer' or 'reader'.
    email_address: User or group e-mail address (needed if perm_type is 'user' or 'group')
    domain: Domain name (needed if perm_type is 'domain')
    Returns:
    The inserted permission if successful, None otherwise.
    """
    service = auth.get_service("drive")
    new_permission = {
        'type': perm_type,
        'role': role,
        'emailAddress': email_address,
        'domain': domain
    }
    try:
        return service.permissions().create(fileId=file_id, body=new_permission, **kwargs).execute()
    except errors.HttpError as error:
        print('An error occurred: %s' % error)


def copy_permissions(start_file_id, end_file_id, **kwargs):
    """Copy permissions from one file to another.
    Args:
    start_file_id: ID of the file to retrieve permissions for.
    end_file_id: ID of the file to insert permission for.
    Returns:
    The copied permissions if successful, None otherwise.
    """
    
    # Values of needed kwargs
    retrieve_fields = kwargs['fields'] if 'fields' in kwargs else '*'
    supports_all_drives = kwargs['supportsAllDrives'] if 'supportsAllDrives' in kwargs else False
    transfer_ownership = kwargs['transferOwnership'] if 'transferOwnership' in kwargs else False
    send_notification_email = kwargs['sendNotificationEmail'] if 'sendNotificationEmail' in kwargs and transfer_ownership == False else True
    
    # Retrieve permissions
    start_permissions = retrieve_permissions(file_id=start_file_id, fields=retrieve_fields)

    # Insert permissions one by one
    for permission in start_permissions:
        perm_type = permission['type']
        # Ownership transfers are not supported for files and folders in shared drives. - OR maybe yes with additional arg "supportAllDrives"
        # Owndership transfer is only possible if service account has domain-wide authority
        role = 'writer' if transfer_ownership == False and permission['role'] == 'owner' else permission['role']
        # value: User or group e-mail address, domain name or None for  for 'anyone' or 'default' type.
        email_address = permission['emailAddress'] if perm_type in ('user', 'group') else None
        domain = permission['domain'] if perm_type == 'domain' else None
            
        end_permissions = list()
        try:
            new_permission = insert_permission(file_id=end_file_id,
                                     perm_type=perm_type,
                                     role=role,
                                     email_address=email_address,
                                     domain=domain,
                                     supportsAllDrives=supports_all_drives,
                                     transferOwnership=transfer_ownership,
                                     sendNotificationEmail=send_notification_email)
            end_permissions = end_permissions.append(new_permission)
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
    
    print('Successfully transferred permissions from file {} to file {}'.format(start_file_id, end_file_id))
    return end_permissions

def get_file_name(file_id):
    service = auth.get_service("drive")
    response = service.files().get(fileId=file_id,
                                   fields='name').execute()
    return response


def move_file(file_id, folder_destination_id):
    print('Moving file id {} to folder with id {}'.format(
        file_id, folder_destination_id))
    service = auth.get_service("drive")
    file = service.files().get(fileId=file_id,
                               fields='parents',
                               supportsAllDrives=True).execute()

    previous_parents = ",".join(file.get('parents'))

    response = service.files().update(fileId=file_id,
                                      addParents=folder_destination_id,
                                      removeParents=previous_parents,
                                      supportsAllDrives=True,
                                      fields='id, parents').execute()
    return response


def delete_file(file_id):
    service = auth.get_service("drive")
    response = service.files().delete(fileId=file_id).execute()
    return response


def copy_file(file_from_id, new_file_name='', supports_all_drives=False, transfer_permissions=False, **kwargs):
    """
    By passing an old file id, creates a copy and returns the id of the file copy
    Set transfer_permissions to True if you want to transfer the permissions from the old file to the new file
    """
    print('Copying file {} with name {}'.format(file_from_id, new_file_name))
    body = {'name': new_file_name}

    service = auth.get_service("drive")
    drive_response = service.files().copy(fileId=file_from_id,
                                          body=body,
                                          supportsAllDrives=supports_all_drives,
                                          ).execute()
    
    new_file_id = drive_response.get('id')
    
    if transfer_permissions:
        copy_permissions(start_file_id=file_from_id, 
                         end_file_id=new_file_id, 
                         supportsAllDrives=supports_all_drives,
                         **kwargs)

    return new_file_id


def upload_image_to_drive(image_name: str, image_file_path: str, folder_destination_id='None'):
    service = auth.get_service("drive")

    file = service.files().create(
        body={'name': image_name, 'mimeType': 'image/png'}, media_body=image_file_path).execute()
    file_id = file.get('id')
    service.permissions().create(fileId=file_id,
                                 body={"role": "reader", "type": "anyone", "withLink": True}).execute()

    image_url = 'https://drive.google.com/uc?id={file_id}'.format(
        file_id=file_id)

    # Copy the image to destination if passed
    if not folder_destination_id:
        move_file(file_id=file_id, folder_destination_id=folder_destination_id)

    return {'image_url': image_url, 'file_id': file_id}


def create_folder(name, parent_folder: list = list()):
    service = auth.get_service("drive")

    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': parent_folder,
    }

    response = service.files().create(
        body=file_metadata,
        fields='id',
        supportsAllDrives=True).execute()
    return response


def folders_in_folder(parent_folder):
    service = auth.get_service("drive")

    response = service.files().list(q="mimeType='application/vnd.google-apps.folder' \
                                    and parents='{parent_folder}'".format(parent_folder=parent_folder)).execute()
    return response['files']


def files_in_folder(parent_folder):
    service = auth.get_service("drive")

    response = service.files().list(q="parents='{parent_folder}'".format(parent_folder=parent_folder)).execute()
    return response['files']


def search_folder_id_by_name(name, parent_folder):
    service = auth.get_service("drive")

    response = service.files().list(q="mimeType='application/vnd.google-apps.folder' \
                                    and name='{name}' and parents='{parent_folder}'".format(
                                        name=name, parent_folder=parent_folder)).execute()
    
    files = response['files'] 
    
    if len(files) > 1:
        print('Warning: There\'s more than 1 folder with name {}'.format(name))

    elif len(files) == 0:
        raise ('TODO: Create folder {}'.format(name))

    return files[0]['id']


def download_file(file_id, destination_path='test.pdf', mime_type='application/pdf'):
    service = auth.get_service("drive")
    data = service.files().export(
        fileId=file_id,
        mimeType=mime_type
    ).execute()

    f = open(destination_path, 'wb')
    f.write(data)
    f.close()
    return
    

# Specific Team Drive functions

def get_folder_id_by_path(path, team_drive_id):
    print('Retrieving folder id for path {} inside TeamDrive with id {}'.format(
        path, team_drive_id))
    parent_folder = ''
    last_level = ''
    for level in path.split('/'):
        if parent_folder == '':
            parent_folder = get_folder_id_by_name(level, team_drive_id)
        else:
            folders_in_folder = list_folders_in_folder(
                parent_folder, team_drive_id)
            if level in [response['name'] for response in folders_in_folder]:
                parent_folder = [
                    response['id'] for response in folders_in_folder if response['name'] == level][0]
            else:
                print('Creating folder {} inside parent folder {} with folder id = {}'.format(
                    level, last_level, parent_folder))
                parent_folder = create_folder(level, [parent_folder])['id']
        last_level = level
    return parent_folder


def list_folders_in_folder(parent_folder, team_drive_id):
    service = auth.get_service("drive")

    response = service.files().list(teamDriveId=team_drive_id, includeTeamDriveItems=True,
                                    corpora='teamDrive', supportsAllDrives=True,
                                    q="mimeType='application/vnd.google-apps.folder' \
                                    and parents='{parent_folder}'".format(parent_folder=parent_folder)).execute()
    return response['files']


def get_folder_id_by_name(name, team_drive_id):
    service = auth.get_service("drive")

    response = service.files().list(teamDriveId=team_drive_id, includeTeamDriveItems=True,
                                    corpora='teamDrive', supportsAllDrives=True,
                                    q="mimeType='application/vnd.google-apps.folder' \
                                    and name='{name}'".format(name=name)).execute()

    if len(response['files']) > 1:
        print('Warning: There\'s more than 1 folder with name {}'.format(name))

    elif len(response['files']) == 0:
        raise ('TODO: Create folder {}'.format(name))

    return response['files'][0]['id']
from GoogleApiSupport import auth


def get_file_name(file_id):
    service = auth.get_service("drive")
    response = service.files().get(fileId=file_id,
                                   fields='name').execute()
    return response


def move_file(file_id, folder_destination_id):
    print('Moving file id {} to folder with id{}'.format(
        file_id, folder_destination_id))
    service = auth.get_service("drive")
    file = service.files().get(fileId=file_id,
                               fields='parents',
                               supportsTeamDrives=True).execute()

    previous_parents = ",".join(file.get('parents'))

    response = service.files().update(fileId=file_id,
                                      addParents=folder_destination_id,
                                      removeParents=previous_parents,
                                      supportsTeamDrives=True,
                                      fields='id, parents').execute()
    return response


def delete_file(file_id):
    service = auth.get_service("drive")
    response = service.files().delete(fileId=file_id).execute()
    return response


def copy_file(file_from_id, new_file_name=''):
    """
    By passing an old file id, creates a copy and returns the id of the file copy
    """
    print('Copying file {} with name {}'.format(file_from_id, new_file_name))
    body = {'name': new_file_name}

    service = auth.get_service("drive")
    drive_response = service.files().copy(fileId=file_from_id,
                                          body=body,
                                          supportsTeamDrives=True,
                                          ).execute()

    new_file_id = drive_response.get('id')
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
        supportsTeamDrives=True).execute()
    return response


def list_folders_in_folder(parent_folder, team_drive_id):
    service = auth.get_service("drive")

    response = service.files().list(teamDriveId=team_drive_id, includeTeamDriveItems=True,
                                    corpora='teamDrive', supportsTeamDrives=True,
                                    q="mimeType='application/vnd.google-apps.folder' \
                                    and parents='{parent_folder}'".format(parent_folder=parent_folder)).execute()
    return response['files']


def get_folder_id_by_name(name, team_drive_id):
    service = auth.get_service("drive")

    response = service.files().list(teamDriveId=team_drive_id, includeTeamDriveItems=True,
                                    corpora='teamDrive', supportsTeamDrives=True,
                                    q="mimeType='application/vnd.google-apps.folder' \
                                    and name='{name}'".format(name=name)).execute()

    if len(response['files']) > 1:
        print('Warning: There\'s more than 1 folder with name {}'.format(name))

    elif len(response['files']) == 0:
        raise ('TODO: Create folder {}'.format(name))

    return response['files'][0]['id']


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

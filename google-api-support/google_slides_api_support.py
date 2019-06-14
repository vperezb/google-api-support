import json

import google_api_support as gs

class Size:
    def __init__(self, width: float = 3000000.0, height: float = 3000000.0, unit: str = 'EMU'):
        self.json = {
            "width": {
                "magnitude": width,
                "unit": unit
            },
            "height": {
                "magnitude": height,
                "unit": unit
            }
        }

    def __repr__(self):
        return json.dumps(self.json, indent=4)


class Transform:
    def __init__(self, scale_x: float = 1, scale_y: float = 1, shear_x: float = 0, shear_y: float = 0,
                 translate_x: float = 0, translate_y: float = 0, unit: str = 'EMU'):
        self.json = {
            "scaleX": scale_x,
            "scaleY": scale_y,
            "shearX": shear_x,
            "shearY": shear_y,
            "translateX": translate_x,
            "translateY": translate_y,
            "unit": unit
        }

    def __repr__(self):
        return json.dumps(self.json, indent=4)


def create_presentation(name):
    service = gs.get_service("slides")
    presentation = service.presentations().create(body={"title": name}).execute()
    return presentation['presentationId']


def presentation_info(presentation_id):  # Class ??
    service = gs.get_service("slides")
    presentation = service.presentations().get(
        presentationId=presentation_id).execute()
    return presentation


def presentation_slides(presentation_id):
    slides = presentation_info(presentation_id).get('slides')
    return slides


def slide_notes(slide_object: dict):
    output = []
    try:
        for element in slide_object['slideProperties']['notesPage']['pageElements']:
            if 'shapeType' in element['shape'] and element['shape']['shapeType'] == 'TEXT_BOX':
                for line in element['shape']['text']['textElements'][1::2]:
                    if 'textRun' in line:
                        output += [line['textRun']['content']]
        return ''.join(output)
    except Exception as e:
        return '# Error in slide' + str(e)


def execute_batch_update(requests, presentation_id):
    body = {
        'requests': requests
    }

    slides_service = gs.get_service("slides")
    response = slides_service.presentations().batchUpdate(presentationId=presentation_id,
                                                          body=body).execute()
    return response


def text_replace(old: str, new: str, presentation_id: str, pages: list = []):
    service = gs.get_service("slides")

    service.presentations().batchUpdate(
        body={

            "requests": [
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": '{{' + old + '}}'
                        },
                        "replaceText": new,
                        "pageObjectIds": pages,
                    }
                }
            ]
        },
        presentationId=presentation_id
    ).execute()


def batch_text_replace(text_mapping: dict, presentation_id: str, pages: list = list()):
    """Given a list of tuples with replacement pairs this function replace it all"""
    requests = []
    for placeholder_text, new_value in text_mapping.items():
        if type(new_value) is str:
            requests += [
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": '{{' + placeholder_text + '}}'
                        },
                        "replaceText": new_value,
                        "pageObjectIds": pages
                    }
                }
            ]
        else:
            raise Exception('The text from key {} is not a string'.format(placeholder_text))
    return execute_batch_update(requests, presentation_id)


def insert_image(url: str, page_id: str, presentation_id: str, object_id: str = None,
                 transform=None, size=None):
    requests = [
        {
            'createImage': {
                'objectId': object_id,
                'url': url,
                'elementProperties': {
                    'pageObjectId': page_id,
                    'transform': transform,
                    'size': size
                },
            }
        },
    ]

    return execute_batch_update(requests, presentation_id)


def replace_image(page_id: str, presentation_id: str, old_image_object: dict, new_image_url: str):
    insert_image(new_image_url, page_id, presentation_id,
                 transform=old_image_object['transform'],
                 size=Size())
    delete_object(presentation_id, old_image_object['objectId'])


def replace_shape_with_image(url: str, presentation_id: str, contains_text: str = None):
    requests = [
        {
            "replaceAllShapesWithImage": {
                "imageUrl": url,
                "replaceMethod": "CENTER_INSIDE",
                "containsText": {
                    "text": "{{" + contains_text + "}}",
                }
            }
        }]

    return execute_batch_update(requests, presentation_id)


def batch_replace_shape_with_image(image_mapping: dict, presentation_id: str):
    requests = []

    for contains_text, url in image_mapping.items():
        requests.append(
            {
                "replaceAllShapesWithImage": {
                    "imageUrl": url,
                    "replaceMethod": "CENTER_INSIDE",
                    "containsText": {
                        "text": "{{" + contains_text + "}}",
                    }
                }
            }
        )

    response = execute_batch_update(requests, presentation_id)
    return response


def duplicate_object(presentation_id: str, object_id: str):
    requests = [
        {
            'duplicateObject': {
                'objectId': object_id
            }
        },
    ]

    body = {
        'requests': requests
    }

    service = gs.get_service("slides")
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body=body).execute()
    return response


def delete_object(presentation_id: str, object_id: str = None):
    requests = [
        {
            'deleteObject': {
                'objectId': object_id
            }
        },
    ]

    body = {
        'requests': requests
    }

    service = gs.get_service("slides")
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body=body).execute()
    return response


def batch_delete_object(presentation_id: str, object_id_list: list = None):
    requests = []

    for element in object_id_list:
        requests.append(
            {
                'deleteObject': {
                    'objectId': element
                }
            }
        )

    response = execute_batch_update(requests, presentation_id)
    return response


def batch_delete_text(presentation_id: str, object_id_list: list = None):
    requests = []

    for element in object_id_list:
        requests.append(
            {
                'deleteText': {
                    'objectId': element
                }
            }
        )

    response = execute_batch_update(requests, presentation_id)
    return response


def delete_presentation_notes(presentation_id):
    slides_service = gs.get_service("slides")

    _slides = presentation_slides(presentation_id)

    elements_to_delete = []

    for _slide in _slides:
        if 'notesPage' in _slide['slideProperties']:
            for element in _slide['slideProperties']['notesPage']['pageElements']:
                if 'textRun' in str(element):
                    elements_to_delete.append(element['objectId'])

    batch_delete_text(presentation_id, elements_to_delete)


def transform_object(presentation_id: str, object_id: str, transform, apply_mode='ABSOLUTE'):
    requests = [
        {
            'updatePageElementTransform': {
                'objectId': object_id,
                'transform': transform,
                'applyMode': apply_mode
            }
        },
    ]

    body = {
        'requests': requests
    }

    service = gs.get_service("slides")
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body=body).execute()
    return response


def __get_file_name(file_id):
    service = gs.get_service("drive")
    response = service.files().get(fileId=file_id,
                                   fields='name').execute()
    return response


def move_file(file_id, folder_destination_id):
    print('Moving file id {} to folder with id{}'.format(file_id, folder_destination_id))
    service = gs.get_service("drive")
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
    service = gs.get_service("drive")
    response = service.files().delete(fileId=file_id).execute()
    return response


def copy_file(file_from_id, new_file_name=''):
    """
    By passing an old file id, creates a copy and returns the id of the file copy
    """
    print('Copying file {} with name {}'.format(file_from_id, new_file_name))
    body = {'name': new_file_name}

    service = gs.get_service("drive")
    drive_response = service.files().copy(fileId=file_from_id,
                                          body=body,
                                          supportsTeamDrives=True,
                                          ).execute()

    new_file_id = drive_response.get('id')
    return new_file_id


def upload_image_to_drive(image_name: str, image_file_path: str, folder_destination_id='None'):
    service = gs.get_service("drive")

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
    service = gs.get_service("drive")

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
    service = gs.get_service("drive")

    response = service.files().list(teamDriveId=team_drive_id, includeTeamDriveItems=True,
                                    corpora='teamDrive', supportsTeamDrives=True,
                                    q="mimeType='application/vnd.google-apps.folder' \
                                    and parents='{parent_folder}'".format(parent_folder=parent_folder)).execute()
    return response['files']


def get_folder_id_by_name(name, team_drive_id):
    service = gs.get_service("drive")

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
    print('Retrieving folder id for path {} inside TeamDrive with id {}'.format(path, team_drive_id))
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

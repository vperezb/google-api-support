import json
from GoogleApiSupport import auth


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
    service = auth.get_service("slides")
    presentation = service.presentations().create(
        body={"title": name}).execute()
    return presentation['presentationId']


def get_presentation_info(presentation_id):  # Class ??
    service = auth.get_service("slides")
    presentation = service.presentations().get(
        presentationId=presentation_id).execute()
    return presentation


def get_presentation_slides(presentation_id):
    slides = get_presentation_info(presentation_id).get('slides')
    return slides


def get_slide_notes(slide_object: dict):
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


def execute_batch_update(requests, presentation_id, additional_apis=[]):
    body = {
        'requests': requests
    }
    
    service = auth.get_service("slides", additional_apis=additional_apis)
    
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                          body=body).execute()
    return response


def text_replace(old: str, new: str, presentation_id: str, pages=None):

    if pages is None:
        pages = []
    service = auth.get_service("slides")

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


def batch_text_replace(text_mapping: dict, presentation_id: str, pages=None):
    """Given a list of tuples with replacement pairs this function replace it all"""
    if pages is None:
        pages = list()

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
            raise Exception(
                'The text from key {} is not a string'.format(placeholder_text))
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


def batch_replace_shape_with_image(image_mapping: dict, presentation_id: str, pages=None, fill=False):
    if pages is None:
        pages = []
    requests = []
    if fill:
        replace_method = 'CENTER_CROP'
    else:
        replace_method = "CENTER_INSIDE"

    for contains_text, url in image_mapping.items():
        requests.append(
            {
                "replaceAllShapesWithImage": {
                    "imageUrl": url,
                    "replaceMethod": replace_method,
                    "pageObjectIds": pages,
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

    service = auth.get_service("slides")
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

    service = auth.get_service("slides")
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
    slides_service = auth.get_service("slides")

    _slides = get_presentation_slides(presentation_id)

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

    service = auth.get_service("slides")
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body=body).execute()
    return response


def reindex_slides(presentation_id: str, slide_ids: list, new_index=-1):
    if new_index < 0:
        number = len(get_presentation_slides(presentation_id)) + new_index + 1
    else:
        number = new_index

    requests = [
        {
            "updateSlidesPosition": {
                "slideObjectIds": slide_ids,
                "insertionIndex": number,
            },
        },
    ]

    body = {
        'requests': requests
    }

    service = auth.get_service("slides")
    response = service.presentations().batchUpdate(presentationId=presentation_id,
                                                   body=body).execute()
    return response


def get_all_shapes_placeholders(presentation_id):
    shape_ids = {}
    presentation = get_presentation_info(presentation_id)
    for slide in presentation['slides']:
        for page_element in slide['pageElements']:
            shape_ids[page_element['objectId']] = None
            if 'shape' in page_element:
                if 'text' in page_element['shape']:
                    has_inner_text = [text for text in page_element['shape']['text']['textElements'] if text.get('textRun')]
                    if has_inner_text:
                        shape_ids[page_element['objectId']] = { 'inner_text':has_inner_text[0]['textRun']['content'].strip(), 'page_id':slide['objectId']}
    return shape_ids


def update_shape_type(presentation_id, page_id, page_element, shape_type, size=None, transform=None):   
    
    requests = [
        {
            'deleteObject': {
                'objectId': page_element['objectId']
            }
        },
        {
            'createShape': {
            'objectId': page_element['objectId'],
            'shapeType': shape_type,
            'elementProperties': {
                'pageObjectId': page_id,
                'size': size or page_element['size'],
                'transform': transform or page_element['transform']
            }
        }
        }
    ]

    return execute_batch_update(requests, presentation_id)

def get_page_element(presentation_id, element_id):
    presentation = get_presentation_info(presentation_id)
    for slide in presentation['slides']:
        for page_element in slide['pageElements']:
            if page_element['objectId'] == element_id:
                return page_element
            
def get_page(presentation_id, page_id):
    presentation = get_presentation_info(presentation_id)
    for slide in presentation['slides']:
        if slide['objectID'] == page_id:
            return page


def replace_shape_with_chart(presentation_id: str, placeholder_text, spreadsheet_id, chart_id, linking_mode='NOT_LINKED_IMAGE', target_id_pages=[]):
    requests = []
      
    requests.append(
        {
            "replaceAllShapesWithSheetsChart": {
                "containsText": 
                    {
                        "text": placeholder_text,
                        "matchCase": True
                    },
                "spreadsheetId": spreadsheet_id,
                "chartId": chart_id,
                "linkingMode": linking_mode, # Unlinked by default, see other options https://developers.google.com/slides/api/reference/rest/v1/presentations/request#LinkingMode_1
                "pageObjectIds": target_id_pages
            }
        }
    )

    response = execute_batch_update(requests, presentation_id, additional_apis = ['sheets'])
    
    return response
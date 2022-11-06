# from socket import NI_NUMERICSERV
import pandas as pd
import numpy as np
import re
from itertools import chain, product
from apiclient import errors
import warnings
from drive import GoogleDriveFile
import utils
from slide_table import Table
from GoogleApiSupport import auth, apis

warnings.filterwarnings("error")

class GoogleSlides(GoogleDriveFile):
    """A Google Slides file.

    This class enherits attributes, properties and methods from GoogleDriveFile and expands with presentation-only capabilities.
    """
    
    services = {api_name: auth.get_service(api_name) for api_name in apis.api_configs}
    
    def __new__(cls, file_id=None):
        mime_type = cls.services.get('drive').files().get(fileId=file_id, fields='*').execute().get('mimeType')
        assert mime_type == 'application/vnd.google-apps.presentation', 'The file is of type "{type}", but it needs to be Google Slides to be of this class type.'.format(type=mime_type)
        return super().__new__(cls)
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)
        
        # Additional presentation specific info
        self.__presentation_info = self.services.get('slides').presentations().get(presentationId=file_id, fields='*').execute()
        
        # TODO: Update python version to >= 3.9 and do z = x | y
        # self.__file_info = {**self.__file_info, **slides_info}
            
    # Properties
    @property
    def locale(self):
        return self.__presentation_info.get('locale')
    
    @property
    def slides(self):
        return {slide.get('objectId'):{key:value for key, value in slide.items() if key != 'objectId'} for slide in self.__presentation_info.get('slides')}
    
    @property
    def masters(self):
        return {slide.get('objectId'):{key:value for key, value in slide.items() if key != 'objectId'} for slide in self.__presentation_info.get('masters')}
    
    @property
    def layouts(self):
        return {slide.get('objectId'):{key:value for key, value in slide.items() if key != 'objectId'} for slide in self.__presentation_info.get('layouts')}
    
    @property
    def layout_types(self):
        if self.__presentation_info.get('layouts') is not None:
            layouts_objects = list()
            for prop in self.__presentation_info.get('layouts'):
                obj = {'objectId':prop.get('objectId')}
                name = {key:value for key, value in prop.get('layoutProperties').items() if key in ['name', 'displayName']}
                obj.update(name)
                # obj.update({'pageElements':prop.get('pageElements')})
                layouts_objects.append(pd.DataFrame(obj, index=[0]))
            layouts_objects = pd.concat(layouts_objects, axis=0, ignore_index=True)
        else:
            # If we don't have layouts, return an empty dataframe
            layout_objects = pd.DataFrame()
        return layouts_objects
    
    @property
    def master_theme(self):
        if self.__presentation_info.get('masters') is not None:
            theme = self.__presentation_info.get('masters')[0].get('masterProperties').get('displayName')
    
    @property
    def master_colors(self):
        if self.__presentation_info.get('masters') is not None:
            color_objects = list()
            for prop in self.__presentation_info.get('masters'):
                colors = prop.get('pageProperties').get('colorScheme').get('colors')
                for color in colors:
                    obj = {'type':color.get('type')}
                    obj.update(color.get('color'))
                    color_objects.append(pd.DataFrame(obj, index=[0])) 
            color_objects = pd.concat(color_objects, axis=0, ignore_index=True)
        else:
            color_objects = pd.DataFrame()
        return color_objects
    
    @property
    def master_fonts(self):
        if self.__presentation_info.get('masters') is not None:
            fonts = list()
            for prop in self.__presentation_info.get('masters'):
                for element in prop.get('pageElements'):
                    text = element.get('shape').get('text')
                    if text is not None:
                        for text_element in text.get('textElements'):
                            text_run = text_element.get('textRun')
                            if text_run is not None:
                                fonts.append(text_run.get('style').get('fontFamily'))
            fonts = list(set(fonts)) # To get unique values
        else:
            fonts = list()
        return fonts
        
    @property
    def slides_notes(self):
        notes = dict()
        for slide_id, slide_info in self.slides.items():
            notes.update({slide_id:None})
            page_notes = dict()
            for element in slide_info.get('slideProperties').get('notesPage').get('pageElements'):
                shape = element.get('shape')
                if shape.get('shapeType') == 'TEXT_BOX' and shape.get('text') is not None:
                    note = [text.get('textRun').get('content') for text in shape.get('text').get('textElements') if text.get('textRun') is not None]
                    note = [re.sub('\n$', '', text) for text in note]
                    page_notes.update({element.get('objectId'):note})
            notes[slide_id] = page_notes
        return notes
    
    @property
    def slides_ids(self):
        return list(self.slides.keys())
        
    @classmethod
    def create(cls, file_name, parent_folder_id=None, transfer_permissions=False, **kwargs):
        """Class method to create a Google Slides file.

        Args:
            file_name (str): Name of new file.
            parent_folder_id (str, optional): ID of parent folder. Defaults to None.
            transfer_permissions (bool, optional): Whether to copy permissions from parent folder. Defaults to False.
            
        Returns:
            GoogleSlides object.
        """
        new_file = super().create(file_name=file_name,
                                  mime_type='application/vnd.google-apps.presentation',
                                  parent_folder_id=parent_folder_id,
                                  transfer_permissions=transfer_permissions, 
                                  **kwargs)
        return new_file
    
    def execute_batch_update(self, requests):
        """Applies one or more updates to the presentation.
        Implementation of: https://developers.google.com/slides/api/reference/rest/v1/presentations/batchUpdate.
        Beside updating the presentation, it also updates the __presentation_info attribute.

        Args:
            requests (list): List of update requests.

        Returns:
            dict: Response to the update requests.
        """
        
        body = {'requests': requests}
        response = self.services.get('slides').presentations().batchUpdate(presentationId=self.file_id,
                                                                        body=body).execute()
        # Update presentation info
        self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
        return response
    
    def batch_delete_text(self, elements_ids):
        """Delete text inside of objects.

        Args:
            elements_ids (list): List of IDs of elements from which to delete the text.
        """
        
        ids = ', '.join(elements_ids)
        requests = list()
        for id in elements_ids:
            requests.append({'deleteText': {'objectId': id}})
        try: 
            self.execute_batch_update(requests)
            if len(elements_ids) == 1:
                print('Text in object with ID "{}" deleted.'.format(ids))
            else:
                print('Text in objects with IDs "{}" deleted.'.format(ids))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def delete_slides_notes(self, slides_ids=[]):
        """Delete notes from slides.

        Args:
            slides_ids (list, optional): List of slides IDs from where to delete notes. Defaults to [] (i.e. all).
        """
        if slides_ids==[]:
            slides_ids = self.slides_ids
            
        objects = []
        for id in slides_ids:
            if self.slides_notes.get(id) != {}:
                objects.append(list(self.slides_notes.get(id).keys()))
        objects = list(chain(*objects)) 
        self.batch_delete_text(objects_ids=objects)
    
    def add_slide(self, layout='TITLE_AND_BODY', index=-1):
        """Add slide to presentation.

        Args:
            layout (str, optional): Name or display name of layout. Defaults to 'TITLE_AND_BODY'.
            index (int, optional): Index where to add new slide. Defaults to -1 (i.e. end of presentation).

        Raises:
            ValueError: If the given layout is not included in the property layout types.
        
        Returns:
            str: ID of the new slide.
        """
        
        layouts = self.layout_types
        
        if len(layouts.index) == 0:
            warnings.warn('No specified layouts in the presentation, new slide will be of unspecified layout')
            layout_type='PREDEFINED_LAYOUT_UNSPECIFIED' 
        elif layout in layouts['displayName'].to_list():
            layout_type = layouts[layouts['displayName'] == layout]['name'].values[0]
        elif layout in layouts['name'].to_list():
            layout_type = layout
        else:
            raise ValueError('The layout must be one of those from the property layout types.')
        
        if index < 0:
            number = len(self.slides) + index + 1
        else:
            number = index
            
        requests = [{"createSlide": {"insertionIndex": number,
                                     "slideLayoutReference": {"predefinedLayout": layout_type}}}]
        try:
            response = self.execute_batch_update(requests=requests)
            print('Added slide at index {}'.format(number))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
        return response.get('replies')[0].get('createSlide').get('objectId')
            
    def move_slide(self, slide_id, new_index=-1):
        """Move slide to new position in the presentation.

        Args:
            slide_id (str): ID of the slide to move.
            new_index (int, optional): Index where to move the slide. Defaults to -1 (i.e. end of presentation).
        """
        
        if new_index < 0:
            number = len(self.slides) + new_index + 1
        else:
            number = new_index
        
        requests = [{"updateSlidesPosition": {"slideObjectIds": [slide_id],
                                              "insertionIndex": number,},},]
        # body = {'requests': requests}
        try:
            self.execute_batch_update(requests=requests)
            print('Slide {id} moved to index {index}'.format(id=slide_id, index=number))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def table_to_df(self, page_id='', table_id='', column_names=True):
        """Extract text from a table into a pandas DataFrame.
        
        At least one of page_id or table_id needs to be different than ''.

        Args:
            page_id (str, optional): ID of the page where the table is located. Defaults to ''.
            table_id (str, optional): ID of the table. Defaults to ''.
            column_names (bool, optional): Whether the first row should be considered as the table column names. Defaults to True.

        Raises:
            ValueError: If the given page does not have tables in it.
            ValueError: If both page_id and table_id are ''.

        Returns:
            pandas.DataFrame: Text from table.
        """
        
        if table_id != '' and page_id == '':
            info = self.find_element(element_id=table_id, element_kinds=['table'])
            page_id = list(info.keys())[0]
        elif table_id == '' and page_id != '':
            tables = self.get_elements_ids(element_kinds=['table'], pages_ids=[page_id])
            tables_ids = list(next(iter(tables.values())).keys())
                # If there is only one table in the page, you can leave ID empty, otherwise you need to to indicate it to correctly identify the table
            if len(tables_ids) == 0:
                raise ValueError('The indicated page does not have tables in it.')
            elif len(tables_ids) > 1:
                warnings.warn('The indicated page has more than one table, the first one will be taken.')
            table_id = tables_ids[0]
        elif table_id == '' and page_id == '':
            raise ValueError('At least one of page_id or table_id needs to be given.')
            
        # Get rows of the table
        table = [object for object in self.slides.get(page_id).get('pageElements') if object.get('objectId') == table_id][0]
        table_rows = table.get('table').get('tableRows')

        # Go through every row and its cells to extract text
        table_text = list()
        for row in table_rows:
            row_text = list()
            for cell in row.get('tableCells'):
                cell_text = cell.get('text').get('textElements')[1].get('textRun').get('content')
                cell_text = re.search('\{\{([^)]+)\}\}', cell_text).group(1)
                row_text.append(cell_text)
            table_text.append(row_text)

        # Transform nested list into pandas DataFrame
        if column_names == True:
            columns = table_text[0]
            data = table_text[1:]
            table_df = pd.DataFrame(data, columns=columns)
        elif column_names == False:
            table_df = pd.DataFrame(table_text)
            
        return table_df

    def text_replace(self, placeholder_text, value, pages_ids=[]):
        """Replace a text placeholder with a new value.
        Placeholders are constructed as {{placeholder_text}}, thus here only write the text inside the parenthesis.

        Args:
            placeholder_text (str): Placeholder text to replace.
            value (str): New value to replace placeholder with.
            pages_ids (list, optional): List of page IDs where to perform replacement. Defaults to [] (i.e. all).
        """
            
        assert isinstance(value, str), Exception('The value {} is not a string'.format(value))
        requests = [{"replaceAllText": {"containsText": {"text": '{{' + placeholder_text + '}}'},
                                        "replaceText": str(value),
                                        "pageObjectIds": pages_ids}}]
        try: 
            self.execute_batch_update(requests)
            print('Text successufly replaced.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def batch_text_replace(self, text_mapping, pages_ids=[]):
        """Replaces text placeholders.
        Placeholders are constructed as {{placeholder_text}}, thus here only write the text inside the parenthesis.
        Text mapping needs to be constructed as {placeholder_text:value}.

        Args:
            text_mapping (dict): Keys are the placeholders to replace, values the new values to impute (both must be strings).
            pages_ids (list, optional): List of page IDs where to perform replacement. Defaults to [] (i.e. all).

        Raises:
            Exception: If text from a key is not a string.
        """
        
        requests = list()
        for placeholder_text, new_value in text_mapping.items():
            requests.append({"replaceAllText": {"containsText": {"text": '{{' + placeholder_text + '}}'},
                                                "replaceText": str(new_value),
                                                "pageObjectIds": pages_ids}})
        try: 
            self.execute_batch_update(requests)
            print('Batch text replacement successful.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
    
    def df_text_replace(self, df, page_id='', table_id='', column_names=True):
        """Replaces text placeholders with data from a pandas DataFrame.
        
        At least one of page_id or table_id needs to be different than ''.

        Args:
            df (pandas.DataFrame): DataFrame with the values to raplace with.
            page_id (str, optional): ID of the page where the table is. Defaults to ''.
            table_id (str, optional): ID of the table. Defaults to ''.
            column_names (bool, optional): Whether column names also have placeholders to replace. Defaults to True.
        """
        
        # Get dataframe with placeholders
        placeholders_table = self.table_to_df(page_id=page_id, table_id=table_id, column_names=column_names)
        
        # Check that the tables have the same shape
        assert placeholders_table.shape == df.shape, 'The tables need to have the same shape.'
        
        # Create replacement mapping by getting keys from presentation table and values from df
        placeholders_list = [list(row) for row in placeholders_table.itertuples(index=False, name=None)]
        placeholders_list = list(chain(*placeholders_list))
        placeholders_list = map(lambda x: re.search('\{\{([^)]+)\}\}', x).group(1), placeholders_list)
        values_list = [list(row) for row in df.itertuples(index=False, name=None)]
        values_list = list(chain(*values_list))
        values_list = map(str, values_list)
        df_mapping = dict(zip(placeholders_list, values_list))
        
        # Apply text replace to the created mapping
        self.batch_text_replace(text_mapping=df_mapping, pages_ids=[page_id]) 
        
    def insert_image(self, image_url, page_id, object_id=None, transform=None, size=None):
        """Insert image inside of a page.
        The image needs to be publicly accessible, within size limit and in supported formats.
        You can insert an image from Google Drive by getting the download_url of the GoogleDriveFile object.

        Args:
            image_url (str): URL of the image.
            page_id (str): ID of the page where to insert the image.
            object_id (str, optional): ID of the image object. Defaults to None (i.e. assigned by the API).
            transform (dict, optional): Optional transformations. Defaults to None.
            size (float, optional): Sizing of image. Defaults to None.

        Returns:
            str: ID of image element.
        """
        requests = [
            {
                'createImage': {
                    'objectId': object_id,
                    'url': image_url,
                    'elementProperties': {
                        'pageObjectId': page_id,
                        'transform': transform,
                        'size': size
                    },
                }
            },
        ]

        try: 
            response = self.execute_batch_update(requests)
            print('Inserted image in page with ID {}.'.format(page_id))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
        return response.get('replies')[0].get('createImage').get('objectId')

    def replace_shape_with_image(self, placeholder_text, image_url):
        """Replace shape with placeholder with image.
        
        Placeholders are constructed as {{placeholder_text}}, thus here only write the text inside the parenthesis.
        The image needs to be publicly accessible, within size limit and in supported formats.
        You can insert an image from Google Drive by getting the download_url of the GoogleDriveFile object.

        Args:
            placeholder_text (str): Placeholder text to replace.
            image_url (str): URL of the image.
        """
        
        # TODO: CHeck if the pages can be limited as in replace_text
        requests = [
            {
                "replaceAllShapesWithImage": {
                    "imageUrl": image_url,
                    "replaceMethod": "CENTER_INSIDE",
                    "containsText": {
                        "text": "{{" + placeholder_text + "}}",
                    }
                }
            }]
        try: 
            self.execute_batch_update(requests)
            print('Shape replaced with image.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    def replace_shape_with_chart(self, placeholder_text, 
                                spreadsheet_id, chart_id, 
                                linking_mode='NOT_LINKED_IMAGE', 
                                pages_ids=[]):
        """Replace shape with placeholder with a chart from a Google Sheets file.
        
        Placeholders are constructed as {{placeholder_text}}, thus here only write the text inside the parenthesis.
        See https://developers.google.com/slides/api/reference/rest/v1/presentations/request#LinkingMode_1 for the two linking_mode options.

        Args:
            placeholder_text (str): Placeholder text to replace.
            spreadsheet_id (str): ID of a Google Sheets file.
            chart_id (str): ID of chart inside of the Google Sheets file.
            linking_mode (str, optional): Mode of linking presentatation to spreadsheet chart. Defaults to 'NOT_LINKED_IMAGE'.
            pages_ids (list, optional): List of page IDs where to perform replacement. Defaults to [] (i.e. all).
        """
        
        assert linking_mode in ['NOT_LINKED_IMAGE', 'LINKED'], 'See https://developers.google.com/slides/api/reference/rest/v1/presentations/request#LinkingMode_1 for the two linking_mode options.'
        
        requests = [{
                "replaceAllShapesWithSheetsChart": {
                    "containsText": 
                        {
                            "text": placeholder_text,
                            "matchCase": True
                        },
                    "spreadsheetId": spreadsheet_id,
                    "chartId": chart_id,
                    "linkingMode": linking_mode, # Unlinked by default, see other options https://developers.google.com/slides/api/reference/rest/v1/presentations/request#LinkingMode_1
                    "pageObjectIds": pages_ids
                }
            }]
        try: 
            self.execute_batch_update(requests)
            print('Shape replaced with chart.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def get_elements_ids(self, element_kinds=[], pages_ids=[]):
        """Get IDs for the page elements in your presentation.
        Check this link for the possble element kinds: https://developers.google.com/slides/api/concepts/page-elements
        The result is a nested dictionary of the type: {'pageId':{'objectId':'elementKind'}}.

        Args:
            pages_ids (list, optional): IDs of the pages to look at. Defaults to [] (i.e. all).
            element_kinds (list, optional): Kinds of elements to search for. Defaults to [] (i.e. all).

        Returns:
            dict: Nested dictionary where first key is the page ID, second key is the element ID and the final value is the element kind.
        """
        
        if pages_ids==[]:
            pages_ids = self.slides_ids
        if element_kinds==[]:
            element_kinds = utils.page_element_kinds()

        objects = dict()
        for slide_id, slide_info in self.slides.items():
            if slide_id in pages_ids:
                objects.update({slide_id:None})
                page_objects = dict()
                for element in slide_info.get('pageElements'):
                    for kind in element_kinds:
                        if element.get(kind) is not None:
                            page_objects.update({element.get('objectId'):kind})
                objects[slide_id] = page_objects
        # TODO: Review this method according to the info here https://developers.google.com/slides/api/samples/reading
            
        return objects
    
    def find_element(self, element_id, element_kinds = [], pages_ids=[]):
        """Find the page for an element in the presentation.

        Args:
            element_id (str): ID of the element to find.
            element_kinds (list, optional): Kind of the element to find. Defaults to [] (i.e. all).
            pages_ids (list, optional): List of pages where the element could be. Defaults to [] (i.e. all).

        Returns:
            dict: Nested dictionary with page ID, element ID and finally the kind.
        """
        
        if pages_ids==[]:
            pages_ids = self.slides_ids
        if element_kinds==[]:
            element_kinds = utils.page_element_kinds()
            
        objects = dict()
        for slide_id, slide_info in self.slides.items():
            if slide_id in pages_ids:
                objects.update({slide_id:None})
                page_objects = dict()
                for element in slide_info.get('pageElements'):
                    for kind in element_kinds:
                        if element.get(kind) is not None:
                            if element.get('objectId') == element_id:
                                page_objects.update(element)
                objects[slide_id] = page_objects
        element_info = {key:value for key, value in objects.items() if value != {}}
        
        return element_info
    
    def transform_element(self, element_id, transform, apply_mode='ABSOLUTE'):
        """Transform an element.
        
        Args:
            element_id (str): ID of the element to transform.
            transform (dict): Dictionary with the transformations to be performed.
            apply_mode (str, optional): How to apply transformation (https://developers.google.com/slides/api/reference/rest/v1/presentations/request#ApplyMode). Defaults to 'ABSOLUTE'.

        Returns:
            dict: Response of batch update.
        """
        requests = [
            {
                'updatePageElementTransform': {
                    'objectId': element_id,
                    'transform': transform,
                    'applyMode': apply_mode
                }
            },
        ]

        response = self.execute_batch_update(requests)
        return response
    
    def get_shapes_placeholders(self, pages_ids=[]):
        """Get placeholders in shape objects.
        If you need the placeholders inside of table cells, use the method table_to_df.
        The result is a nested dictionary of the type: {'pageId':{'objectId':['placeholder1', 'placeholder2']}}. 

        Args:
            pages_ids (list, optional): IDs of the pages to look at. Defaults to [] (i.e. all).

        Returns:
            dict: Nested dictionary where first key is the page ID, second key is the element ID and the final value is a list of placeholders.
        """
        
        if pages_ids==[]:
            pages_ids = self.slides_ids
            
        shapes = dict()
        for slide_id, slide_info in self.slides.items():
            if slide_id in pages_ids:
                shapes.update({slide_id:None})
                page_shapes = dict()
                for element in slide_info.get('pageElements'):
                    if element.get('shape') is not None:
                        if element.get('shape').get('text') is not None:
                            shape_contents = [text.get('textRun').get('content') for text in element.get('shape').get('text').get('textElements') if text.get('textRun') is not None]
                            shape_contents = shape_contents = [re.search('\{\{([^)]+)\}\}', text).group(0) for text in shape_contents if bool(re.search('\{\{([^)]+)\}\}', text))]
                            page_shapes.update({element.get('objectId'):shape_contents})
                shapes[slide_id] = page_shapes
 
        return shapes
        
    def duplicate_object(self, object_id):
        """Duplicate a presentation object.

        Args:
            object_id (str): ID of the object to duplicate.

        Returns:
            str: ID of the new object.
        """
        
        requests = [{'duplicateObject': {'objectId': object_id}},]
        try: 
            response = self.execute_batch_update(requests)
            print('Object with ID "{}" duplicated.'.format(object_id))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        return response.get('replies')[0].get('duplicateObject').get('objectId')

    def batch_delete_object(self, objects_ids):
        """Delete multiple objects from presentation.

        Args:
            objects_ids (list): List of IDs of objects to delete.
        """
        
        ids = ', '.join(objects_ids)
        requests = list()
        for id in objects_ids:
            requests.append({'deleteObject': {'objectId': id}})
        try: 
            self.execute_batch_update(requests)
            if len(objects_ids) == 1:
                print('Object with ID "{}" deleted.'.format(ids))
            else:
                print('Objects with IDs "{}" deleted.'.format(ids))    
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
                                    
    def format_table(self, table_id, execute=True, text=True,
                    fill_color={'red':1, 'green':1, 'blue': 1}, text_color={'red':0, 'green':0, 'blue': 0},
                    text_bold=False, text_font='Arial', text_size=12,
                    header=True, header_rows=1, header_cols=0, header_fill_color='DARK1',
                    header_text_color='LIGHT1', header_text_bold=True, header_text_font='', header_text_size=14):
        """Format table background color and text and, if desidered, also of header.
        
        The color parameters can be either a dictionary with the values of red, green and blue to use or the name of one of the master colors.

        Args:
            table_id (str): ID of the table to format.
            execute (bool, optional): Whether to execute or to return the requests list. Defaults to True.
            text (bool, optional): Whether also to format text, because when there is no text in the table, formatting it will not change anything. Defaults to True.
            fill_color (str or dict, optional): Color to fill the table. Defaults to {'red':1, 'green':1, 'blue': 1} (i.e. white).
            text_color (str or dict, optional): Color for the table text. Defaults to {'red':0, 'green':0, 'blue': 0} (i.e. black).
            text_bold (bool, optional): Whether table text should be bold. Defaults to False.
            text_font (str, optional): Font of the table text. Defaults to 'Arial'.
            text_size (int, optional): Size of the table text. Defaults to 12.
            header (bool, optional): Whether to format the header differently. Defaults to True.
            header_rows (int, optional): How many rows should be included in header. Defaults to 1.
            header_cols (int, optional): How many columns should be included in header. Defaults to 0.
            header_fill_color (str or dict, optional): Color to fill the header, if header is True. Defaults to 'DARK1'.
            header_text_color (str or dict, optional): Color for the header text, if header is True. Defaults to 'LIGHT1'.
            header_text_bold (bool, optional): Whether the header text should be bold. Defaults to True.
            header_text_font (str, optional): Font of the header text. Defaults to '' (i.e. first master font).
            header_text_size (int, optional): Size of the header text. Defaults to 14.

        Returns:
            list: If requests is set to True, it returns the list of requests. Otherwise it executes them and prints confirmation.
        """
        
        table = Table(slides_file=self, table_id=table_id)  
        
        requests = list()
        
        # Fill cells
        if header == True:
            requests += table.fill_header(header_rows=header_rows, header_cols=header_cols, fill_color=header_fill_color)
            row_index = header_rows
            col_index = header_cols
            row_span = table.n_rows - header_rows
            col_span = table.n_cols - header_cols
        else:
            row_index = 0
            col_index = 0
            row_span = table.n_rows
            col_span = table.n_cols
        if isinstance(fill_color, dict):
            fill=utils.get_rgb_color(color_dict=fill_color)
        elif isinstance(fill_color, str):
            fill=utils.validate_color(slides_file=self, color_type=fill_color)
        requests += table.fill_cells(row_span=row_span, col_span=col_span, 
                                         rgb_color=fill, 
                                         row_index=row_index, col_index=col_index)
        
        # Format cells' text
        if text == True:
            cell_indexes = list(product(list(range(table.n_rows)), list(range(table.n_cols))))
            for row, col in cell_indexes:
                # cell_type = True if cell[0] < header_rows or cell[1] < header_cols else False
                if header == True and (row < header_rows or col < header_cols):
                    if isinstance(header_text_color, dict):
                        color=utils.get_rgb_color(color_dict=header_text_color)
                    elif isinstance(header_text_color, str):
                        color=utils.validate_color(slides_file=self, color_type=header_text_color)
                    bold=header_text_bold
                    font=header_text_font
                    size=header_text_size
                else:
                    if isinstance(text_color, dict):
                        color=utils.get_rgb_color(color_dict=text_color)
                    elif isinstance(text_color, str):
                        color=utils.validate_color(slides_file=self, color_type=text_color)
                    bold=text_bold
                    font=text_font
                    size=text_size
                requests += table.color_text_cell(row=row, col=col, 
                                                    rgb_color=color, 
                                                    bold=bold, 
                                                    font=font, 
                                                    size=size)
        if execute == False:
            return requests
        elif execute == True:
            self.execute_batch_update(requests)
            self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
            print('Formatted table with ID {}.'.format(table_id))
        
    def insert_table(self, page_id, n_rows, n_cols,
                     header=True, header_rows=1, header_cols=0, fill_color='DARK1'):
        """Add a table to a slide.
        The parameters header_rows, header_cols and fill_color are only used only used if header is True. 
        The parameter fill_color can be either a dictionary with the values of red, green and blue to use or the name of one of the master colors.

        Args:
            page_id (str): ID of the page where the table is.
            n_rows (int): Number of rows of the table.
            n_cols (int): Number of columns of the table.
            header (bool, optional): Whether to fill the header. Defaults to True.
            header_rows (int, optional): How many rows should be included in header. Defaults to 1.
            header_cols (int, optional): How many columns should be included in header. Defaults to 0.
            fill_color (str or dict, optional): Color to fill the header, if header is True. Defaults to 'DARK1'.

        Returns:
            str: ID of the created table.
        """
        
        table_request = Table.create(page_id=page_id, n_rows=n_rows, n_cols=n_cols)
        response = self.execute_batch_update(table_request)
        table_id = response.get('replies')[0].get('createTable').get('objectId')
        if header == True:
            # header_request = Table(slides_file=self, table_id=table_id)\
            #             .fill_header(header_rows=header_rows, header_cols=header_cols, fill_color=fill_color)
            header_request = self.format_table(table_id=table_id, page_id=page_id, execute=False, text=False,
                                               header=True, header_rows=header_rows, header_cols=header_cols,
                                               header_fill_color=fill_color)
            self.execute_batch_update(header_request)
        
        print('Created table in page {page} with ID {table}.'.format(page=page_id, table=table_id))
        return table_id   
    
    def fill_table(self, df, table_id, execute=True, column_names=True, row_index=0, col_index=0):
        """Fill table with text from a pandas DataFrame.

        Args:
            df (pandas.DataFrame): DataFrame where to take the values from.
            table_id (str): ID of the table.
            execute (bool, optional):  Whether to execute or to return the requests list. Defaults to True.
            column_names (bool, optional): Whether to include the DataFrame column names in the table. Defaults to True.
            row_index (int, optional): From which row index to start the value imputation. Defaults to 0.
            col_index (int, optional): From which column index to start the value imputation. Defaults to 0.

        Returns:
            list: If requests is set to True, it returns the list of requests. Otherwise it executes them and prints confirmation.
        """
        
        if column_names == True:
            df = pd.DataFrame(np.vstack([df.columns, df]))
        
        # If table is smaller than dataframe, fill with what fits and raise a warning
        table = Table(self, table_id)
        n_rows = table.n_rows
        n_cols = table.n_cols
        if len(df.index) < n_rows or len(df.columns) < n_cols:
            warnings.warn('Dataframe is bigger than table, exceding cells will not be transferred.')
        
        # Fill table with values from dataframe
        requests = list()
        for row in range(n_rows):
            for col in range(n_cols):
                cell = df.iloc[row, col]
                requests.append({"insertText": {"objectId": table_id,
                                                "cellLocation": {
                                                    "rowIndex": row_index+row,
                                                    "columnIndex": col_index+col},
                                                "text": str(cell),
                                                "insertionIndex": 0}}) 
        
        if execute == False:
            return requests
        elif execute == True:
            self.execute_batch_update(requests)
            # https://stackoverflow.com/questions/18425225/getting-the-name-of-a-variable-as-a-string
            print('Table with ID {table} has been filled with data from DataFrame {df}.'.format(table=table_id,
                                                                                                df=f'{df=}'.split('=')[0])) 
        
    def df_to_table(self, df, page_id, 
                    fill_color={'red':1, 'green':1, 'blue': 1}, text_color={'red':0, 'green':0, 'blue': 0},
                    text_bold=False, text_font='Arial', text_size=12,
                    header=True, header_rows=1, header_cols=0, header_fill_color='DARK1',
                    header_text_color='LIGHT1', header_text_bold=True, header_text_font='', header_text_size=14):
        """Insert table from a pandas DataFrame.

        Args:
            df (pandas.DataFrame): DataFrame to insert.
            page_id (str): ID of the page where to insert the table.
            fill_color (str or dict, optional): Color to fill the table. Defaults to {'red':1, 'green':1, 'blue': 1} (i.e. white).
            text_color (str or dict, optional): Color for the table text. Defaults to {'red':0, 'green':0, 'blue': 0} (i.e. black).
            text_bold (bool, optional): Whether table text should be bold. Defaults to False.
            text_font (str, optional): Font of the table text. Defaults to 'Arial'.
            text_size (int, optional): Size of the table text. Defaults to 12.
            header (bool, optional): Whether to format the header differently. Defaults to True.
            header_rows (int, optional): How many rows should be included in header. Defaults to 1.
            header_cols (int, optional): How many columns should be included in header. Defaults to 0.
            header_fill_color (str or dict, optional): Color to fill the header, if header is True. Defaults to 'DARK1'.
            header_text_color (str or dict, optional): Color for the header text, if header is True. Defaults to 'LIGHT1'.
            header_text_bold (bool, optional): Whether the header text should be bold. Defaults to True.
            header_text_font (str, optional): Font of the header text. Defaults to '' (i.e. first master font).
            header_text_size (int, optional): Size of the header text. Defaults to 14.

        Raises:
            ValueError: If page_id is not one of the current presentation.

        Returns:
            str: ID of the newly created table.
        """
        
        assert isinstance(df, pd.DataFrame), 'df must be a pandas DataFrame.'
        if page_id not in self.slides_ids:
            raise ValueError('page_id must be an existing ID of a slide in this presentation.')
        
        # Convert column names into first row
        df = pd.DataFrame(np.vstack([df.columns, df]))
        
        # Create table
        table_id = self.insert_table(page_id=page_id, n_rows=len(df.index), n_cols=len(df.columns), header=False)
        
        # Fill table with values from dataframe
        requests = self.fill_table(df=df, table_id=table_id, execute=False, column_names=False)  
                
        # Format table
        requests += self.format_table(table_id=table_id, execute=False, text=True,
                                          fill_color=fill_color, text_color=text_color,
                                          text_bold=text_bold, text_font=text_font, text_size=text_size,
                                          header=header, header_rows=header_rows, header_cols=header_cols,
                                          header_fill_color=header_fill_color, header_text_color=header_text_color,
                                          header_text_bold=header_text_bold, header_text_font=header_text_font,
                                          header_text_size=header_text_size)
        try:
            self.execute_batch_update(requests)
        except Warning:
            print('Cell filling and/or formatting was unsuccessful, but table was still created.')

        return table_id 
        
        
        

    

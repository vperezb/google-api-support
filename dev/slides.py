# from socket import NI_NUMERICSERV
import pandas as pd
import numpy as np
import re
from itertools import chain
from apiclient import errors
from warnings import warn
from dev.drive import GoogleDriveFile
from dev import utils
from dev.slide_table import Table
from GoogleApiSupport import auth, apis

class GoogleSlides(GoogleDriveFile):
    
    services = {api_name: auth.get_service(api_name) for api_name in apis.api_configs}
    
    def __new__(cls, file_id=None):
        mime_type = cls.services.get('drive').files().get(fileId=file_id, fields='*').execute().get('mimeType')
        assert mime_type == 'application/vnd.google-apps.presentation', 'The file is of type "{type}", but it needs to be Google Slides to be of this class type.'.format(type=mime_type)
        return super().__new__(cls)
    
    def __init__(self, file_id=None):
        super().__init__(file_id=file_id)
        
        # Additional spreadsheet specific info
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
        new_file = super().create(file_name=file_name, 
                                  mime_type='application/vnd.google-apps.presentation',
                                  parent_folder_id=parent_folder_id, 
                                  transfer_permissions=transfer_permissions, 
                                  **kwargs)
        return new_file
    
    def execute_batch_update(self, requests):
        body = {'requests': requests}
        response = self.services.get('slides').presentations().batchUpdate(presentationId=self.file_id,
                                                                        body=body).execute()
        # Update presentation info
        self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
        return response

    def delete_slides_notes(self, slides_ids=[]):
        if slides_ids==[]:
            slides_ids = self.slides_ids
            
        objects = []
        for id in slides_ids:
            if self.slides_notes.get(id) != {}:
                objects.append(list(self.slides_notes.get(id).keys()))
        objects = list(chain(*objects)) 
        self.batch_delete_text(objects_ids=objects)
    
    def add_slide(self, layout='TITLE_AND_BODY', index=-1):
        layouts = self.layout_types
        
        if len(layouts.index) == 0:
            warn('No specified layouts in the presentation, new slide will be of unspecified layout')
            layout_type='PREDEFINED_LAYOUT_UNSPECIFIED' 
        elif layout in layouts['displayName'].to_list():
            layout_type = layouts[layouts['displayName'] == layout]['name'].values[0]
        elif layout in layouts['name'].to_list():
            layout_type = layout
        else:
            raise ValueError('The layout must be one of those from the attribute layout types.')
        
        if index < 0:
            number = len(self.slides) + index + 1
        else:
            number = index
            
        requests = [{"createSlide": {"insertionIndex": number,
                                     "slideLayoutReference": {"predefinedLayout": layout_type}}}]
        try:
            # QQ: return ID of new slide?
            self.execute_batch_update(requests=requests)
            print('Added slide at index {}'.format(number))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def move_slide(self, slide_id, new_index=-1):
        
        if new_index < 0:
            number = len(self.slides) + new_index + 1
        else:
            number = new_index
        
        requests = [{"updateSlidesPosition": {"slideObjectIds": [slide_id],
                                              "insertionIndex": number,},},]
        # body = {'requests': requests}
        try:
            # response = services.get('slides').presentations().batchUpdate(presentationId=self.file_id,
            #                                                               body=body).execute()
            self.execute_batch_update(requests=requests)
            # slides_info = self.services.get('slides').spreadsheets().get(spreadsheetId=self.file_id, fields='slides').execute()
            # self.slides = {slide.get('objectId'):{key:value for key, value in slide.items() if key != 'objectId'} for slide in slides_info.get('slides')}
            print('Slide {id} moved to index {index}'.format(id=slide_id, index=number))
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def text_replace(self, placeholder_text, value, pages_ids=None):

        if pages_ids is None:
            pages_ids = list()
            
        assert isinstance(value, str), Exception('The value {} is not a string'.format(value))
        requests = [{"replaceAllText": {"containsText": {"text": '{{' + placeholder_text + '}}'},
                                        "replaceText": value,
                                        "pageObjectIds": pages_ids}}]
        try: 
            self.execute_batch_update(requests)
            print('Text successufly replaced.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def batch_text_replace(self, text_mapping, pages_ids=[]):
        """Replaces text placeholders.
        This needs to be written as {{placeholder_text}}.

        Args:
            text_mapping (dict): Keys are the placeholders to replace, values the new values to impute (both must be strings).
            pages_ids (list, optional): List ofIDs of the pages. Defaults to empty list (i.e. all)

        Raises:
            Exception: If text from a key is not a string.
        """
        
        requests = list()
        for placeholder_text, new_value in text_mapping.items():
            if isinstance(new_value, str):
                requests += [{"replaceAllText": {"containsText": {"text": '{{' + placeholder_text + '}}'},
                                                    "replaceText": new_value,
                                                    "pageObjectIds": pages_ids}}]
            else:
                raise Exception('The value from key {} is not a string'.format(placeholder_text))
        try: 
            self.execute_batch_update(requests)
            print('Batch text replacement successful.')
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
        
    # def df_text_replace(self, df, sep='_', pages_ids=[]):
    #     """Replaces text placeholders with data from a pandas DataFrame.
    #     This is meant to be used for replace placeholders in a table with data from a dataframe of the same size.
    #     The placeholder text needs to written as {{df_column_name+sep+df_index}}.

    #     Args:
    #         df (pandas.DataFrame): Pandas DataFrame with the values to raplace with.
    #         sep (str, optional): Separator for DataFrame column name and index in the placeholder text. Defaults to '_'.
    #         pages_ids (list, optional): List ofIDs of the pages. Defaults to empty list (i.e. all)
    #     """
        
    #     # Creating the mapping of text name and value from dataframe
    #     nested_dict = df.to_dict()
    #     list_of_dict = pd.json_normalize(nested_dict, sep=sep).to_dict('records')
    #     df_mapping = list_of_dict[0]    
        
    #     # Apply text replace to the created mapping
    #     self.batch_text_replace(text_mapping=df_mapping, pages_ids=pages_ids) 
    
    def df_text_replace(self, df, page_id, table_id='', column_names=True):
        """Replaces text placeholders with data from a pandas DataFrame.
        This is meant to be used for replace placeholders in a table with data from a dataframe of the same size.
        The placeholder text needs to written as {{df_column_name+sep+df_index}}.

        Args:
            df (pandas.DataFrame): Pandas DataFrame with the values to raplace with.
            sep (str, optional): Separator for DataFrame column name and index in the placeholder text. Defaults to '_'.
            page_id (str): ID of the page where the table is.
            table_id (str, optional): ID of the table. Defaults to '', which works only if there is just one table in the page.
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

    def replace_shape_with_image(self, placeholder_text, image_url):
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
            # Update presentation info
            # self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def replace_shape_with_drive_image(self, placeholder_text, image_file_id):
        image_file = GoogleDriveFile(file_id=image_file_id)
        image_url = image_file._info.get('webContentLink')
        self.replace_shape_with_image(placeholder_text=placeholder_text,
                                      image_url=image_url)
        
    def replace_shape_with_chart(self, placeholder_text, 
                                spreadsheet_id, chart_id, 
                                linking_mode='NOT_LINKED_IMAGE', 
                                pages_ids=[]):
        
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
            # Update presentation info
            # self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
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
    
    def table_to_df(self, page_id, table_id='', column_names=True):
        """Extract text from a table into a pandas DataFrame.

        Args:
            page_id (str): ID of the page where the table is located
            table_id (str, optional): ID of the table. It must be given if more than one table exists in the page. Defaults to '' (i.e. only table in page).
            column_names (bool, optional): Whether the first row should be considered as the table column names. Defaults to True.

        Raises:
            ValueError: If the indicated page has more than one table but the table ID is not specified.
            ValueError: If the table ID dos not exist in the indicated page.

        Returns:
            pandas.DataFrame: Text from table.
        """
        
        # Get information about tables in the indicated page
        tables = self.get_elements_ids(element_kinds=['table'], pages_ids=[page_id])
        tables_ids = list(next(iter(tables.values())).keys())

        if table_id == '':
            # If there is only one table in the page, you can leave ID empty, otherwise you need to to indicate it to correctly identify the table
            if len(tables_ids) != 1:
                raise ValueError('The indicated page has more than one table, need to given also the objectId of the table.')
            else:
                table_id = tables_ids[0]
        elif isinstance(table_id, str):
            if table_id not in tables_ids:
                raise ValueError('Could not find a table with that table_id. Check the indicated value.')
            
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
    
    def duplicate_object(self, object_id):
        requests = [{'duplicateObject': {'objectId': object_id}},]
        try: 
            self.execute_batch_update(requests)
            print('Object with ID "{}" duplicated.'.format(object_id))
            # Update presentation info
            # self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)

    def batch_delete_object(self, objects_ids):
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
            # Update presentation info
            # self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()       
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
    def batch_delete_text(self, objects_ids):
        ids = ', '.join(objects_ids)
        requests = list()
        for id in objects_ids:
            requests.append({'deleteText': {'objectId': id}})
        try: 
            self.execute_batch_update(requests)
            if len(objects_ids) == 1:
                print('Text in object with ID "{}" deleted.'.format(ids))
            else:
                print('Text in objects with IDs "{}" deleted.'.format(ids))
            # Update presentation info
            # self.__presentation_info = self.services.get('slides').presentations().get(presentationId=self.file_id, fields='*').execute()
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
                
    def create_table(self, page_id, n_rows, n_cols, 
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
            header_request = Table(slides_file=self, table_id=table_id)\
                        .fill_header(header_rows=header_rows, header_cols=header_cols, fill_color=fill_color)
            self.execute_batch_update(header_request)
        print('Created table in page {page} with ID {table}.'.format(page=page_id, table=table_id))
        return table_id   
            
    def df_to_table(self, df, page_id, header=True,
                    header_rows=1, header_cols=0, fill_color='DARK1',
                    text_color='LIGHT1', text_bold=True, text_font='', text_size=18):
        
        assert isinstance(df, pd.DataFrame), 'df must be a pandas DataFrame.'
        if page_id not in self.slides_ids:
            raise ValueError('page_id must be an existing ID of a slide in this presentation.')
        
        # Convert column names into first row and get number of rows and columns
        df = pd.DataFrame(np.vstack([df.columns, df]))
        n_rows = len(df.index)
        n_cols = len(df.columns)
        
        # Create table
        table_id = self.create_table(page_id=page_id, n_rows=n_rows, n_cols=n_cols, header=False)
        
        # Fill table with values from dataframe
        requests = list()
        for row in range(n_rows):
            for col in range(n_cols):
                cell = df.iloc[row, col]
                requests.append({"insertText": {"objectId": table_id,
                                                "cellLocation": {
                                                    "rowIndex": row,
                                                    "columnIndex": col},
                                                "text": str(cell),
                                                "insertionIndex": 0}})  
        
        # Add header
        if header == True:
            table = Table(slides_file=self, table_id=table_id)
            requests.append(table.fill_header(header_rows=header_rows, header_cols=header_cols, fill_color=fill_color))
            requests.append(table.color_text_header(header_rows=header_rows, header_cols=header_cols,
                                                   text_color=text_color, text_bold=text_bold,
                                                   text_font=text_font, text_size=text_size))

        self.execute_batch_update(requests)

        return table_id 
        
        
        

    

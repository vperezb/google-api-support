from dev import utils
from numpy import isnan

class Table:
    
    def __init__(self, slides_file, table_id):
        self.file = slides_file
        self.table_id = table_id
        
        # Table info
        element_info = self.file.find_element(element_id=self.table_id, element_kinds = ['table'])
        table_info = list(element_info.values())[0].get('table')
        self.n_rows = table_info.get('rows')
        self.n_cols = table_info.get('columns')
         
    @classmethod   
    def create(cls, page_id, n_rows, n_cols):
        requests = [{"createTable": {"elementProperties": {"pageObjectId": page_id},
                        "rows": n_rows,
                        "columns": n_cols}}]
        return requests
    
    def fill_cells(self, row_span, col_span, rgb_color):
        requests = [{"updateTableCellProperties": {"objectId": self.table_id,
                                            "tableRange": {"location": {"rowIndex": 0,
                                                                        "columnIndex": 0},
                                                    "rowSpan": row_span,
                                                    "columnSpan": col_span}, 
                                        "tableCellProperties": {"tableCellBackgroundFill": {"solidFill": 
                                                                        {"color": {"rgbColor": rgb_color}}}},
                                        "fields": "tableCellBackgroundFill.solidFill.color"}}]
        return requests
    
    def color_text_cell(self, row, col, rgb_color, bold=True, font='', size=18):
        # https://developers.google.com/slides/api/reference/rest/v1/presentations.pages/text
        # The font family can be any font from the Font menu in Slides or from Google Fonts . If the font name is unrecognized, the text is rendered in Arial . 
        if font == '':
            fonts = self.file.master_fonts
            if fonts != []:
                font = fonts[0]
            else:
                font = 'Arial'
        requests = [{"updateTextStyle": {"objectId": self.table_id,
                                                     "cellLocation": {
                                                         "rowIndex": row,
                                                         "columnIndex": col},
                                                     "style": {
                                                         "foregroundColor": {
                                                             "opaqueColor": {
                                                                 "rgbColor": rgb_color}},
                                                         "bold": bold,
                                                         "fontFamily": font,
                                                         "fontSize": {
                                                             "magnitude": size,
                                                             "unit": "PT"}},
                                                     "textRange": {
                                                         "type": "ALL"},
                                                     "fields": "foregroundColor,bold,fontFamily,fontSize"}}]    
        return requests    
        
    def fill_header(self, header_rows=1, header_cols=0, fill_color='DARK1'):
        if isinstance(fill_color, dict):
            assert all([fill_color.get('red') is None, fill_color.get('green') is None, fill_color.get('blue') is None]), 'At least one of red, green, blue needs to be provided in the dictionary.'
            rgb_color = {key:float(value) for key, value in fill_color.items() if key in ['red', 'green', 'blue'] and not (value is None or isnan(value))}
            
        elif isinstance(fill_color, str):
            rgb_color = utils.validate_color(slides_file=self.file, color_type=fill_color)
        else:
            raise ValueError('fill_color needs to be either a dictionary with values for red, green, blue or a type from master colors.')
                
        requests = self.fill_cells(row_span=header_rows, col_span=self.n_cols, rgb_color=rgb_color)

        if header_cols > 0:
            requests += self.fill_cells(row_span=self.n_rows, col_span=header_cols, rgb_color=rgb_color)
            
        return requests
    
    def color_text_header(self, header_rows=1, header_cols=0, 
                          text_color='LIGHT1', text_bold=True,
                          text_font='', text_size=18):
        
        if isinstance(text_color, dict):
            assert all([text_color.get('red') is None, text_color.get('green') is None, text_color.get('blue') is None]), 'At least one of red, green, blue needs to be provided in the dictionary.'
            rgb_color = {key:float(value) for key, value in text_color.items() if key in ['red', 'green', 'blue'] and not (value is None or isnan(value))}
            
        elif isinstance(text_color, str):
            rgb_color = utils.validate_color(slides_file=self.file, color_type=text_color)
        else:
            raise ValueError('text_color needs to be either a dictionary with values for red, green, blue or a type from master colors.')

        requests = list()
        for row in range(header_rows):
            for col in range(self.n_cols):
                requests += self.color_text_cell(row=row, col=col, rgb_color=rgb_color, 
                                                 bold=text_bold, font=text_font, size=text_size)
        for col in range(header_cols):
            for row in range(self.n_rows):
                requests += self.color_text_cell(row=row, col=col, rgb_color=rgb_color, 
                                                 bold=text_bold, font=text_font, size=text_size)   
                     
        return requests
        
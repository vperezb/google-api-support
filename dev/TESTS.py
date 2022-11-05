########################################################################## 
# This file is to check that the class GoogleDriveFile works as expected #
########################################################################## 
# from msilib.schema import ServiceControl
import os

# Credentials
ROOT_DIR=os.getcwd()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".credentials/service_credentials.json")

from dev import drive
from dev import sheets
from dev import slides
import pandas as pd
import numpy as np

#########
# Drive # 
#########

# General file #
################

# Initialising file with file id
file_id = '1VN9ERFogXy5TCVfHOe1xdK-nNm_mL4y3'
file_with_id = drive.GoogleDriveFile(file_id=file_id)
vars(file_with_id)

# Creating new file with copied permissions
file_created = drive.GoogleDriveFile.create(file_name='Class Test', 
                                            mime_type='application/vnd.google-apps.document', 
                                            parent_folder_id='1SNyrByFiT--CqHW3s0IWHGmXN7G_2o7H', 
                                            transfer_permissions=True)

# Insert permission method is already used in the above example

# Open url
file_created.open()

# Download file (file_with_id which is a picture)
file_with_id.download()

# Export file
file_created.export()

# Move file
drive.GoogleDriveFile(file_id='10oD3qkgnGpen4Qtdu7Dk_fD9HiC-3qZxQXKsifWO0W8').move(destination_folder_id='15nKbMkj8hh0G4a3xQuuKnpTKPRS6QUqR')

# Delete file
drive.GoogleDriveFile(file_id='1Tme3hLY8uCjQfFuN-_u5CW_T6jYUvaA4EWpuIgl6kls').delete()

# Copy file with permissions
file_copied = file_created.copy(new_file_name='Class Test - Copy',
                                supports_all_drives=True,
                                transfer_permissions=True,
                                sendNotificationEmail=False)

# Rename file
file_created.rename(new_file_name='Another class test')

# Folder #
##########

# Initialise folder object with id
folder = drive.GoogleDriveFolder(file_id='1SNyrByFiT--CqHW3s0IWHGmXN7G_2o7H')
folder.permissions

# Show info for Google Docs files in the folder
folder.children(which='specific', mime_type='application/vnd.google-apps.document')

# Upload file into folder
folder.upload_file(origin_path='../../Desktop/IMG_1729.JPG',
                   start_url=True)

#########
# sheets #
##########

# Initialize with file id
spreadsheet_id = '145f49AjFuS31dAw9GXYvgRlmxZIDyg0P6Z4O_052Pxw'
spreadsheet_from_id = sheets.GoogleSheets(file_id=spreadsheet_id)
vars(spreadsheet_from_id)

# Properties
spreadsheet_from_id.file_name
spreadsheet_from_id.sheets_ids
spreadsheet_from_id.sheets_names

# Sheet URl
spreadsheet_from_id.sheet_url(sheet_id=0)

# Open sheet
spreadsheet_from_id.open(sheet_id=1809942099)

# Add sheet
spreadsheet_from_id.add_sheet(sheet_name='Beginning', index=0)

# Delete sheet
spreadsheet_from_id.delete_sheet(sheet_id=681015510)

# Data from sheet
data = spreadsheet_from_id.sheet_to_df(sheet_name='Sheet3')
data

# Data to sheet
new_data = pd.DataFrame({'col1':[1, 1, 1, 1, 1],
                        'col2':[3, 3, 3, 3, 3],
                        'col3':[4, 5, np.NaN, 5, 5]})
spreadsheet_from_id.df_to_sheet(df=new_data, sheet_name='New sheet')

# Clear sheet
spreadsheet_from_id.clear_sheet(sheet_name='Sheet1')

# Create new spreadsheet
new_spreadsheet = sheets.GoogleSheets.create(file_name='It works',
                                             parent_folder_id='1SNyrByFiT--CqHW3s0IWHGmXN7G_2o7H',
                                             transfer_permissions=True)

from GoogleApiSupport import slides

shapes = slides.get_all_shapes_placeholders(presentation_id='1lg-skFt676nQdQ0tUbb_3y4F8_82-hKacEj23unuxdk')


presentation = slides.GoogleSlides(file_id='1lg-skFt676nQdQ0tUbb_3y4F8_82-hKacEj23unuxdk')




# Add table
page_id='SLIDES_API1209340472_0'
n_rows=3
n_cols=11
header=True
color='DARK1'

from dev.slide_table import Table
from dev import utils

fill_request = Table(slides_file=presentation, table_id='SLIDES_API1459332045_0').fill_header()
text_request = Table(slides_file=presentation, table_id='SLIDES_API1459332045_0').color_text_header()

presentation.execute_batch_update(text_request)

df = pd.DataFrame({'var1': [1, 2, 3],
                   'var2': [4, 5, 6],
                   'var3': [7, 8 , 9]})

presentation.df_to_table(df=df, page_id=page_id, text_color={'red':1, 'green':1, 'blue': 1}, fill_color={'red':0, 'green':0, 'blue': 0})

table_id='SLIDES_API414104160_0'
df = pd.DataFrame(np.vstack([df.columns, df]))
n_rows = len(df.index)
n_cols = len(df.columns)


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
        
table = Table(slides_file=presentation, table_id=table_id)        

# Fill cells
if header == True:
    requests.append(table.fill_header(header_rows=header_rows, header_cols=header_cols, fill_color=header_fill_color))
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
requests.append(table.fill_cells(row_span=row_span, col_span=col_span, 
                                    rgb_color=fill, 
                                    row_index=row_index, col_index=col_index))






header_rows=1
header_cols=1

n_rows=4
n_cols=3

from dev.utils import validate_color
rgb_color = validate_color(presentation, text_color)
text_font='Arial'

from itertools import product

header_rows=1
header_cols=1

result = list()
cell_indexes = list(product(list(range(n_rows)), list(range(n_cols))))
for cell in cell_indexes:
    cell_type = True if cell[0] < header_rows or cell[1] < header_cols else False
    result.append(cell_type)

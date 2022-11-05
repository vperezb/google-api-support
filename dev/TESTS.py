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
page_id='SLIDES_API1912518732_0'
n_rows=3
n_cols=11
header=True
color='DARK1'



df = pd.DataFrame({'var1': [1, 2, 3],
                   'var2': [4, 5, 6],
                   'var3': [7, 8 , 9]})

presentation.df_to_table(df=df, page_id=page_id)


n_rows=len(df.index)
n_cols=len(df.columns)

[1, 2, 3] + [4, 5, 6]





requests = list()
for row in range(n_rows):
    for col in range(n_cols):
        cell = df.iloc[row, col]
        requests.append({"insertText": {"objectId": tbl_id,
                                        "cellLocation": {
                                            "rowIndex": row,
                                            "columnIndex": col},
                                        "text": cell,
                                        "insertionIndex": 0}})  

# dict_keys(['objectId', 'pageType', 'pageElements', 'pageProperties', 'masterProperties'])
fonts = list()
page_elements = presentation._GoogleSlides__presentation_info.get('masters')[0].get('pageElements')
for element in page_elements:
    text = element.get('shape').get('text')
    if text is not None:
        for text_element in text.get('textElements'):
            text_run = text_element.get('textRun')
            if text_run is not None:
                fonts.append(text_run.get('style').get('fontFamily'))
fonts = list(set(fonts)) # To get unique values
      
                
[0].get('shape').get('text').get('textElements')[1]
text_element.get('textRun').get('style').get('fontFamily')

get('paragraphMarker').get('style')
get('lists')
        










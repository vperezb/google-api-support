########################################################################## 
# This file is to check that the class GoogleDriveFile works as expected #
########################################################################## 
# from msilib.schema import ServiceControl
import os

# Credentials
ROOT_DIR=os.getcwd()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".service_credentials/credentials.json")

# Doing this to import local versions
import sys
sys.path.append('../GoogleApiSupport')
from GoogleApiSupport import apis, auth
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
file_created = drive.GoogleDriveFile.create(file_name='New spreadsheet', 
                                            mime_type='application/vnd.google-apps.spreadsheet', 
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

from GoogleApiSupport import auth

shapes = slides.get_all_shapes_placeholders(presentation_id='1lg-skFt676nQdQ0tUbb_3y4F8_82-hKacEj23unuxdk')


presentation = slides.GoogleSlides(file_id='1lg-skFt676nQdQ0tUbb_3y4F8_82-hKacEj23unuxdk')


from GoogleApiSupport import auth

auth.get_service('drive', additional_apis=['sheets'])



# Credentials
import os
ROOT_DIR=os.getcwd()
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(ROOT_DIR, ".credentials/service_credentials.json")
os.environ['GOOGLE_OAUTH_CREDENTIALS'] = os.path.join(ROOT_DIR, ".oauth_credentials/credentials.json")

# Doing this to import local versions
import sys
sys.path.append('../GoogleApiSupport')
from GoogleApiSupport import apis, auth

from dev import slides
from dev import sheets
from dev import drive




slides_id = '1eHfgugjfymloWLd9IUkiJlqaVmS-VmVJdCQNl0AFT0Q'
sheets_id = '1cuNDHr7gvZeA0srrXgAHtPfC_WraWP2l_5H3SGwKICQ'

sheets_file = sheets.GoogleSheets(file_id=sheets_id)
vars(sheets_file).keys()
sheets_file._GoogleSheets__spreadsheet_info.get('sheets')[0].get('charts')[0].get('chartId')

sheets_file.download_chart(chart_id='148582788', open_file=True)

sheets_file.add_sheet(sheet_name='Testing the move')
requests = [{'updateSheetProperties': {'properties':{"sheetId": '460050652',
                                                            'index': 0},
                                       'fields': 'index'}}] 
sheets_file.execute_batch_update(requests)

sheets_file.move_sheet(sheet_id='460050652', new_index=0)

move_sheet

slides_file = slides.GoogleSlides(file_id=slides_id)
slides_file.replace_shape_with_chart(placeholder_text='chart',
                                     spreadsheet_id=sheets_id,
                                     chart_id='148582788')

slides_file.slides_ids
chart_id = slides_file.insert_chart(spreadsheet_id=sheets_id,
                                chart_id='148582788',
                                page_id='g16bd45dcd4f_0_1')


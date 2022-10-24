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

# Folder #
##########

# Initialise folder object with id
folder = drive.GoogleDriveFolder(file_id='1SNyrByFiT--CqHW3s0IWHGmXN7G_2o7H')
folder.permissions

# Show info for Google Docs files in the folder
folder.children(which='specific', mime_type='application/vnd.google-apps.document')


##########
# sheets #
##########

# Initialize with file id
spreadsheet_id = '145f49AjFuS31dAw9GXYvgRlmxZIDyg0P6Z4O_052Pxw'
spreadsheet_from_id = sheets.GoogleSheets(file_id=spreadsheet_id)
vars(spreadsheet_from_id)

# Properties
spreadsheet_from_id.sheets_ids
spreadsheet_from_id.sheets_names

# Add sheet
spreadsheet_from_id.add_sheet(sheet_name='Testing')

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
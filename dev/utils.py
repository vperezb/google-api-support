import os, sys, subprocess
import pandas as pd
from numpy import isnan
import datetime as dt
import mimetypes
import openxmllib # https://pythonhosted.org/openxmllib/mimetypes-adds.html
from GoogleApiSupport import auth
from apiclient import errors
import sys

# https://stackoverflow.com/questions/17317219/is-there-an-platform-independent-equivalent-of-os-startfile
def start_file(path):
    """Open local file.

    Args:
        path (str): Location path of file to open.
    """
    if sys.platform == "win32":
        os.startfile(path)
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path])
        
def copy_permissions(start_file, end_file, **kwargs):
    """
    Copy permissions from one file to another.

    Args:
        start_file (GoogleDriveFile, GoogleDriveFolder): File where to take permissions from.
        end_file (GoogleDriveFile, GoogleDriveFolder): File to copy permissions to.
        
    Returns:
        GoogleDriveFile: Copy of end_file with new permissions.
    """
    
    # Values of needed kwargs
    retrieve_fields = kwargs['fields'] if 'fields' in kwargs else '*'
    supports_all_drives = kwargs['supportsAllDrives'] if 'supportsAllDrives' in kwargs else False
    transfer_ownership = kwargs['transferOwnership'] if 'transferOwnership' in kwargs else False
    send_notification_email = kwargs['sendNotificationEmail'] if 'sendNotificationEmail' in kwargs and transfer_ownership == False else True
    
    # Insert permissions one by one
    for permission in start_file.permissions:
        perm_type = permission['type']
        # Ownership transfers are not supported for files and folders in shared drives. - OR maybe yes with additional arg "supportAllDrives"
        # Owndership transfer is only possible if service account has domain-wide authority
        role = 'writer' if transfer_ownership == False and permission['role'] == 'owner' else permission['role']
        # value: User or group e-mail address, domain name or None for  for 'anyone' or 'default' type.
        email_address = permission['emailAddress'] if perm_type in ('user', 'group') else None
        domain = permission['domain'] if perm_type == 'domain' else None
            
        try:
            end_file.share(perm_type=perm_type,
                           role=role,
                           email_address=email_address,
                           domain=domain,
                           supportsAllDrives=supports_all_drives,
                           transferOwnership=transfer_ownership,
                           sendNotificationEmail=send_notification_email)
        except errors.HttpError as error:
            print('An error occurred: %s' % error)
            
        return end_file
            
def drive_about(fields='*'):
    """Function to get information about the Drive and the system capabilities.
    Uses the following: https://developers.google.com/drive/api/v3/reference/about/get

    Args:
        fields (str, optional): Which fields to extract. Defaults to '*', i.e. all the fields.

    Returns:
        dict: Dictionary with the requested fields.
    """
    service = auth.get_service("drive")
    drive_about = service.about().get(fields='*').execute()
    return drive_about

def google_export_types():
    """Get dataframe of export MIME types for Google Workspace files.
    
    Beside the MIME type, it will include the extension and a default option.
    Defaults:
    - Google Docs: .docx
    - Google Drawings: .jpeg
    - Google Form: .zip
    - Google Slides: .pptx
    - Google Script: ...
    - Google Sheets: .xlsx
    """
    
    # Getting drive export formats
    export_dict = drive_about(fields='exportFormats')
    export_formats = pd.DataFrame.from_dict(data=export_dict.get('exportFormats'), orient='index').reset_index()
    export_formats = export_formats.melt(id_vars='index', var_name='order', value_name='to_mime_type')
    export_formats.drop(columns='order', inplace=True)
    export_formats.rename(columns={'index': 'from_mime_type'}, inplace=True)
    export_formats.dropna(inplace=True)
    
    # Map MIME types to extensions
    mime_types_map = {v: k for k, v in mimetypes.types_map.items()}
    export_formats['extension'] = export_formats['to_mime_type'].map(mime_types_map)

    # Set default formats for the export
    export_defaults = {'application/vnd.google-apps.document':['application/vnd.openxmlformats-officedocument.wordprocessingml.document',True],
                    'application/vnd.google-apps.spreadsheet':['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',True],
                    'application/vnd.google-apps.presentation':['application/vnd.openxmlformats-officedocument.presentationml.presentation',True],
                    'application/vnd.google-apps.drawing':['image/jpeg',True],
                    'application/vnd.google-apps.jam':['application/pdf',True],
                    'application/vnd.google-apps.script':['application/vnd.google-apps.script+json',True],
                    'application/vnd.google-apps.form':['application/zip',True],
                    'application/vnd.google-apps.site':['text/plain',True]}
    export_defaults = pd.DataFrame.from_dict(data=export_defaults,orient='index').reset_index()
    export_defaults.columns = ['from_mime_type', 'to_mime_type', 'default']
    export_formats = export_formats.merge(right=export_defaults, how='left', on=['from_mime_type', 'to_mime_type'])
    # Missing info 
    missing_info = {'application/x-vnd.oasis.opendocument.spreadsheet': '.ods',
                    'application/vnd.google-apps.script+json':'json'}
    export_formats['extension'].mask(cond=export_formats['extension'].isnull(),
                                     other=export_formats['to_mime_type'].map(missing_info),
                                     inplace=True)
    export_formats['default'].fillna(value=False, inplace=True)
    export_formats.sort_values(by=['from_mime_type', 'default', 'to_mime_type'], 
                               ascending=[True, False, True],
                               inplace=True)
    
    return export_formats

# https://developers.google.com/slides/api/concepts/page-elements
def page_element_kinds():
    return ['elementGroup', 'shape', 'image', 'video', 'line', 'table', 'wordArt', 'sheetsChart']

def get_rgb_color(color_dict):
    assert not all([color_dict.get('red') is None, color_dict.get('green') is None, color_dict.get('blue') is None]), 'At least one of red, green, blue needs to be provided in the dictionary.'
    rgb_color = {key:float(value) for key, value in color_dict.items() if key in ['red', 'green', 'blue'] and not (value is None or isnan(value))}
    return rgb_color

def validate_color(slides_file, color_type):
    """Check if color type is inside the file master colors.

    Args:
        slides_file (GoogleSlides): Object of GoogleSlides class.
        color_type (str): Type of color.

    Returns:
        dict: Dictionary with RGB colors.
    """
    color_styles = slides_file.master_colors
    row = color_styles[color_styles['type'] == color_type]
    assert not row.empty, 'Color type needs to be ones available inside the master colors.'
    rgb_color = {}
    if not isnan(float(row['red'])):
        rgb_color.update({'red':float(row['red'])})
    if not isnan(float(row['green'])):
        rgb_color.update({'green':float(row['green'])})                  
    if not isnan(float(row['blue'])):
        rgb_color.update({'blue':float(row['blue'])})
    return rgb_color

def from_timestamp_to_rfc339(timestamp_text, start_format='%Y-%m-%d %H:%M:%S'):
    datetime_obj = dt.datetime.strptime(timestamp_text, start_format)
    rfc339_text = datetime_obj('%Y-%m-%dT%H:%M:%S.000Z')
    return rfc339_text






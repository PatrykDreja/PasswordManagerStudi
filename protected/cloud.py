# cloud.py
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os
from paths import get_local_path

def authenticate():
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Otwiera przeglądarkę do logowania
    return GoogleDrive(gauth)

def upload_file(filename):
    drive = authenticate()
    filepath = get_local_path(filename)
    file_drive = drive.CreateFile({'title': filename})
    file_drive.SetContentFile(filepath)
    file_drive.Upload()
    print(f"{filename} uploaded to Google Drive.")

def download_file(filename):
    drive = authenticate()
    file_list = drive.ListFile({'q': f"title='{filename}'"}).GetList()
    if file_list:
        file_drive = file_list[0]
        file_drive.GetContentFile(get_local_path(filename))
        print(f"{filename} downloaded from Google Drive.")
    else:
        print(f"{filename} not found in Google Drive.")
